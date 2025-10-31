"""
Planner Agent - Creates execution plans for financial queries

The Planner Agent:
1. Analyzes the user query
2. Understands available tools and their capabilities
3. Creates a step-by-step execution plan
4. Adapts plan complexity based on [Chat] vs [Report] mode
"""

from typing import List, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import os
from agent.graph.multi_agent_state import MultiAgentState, PlanStep
from agent.graph.request_parser import get_plan_complexity


# Tool Catalog - Describes all available tools for the planner
TOOL_CATALOG = """
## Available Financial Analysis Tools

### 1. QUANTITATIVE ANALYSIS TOOLS (Stock-focused, requires ticker)
- **get_valuation_metrics(ticker: str)**
  Returns: P/E ratio, P/S ratio, PEG ratio, EV/EBITDA
  Use for: Valuation questions, "Is stock overvalued?", price ratios
  Speed: Fast (1-2s)

- **get_profitability_metrics(ticker: str)**
  Returns: Profit margin, operating margin, ROA, ROE
  Use for: Profitability analysis, efficiency questions
  Speed: Fast (1-2s)

- **get_historical_growth(ticker: str)**
  Returns: YoY revenue and income growth (3 years)
  Use for: Growth trends, historical performance
  Speed: Fast (1-2s)

- **get_stock_price_summary(ticker: str)**
  Returns: Current price, 52-week range, moving averages, beta
  Use for: Price questions, volatility, market performance
  Speed: Fast (1-2s)

- **get_analyst_recommendations(ticker: str)**
  Returns: Latest analyst ratings and price targets
  Use for: "What do analysts think?", consensus ratings
  Speed: Fast (1-2s)

- **compare_key_metrics(tickers: List[str])**
  Returns: Side-by-side comparison table
  Use for: Comparing 2+ companies
  Speed: Fast (2-3s)
  Example: compare_key_metrics(['AAPL', 'MSFT', 'GOOGL'])

### 2. NEWS & SENTIMENT TOOLS
- **get_stock_news(ticker: str, days: int = 7)**
  Returns: Recent news articles for a company
  Use for: "What's happening with X?", recent developments
  Speed: Fast (2-3s)

- **get_market_news(category: str = "general", max_articles: int = 10)**
  Returns: Market-wide news
  Categories: "general", "technology", "finance", "crypto"
  Use for: Market overview, sector news
  Speed: Fast (2-3s)

- **get_full_article_content(url: str)**
  Returns: Full article text
  Use for: Deep reading of specific articles
  Speed: Moderate (3-5s)

### 3. SEC FILING TOOLS (Official company filings)
- **get_sec_filing_summary(ticker: str, filing_type: str = "10-K")**
  Returns: Quick overview of latest filing
  Filing types: "10-K" (annual), "10-Q" (quarterly), "8-K" (current)
  Speed: Moderate (3-5s)

- **get_sec_financial_data(ticker: str, filing_type: str = "10-K")**
  Returns: Extracted financial statements
  Speed: Moderate (3-5s)

- **compare_sec_filings(ticker: str, years: List[int])**
  Returns: Multi-year comparison
  Speed: Slow (5-10s)

### 4. RAG-ENHANCED DEEP ANALYSIS TOOLS
- **semantic_search_sec_filing(ticker: str, query: str)**
  Returns: Relevant sections from SEC filings using semantic search
  Use for: Specific questions about filings (risks, strategy, etc.)
  Speed: Moderate (5-8s)

- **semantic_search_news(ticker: str, query: str, days_back: int = 30)**
  Returns: Semantically relevant news articles
  Use for: Historical news search on specific topics
  Speed: Moderate (5-8s)

- **multi_document_analysis(ticker: str, query: str)**
  Returns: MOST COMPREHENSIVE - combines SEC filings + news
  Use for: Deep research questions requiring multiple sources
  Speed: Slow (10-15s)

- **index_news_for_ticker(ticker: str, days_back: int = 30)**
  Returns: Indexes news for semantic search (prerequisite)
  Speed: Slow (10-20s, only needed once per ticker)

### 5. WEB SEARCH TOOLS (Real-time information)
- **web_search(query: str, max_results: int = 10)**
  Returns: Real-time web search results
  Use for: Very recent events, current prices, general web queries
  Speed: Moderate (3-5s)

- **financial_web_search(ticker: str, query: str, max_results: int = 8)**
  Returns: Financial-focused web search for a company
  Use for: Company-specific real-time info
  Speed: Moderate (3-5s)

- **real_time_market_search(query: str, time_filter: str = "day")**
  Returns: Breaking market news (uses news search)
  Time filters: "day", "week", "month"
  Use for: Market-wide events, economic news
  Speed: Moderate (3-5s)

- **search_and_summarize(query: str, num_sources: int = 3)**
  Returns: Deep web research with full content extraction
  Use for: Comprehensive web research
  Speed: Very Slow (10-15s)

## Tool Selection Guidelines

### For CHAT mode (brief responses):
- Use 1-3 tools maximum
- Prefer fast tools (quantitative, news)
- Avoid slow tools unless absolutely necessary
- Direct, single-purpose queries

### For REPORT mode (comprehensive):
- Use 5-10+ tools for thorough coverage
- Combine multiple tool categories
- Include comparative analysis
- Use RAG tools for deep insights
- Add web search for current context

### Tool Combinations:
- **Company Analysis**: valuation + profitability + growth + news
- **Comparison**: compare_key_metrics + individual metrics for details
- **Deep Research**: multi_document_analysis + web_search + financial data
- **Current Events**: real_time_market_search + get_stock_news
- **Historical Deep Dive**: semantic_search_sec_filing + compare_sec_filings
"""


