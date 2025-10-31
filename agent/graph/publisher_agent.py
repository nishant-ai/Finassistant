"""
Publisher Agent - Formats final output for Chat or Report mode

This agent:
1. Takes all execution results from Financial Agent
2. Synthesizes data into coherent narrative
3. Formats output based on mode (Chat vs Report)
4. Generates web-friendly markdown with tables, charts, and structure

For CHAT mode:
- Conversational tone
- Concise (based on desired_length)
- Direct answers with supporting data
- Simple formatting (paragraphs, maybe 1-2 tables)

For REPORT mode:
- Professional structure
- Comprehensive sections
- Rich formatting (tables, lists, emphasis)
- Executive summary
- Detailed analysis
- Data visualizations (tables)
- Conclusions and recommendations
"""

from typing import Dict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from agent.graph.multi_agent_state import MultiAgentState


CHAT_PUBLISHER_PROMPT = """You are an expert Financial Content Publisher specializing in CONVERSATIONAL responses.

Your job is to take raw tool outputs and create a natural, engaging response.

## Chat Mode Guidelines

**Tone**: Conversational, helpful, professional but friendly
**Length**: {desired_length}
**Format**: Markdown (paragraphs, occasional tables/lists)
**Structure**: Natural flow, not rigid sections

## Content Strategy

1. **Direct Answer First** - Answer the user's question immediately
2. **Support with Data** - Use tool outputs to back up your answer
3. **Context and Insights** - Explain what the numbers mean
4. **Concise** - Respect the desired length

## Formatting Rules

- Use **bold** for emphasis on key metrics
- Use tables ONLY when comparing multiple items
- Use bullet lists for 3+ related points
- NO emoji headers or excessive formatting
- NO long disclaimers (keep it brief at end)

## Example Output Structure

[Direct answer to the question]

[1-2 paragraphs with key data points and insights]

[Optional: Small table if comparing things]

[Brief context or implications]

*Note: This is informational analysis, not investment advice.*

## Important

- Synthesize, don't just list tool outputs
- Make it readable and engaging
- Focus on what matters to the user
- Stay within length constraints
"""

REPORT_PUBLISHER_PROMPT = """You are an expert Financial Content Publisher specializing in COMPREHENSIVE REPORTS.

Your job is to take raw tool outputs and create a professional, in-depth report.

## Report Mode Guidelines

**Tone**: Professional, authoritative, analytical
**Length**: Comprehensive (typically 8-15 sections)
**Format**: Structured Markdown with rich formatting
**Structure**: Formal report sections

## Report Structure Template

```markdown
# [Company/Topic] Financial Analysis Report

## Executive Summary
[2-3 paragraph overview of key findings]

## 1. Overview
[Current state, basic facts]

## 2. Market Performance
[Stock price, trends, volatility]
- Use tables for price data
- Include 52-week ranges, moving averages

## 3. Valuation Analysis
[P/E, P/S, PEG ratios]
- Table format for multiple metrics
- Context: industry averages, historical comparison

## 4. Profitability & Efficiency
[Margins, ROA, ROE]
- Compare to competitors or historical data

## 5. Growth Trajectory
[Revenue and earnings growth]
- Use tables to show multi-year trends
- YoY growth rates

## 6. Financial Position
[From SEC filings if available]
- Balance sheet highlights
- Cash flow

## 7. Market Sentiment & News
[Recent news, analyst opinions]
- Key developments
- Analyst consensus

## 8. Risks & Challenges
[From SEC filings or web search]
- Identified risk factors
- Competitive pressures

## 9. Strategic Initiatives
[Future plans, growth drivers]

## 10. Analyst Perspective
[Wall Street consensus, price targets]

## Conclusions
[Summary of findings]

## Key Takeaways
- [Bullet point 1]
- [Bullet point 2]
- [Bullet point 3]

---
*Report generated on [date]. Data sources: [list tools used]. This is informational analysis, not investment advice.*
```

## Formatting Excellence

- **Tables**: Use for all quantitative comparisons
- **Headers**: Clear hierarchy (##, ###)
- **Lists**: For risks, takeaways, recommendations
- **Emphasis**: Bold for key metrics, italic for context
- **Data Citations**: Reference tool sources
- **Professional**: No emojis, clean formatting

## Content Depth

- Each section should be 2-5 paragraphs
- Include ALL relevant data from tools
- Synthesize insights across multiple tools
- Compare and contrast data points
- Provide context and interpretation
- Draw conclusions

## Important

- Use ALL tool outputs - don't leave data unused
- Create cohesive narrative across sections
- Ensure logical flow between sections
- Rich in tables and structured data
- Professional quality suitable for stakeholders
"""


