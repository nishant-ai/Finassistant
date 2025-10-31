# Multi-Agent System Architecture

## 🏗️ System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT                                  │
│  "[Chat] What's Apple's P/E ratio?"                                 │
│  "[Report] Analyze Tesla's financial health"                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PARSE REQUEST NODE                               │
│  - Extract [Chat] or [Report] tag                                   │
│  - Determine desired length                                         │
│  - Clean query text                                                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    🎯 PLANNER AGENT                                 │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ LLM: Gemini 2.0 Flash (Temperature: 0)                        │ │
│  │                                                                │ │
│  │ Inputs:                                                        │ │
│  │  • User query                                                  │ │
│  │  • Output mode (chat/report)                                   │ │
│  │  • Tool catalog (23+ tools)                                    │ │
│  │                                                                │ │
│  │ Outputs:                                                       │ │
│  │  • Execution plan (JSON)                                       │ │
│  │  • Tool selections                                             │ │
│  │  • Parameter specifications                                    │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Plan Example:                                                      │
│  {                                                                  │
│    "steps": [                                                       │
│      {                                                              │
│        "step_number": 1,                                            │
│        "tool_name": "get_valuation_metrics",                        │
│        "tool_args": {"ticker": "AAPL"}                              │
│      }                                                              │
│    ]                                                                │
│  }                                                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    🔧 FINANCIAL AGENT                               │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ NO LLM - Direct Tool Execution                                 │ │
│  │                                                                │ │
│  │ Loop Through Plan Steps:                                       │ │
│  │  ┌─────────────────────────────────────────────────┐          │ │
│  │  │ Step 1: Execute get_valuation_metrics(AAPL)    │          │ │
│  │  │ Result: "P/E: 28.5, P/S: 7.2, ..."             │          │ │
│  │  └─────────────────────────────────────────────────┘          │ │
│  │                          │                                      │ │
│  │                          ▼                                      │ │
│  │  ┌─────────────────────────────────────────────────┐          │ │
│  │  │ Step 2: Execute get_profitability_metrics(...)  │          │ │
│  │  │ Result: "Profit Margin: 25.4%, ROE: 147%, ..."  │          │ │
│  │  └─────────────────────────────────────────────────┘          │ │
│  │                          │                                      │ │
│  │                          ▼                                      │ │
│  │                        [...]                                    │ │
│  │                                                                │ │
│  │ Collects all outputs → passes to Publisher                    │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Available Tools (23):                                              │
│  • Quantitative: valuation, profitability, growth, price, analysts │
│  • News: stock news, market news, article content                  │
│  • SEC: filings, financial data, comparisons                        │
│  • RAG: semantic search, multi-doc analysis                         │
│  • Web: real-time search, financial search, market news             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                   ┌─────────┴─────────┐
                   │ All steps done?   │
                   └─────────┬─────────┘
                             │ YES
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    📝 PUBLISHER AGENT                               │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ LLM: Gemini 2.0 Flash (Temperature: 0.3)                      │ │
│  │                                                                │ │
│  │ Inputs:                                                        │ │
│  │  • All tool outputs from Financial Agent                      │ │
│  │  • Output mode (chat/report)                                   │ │
│  │  • Desired length                                              │ │
│  │                                                                │ │
│  │ CHAT MODE:                    REPORT MODE:                     │ │
│  │ ┌──────────────────┐         ┌──────────────────┐            │ │
│  │ │ Conversational   │         │ Professional     │            │ │
│  │ │ 3-4 paragraphs   │         │ 8-15 sections    │            │ │
│  │ │ Simple format    │         │ Rich formatting  │            │ │
│  │ │ Direct answer    │         │ Executive summary│            │ │
│  │ └──────────────────┘         └──────────────────┘            │ │
│  │                                                                │ │
│  │ Output: Web-friendly Markdown                                  │ │
│  └───────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FINAL OUTPUT                                   │
│                                                                     │
│  CHAT MODE EXAMPLE:                                                 │
│  ───────────────────────────────────────────────────────           │
│  Apple (AAPL) currently has a P/E ratio of 28.5, which is         │
│  slightly above the tech sector average of 25.3...                 │
│                                                                     │
│  The company demonstrates strong profitability with a profit       │
│  margin of 25.4% and ROE of 147%...                                │
│                                                                     │
│  *Note: This is informational analysis, not investment advice.*    │
│  ───────────────────────────────────────────────────────           │
│                                                                     │
│  REPORT MODE EXAMPLE:                                               │
│  ───────────────────────────────────────────────────────           │
│  # Tesla Inc. Financial Analysis Report                            │
│                                                                     │
│  ## Executive Summary                                               │
│  Tesla demonstrates strong growth trajectory with revenue          │
│  increasing 51% YoY...                                              │
│                                                                     │
│  ## 1. Market Performance                                           │
│  | Metric | Value |                                                 │
│  |--------|-------|                                                 │
│  | Price  | $242  |                                                 │
│  ...                                                                │
│  ───────────────────────────────────────────────────────           │
└─────────────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow Diagram

