import os
import re
import uuid
import requests
import yfinance as yf
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import motor.motor_asyncio

from fastapi.responses import JSONResponse

# --- Helper Module Imports ---
from utils import cleanup_files
from preprocess import SECFilingCleaner
from vector_store import VectorStore
from llm import get_llama3_groq_response, get_gemini_flash_llm, create_vector_query_prompt, create_synthesis_prompt

# --- Load Environment Variables ---
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
PINECONE_INDEX_NAME = "sec-filings-agent"
CACHE_DURATION_HOURS = 24

# --- API & DB Setup ---
app = FastAPI(title="SEC Filing Analysis AI")
origins = ["http://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- MongoDB Client Setup with SSL Fix ---
if not MONGO_URI:
    raise ValueError("MONGO_URI not found.")

# Add TLS parameters to fix SSL handshake issue
client = motor.motor_asyncio.AsyncIOMotorClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=True,  # For development - remove in production
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000
)
db = client.sec_filing_db
news_cache_collection = db.news_cache
key_info_cache_collection = db.key_info_cache

# --- Global Initializations ---
if not all([PINECONE_API_KEY, ALPHA_VANTAGE_API_KEY, NEWS_API_KEY]):
    raise ValueError("API keys are missing.")
vector_store = VectorStore(pinecone_api_key=PINECONE_API_KEY, index_name=PINECONE_INDEX_NAME)

# --- Pydantic Models ---
class PreprocessRequest(BaseModel): 
    ticker: str

class AskRequest(BaseModel): 
    document_id: str
    ticker: str
    question: str

# --- Health Check Endpoint ---
@app.get("/", tags=["Health Check"])
async def read_root(): 
    try:
        # Test MongoDB connection
        await db.command('ping')
        return {"status": "API is running", "mongodb": "connected"}
    except Exception as e:
        return {"status": "API is running", "mongodb": f"error: {str(e)}"}

# --- CACHED NEWS ENDPOINTS ---
@app.get("/news/general", tags=["News"])
async def get_general_news(period: str = "week", limit: int = 10):
    query_key = f"general_{period}"
    cache_expiry = datetime.utcnow() - timedelta(hours=CACHE_DURATION_HOURS)
    
    try:
        cached_data = await news_cache_collection.find_one({
            "query_key": query_key, 
            "fetched_at": {"$gte": cache_expiry}
        })
        
        if cached_data:
            print(f"✅ Cache HIT for general news (period: {period})")
            cached_data.pop("_id", None)
            return cached_data.get("data")
    except Exception as e:
        print(f"⚠️ MongoDB cache read failed: {e}. Fetching fresh data...")

    print(f"⚠️ Cache MISS for general news (period: {period}).")
    from_date = (datetime.now() - timedelta(days=7 if period == "week" else 30)).strftime('%Y-%m-%d')
    url = f"https://newsapi.org/v2/everything?q=finance&from={from_date}&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}&pageSize={limit}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        news_data = response.json()

        if news_data.get("status") != "ok" or "articles" not in news_data:
            print(f"ERROR: Invalid response from NewsAPI: {news_data}")
            raise HTTPException(status_code=502, detail="Received invalid data from news provider.")

        formatted_response = {"articles": news_data.get("articles", [])}
        
        # Try to cache, but don't fail if MongoDB is down
        try:
            await news_cache_collection.update_one(
                {"query_key": query_key},
                {"$set": {"data": formatted_response, "fetched_at": datetime.utcnow()}},
                upsert=True
            )
        except Exception as cache_error:
            print(f"⚠️ Failed to cache data: {cache_error}")
        
        return formatted_response
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {e}")