def create_publisher_agent(llm: ChatGoogleGenerativeAI = None):
    """
    Creates the publisher agent function.

    Args:
        llm: Optional LLM instance. If not provided, creates one.

    Returns:
        Publisher function that takes state and returns formatted output
    """

    if llm is None:
        llm = ChatGoogleGenerativeAI(
            model=os.getenv("PUBLISHER_MODEL", "gemini-2.0-flash-exp"),
            temperature=0.3,  # Slightly higher for more natural writing
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

    def publisher_agent(state: MultiAgentState) -> Dict:
        """
        Publisher agent that formats final output.

        Takes all execution results and creates polished output.
        """

        user_query = state["user_query"]
        output_mode = state["output_mode"]
        desired_length = state.get("desired_length", "standard")
        plan = state["plan"]
        execution_results = state["execution_results"]
        all_tool_outputs = state["all_tool_outputs"]
        has_errors = state.get("has_errors", False)
        error_messages = state.get("error_messages", [])

        print(f"\n📝 Publishing {output_mode.upper()} mode output...")

        # Select appropriate system prompt
        if output_mode == "report":
            system_prompt = REPORT_PUBLISHER_PROMPT
        else:
            system_prompt = CHAT_PUBLISHER_PROMPT.format(desired_length=desired_length)

        # Build context from execution results
        context = f"""
## User Query
{user_query}

## Output Requirements
- Mode: {output_mode.upper()}
- Desired Length: {desired_length}

## Execution Plan Summary
{state.get('plan_summary', 'N/A')}

## Tool Outputs

"""

        # Add each tool output
        for i, result in enumerate(execution_results, 1):
            step_info = plan[i-1] if i <= len(plan) else {}

            context += f"### Step {i}: {step_info.get('description', 'N/A')}\n"
            context += f"**Tool**: {result['tool_name']}\n"

            if result['success']:
                context += f"**Output**:\n```\n{result['output']}\n```\n\n"
            else:
                context += f"**Error**: {result['error']}\n\n"

        # Add error summary if any
        if has_errors:
            context += f"\n## Errors Encountered\n"
            for error in error_messages:
                context += f"- {error}\n"
            context += "\n"

        # Create publishing prompt
        if output_mode == "report":
            publishing_prompt = f"""
{context}

Create a COMPREHENSIVE FINANCIAL REPORT based on the tool outputs above.

Requirements:
- Follow the report structure template
- Use ALL available tool outputs
- Create tables for quantitative data
- Synthesize insights across all data sources
- Professional, in-depth analysis
- 8-15 sections minimum
- Rich markdown formatting

Generate the complete report now.
"""
        else:  # chat mode
            publishing_prompt = f"""
{context}

Create a CONVERSATIONAL RESPONSE based on the tool outputs above.

Requirements:
- Direct answer to: "{user_query}"
- Length: {desired_length}
- Use data from tool outputs
- Natural, engaging tone
- Simple markdown formatting
- Focus on what the user asked

Generate the response now.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=publishing_prompt)
        ]

        # Generate final output
        try:
            response = llm.invoke(messages)
            final_output = response.content

            print(f"   ✅ Published - Output length: {len(final_output)} characters")

            return {
                "final_output": final_output,
                "output_format": "markdown"
            }

        except Exception as e:
            # Fallback output in case of publishing error
            error_output = f"""# Error Generating Output

An error occurred while formatting the final output: {str(e)}

## Raw Tool Outputs

"""
            for i, result in enumerate(execution_results, 1):
                error_output += f"### Step {i}: {result['tool_name']}\n"
                if result['success']:
                    error_output += f"{result['output']}\n\n"
                else:
                    error_output += f"Error: {result['error']}\n\n"

            return {
                "final_output": error_output,
                "output_format": "markdown",
                "has_errors": True,
                "error_messages": error_messages + [f"Publishing error: {str(e)}"]
            }

    return publisher_agent


# Testing
if __name__ == "__main__":
    print("Publisher Agent module loaded successfully")
