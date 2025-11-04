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

from agent.states.states import MultiAgentState
from agent.subagents.planner_agent import create_planner_agent
from agent.subagents.financial_agent import create_financial_execution_agent, should_continue_execution
from agent.subagents.publisher_agent import create_publisher_agent


def create_multi_agent_graph(tools):
    """
    Creates the complete multi-agent orchestration graph.

    Args:
        tools: List of available financial analysis tools

    Returns:
        Compiled LangGraph workflow
    """

    # Create all agent nodes
    planner_node = create_planner_agent()
    financial_node = create_financial_execution_agent(tools)
    publisher_node = create_publisher_agent()

    # Build the state graph
    workflow = StateGraph(MultiAgentState)

    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("financial", financial_node)
    workflow.add_node("publisher", publisher_node)

    # Set entrypoint: START → Planner
    workflow.set_entry_point("planner")

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