@app.get("/news/{ticker}", tags=["News"])
async def get_ticker_news(ticker: str, limit: int = 10):
    query_key = ticker.upper()
    cache_expiry = datetime.utcnow() - timedelta(hours=CACHE_DURATION_HOURS)
    
    try:
        cached_data = await news_cache_collection.find_one({
            "query_key": query_key, 
            "fetched_at": {"$gte": cache_expiry}
        })
        
        if cached_data:
            print(f"✅ Cache HIT for ticker: {ticker}")
            cached_data.pop("_id", None)
            return cached_data.get("data")
    except Exception as e:
        print(f"⚠️ MongoDB cache read failed: {e}. Fetching fresh data...")
        
    print(f"⚠️ Cache MISS for ticker: {ticker}.")
    url = f"https://newsapi.org/v2/everything?q={ticker}&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}&pageSize={limit}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        news_data = response.json()

        if news_data.get("status") != "ok" or "articles" not in news_data:
            print(f"ERROR: Invalid response from NewsAPI for {ticker}: {news_data}")
            raise HTTPException(status_code=502, detail="Received invalid data from news provider.")

        formatted_response = {"articles": news_data.get("articles", [])}
        
        try:
            await news_cache_collection.update_one(
                {"query_key": query_key},
                {"$set": {"data": formatted_response, "fetched_at": datetime.utcnow()}},
                upsert=True
            )
        except Exception as cache_error:
            print(f"⚠️ Failed to cache data: {cache_error}")
        
        return formatted_response
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news for {ticker}: {e}")