```
User Query
    │
    ├─→ [Chat] tag detected
    │   └─→ Planner creates minimal plan (1-3 tools)
    │       └─→ Financial executes quickly
    │           └─→ Publisher creates concise response
    │
    └─→ [Report] tag detected
        └─→ Planner creates exhaustive plan (5-10+ tools)
            └─→ Financial executes comprehensively
                └─→ Publisher creates detailed report
```

## 🔄 State Flow

```
MultiAgentState {
  ┌─ Parse Phase ────────────────────────────────────┐
  │ user_query: "What's Apple's P/E ratio?"          │
  │ output_mode: "chat"                              │
  │ desired_length: "3-4 paragraphs"                 │
  └──────────────────────────────────────────────────┘
             ↓
  ┌─ Planning Phase ──────────────────────────────────┐
  │ plan: [                                           │
  │   {step: 1, tool: "get_valuation_metrics", ...}   │
  │ ]                                                 │
  │ total_steps: 1                                    │
  └──────────────────────────────────────────────────┘
             ↓
  ┌─ Execution Phase ─────────────────────────────────┐
  │ current_step: 0 → 1                               │
  │ execution_results: [                              │
  │   {success: true, output: "P/E: 28.5..."}         │
  │ ]                                                 │
  │ all_tool_outputs: {                               │
  │   "step_1": "P/E: 28.5, P/S: 7.2..."              │
  │ }                                                 │
  └──────────────────────────────────────────────────┘
             ↓
  ┌─ Publishing Phase ────────────────────────────────┐
  │ final_output: "Apple (AAPL) currently has..."     │
  │ output_format: "markdown"                         │
  └──────────────────────────────────────────────────┘
}
```

## 🎯 Tool Selection Logic

```
┌────────────────────────────────────────────────────────┐
│             PLANNER'S DECISION TREE                    │
└────────────────────────────────────────────────────────┘

Query: "What's Apple's P/E ratio?"
  │
  ├─ Mode: [Chat]
  │   ├─ Complexity: Minimal
  │   └─ Tools: 1 tool
  │       └─ get_valuation_metrics(AAPL)
  │
Query: "Analyze Tesla comprehensively" [Report]
  │
  ├─ Mode: [Report]
  │   ├─ Complexity: Exhaustive
  │   └─ Tools: 8 tools
  │       ├─ get_stock_price_summary(TSLA)
  │       ├─ get_valuation_metrics(TSLA)
  │       ├─ get_profitability_metrics(TSLA)
  │       ├─ get_historical_growth(TSLA)
  │       ├─ get_analyst_recommendations(TSLA)
  │       ├─ semantic_search_sec_filing(TSLA, "risks")
  │       ├─ get_stock_news(TSLA, 30)
  │       └─ financial_web_search(TSLA, "earnings")
  │
Query: "Compare Apple and Microsoft" [Chat]
  │
  ├─ Mode: [Chat]
  │   ├─ Complexity: Moderate
  │   └─ Tools: 3 tools
  │       ├─ compare_key_metrics([AAPL, MSFT])
  │       ├─ get_stock_news(AAPL, 7)
  │       └─ get_stock_news(MSFT, 7)
```

