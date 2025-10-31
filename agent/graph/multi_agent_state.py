"""
Multi-Agent State Management for Planner → Financial → Publisher Pipeline

This module defines the state structure for the three-agent system:
1. Planner Agent: Creates execution plans based on user queries
2. Financial Agent: Executes the plan using available tools
3. Publisher Agent: Formats results for Chat or Report output
"""

from typing import TypedDict, Literal, List, Dict, Optional, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class PlanStep(TypedDict):
    """Represents a single step in the execution plan"""
    step_number: int
    description: str
    tool_name: str
    tool_args: Dict
    reasoning: str
    expected_output: str


class ExecutionResult(TypedDict):
    """Result from executing a plan step"""
    step_number: int
    tool_name: str
    success: bool
    output: str
    error: Optional[str]


class MultiAgentState(TypedDict):
    """
    State for the multi-agent financial analysis system.

    Flow:
    1. User query comes in with [Chat] or [Report] tag
    2. Planner creates execution plan
    3. Financial agent executes each step
    4. Publisher formats final output
    """

    # Original user input
    messages: Annotated[List[BaseMessage], add_messages]
    user_query: str
    output_mode: Literal["chat", "report"]  # Determined from [Chat] or [Report] tag
    desired_length: Optional[str]  # e.g., "3-4 paragraphs", "comprehensive", "brief"

    # Planning phase
    plan: List[PlanStep]
    plan_summary: str
    planner_reasoning: str

    # Execution phase
    execution_results: List[ExecutionResult]
    current_step: int
    all_tool_outputs: Dict[str, str]  # Keyed by step number for easy reference

    # Publishing phase
    final_output: str
    output_format: str  # "markdown", "json", etc.

    # Metadata
    total_steps: int
    completed_steps: int
    has_errors: bool
    error_messages: List[str]
