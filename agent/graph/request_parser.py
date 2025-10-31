"""
Request Parser for Multi-Agent System

Parses user queries to extract:
- Output mode: [Chat] or [Report]
- Desired length/depth
- Clean query text
"""

import re
from typing import Tuple, Literal, Optional


def parse_user_request(query: str) -> Tuple[str, Literal["chat", "report"], Optional[str]]:
    """
    Parse user query to extract mode and clean query.

    Args:
        query: Raw user input

    Returns:
        Tuple of (clean_query, output_mode, desired_length)

    Examples:
        "[Chat] What's Apple's P/E ratio?"
        → ("What's Apple's P/E ratio?", "chat", "3-4 paragraphs")

        "[Report] Analyze Tesla's financial performance"
        → ("Analyze Tesla's financial performance", "report", "comprehensive")

        "Compare AAPL and MSFT [Chat] keep it brief"
        → ("Compare AAPL and MSFT keep it brief", "chat", "brief")
    """

    # Default values
    output_mode: Literal["chat", "report"] = "chat"
    desired_length: Optional[str] = None
    clean_query = query

    # Check for [Chat] or [Report] tags (case insensitive)
    chat_match = re.search(r'\[chat\]', query, re.IGNORECASE)
    report_match = re.search(r'\[report\]', query, re.IGNORECASE)

    if report_match:
        output_mode = "report"
        desired_length = "comprehensive"
        # Remove the tag
        clean_query = re.sub(r'\[report\]', '', clean_query, flags=re.IGNORECASE).strip()

    elif chat_match:
        output_mode = "chat"
        # Remove the tag
        clean_query = re.sub(r'\[chat\]', '', clean_query, flags=re.IGNORECASE).strip()

        # Look for length indicators in the query
        if any(word in clean_query.lower() for word in ['brief', 'short', 'quick', 'concise']):
            desired_length = "brief"
        elif any(word in clean_query.lower() for word in ['detailed', 'comprehensive', 'in-depth', 'thorough']):
            desired_length = "detailed"
        else:
            desired_length = "3-4 paragraphs"  # Default for chat mode

    else:
        # No tag found - default to chat mode
        output_mode = "chat"
        desired_length = "3-4 paragraphs"

    # Check for explicit paragraph/sentence requests
    paragraph_match = re.search(r'(\d+)[-\s]?(?:to[-\s])?(\d+)?\s*paragraphs?', clean_query, re.IGNORECASE)
    if paragraph_match:
        if paragraph_match.group(2):
            desired_length = f"{paragraph_match.group(1)}-{paragraph_match.group(2)} paragraphs"
        else:
            desired_length = f"{paragraph_match.group(1)} paragraphs"

    sentence_match = re.search(r'(\d+)[-\s]?(?:to[-\s])?(\d+)?\s*sentences?', clean_query, re.IGNORECASE)
    if sentence_match:
        if sentence_match.group(2):
            desired_length = f"{sentence_match.group(1)}-{sentence_match.group(2)} sentences"
        else:
            desired_length = f"{sentence_match.group(1)} sentences"

    return clean_query.strip(), output_mode, desired_length


def get_plan_complexity(output_mode: Literal["chat", "report"], desired_length: Optional[str]) -> str:
    """
    Determine plan complexity based on output mode and desired length.

    Returns:
        One of: "minimal", "moderate", "comprehensive", "exhaustive"
    """

    if output_mode == "report":
        return "exhaustive"

    if output_mode == "chat":
        if desired_length in ["brief", "1 sentence", "2 sentences"]:
            return "minimal"
        elif desired_length in ["detailed", "comprehensive"]:
            return "comprehensive"
        else:
            return "moderate"

    return "moderate"


def format_mode_description(output_mode: Literal["chat", "report"], desired_length: Optional[str]) -> str:
    """
    Generate human-readable description of the output mode.

    Returns:
        Description string for logging/display
    """

    if output_mode == "report":
        return "Comprehensive Report with tables, graphs, and in-depth analysis"

    if output_mode == "chat":
        length_desc = desired_length or "standard length"
        return f"Conversational response ({length_desc})"

    return "Standard response"


# Example usage and testing
if __name__ == "__main__":
    test_queries = [
        "[Chat] What's Apple's P/E ratio?",
        "[Report] Analyze Tesla's financial performance",
        "Compare AAPL and MSFT [Chat] keep it brief",
        "Give me 5 paragraphs on NVIDIA's growth",
        "What happened to the market today?",
        "[REPORT] Deep dive into semiconductor industry",
        "Quick summary of Amazon earnings [Chat]"
    ]

    print("Testing Request Parser:\n")
    for query in test_queries:
        clean, mode, length = parse_user_request(query)
        complexity = get_plan_complexity(mode, length)
        description = format_mode_description(mode, length)

        print(f"Original: {query}")
        print(f"  Clean Query: {clean}")
        print(f"  Mode: {mode}")
        print(f"  Length: {length}")
        print(f"  Complexity: {complexity}")
        print(f"  Description: {description}")
        print()