PLANNER_SYSTEM_PROMPT = f"""You are an expert Financial Research Planner Agent.

Your job is to create OPTIMAL execution plans for financial queries by selecting the right tools in the right order.

{TOOL_CATALOG}

## Your Task

Given a user query and output mode (Chat or Report), create a JSON plan with these steps:

1. **Analyze** what the user wants to know
2. **Select** the minimum necessary tools (Chat) or comprehensive tools (Report)
3. **Order** tools logically (basic info → detailed analysis → synthesis)
4. **Specify** exact tool calls with parameters

## Output Format

Return a JSON object with this EXACT structure:

{{
  "plan_summary": "Brief description of the plan",
  "reasoning": "Why you chose these tools and this order",
  "complexity": "minimal|moderate|comprehensive|exhaustive",
  "steps": [
    {{
      "step_number": 1,
      "description": "What this step accomplishes",
      "tool_name": "exact_tool_name",
      "tool_args": {{"arg1": "value1"}},
      "reasoning": "Why this tool for this step",
      "expected_output": "What data this will provide"
    }}
  ]
}}

## Important Rules

1. **Tool names must be EXACT** - match the function names above
2. **Ticker symbols** - always uppercase (AAPL, MSFT, TSLA)
3. **List arguments** - use proper JSON arrays: ["AAPL", "MSFT"]
4. **Order matters** - fast tools first, context before details
5. **No hallucination** - only use tools from the catalog above
6. **Be efficient** - don't call redundant tools

## Examples

### Example 1: Chat Mode - Simple Query
Query: "[Chat] What's Apple's P/E ratio?"
Complexity: minimal

{{
  "plan_summary": "Get Apple's valuation metrics",
  "reasoning": "Simple query needs just one valuation tool",
  "complexity": "minimal",
  "steps": [
    {{
      "step_number": 1,
      "description": "Fetch Apple's valuation ratios including P/E",
      "tool_name": "get_valuation_metrics",
      "tool_args": {{"ticker": "AAPL"}},
      "reasoning": "Direct tool to get P/E ratio",
      "expected_output": "P/E, P/S, PEG ratios"
    }}
  ]
}}

### Example 2: Chat Mode - Moderate Query
Query: "[Chat] Compare Microsoft and Google"
Complexity: moderate

{{
  "plan_summary": "Compare MSFT and GOOGL across key metrics",
  "reasoning": "Use comparison tool for side-by-side view, then add recent news for context",
  "complexity": "moderate",
  "steps": [
    {{
      "step_number": 1,
      "description": "Compare key financial metrics",
      "tool_name": "compare_key_metrics",
      "tool_args": {{"tickers": ["MSFT", "GOOGL"]}},
      "reasoning": "Most efficient way to compare multiple companies",
      "expected_output": "Side-by-side comparison of P/E, P/S, margins, ROE"
    }},
    {{
      "step_number": 2,
      "description": "Get recent Microsoft news",
      "tool_name": "get_stock_news",
      "tool_args": {{"ticker": "MSFT", "days": 7}},
      "reasoning": "Add current context for Microsoft",
      "expected_output": "Recent MSFT news articles"
    }},
    {{
      "step_number": 3,
      "description": "Get recent Google news",
      "tool_name": "get_stock_news",
      "tool_args": {{"ticker": "GOOGL", "days": 7}},
      "reasoning": "Add current context for Google",
      "expected_output": "Recent GOOGL news articles"
    }}
  ]
}}

### Example 3: Report Mode - Comprehensive
Query: "[Report] Analyze Tesla's financial health and growth prospects"
Complexity: exhaustive

{{
  "plan_summary": "Comprehensive Tesla analysis covering valuation, profitability, growth, filings, and market sentiment",
  "reasoning": "Report mode requires multi-faceted analysis using quantitative metrics, SEC filings, news, and deep research",
  "complexity": "exhaustive",
  "steps": [
    {{
      "step_number": 1,
      "description": "Get current market performance and price metrics",
      "tool_name": "get_stock_price_summary",
      "tool_args": {{"ticker": "TSLA"}},
      "reasoning": "Start with current market context",
      "expected_output": "Price, 52-week range, moving averages, beta"
    }},
    {{
      "step_number": 2,
      "description": "Analyze valuation ratios",
      "tool_name": "get_valuation_metrics",
      "tool_args": {{"ticker": "TSLA"}},
      "reasoning": "Assess if stock is over/undervalued",
      "expected_output": "P/E, P/S, PEG, EV/EBITDA"
    }},
    {{
      "step_number": 3,
      "description": "Evaluate profitability",
      "tool_name": "get_profitability_metrics",
      "tool_args": {{"ticker": "TSLA"}},
      "reasoning": "Understand profit generation efficiency",
      "expected_output": "Margins, ROA, ROE"
    }},
    {{
      "step_number": 4,
      "description": "Examine historical growth trends",
      "tool_name": "get_historical_growth",
      "tool_args": {{"ticker": "TSLA"}},
      "reasoning": "Show revenue and income growth trajectory",
      "expected_output": "3-year revenue and income growth"
    }},
    {{
      "step_number": 5,
      "description": "Get analyst perspectives",
      "tool_name": "get_analyst_recommendations",
      "tool_args": {{"ticker": "TSLA"}},
      "reasoning": "Include Wall Street consensus",
      "expected_output": "Analyst ratings and price targets"
    }},
    {{
      "step_number": 6,
      "description": "Search SEC filings for risk factors and strategy",
      "tool_name": "semantic_search_sec_filing",
      "tool_args": {{"ticker": "TSLA", "query": "business risks and growth strategy"}},
      "reasoning": "Get official company perspective on risks and plans",
      "expected_output": "Risk factors and strategic initiatives from 10-K"
    }},
    {{
      "step_number": 7,
      "description": "Get recent company news and sentiment",
      "tool_name": "get_stock_news",
      "tool_args": {{"ticker": "TSLA", "days": 30}},
      "reasoning": "Understand recent developments and market sentiment",
      "expected_output": "30 days of TSLA news"
    }},
    {{
      "step_number": 8,
      "description": "Search for real-time market developments",
      "tool_name": "financial_web_search",
      "tool_args": {{"ticker": "TSLA", "query": "latest financial results earnings"}},
      "reasoning": "Get most current financial information",
      "expected_output": "Recent earnings and financial updates"
    }}
  ]
}}

Now create a plan for the user's query.
"""


