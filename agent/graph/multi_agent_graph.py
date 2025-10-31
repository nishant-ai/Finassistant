"""
Multi-Agent Orchestration Graph

This module creates the complete workflow:

User Query → Parse Request → Planner Agent → Financial Agent (loop) → Publisher Agent → Final Output

Architecture:
1. PARSE NODE: Extracts mode ([Chat]/[Report]) and clean query
2. PLANNER NODE: Creates execution plan with tool selections
3. FINANCIAL NODE: Executes plan steps (loops until all steps complete)
4. PUBLISHER NODE: Formats final output based on mode
5. END: Returns formatted response
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from typing import Dict

from agent.graph.multi_agent_state import MultiAgentState
from agent.graph.request_parser import parse_user_request, format_mode_description
from agent.graph.planner_agent import create_planner_agent
from agent.graph.financial_agent import create_financial_execution_agent, should_continue_execution
from agent.graph.publisher_agent import create_publisher_agent


def create_parse_node():
    """
    Creates the request parsing node.

    Extracts [Chat] or [Report] tag and cleans query.
    """
    def parse_node(state: MultiAgentState) -> Dict:
        """Parse user request and extract mode"""

        # Get original query from messages
        messages = state.get("messages", [])
        if messages:
            raw_query = messages[-1].content
        else:
            raw_query = state.get("user_query", "")

        # Parse the request
        clean_query, output_mode, desired_length = parse_user_request(raw_query)

        mode_desc = format_mode_description(output_mode, desired_length)

        print("=" * 70)
        print("🎯 MULTI-AGENT FINANCIAL ANALYSIS SYSTEM")
        print("=" * 70)
        print(f"📥 Raw Query: {raw_query}")
        print(f"✨ Clean Query: {clean_query}")
        print(f"📋 Mode: {mode_desc}")
        print("=" * 70)

        return {
            "user_query": clean_query,
            "output_mode": output_mode,
            "desired_length": desired_length
        }

    return parse_node


def create_multi_agent_graph(tools):
    """
    Creates the complete multi-agent orchestration graph.

    Args:
        tools: List of available financial analysis tools

    Returns:
        Compiled LangGraph workflow
    """

    # Create all agent nodes
    parse_node = create_parse_node()
    planner_node = create_planner_agent()
    financial_node = create_financial_execution_agent(tools)
    publisher_node = create_publisher_agent()

    # Build the state graph
    workflow = StateGraph(MultiAgentState)

    # Add nodes
    workflow.add_node("parse", parse_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("financial", financial_node)
    workflow.add_node("publisher", publisher_node)

    # Set entry point
    workflow.set_entry_point("parse")

    # Define edges
    # Parse → Planner (always)
    workflow.add_edge("parse", "planner")

    # Planner → Financial (always, starts execution)
    workflow.add_edge("planner", "financial")

    # Financial → Financial OR Publisher (conditional - loop until done)
    workflow.add_conditional_edges(
        "financial",
        should_continue_execution,
        {
            "continue": "financial",  # Loop back for next step
            "publish": "publisher"     # All steps done, publish
        }
    )

    # Publisher → END (always)
    workflow.add_edge("publisher", END)

    return workflow.compile()


def print_execution_summary(state: MultiAgentState):
    """
    Print a summary of the execution.

    For debugging and monitoring.
    """
    print("\n" + "=" * 70)
    print("📊 EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Query: {state['user_query']}")
    print(f"Mode: {state['output_mode'].upper()}")
    print(f"Total Steps: {state['total_steps']}")
    print(f"Completed: {state['completed_steps']}")
    print(f"Errors: {'Yes' if state['has_errors'] else 'No'}")

    print(f"\n📋 Plan Summary:")
    print(f"   {state.get('plan_summary', 'N/A')}")

    print(f"\n🔧 Executed Tools:")
    for result in state.get("execution_results", []):
        status = "✅" if result["success"] else "❌"
        print(f"   {status} Step {result['step_number']}: {result['tool_name']}")

    if state.get("error_messages"):
        print(f"\n⚠️  Errors:")
        for error in state["error_messages"]:
            print(f"   - {error}")

    print(f"\n📝 Final Output Length: {len(state.get('final_output', ''))} characters")
    print("=" * 70 + "\n")


# Testing
if __name__ == "__main__":
    from dotenv import load_dotenv
    from agent.tools import (
        get_valuation_metrics,
        get_profitability_metrics,
        get_stock_price_summary,
        web_search
    )

    load_dotenv()

    # Create test graph with limited tools
    test_tools = [
        get_valuation_metrics,
        get_profitability_metrics,
        get_stock_price_summary,
        web_search
    ]

    graph = create_multi_agent_graph(test_tools)

    # Test with chat mode
    print("\nTest 1: Chat Mode")
    result = graph.invoke({
        "messages": [HumanMessage(content="[Chat] What's Apple's P/E ratio?")]
    })

    print("\nFinal Output:")
    print(result["final_output"][:500] + "...")

    # Test with report mode (commented out to avoid long execution)
    # print("\n\nTest 2: Report Mode")
    # result = graph.invoke({
    #     "messages": [HumanMessage(content="[Report] Analyze Microsoft")]
    # })
    # print_execution_summary(result)