## ⚡ Performance Characteristics

```
┌─────────────────────────────────────────────────────────┐
│                   CHAT MODE                             │
├─────────────────────────────────────────────────────────┤
│ LLM Calls:     2 (Planner + Publisher)                  │
│ Tool Calls:    1-3                                      │
│ Total Time:    5-15 seconds                             │
│ Cost:          ~$0.001-0.005                            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  REPORT MODE                            │
├─────────────────────────────────────────────────────────┤
│ LLM Calls:     2 (Planner + Publisher)                  │
│ Tool Calls:    5-10+                                    │
│ Total Time:    30-90 seconds                            │
│ Cost:          ~$0.01-0.05                              │
└─────────────────────────────────────────────────────────┘

Breakdown:
  Parse:     <0.1s
  Planning:  2-3s   (LLM call)
  Execution: 3-60s  (tool calls)
  Publishing: 2-5s   (LLM call)
```

## 🧩 Component Relationships

```
┌──────────────────────────────────────────────────────────┐
│                   COMPONENTS                             │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐                                    │
│  │ Request Parser  │                                     │
│  │  - parse_user   │                                     │
│  │  - extract tags │                                     │
│  └────────┬────────┘                                    │
│           │ provides                                     │
│           ▼                                              │
│  ┌─────────────────┐                                    │
│  │ Planner Agent   │◄───── Tool Catalog                 │
│  │  - create_plan  │                                     │
│  │  - select_tools │                                     │
│  └────────┬────────┘                                    │
│           │ plan                                         │
│           ▼                                              │
│  ┌─────────────────┐                                    │
│  │ Financial Agent │◄───── 23 Financial Tools           │
│  │  - execute_step │                                     │
│  │  - collect_data │                                     │
│  └────────┬────────┘                                    │
│           │ results                                      │
│           ▼                                              │
│  ┌─────────────────┐                                    │
│  │ Publisher Agent │◄───── Format Templates             │
│  │  - synthesize   │                                     │
│  │  - format_output│                                     │
│  └────────┬────────┘                                    │
│           │                                              │
│           ▼                                              │
│  ┌─────────────────┐                                    │
│  │ Markdown Output │                                     │
│  └─────────────────┘                                    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 🎨 Output Format Comparison

```
┌────────────────────────────────────────────────────────┐
│                  CHAT vs REPORT                        │
├────────────────────────────────────────────────────────┤
│                                                        │
│  CHAT MODE                  REPORT MODE                │
│  ─────────                  ───────────                │
│                                                        │
│  Structure:                 Structure:                 │
│  • 3-4 paragraphs           • Executive Summary        │
│  • Direct answer            • 8-15 sections            │
│  • Optional table           • Multiple tables          │
│  • Brief conclusion         • Detailed analysis        │
│                             • Key takeaways            │
│                                                        │
│  Formatting:                Formatting:                │
│  • Simple markdown          • Rich markdown            │
│  • **Bold** emphasis        • Headers (##, ###)        │
│  • Basic lists              • Tables                   │
│                             • Bullet lists             │
│                             • Emphasis                 │
│                                                        │
│  Tone:                      Tone:                      │
│  • Conversational           • Professional            │
│  • Friendly                 • Analytical              │
│  • Concise                  • Comprehensive           │
│                                                        │
│  Use Case:                  Use Case:                  │
│  • Quick questions          • Deep research           │
│  • Metric lookup            • Stakeholder reports     │
│  • Comparisons              • Investment analysis     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

**Legend**:
- `→` : Data flow
- `▼` : Sequential step
- `◄─` : Input from
- `┌┐└┘` : Component boundaries