@app.post("/preprocess-and-index", tags=["Processing"])
def preprocess_and_index(request: PreprocessRequest, background_tasks: BackgroundTasks):
    ticker = request.ticker.upper()
    existing_doc_id = vector_store.check_if_ticker_exists(ticker)
    
    if existing_doc_id:
        return {
            "message": f"Filing for {ticker} already exists. Using cached document.",
            "document_id": existing_doc_id
        }

    print(f"No existing document for {ticker}. Starting fresh processing.")
    output_filename = f"cleaned_{ticker}_financial_data.xml"
    sec_filings_dir = "sec-edgar-filings" 
    background_tasks.add_task(cleanup_files, temp_file_path=output_filename, temp_dir_path=sec_filings_dir)
    doc_id = str(uuid.uuid4())

    try:
        cleaner = SECFilingCleaner(ticker=ticker)
        cleaner.process_and_save(output_filename=output_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clean the SEC filing for {ticker}: {e}")
    
    try:
        vector_store.embed_and_upsert(
            file_path=output_filename, 
            document_id=doc_id,
            ticker=ticker  
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index data for {ticker}: {e}")

    return {
        "message": f"Successfully processed and indexed 10-K filing for {ticker}.",
        "document_id": doc_id
    }

@app.post("/ask", tags=["Agent"])
def ask_agent(request: AskRequest):
    try:
        query_prompt = create_vector_query_prompt(request.question, num_queries=3)
        expanded_queries_text = get_llama3_groq_response(query_prompt)
        search_queries = [re.sub(r'^\d+\.\s*', '', q).strip() for q in expanded_queries_text.split('\n') if q.strip()]
        if not search_queries: 
            search_queries = [request.question]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed during query expansion: {e}")

    try:
        all_context = ""
        for query in search_queries:
            results = vector_store.query(
                query_text=query, 
                document_id=request.document_id, 
                top_k=3
            )
            for match in results:
                if match.get('metadata') and match['metadata'].get('text'):
                    all_context += match['metadata']['text'] + "\n\n"
        
        if not all_context.strip():
            return {"answer": "Could not find relevant information in the specified financial document for your query."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed during vector search: {e}")

    try:
        synthesis_prompt = create_synthesis_prompt(question=request.question, context=all_context)
        final_answer = get_gemini_flash_llm(synthesis_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed during answer synthesis: {e}")

    return {"ticker": request.ticker, "question": request.question, "answer": final_answer}

# --- STOCK DATA ENDPOINTS ---
@app.get("/stock/{ticker}/key-info", tags=["Stock Data"])
async def get_stock_key_info(ticker: str):
    query_key = ticker.upper()
    cache_expiry = datetime.utcnow() - timedelta(hours=CACHE_DURATION_HOURS)
    
    try:
        cached_data = await key_info_cache_collection.find_one({
            "query_key": query_key, 
            "fetched_at": {"$gte": cache_expiry}
        })
        
        if cached_data:
            print(f"✅ Cache HIT for key info: {ticker}")
            cached_data.pop("_id", None)
            return cached_data.get("data")
    except Exception as e:
        print(f"⚠️ MongoDB cache read failed: {e}. Fetching fresh data...")

    print(f"⚠️ Cache MISS for key info: {ticker}. Fetching from API.")
    
    # Try Alpha Vantage first
    try:
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "Note" in data or "Information" in data:
            print(f"⚠️ Alpha Vantage rate limit hit for {ticker}. Falling back to yfinance.")
            raise Exception("Rate limited")
        
        if data and data.get("MarketCapitalization"):
            print(f"✅ Got valid data from Alpha Vantage for {ticker}")
            try:
                await key_info_cache_collection.update_one(
                    {"query_key": query_key}, 
                    {"$set": {"data": data, "fetched_at": datetime.utcnow(), "source": "alpha_vantage"}}, 
                    upsert=True
                )
            except Exception as cache_error:
                print(f"⚠️ Failed to cache data: {cache_error}")
            return data
        else:
            raise Exception("Invalid data")
            
    except Exception as e:
        print(f"Alpha Vantage failed for {ticker}: {e}. Using yfinance fallback.")
    
    # Fallback to yfinance
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        fallback_data = {
            "Symbol": ticker.upper(),
            "MarketCapitalization": str(info.get("marketCap", 0)),
            "PERatio": str(info.get("trailingPE", "N/A")),
            "DividendYield": str(info.get("dividendYield", "0")),
            "Beta": str(info.get("beta", "N/A")),
            "AnalystTargetPrice": str(info.get("targetMeanPrice", "N/A")),
            "52WeekHigh": str(info.get("fiftyTwoWeekHigh", "N/A")),
            "52WeekLow": str(info.get("fiftyTwoWeekLow", "N/A")),
            "Name": info.get("longName", ticker.upper()),
            "_source": "yfinance"
        }
        
        print(f"✅ Successfully fetched data from yfinance for {ticker}")
        
        try:
            await key_info_cache_collection.update_one(
                {"query_key": query_key}, 
                {"$set": {"data": fallback_data, "fetched_at": datetime.utcnow(), "source": "yfinance"}}, 
                upsert=True
            )
        except Exception as cache_error:
            print(f"⚠️ Failed to cache data: {cache_error}")
        
        return fallback_data
        
    except Exception as yf_error:
        print(f"❌ Both Alpha Vantage and yfinance failed for {ticker}: {yf_error}")
        raise HTTPException(
            status_code=404, 
            detail=f"Could not fetch key info for {ticker} from any source."
        )

@app.get("/stock/{ticker}/intraday-data", tags=["Stock Data"])
def get_stock_intraday_data(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="7d", interval="5m")
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"Could not retrieve intraday data for {ticker}.")
        
        hist.reset_index(inplace=True)
        time_col = 'Datetime' if 'Datetime' in hist.columns else 'index'
        if time_col not in hist.columns:
            raise ValueError("Expected time column not found in intraday data.")

        hist['x'] = hist[time_col].apply(lambda ts: ts.isoformat())
        data = hist.rename(columns={"Open": "o", "High": "h", "Low": "l", "Close": "c"})
        result = data[['x', 'o', 'h', 'l', 'c']].to_dict('records')
        return JSONResponse(content=result)
    except Exception as e:
        print(f"ERROR in intraday-data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process intraday data: {e}")

@app.get("/stock/{ticker}/historical-data", tags=["Stock Data"])
def get_stock_historical_data(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No yfinance historical data for {ticker}.")
        
        hist.reset_index(inplace=True)
        if 'Date' not in hist.columns:
            raise ValueError("Expected 'Date' column not found in historical data.")
            
        hist['x'] = hist['Date'].apply(lambda ts: ts.isoformat())
        data = hist.rename(columns={"Open": "o", "High": "h", "Low": "l", "Close": "c"})
        result = data[['x', 'o', 'h', 'l', 'c']].to_dict('records')
        return JSONResponse(content=result)
    except Exception as e:
        print(f"ERROR in historical-data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process historical data: {e}")