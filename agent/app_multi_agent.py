"""
Multi-Agent Financial Analysis System - Main Application

This is the enhanced version with three agents:
1. Planner Agent: Creates execution plans
2. Financial Agent: Executes tools
3. Publisher Agent: Formats output

Usage:
    python -m agent.app_multi_agent "[Chat] What's Apple's P/E ratio?"
    python -m agent.app_multi_agent "[Report] Analyze Tesla's financial health"

Interactive mode:
    python -m agent.app_multi_agent
"""

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent.graph.multi_agent_graph import create_multi_agent_graph, print_execution_summary
from agent.tools import (
    # Quantitative Analysis Tools
    get_valuation_metrics,
    get_profitability_metrics,
    get_historical_growth,
    get_stock_price_summary,
    get_analyst_recommendations,
    compare_key_metrics,

    # News Tools
    get_stock_news,
    get_market_news,
    get_full_article_content,

    # SEC Filing Tools
    get_sec_filing_summary,
    get_sec_financial_data,
    # search_sec_filing,  # Deprecated
    compare_sec_filings,

    # RAG-Enhanced Tools
    semantic_search_sec_filing,
    semantic_search_news,
    multi_document_analysis,
    index_news_for_ticker,
    rag_system_status,

    # Web Search Tools
    web_search,
    financial_web_search,
    real_time_market_search,
    search_and_summarize
)

load_dotenv()


def run_multi_agent(query: str, verbose: bool = True) -> str:
    """
    Run the multi-agent financial analysis system.

    Args:
        query: User query (can include [Chat] or [Report] tags)
        verbose: Whether to print execution details

    Returns:
        Final formatted output
    """

    # Collect all tools
    tools = [
        # Quantitative Analysis Tools
        get_valuation_metrics,
        get_profitability_metrics,
        get_historical_growth,
        get_stock_price_summary,
        get_analyst_recommendations,
        compare_key_metrics,

        # News Tools
        get_stock_news,
        get_market_news,
        get_full_article_content,

        # SEC Filing Tools
        get_sec_filing_summary,
        get_sec_financial_data,
        compare_sec_filings,

        # RAG-Enhanced Tools
        semantic_search_sec_filing,
        semantic_search_news,
        multi_document_analysis,
        index_news_for_ticker,
        rag_system_status,

        # Web Search Tools
        web_search,
        financial_web_search,
        real_time_market_search,
        search_and_summarize
    ]

    # Create the multi-agent graph
    graph = create_multi_agent_graph(tools)

    # Execute
    result = graph.invoke({
        "messages": [HumanMessage(content=query)]
    })

    # Print summary if verbose
    if verbose:
        print_execution_summary(result)

    # Return final output
    return result['final_output']


def interactive_mode():
    """
    Interactive CLI mode for the multi-agent system.
    """
    print("=" * 70)
    print("🤖 MULTI-AGENT FINANCIAL ANALYSIS SYSTEM")
    print("=" * 70)
    print("\nWelcome! I'm your AI financial analyst with three specialized agents:")
    print("  1. 🎯 Planner - Creates optimal execution plans")
    print("  2. 🔧 Financial - Executes analysis tools")
    print("  3. 📝 Publisher - Formats beautiful outputs")
    print("\nMode Selection:")
    print("  [Chat] - Quick, conversational responses (1-4 paragraphs)")
    print("  [Report] - Comprehensive, in-depth reports (8-15 sections)")
    print("\nExamples:")
    print("  [Chat] What's Apple's P/E ratio?")
    print("  [Report] Analyze Tesla's financial performance")
    print("  Compare Microsoft and Google [Chat] keep it brief")
    print("\nCommands: 'quit', 'exit', 'q' to exit")
    print("=" * 70)

    while True:
        print("\n")
        query = input("You: ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye! Thank you for using the Multi-Agent Financial System.")
            break

        if not query:
            continue

        try:
            print("\n")
            output = run_multi_agent(query, verbose=True)

            print("\n" + "=" * 70)
            print("📄 FINAL OUTPUT")
            print("=" * 70)
            print(output)
            print("=" * 70)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try a different query or check your configuration.")


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1:
        # Command-line mode
        query = " ".join(sys.argv[1:])
        print(run_multi_agent(query, verbose=True))
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
