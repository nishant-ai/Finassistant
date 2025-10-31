# Multi-Agent Financial Analysis System

A sophisticated three-agent system for financial research and analysis with adaptive output modes.

## 🏗️ Architecture

```
User Query
    ↓
[Parse Request] - Extract [Chat] or [Report] tag
    ↓
[PLANNER AGENT] - Creates optimal execution plan
    ↓
[FINANCIAL AGENT] - Executes tools step-by-step (loops)
    ↓
[PUBLISHER AGENT] - Formats output (Chat vs Report)
    ↓
Final Output (Markdown)
```

## 🤖 The Three Agents

### 1. **Planner Agent** 🎯
- **Role**: Strategic planning and tool selection
- **Input**: User query + output mode
- **Output**: Structured execution plan
- **Capabilities**:
  - Understands all 23+ available financial tools
  - Adapts plan complexity based on [Chat] vs [Report]
  - Optimizes for speed (Chat) or depth (Report)
  - Creates logical tool execution sequences

### 2. **Financial Agent** 🔧
- **Role**: Tool execution and data collection
- **Input**: Execution plan from Planner
- **Output**: Raw tool outputs
- **Capabilities**:
  - Executes tools sequentially with proper parameters
  - Handles errors gracefully
  - Collects and aggregates results
  - Loops until all plan steps complete

### 3. **Publisher Agent** 📝
- **Role**: Content formatting and presentation
- **Input**: All tool outputs + mode
- **Output**: Web-friendly formatted content
- **Capabilities**:
  - **Chat Mode**: Conversational, concise (3-4 paragraphs)
  - **Report Mode**: Comprehensive, structured (8-15 sections)
  - Rich markdown formatting (tables, lists, emphasis)
  - Synthesizes insights across multiple data sources

## 📋 Output Modes

### [Chat] Mode
**Purpose**: Quick, conversational responses

**Characteristics**:
- Length: 3-4 paragraphs (customizable)
- Tools: 1-3 tools maximum
- Tone: Conversational, friendly
- Format: Simple markdown (paragraphs, occasional tables)
- Speed: Fast (5-15 seconds)

**Example**:
```
[Chat] What's Apple's P/E ratio?
```

**Output Structure**:
- Direct answer
- Supporting data
- Brief context
- Simple disclaimer

### [Report] Mode
**Purpose**: In-depth, comprehensive analysis

**Characteristics**:
- Length: 8-15 sections, comprehensive
- Tools: 5-10+ tools for thorough coverage
- Tone: Professional, analytical
- Format: Rich markdown (tables, structured sections)
- Speed: Slower (30-90 seconds)

**Example**:
```
[Report] Analyze Tesla's financial health
```

**Output Structure**:
- Executive Summary
- Market Performance
- Valuation Analysis
- Profitability & Efficiency
- Growth Trajectory
- Financial Position
- Market Sentiment & News
- Risks & Challenges
- Strategic Initiatives
- Analyst Perspective
- Conclusions
- Key Takeaways

## 🎮 Usage

### Command Line
```bash
# Chat mode
python -m agent.app_multi_agent "[Chat] What's NVDA's current price?"

# Report mode
python -m agent.app_multi_agent "[Report] Comprehensive analysis of Microsoft"

# Chat with length specification
python -m agent.app_multi_agent "[Chat] Compare Apple and Google - keep it brief"
```

### Interactive Mode
```bash
python -m agent.app_multi_agent

# Then enter queries interactively:
You: [Chat] What happened to the market today?
You: [Report] Deep dive into semiconductor industry
```

### Python API
```python
from agent.app_multi_agent import run_multi_agent

# Chat mode
result = run_multi_agent("[Chat] What's Tesla's P/E ratio?")
print(result)

# Report mode
result = run_multi_agent("[Report] Analyze Amazon's financial performance")
print(result)
```

## 🔧 Available Tools (23 Total)

### Quantitative Analysis (6 tools)
- `get_valuation_metrics` - P/E, P/S, PEG ratios
- `get_profitability_metrics` - Margins, ROA, ROE
- `get_historical_growth` - Revenue/earnings growth
- `get_stock_price_summary` - Price, ranges, volatility
- `get_analyst_recommendations` - Ratings, targets
- `compare_key_metrics` - Multi-company comparison

### News & Sentiment (3 tools)
- `get_stock_news` - Company-specific news
- `get_market_news` - Market-wide news
- `get_full_article_content` - Deep article reading

### SEC Filings (3 tools)
- `get_sec_filing_summary` - Filing overview
- `get_sec_financial_data` - Financial statements
- `compare_sec_filings` - Multi-year comparison

### RAG Deep Analysis (5 tools)
- `semantic_search_sec_filing` - Semantic search in filings
- `semantic_search_news` - Historical news search
- `multi_document_analysis` - Most comprehensive
- `index_news_for_ticker` - Prepare news for search
- `rag_system_status` - Check RAG status

### Web Search (4 tools)
- `web_search` - Real-time web search
- `financial_web_search` - Company-specific search
- `real_time_market_search` - Breaking news
- `search_and_summarize` - Deep web research

## 📊 Example Queries

### Chat Mode Examples
```
[Chat] What's Apple's P/E ratio?
[Chat] Compare Microsoft and Google
[Chat] What happened to NVIDIA today?
[Chat] Give me 2 paragraphs on Tesla's profitability
[Chat] Quick summary of market news - keep it brief
```

### Report Mode Examples
```
[Report] Analyze Tesla's financial health
[Report] Comprehensive analysis of Apple vs Microsoft
[Report] Deep dive into semiconductor industry trends
[Report] Evaluate Amazon's growth prospects
[Report] Full analysis of Meta's business strategy
```

