from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent.graph import create_agent_graph
from agent.tools import (
    get_valuation_metrics,
    get_profitability_metrics,
    get_historical_growth,
    get_stock_price_summary,
    get_analyst_recommendations,
    compare_key_metrics,
    get_stock_news,
    get_market_news,
    get_full_article_content,
    get_sec_filing_summary,
    get_sec_financial_data,
    search_sec_filing,
    compare_sec_filings,
    semantic_search_sec_filing,
    semantic_search_news,
    multi_document_analysis,
    index_news_for_ticker,
    rag_system_status,
    web_search,
    financial_web_search,
    real_time_market_search,
    search_and_summarize
)

load_dotenv()

def run_agent(query: str) -> str:
    tools = [
        # Quantitative Analysis Tools
        get_valuation_metrics,
        get_profitability_metrics,
        get_historical_growth,
        get_stock_price_summary,
        get_analyst_recommendations,
        compare_key_metrics,

        # News Tools (Real-Time)
        get_stock_news,
        get_market_news,
        get_full_article_content,

        # SEC Filing Tools (Basic)
        get_sec_filing_summary,          # Quick overview/preview
        get_sec_financial_data,          # Extract financial statements
        # search_sec_filing,              # DEPRECATED - use semantic_search_sec_filing instead
        compare_sec_filings,             # Compare multiple years

        # RAG-Enhanced Tools (Primary for Deep Analysis)
        semantic_search_sec_filing,      # PRIMARY tool for SEC filing questions
        semantic_search_news,            # Historical news semantic search
        multi_document_analysis,         # Most comprehensive - combines SEC + news
        index_news_for_ticker,           # Index news for semantic search
        rag_system_status,               # Check RAG system status

        # Web Search Tools (Real-Time Information)
        web_search,                      # General real-time web search
        financial_web_search,            # Company-specific financial search
        real_time_market_search,         # Breaking market news
        search_and_summarize             # Deep web search with content extraction
    ]

    graph = create_agent_graph(tools)

    result = graph.invoke({
        "messages": [HumanMessage(content=query)]
    })

    return result['messages'][-1].content

def main():
    import sys

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(run_agent(query))
    else:
        print("Financial AI Agent - Quant Tools")
        print("-" * 40)
        while True:
            query = input("\nYou: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            if query:
                print(f"\nAgent: {run_agent(query)}")

if __name__ == "__main__":
    main()
