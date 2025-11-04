"""
Unified Agent Runner - Single entry point for both Chat and Report modes

This module provides a unified interface to run financial analysis agents:
- Chat mode: Uses single-agent graph for quick, conversational responses
- Report mode: Uses multi-agent graph for comprehensive, structured reports

No tag parsing needed - mode is explicitly specified as a parameter.
"""

from dotenv import load_dotenv
from typing import Literal, Optional
from langchain_core.messages import HumanMessage

# Import both graph systems
from agent.graph.single_agent_graph import create_agent_graph
from agent.graph.multi_agent_graph import create_multi_agent_graph

# Import all tools
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
    compare_sec_filings,
    cleanup_sec_cache,
    get_sec_cache_info,

    # RAG-Enhanced Tools
    semantic_search_sec_filing,
    multi_document_analysis,
    rag_system_status,

    # Web Search Tools
    web_search,
    financial_web_search,
    real_time_market_search,
    search_and_summarize
)

load_dotenv()


def run_agent(
    query: str,
    mode: Literal["chat", "report"] = "chat",
    verbose: bool = False
) -> str:
    """
    Unified agent runner - automatically selects single or multi-agent based on mode.

    Args:
        query: User's financial question (NO TAGS NEEDED)
        mode: "chat" for quick responses, "report" for comprehensive analysis
        verbose: Print execution details (only applies to report mode)

    Returns:
        Final formatted output

    Examples:
        >>> run_agent("What's Apple's P/E ratio?", mode="chat")
        >>> run_agent("Analyze Tesla's financial health", mode="report")
        >>> run_agent("Compare Microsoft and Google", mode="chat", verbose=True)
    """

    # Collect all available tools
    tools = [
        # Quantitative Tools
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
        cleanup_sec_cache,
        get_sec_cache_info,

        # RAG Tools
        semantic_search_sec_filing,
        multi_document_analysis,
        rag_system_status,

        # Web Search Tools
        web_search,
        financial_web_search,
        real_time_market_search,
        search_and_summarize
    ]

    # Route to appropriate graph based on mode
    if mode == "chat":
        # Use single-agent graph (efficient, 2-4 LLM calls)
        graph = create_agent_graph(tools)
        result = graph.invoke({
            "messages": [HumanMessage(content=query)]
        })
        return result['messages'][-1].content

    elif mode == "report":
        # Use multi-agent graph (comprehensive, planner → financial → publisher)
        graph = create_multi_agent_graph(tools)
        result = graph.invoke({
            "messages": [HumanMessage(content=query)],
            "output_mode": "report",
            "user_query": query
        })

        # Optional: Print execution summary for reports
        if verbose:
            print("\n" + "=" * 70)
            print("EXECUTION SUMMARY")
            print("=" * 70)
            print(f"Plan Steps: {len(result.get('plan', []))}")
            print(f"Execution Results: {len(result.get('execution_results', []))}")
            for i, step in enumerate(result.get('plan', []), 1):
                print(f"  {i}. {step.get('tool_name', 'unknown')} - {step.get('status', 'unknown')}")
            print("=" * 70)

        return result['final_output']

    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'chat' or 'report'")


def main():
    """CLI interface with mode selection"""
    import sys

    print("=" * 70)
    print("🤖 UNIFIED FINANCIAL AGENT")
    print("=" * 70)
    print("\nModes:")
    print("  chat   - Quick conversational responses (single-agent)")
    print("  report - Comprehensive in-depth reports (multi-agent)")
    print("\nUsage:")
    print("  python -m agent.agent <mode> <query>")
    print("\nExamples:")
    print('  python -m agent.agent chat "What\'s Apple\'s P/E?"')
    print('  python -m agent.agent report "Analyze Tesla"')
    print('  python -m agent.agent  # Interactive mode')
    print("=" * 70)

    if len(sys.argv) < 2:
        # Interactive mode with mode selection
        interactive_mode()
    elif len(sys.argv) == 2:
        # Interactive mode with initial mode selection
        mode = sys.argv[1].lower()
        if mode in ["chat", "report"]:
            interactive_mode(initial_mode=mode)
        else:
            print(f"❌ Invalid mode: {mode}. Use 'chat' or 'report'")
    else:
        # CLI mode
        mode = sys.argv[1].lower()
        query = " ".join(sys.argv[2:])

        if mode not in ["chat", "report"]:
            print(f"❌ Invalid mode: {mode}. Use 'chat' or 'report'")
            return

        print(f"\n🔍 Mode: {mode.upper()}")
        print(f"📝 Query: {query}\n")

        try:
            result = run_agent(query, mode=mode, verbose=True)
            print("\n" + "=" * 70)
            print("📄 FINAL OUTPUT")
            print("=" * 70)
            print(result)
            print("=" * 70)
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


def interactive_mode(initial_mode: str = "chat"):
    """Interactive CLI with mode switching"""
    print("\n💬 INTERACTIVE MODE")
    print("Commands:")
    print("  /chat   - Switch to chat mode")
    print("  /report - Switch to report mode")
    print("  /quit   - Exit")
    print("  /help   - Show this help")
    print()

    current_mode = initial_mode

    while True:
        try:
            prompt = f"[{current_mode.upper()}] You: "
            user_input = input(prompt).strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == "/quit":
                print("\n👋 Goodbye!")
                break
            elif user_input.lower() == "/chat":
                current_mode = "chat"
                print("✅ Switched to CHAT mode (quick responses)")
                continue
            elif user_input.lower() == "/report":
                current_mode = "report"
                print("✅ Switched to REPORT mode (comprehensive analysis)")
                continue
            elif user_input.lower() == "/help":
                print("\nCommands:")
                print("  /chat   - Switch to chat mode")
                print("  /report - Switch to report mode")
                print("  /quit   - Exit")
                print("  /help   - Show this help")
                continue

            # Execute query
            print()  # Blank line for readability
            result = run_agent(
                user_input,
                mode=current_mode,
                verbose=(current_mode == "report")
            )
            print(f"\n🤖 Agent:\n{result}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    main()