def create_planner_agent(llm: ChatGoogleGenerativeAI = None):
    """
    Creates the planner agent function.

    Args:
        llm: Optional LLM instance. If not provided, creates one.

    Returns:
        Planner function that takes state and returns updated state
    """

    if llm is None:
        llm = ChatGoogleGenerativeAI(
            model=os.getenv("PLANNER_MODEL", "gemini-2.0-flash-exp"),
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

    def planner_agent(state: MultiAgentState) -> Dict:
        """
        Planner agent that creates execution plan.

        Takes user query and creates structured plan with tool calls.
        """

        user_query = state["user_query"]
        output_mode = state["output_mode"]
        desired_length = state.get("desired_length", "standard")

        # Get complexity level
        complexity = get_plan_complexity(output_mode, desired_length)

        # Create planning prompt
        planning_prompt = f"""
Create an execution plan for this financial query:

**User Query**: {user_query}
**Output Mode**: {output_mode.upper()}
**Desired Length**: {desired_length}
**Plan Complexity**: {complexity}

Remember:
- CHAT mode: Use 1-3 tools, keep it focused and efficient
- REPORT mode: Use 5-10+ tools, be comprehensive and thorough
- Only use tools from the catalog
- Return valid JSON only, no other text
"""

        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=planning_prompt)
        ]

        # Get plan from LLM
        response = llm.invoke(messages)
        response_text = response.content

        # Parse JSON response
        try:
            # Clean up response - sometimes LLMs wrap JSON in markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            plan_data = json.loads(response_text)

            # Extract plan components
            plan_steps: List[PlanStep] = []
            for step in plan_data.get("steps", []):
                plan_steps.append({
                    "step_number": step["step_number"],
                    "description": step["description"],
                    "tool_name": step["tool_name"],
                    "tool_args": step["tool_args"],
                    "reasoning": step["reasoning"],
                    "expected_output": step["expected_output"]
                })

            return {
                "plan": plan_steps,
                "plan_summary": plan_data.get("plan_summary", ""),
                "planner_reasoning": plan_data.get("reasoning", ""),
                "total_steps": len(plan_steps),
                "current_step": 0,
                "completed_steps": 0,
                "execution_results": [],
                "all_tool_outputs": {},
                "has_errors": False,
                "error_messages": []
            }

        except json.JSONDecodeError as e:
            # Fallback plan in case of JSON parsing error
            print(f"JSON parsing error: {e}")
            print(f"Response was: {response_text}")

            # Create a minimal fallback plan
            fallback_plan = [{
                "step_number": 1,
                "description": "Perform web search to answer query",
                "tool_name": "web_search",
                "tool_args": {"query": user_query},
                "reasoning": "Fallback to web search due to planning error",
                "expected_output": "Web search results"
            }]

            return {
                "plan": fallback_plan,
                "plan_summary": "Fallback plan - web search",
                "planner_reasoning": f"Planning error, using fallback: {str(e)}",
                "total_steps": 1,
                "current_step": 0,
                "completed_steps": 0,
                "execution_results": [],
                "all_tool_outputs": {},
                "has_errors": True,
                "error_messages": [f"Planning error: {str(e)}"]
            }

    return planner_agent


# Testing
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Test the planner
    planner = create_planner_agent()

    test_state = {
        "user_query": "Compare Apple and Microsoft",
        "output_mode": "chat",
        "desired_length": "3-4 paragraphs",
        "messages": []
    }

    result = planner(test_state)
    print("Plan Summary:", result["plan_summary"])
    print("\nSteps:")
    for step in result["plan"]:
        print(f"  {step['step_number']}. {step['description']}")
        print(f"     Tool: {step['tool_name']}({step['tool_args']})")
