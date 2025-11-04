"""
Financial Execution Agent - Executes the plan created by Planner Agent

This agent:
1. Takes the plan from Planner Agent
2. Executes each step sequentially
3. Calls the appropriate tools with the specified arguments
4. Collects results and handles errors
5. Passes results to Publisher Agent
"""

from typing import Dict, Any, List
from agent.states.states import MultiAgentState, ExecutionResult


def create_financial_execution_agent(tools: List):
    """
    Creates the financial execution agent.

    Args:
        tools: List of available tool functions

    Returns:
        Financial agent function that executes plan steps
    """

    # Create tool lookup dictionary
    tool_map = {tool.name: tool for tool in tools}

    def financial_agent(state: MultiAgentState) -> Dict:
        """
        Execute the next step in the plan.

        This agent is called multiple times - once per step in the plan.
        It executes one step at a time and updates the state.
        """

        plan = state["plan"]
        current_step = state["current_step"]
        execution_results = state.get("execution_results", [])
        all_tool_outputs = state.get("all_tool_outputs", {})
        error_messages = state.get("error_messages", [])

        # Check if we've completed all steps
        if current_step >= len(plan):
            return {
                "current_step": current_step,
                "completed_steps": current_step,
                "execution_results": execution_results,
                "all_tool_outputs": all_tool_outputs,
                "error_messages": error_messages
            }

        # Get current step to execute
        step = plan[current_step]
        step_number = step["step_number"]
        tool_name = step["tool_name"]
        tool_args = step["tool_args"]

        print(f"\n🔧 Executing Step {step_number}/{len(plan)}: {step['description']}")
        print(f"   Tool: {tool_name}({tool_args})")

        # Execute the tool
        result: ExecutionResult = {
            "step_number": step_number,
            "tool_name": tool_name,
            "success": False,
            "output": "",
            "error": None
        }

        try:
            # Get the tool function
            if tool_name not in tool_map:
                raise ValueError(f"Tool '{tool_name}' not found in available tools")

            tool = tool_map[tool_name]

            # Execute the tool with arguments
            output = tool.invoke(tool_args)

            # Store successful result
            result["success"] = True
            result["output"] = str(output)
            result["error"] = None

            print(f"   ✅ Success - Output length: {len(str(output))} characters")

        except Exception as e:
            # Handle errors gracefully
            error_msg = f"Error in step {step_number} ({tool_name}): {str(e)}"
            result["success"] = False
            result["output"] = ""
            result["error"] = str(e)
            error_messages.append(error_msg)

            print(f"   ❌ Error: {str(e)}")

        # Update results
        execution_results.append(result)
        all_tool_outputs[f"step_{step_number}"] = result["output"]

        # Return updated state
        return {
            "current_step": current_step + 1,
            "completed_steps": current_step + 1,
            "execution_results": execution_results,
            "all_tool_outputs": all_tool_outputs,
            "has_errors": len(error_messages) > 0,
            "error_messages": error_messages
        }

    return financial_agent


def should_continue_execution(state: MultiAgentState) -> str:
    """
    Determines if execution should continue or move to publishing.

    Returns:
        "continue" if more steps to execute
        "publish" if all steps completed
    """

    current_step = state["current_step"]
    total_steps = state["total_steps"]

    if current_step < total_steps:
        return "continue"
    else:
        return "publish"


# Testing
if __name__ == "__main__":
    # Mock test
    print("Financial Execution Agent module loaded successfully")
