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
    get_full_article_content
)

load_dotenv()

def run_agent(query: str) -> str:
    tools = [
        get_valuation_metrics,
        get_profitability_metrics,
        get_historical_growth,
        get_stock_price_summary,
        get_analyst_recommendations,
        compare_key_metrics,
        get_stock_news,
        get_market_news,
        get_full_article_content
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