### Mixed Examples
```
Compare AAPL, MSFT, GOOGL [Chat]
What are the risks for NVDA? [Report]
Market overview today [Chat] 5 sentences
```

## 🔄 Workflow Details

### Step-by-Step Execution

1. **Parse Phase**
   - Extract [Chat] or [Report] tag
   - Determine desired length
   - Clean query text

2. **Planning Phase**
   - Planner analyzes query
   - Selects optimal tools
   - Creates execution order
   - Returns JSON plan

3. **Execution Phase** (loops)
   - Financial agent executes Step 1
   - Collects result
   - Executes Step 2
   - ... continues until all steps complete

4. **Publishing Phase**
   - Publisher receives all results
   - Synthesizes insights
   - Formats based on mode
   - Returns markdown output

### Example Execution Log
```
==================================================================
🎯 MULTI-AGENT FINANCIAL ANALYSIS SYSTEM
==================================================================
📥 Raw Query: [Chat] What's Apple's P/E ratio?
✨ Clean Query: What's Apple's P/E ratio?
📋 Mode: Conversational response (3-4 paragraphs)
==================================================================

🔧 Executing Step 1/1: Fetch Apple's valuation ratios
   Tool: get_valuation_metrics({'ticker': 'AAPL'})
   ✅ Success - Output length: 234 characters

📝 Publishing CHAT mode output...
   ✅ Published - Output length: 512 characters

==================================================================
📊 EXECUTION SUMMARY
==================================================================
Query: What's Apple's P/E ratio?
Mode: CHAT
Total Steps: 1
Completed: 1
Errors: No
==================================================================
```

## 🎨 Output Formatting

### Chat Mode Format
```markdown
[Direct answer to the question]

[Supporting data with key metrics in **bold**]

[Context and interpretation]

*Note: Informational analysis, not investment advice.*
```

### Report Mode Format
```markdown
# [Company] Financial Analysis Report

## Executive Summary
[2-3 paragraph overview]

## 1. Overview
[Current state]

## 2. Market Performance
[Price data, trends]

| Metric | Value |
|--------|-------|
| Current Price | $XXX |

## 3. Valuation Analysis
[P/E, P/S ratios]

## 4. Profitability & Efficiency
[Margins, returns]

...

## Conclusions
[Summary]

## Key Takeaways
- Point 1
- Point 2
- Point 3

---
*Report generated [date]. This is informational analysis, not investment advice.*
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Optional (defaults shown)
PLANNER_MODEL=gemini-2.0-flash-exp
AGENT_MODEL=gemini-2.0-flash-exp
PUBLISHER_MODEL=gemini-2.0-flash-exp
```

### Model Selection
- **Planner**: Uses Flash for speed and cost efficiency
- **Financial**: No LLM (direct tool calls)
- **Publisher**: Uses Flash with higher temperature (0.3) for natural writing

## 🔍 Advanced Features

### Length Customization
```
[Chat] Analysis of TSLA - give me 5 paragraphs
[Chat] Quick 2 sentence summary
Compare AAPL and MSFT [Chat] keep it detailed
```

### Tool Selection Strategy

**Chat Mode** (minimal/moderate):
- Prefers fast tools (quantitative, basic news)
- 1-3 tools maximum
- Direct queries

**Report Mode** (exhaustive):
- Uses slow/comprehensive tools (RAG, multi-doc)
- 5-10+ tools
- Multiple data sources
- Cross-referencing

### Error Handling
- Graceful degradation on tool failures
- Continues execution even if some steps fail
- Reports errors in final output
- Fallback plans when parsing fails

## 📁 File Structure

```
agent/
├── app_multi_agent.py           # Main application
├── graph/
│   ├── multi_agent_state.py     # State management
│   ├── request_parser.py        # [Chat]/[Report] parsing
│   ├── planner_agent.py         # Planner agent
│   ├── financial_agent.py       # Financial execution agent
│   ├── publisher_agent.py       # Publisher agent
│   └── multi_agent_graph.py     # Graph orchestration
└── tools/                       # 23+ financial tools
```

## 🚀 Performance

### Chat Mode
- **Speed**: 5-15 seconds
- **API Calls**: 2-3 LLM calls (Planner + Publisher)
- **Tools**: 1-3 tool executions
- **Cost**: Low (~$0.001-0.005 per query)

### Report Mode
- **Speed**: 30-90 seconds
- **API Calls**: 2-3 LLM calls (Planner + Publisher)
- **Tools**: 5-10+ tool executions
- **Cost**: Moderate (~$0.01-0.05 per query)

## 🎯 Design Principles

1. **Separation of Concerns**: Each agent has one clear responsibility
2. **Adaptive Complexity**: Plan adjusts to output mode
3. **Tool-Aware Planning**: Planner knows all tool capabilities
4. **Error Resilience**: Graceful handling of failures
5. **User Control**: [Chat] vs [Report] puts user in control
6. **Web-Friendly**: Markdown output ready for frontend parsing

## 🔮 Future Enhancements

- [ ] Support for [Summary] mode (1-2 sentences)
- [ ] Chart/graph generation (plotly, matplotlib)
- [ ] PDF report export
- [ ] Streaming output for long reports
- [ ] Multi-language support
- [ ] Custom report templates
- [ ] Forex-specific tools and handling
- [ ] Cryptocurrency analysis tools

## 📝 License

MIT License - See LICENSE file for details

---

**Built with**: LangGraph, Google Gemini, yfinance, SEC-API, DuckDuckGo Search
