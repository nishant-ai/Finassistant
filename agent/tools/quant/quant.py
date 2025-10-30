import yfinance as yf
import pandas as pd
from functools import lru_cache
from langchain_core.tools import tool
from typing import List

@lru_cache(maxsize=128)
def get_ticker(ticker: str) -> yf.Ticker:
    """
    Fetches and caches the yfinance.Ticker object to avoid redundant API calls.
    """
    return yf.Ticker(ticker)

# --- 1. Valuation Tools ---
@tool
def get_valuation_metrics(ticker: str) -> str:
    """
    Fetches key valuation ratios to help determine if a stock is overvalued or
    undervalued. Use this tool when a user asks about a company's
    valuation, P/E ratio, P/S ratio, or PEG ratio.
    """
    try:
        stock = get_ticker(ticker)
        info = stock.info
        
        pe_ratio = info.get('trailingPE', 'N/A')
        ps_ratio = info.get('priceToSalesTrailing12Months', 'N/A')
        peg_ratio = info.get('pegRatio', 'N/A')
        ev_to_ebitda = info.get('enterpriseToEbitda', 'N/A')

        response = f"**Valuation Metrics for {ticker.upper()}**\n"
        response += f"- P/E Ratio (TTM): {pe_ratio if pe_ratio == 'N/A' else f'{pe_ratio:.2f}'}\n"
        response += f"- P/S Ratio (TTM): {ps_ratio if ps_ratio == 'N/A' else f'{ps_ratio:.2f}'}\n"
        response += f"- PEG Ratio: {peg_ratio if peg_ratio == 'N/A' else f'{peg_ratio:.2f}'}\n"
        response += f"- EV/EBITDA: {ev_to_ebitda if ev_to_ebitda == 'N/A' else f'{ev_to_ebitda:.2f}'}\n"
        
        return response
    except Exception as e:
        return f"Error fetching valuation for {ticker.upper()}: {e}. Data may be unavailable."


# --- 2. Profitability & Growth Tools ---
@tool
def get_profitability_metrics(ticker: str) -> str:
    """
    Fetches key profitability ratios to assess how efficiently a company
    generates profit. Use this when a user asks about a company's
    profitability, profit margin, or returns (ROA, ROE).
    """
    try:
        stock = get_ticker(ticker)
        info = stock.info
        
        profit_margin = info.get('profitMargins', 0)
        operating_margin = info.get('operatingMargins', 0)
        roa = info.get('returnOnAssets', 0)
        roe = info.get('returnOnEquity', 0)

        response = f"**Profitability Metrics for {ticker.upper()}**\n"
        response += f"- Profit Margin: {profit_margin * 100:.2f}%\n"
        response += f"- Operating Margin: {operating_margin * 100:.2f}%\n"
        response += f"- Return on Assets (ROA): {roa * 100:.2f}%\n"
        response += f"- Return on Equity (ROE): {roe * 100:.2f}%\n"
        
        return response
    except Exception as e:
        return f"Error fetching profitability for {ticker.upper()}: {e}. Data may be unavailable."

@tool
def get_historical_growth(ticker: str) -> str:
    """
    Calculates the Year-over-Year (YoY) revenue and net income growth for the
    last 3 years. Use this when a user asks about a company's historical
    growth, revenue trend, or earnings growth.
    Returns the data in a Markdown table.
    """
    try:
        stock = get_ticker(ticker)
        financials = stock.financials
        
        if 'Total Revenue' not in financials.index or 'Net Income' not in financials.index:
            return f"Could not retrieve full financial data for {ticker.upper()}."

        # Select relevant rows
        data = financials.loc[['Total Revenue', 'Net Income']]
        
        # Calculate YoY Growth
        growth_data = data.pct_change(axis='columns', periods=-1) * 100
        
        # Format the data for display
        df = pd.DataFrame({
            "Metric": ["Total Revenue", "Revenue Growth (YoY)", "Net Income", "Net Income Growth (YoY)"]
        })
        
        for col in data.columns:
            year = col.strftime('%Y')
            df[year] = [
                f"${data[col]['Total Revenue']/1e6:.2f}M",
                f"{growth_data[col]['Total Revenue']:.2f}%" if col in growth_data.columns else "N/A",
                f"${data[col]['Net Income']/1e6:.2f}M",
                f"{growth_data[col]['Net Income']:.2f}%" if col in growth_data.columns else "N/A"
            ]
        
        return f"**Historical Growth for {ticker.upper()}**\n{df.to_markdown(index=False)}"
        
    except Exception as e:
        return f"Error fetching historical growth for {ticker.upper()}: {e}."

