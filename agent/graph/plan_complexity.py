from typing import Literal

def get_plan_complexity(output_mode: Literal["chat", "report"], desired_length: str = "standard") -> Literal["minimal", "moderate", "comprehensive", "exhaustive"]:
    """
    Determine plan complexity based on output mode and desired length.
    
    Args:
        output_mode: "chat" or "report"
        desired_length: Length preference (e.g., "brief", "standard", "comprehensive")
    
    Returns:
        Complexity level for planner
    """

    if output_mode == "chat":
        if "brief" in desired_length.lower():
            return "minimal"
        else:
            return "moderate"
    
    else:
        if "comprehensive" in desired_length.lower():
            return "comprehensive"
        else:
            return "exhaustive"