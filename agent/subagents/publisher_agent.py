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
from agent.states.states import MultiAgentState


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

Your job is to take raw tool outputs and create a professional, in-depth report that ADAPTS to the query intent.

## Report Mode Guidelines

**Tone**: Professional, authoritative, analytical
**Length**: Comprehensive (varies based on query focus)
**Format**: Structured Markdown with rich formatting
**Structure**: ADAPTIVE - matches the query intent and available data

## CRITICAL: Query-Aware Formatting

**DO NOT use a rigid template.** Instead, analyze:
1. **Query Intent** - What is the user asking for? (news, valuation, filings, comparison, etc.)
2. **Available Data** - What tool outputs do you have?
3. **Report Focus** - Create sections that match the intent

### Intent-Based Structures

**For NEWS-FOCUSED queries** (intent: news, market):
- Executive Summary
- Recent Developments (major section with news synthesis)
- Market Sentiment & Impact
- Stock Price Context (brief)
- Key Takeaways
*Avoid heavy valuation/profitability sections if query doesn't ask for them*

**For VALUATION-FOCUSED queries** (intent: valuation):
- Executive Summary
- Current Valuation Metrics (major section with tables)
- Price Analysis
- Peer Comparison (if available)
- Historical Context
- Analyst Perspective
- Conclusions
*Focus on P/E, P/S, PEG - keep news minimal unless relevant*

**For GROWTH-FOCUSED queries** (intent: growth):
- Executive Summary
- Historical Growth Trends (major section)
- Revenue & Earnings Analysis
- Growth Drivers
- Future Outlook
- Conclusions

**For FILINGS-FOCUSED queries** (intent: filings):
- Executive Summary
- SEC Filing Overview
- Business Strategy & Operations
- Risk Factors (major section)
- Financial Position from Filings
- Management Discussion
- Key Insights

**For COMPARISON queries** (intent: comparison):
- Executive Summary
- Side-by-Side Metrics Comparison (major table)
- Company A Deep Dive
- Company B Deep Dive
- Comparative Analysis
- Recommendations

**For COMPREHENSIVE queries** (intent: comprehensive):
- Use broader structure covering multiple aspects
- Include: Overview, Performance, Valuation, Growth, News, Risks, Conclusions
- Balanced coverage across categories

## Adaptive Section Guidelines

1. **Start with Executive Summary** - Always include this
2. **Create Major Sections** based on available data and intent:
   - If 80% of data is news → Make news the main focus (3-4 sections)
   - If 80% is metrics → Make valuation/profitability main focus
   - If mixed → Balance sections proportionally
3. **End with Conclusions/Key Takeaways** - Always include this

## Formatting Excellence

- **Tables**: Use for all quantitative comparisons
- **Headers**: Clear hierarchy (##, ###)
- **Lists**: For risks, takeaways, recommendations
- **Emphasis**: Bold for key metrics, italic for context
- **Data Citations**: Reference tool sources
- **Professional**: No emojis, clean formatting

## Content Strategy

- **Synthesize, don't list** - Weave tool outputs into narrative
- **Focus on what matters** - If query asks about news, don't spend 5 sections on ratios
- **Use ALL tool outputs** - But prioritize based on query intent
- **Create logical flow** - Sections should flow naturally
- **Be comprehensive where it counts** - Deep dive on the intent, lighter on peripherals

## Important Rules

- NEVER force a section if you don't have relevant data
- NEVER create irrelevant sections just to fill space
- ALWAYS adapt structure to match the query intent
- ALWAYS use available data efficiently
- Professional quality suitable for stakeholders
- **If tools failed or returned no data**: Supplement with general knowledge about the topic, but be transparent about the lack of real-time data

## Example Adaptations

Query: "Recent news about Apple"
→ Focus: 70% news sections, 20% price context, 10% brief metrics

Query: "Is Tesla overvalued?"
→ Focus: 70% valuation metrics/analysis, 20% growth context, 10% news

Query: "Analyze Amazon's risks"
→ Focus: 70% SEC filing risks/challenges, 20% market context, 10% financials

**Adapt your report structure intelligently based on what the user actually wants to know.**
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
        query_intent = state.get("query_intent", ["comprehensive"])

        print(f"\n📝 Publishing {output_mode.upper()} mode output...")
        print(f"   Query Intent: {', '.join(query_intent)}")

        # Select appropriate system prompt
        if output_mode == "report":
            system_prompt = REPORT_PUBLISHER_PROMPT
        else:
            system_prompt = CHAT_PUBLISHER_PROMPT.format(desired_length=desired_length)

        # Build context from execution results
        context = f"""
## User Query
{user_query}

## Query Intent
{', '.join(query_intent)}

## Output Requirements
- Mode: {output_mode.upper()}
- Desired Length: {desired_length}
- Primary Focus: {query_intent[0] if query_intent else 'comprehensive'}

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
- **ADAPT structure to the Query Intent**: {', '.join(query_intent)}
- If intent is "news" → Focus heavily on news sections, light on metrics
- If intent is "valuation" → Focus heavily on valuation/metrics, light on news
- If intent is "filings" → Focus heavily on SEC filing analysis
- If intent is "comparison" → Focus on side-by-side analysis
- Use ALL available tool outputs intelligently
- Create tables for quantitative data
- Synthesize insights across data sources
- Professional, in-depth analysis
- Adaptive section count (match the query focus)
- Rich markdown formatting

**Handling Missing/Failed Tool Data:**
- If some tools failed or returned no useful data, supplement with general knowledge
- Be transparent: "Note: Real-time data was unavailable, the following is based on general industry knowledge..."
- Still provide value to the user even if tools failed

**DO NOT use a rigid 10-section template. Adapt to what the user asked for.**

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

**Handling Missing/Failed Tool Data:**
- If tools failed or returned no data, answer from general knowledge
- Be transparent about using general knowledge vs. live data
- Still provide helpful information to the user

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