# --- 4. Market Performance Tools ---
@tool
def get_stock_price_summary(ticker: str) -> str:
    """
    Gets a summary of the stock's recent price performance and volatility.
    Use this when a user asks about the stock price, 52-week range,
    moving averages, or beta.
    """
    try:
        stock = get_ticker(ticker)
        info = stock.info

        response = f"**Market Performance for {ticker.upper()}**\n"
        response += f"- Current Price: ${info.get('currentPrice', 'N/A'):.2f}\n"
        response += f"- 52-Week High: ${info.get('fiftyTwoWeekHigh', 'N/A'):.2f}\n"
        response += f"- 52-Week Low: ${info.get('fiftyTwoWeekLow', 'N/A'):.2f}\n"
        response += f"- 50-Day Moving Avg: ${info.get('fiftyDayAverage', 'N/A'):.2f}\n"
        response += f"- 200-Day Moving Avg: ${info.get('twoHundredDayAverage', 'N/A'):.2f}\n"
        response += f"- Beta (Volatility): {info.get('beta', 'N/A'):.2f}\n"

        return response
    except Exception as e:
        return f"Error fetching market performance for {ticker.upper()}: {e}."

@tool
def get_analyst_recommendations(ticker: str) -> str:
    """
    Fetches the latest analyst recommendations and price targets.
    Use this when a user asks what analysts think about a stock
    or what its price target is. Returns data as a Markdown table.
    """
    try:
        stock = get_ticker(ticker)
        recs = stock.recommendations
        
        if recs is None or recs.empty:
            return f"No analyst recommendations found for {ticker.upper()}."
        
        # Get the last 10 recommendations
        latest_recs = recs.tail(10).sort_index(ascending=False)
        
        # Format for display
        latest_recs = latest_recs.reset_index()
        latest_recs['Date'] = latest_recs['Date'].dt.strftime('%Y-%m-%d')
        
        # Select and rename columns for clarity
        df = latest_recs[['Date', 'Firm', 'To Grade', 'Target Price']]
        df.columns = ['Date', 'Firm', 'Recommendation', 'Target Price']
        
        return f"**Latest Analyst Recommendations for {ticker.upper()}**\n{df.to_markdown(index=False)}"

    except Exception as e:
        return f"Error fetching analyst recommendations for {ticker.upper()}: {e}."

# --- 5. Comparative Tool ---
@tool
def compare_key_metrics(tickers: List[str]) -> str:
    """
    Compares multiple companies side-by-side on key metrics.
    This is the most powerful tool for peer comparison.
    Use this when a user asks to compare two or more companies.
    The input MUST be a list of stock tickers, e.g., ['AAPL', 'MSFT', 'GOOGL'].
    Returns a Markdown table.
    """
    if not tickers or len(tickers) < 2:
        return "Error: Please provide at least two tickers to compare."
        
    data = []
    for ticker in tickers:
        try:
            stock = get_ticker(ticker)
            info = stock.info
            
            # Fetch metrics, with fallbacks
            pe_ratio = info.get('trailingPE', 'N/A')
            ps_ratio = info.get('priceToSalesTrailing12Months', 'N/A')
            profit_margin = info.get('profitMargins', 'N/A')
            roe = info.get('returnOnEquity', 'N/A')
            
            data.append({
                "Ticker": ticker.upper(),
                "P/E Ratio": f"{pe_ratio:.2f}" if isinstance(pe_ratio, float) else "N/A",
                "P/S Ratio": f"{ps_ratio:.2f}" if isinstance(ps_ratio, float) else "N/A",
                "Profit Margin": f"{profit_margin*100:.2f}%" if isinstance(profit_margin, float) else "N/A",
                "Return on Equity (ROE)": f"{roe*100:.2f}%" if isinstance(roe, float) else "N/A"
            })
        except Exception:
            data.append({
                "Ticker": ticker.upper(),
                "P/E Ratio": "Error",
                "P/S Ratio": "Error",
                "Profit Margin": "Error",
                "Return on Equity (ROE)": "Error"
            })
            
    # Use pandas to easily convert the list of dicts to a Markdown table
    df = pd.DataFrame(data)
    return df.to_markdown(index=False)
