# Tool Selection Guide for Financial AI Agent

## Overview

Your agent has **22 active tools** organized into 5 categories. The LLM (Gemini 2.0 Flash) reads the tool docstrings and selects the most appropriate tool(s) based on the user's query.

## How the Agent Decides

1. **User asks a question** → LLM analyzes the query
2. **LLM reads ALL tool descriptions** (docstrings)
3. **Selects best tool(s)** based on:
   - Keywords in the query ("latest", "comprehensive", "risks", etc.)
   - Tool descriptions ("PRIMARY TOOL for...", "When to use...")
   - Example queries in the docstring
4. **Executes tool(s)** and synthesizes response

## Tool Categories & Decision Tree

### 1. SEC Filing Questions

**User Query Type** → **Tool to Use**

- ❓ "What are Apple's risks?" → ✅ `semantic_search_sec_filing` (RAG - semantic understanding)
- ❓ "Describe Microsoft's AI strategy in their 10-K" → ✅ `semantic_search_sec_filing` (RAG)
- ❓ "Does Tesla's 10-K mention 'Cybertruck' exactly?" → ⚠️ `search_sec_filing` (exact phrase only)
- ❓ "Give me an overview of Apple's 10-K" → ✅ `get_sec_filing_summary` (quick preview)
- ❓ "Show me Apple's balance sheet" → ✅ `get_sec_financial_data` (XBRL data)

**Default Rule:** Use `semantic_search_sec_filing` for 95% of SEC filing questions.

---

### 2. News Questions

**User Query Type** → **Tool to Use**

- ❓ "Latest news about Apple" → ✅ `get_stock_news` (real-time, 7-30 days)
- ❓ "What's in the market news today?" → ✅ `get_market_news` (general headlines)
- ❓ "What themes appear in Tesla news?" → ✅ `semantic_search_news` (historical, indexed)
- ❓ "Read this article: [URL]" → ✅ `get_full_article_content` (extract full text)

**Key Distinction:**
- **Real-time news (now)** → `get_stock_news` or `get_market_news`
- **Historical analysis (themes)** → `semantic_search_news` (requires indexing)

---

### 3. Web Search Questions

**User Query Type** → **Tool to Use**

- ❓ "What's Apple's stock price right now?" → ✅ `web_search` or `financial_web_search`
- ❓ "When is NVIDIA's earnings call?" → ✅ `financial_web_search`
- ❓ "S&P 500 movement today" → ✅ `real_time_market_search`
- ❓ "Who is the current CEO of Tesla?" → ✅ `web_search`
- ❓ "Comprehensive analysis of this topic" → ✅ `search_and_summarize` (deep search)

**Key Distinction:**
- **Company-specific** → `financial_web_search`
- **Market-wide events** → `real_time_market_search`
- **General info** → `web_search`
- **Deep research** → `search_and_summarize`

---

### 4. Comprehensive Analysis

**User Query Type** → **Tool to Use**

- ❓ "Give me a comprehensive analysis of Microsoft's cloud strategy" → ✅ `multi_document_analysis`
- ❓ "Analyze Apple's risks from all sources" → ✅ `multi_document_analysis`
- ❓ "Compare official statements with media coverage" → ✅ `multi_document_analysis`

**Rule:** Keywords like "comprehensive", "overall", "all sources", "complete picture" trigger `multi_document_analysis`.

---

### 5. Quantitative Data

**User Query Type** → **Tool to Use**

- ❓ "Apple's P/E ratio" → ✅ `get_valuation_metrics`
- ❓ "Microsoft's profit margin" → ✅ `get_profitability_metrics`
- ❓ "Tesla's revenue growth" → ✅ `get_historical_growth`
- ❓ "NVIDIA stock price summary" → ✅ `get_stock_price_summary`
- ❓ "Analyst ratings for Apple" → ✅ `get_analyst_recommendations`
- ❓ "Compare Apple vs Microsoft metrics" → ✅ `compare_key_metrics`

---

## Complete Tool List (22 Tools)

### Quantitative Analysis (6 tools)
1. ✅ `get_valuation_metrics` - P/E, PEG, P/B, etc.
2. ✅ `get_profitability_metrics` - Margins, ROE, ROA
3. ✅ `get_historical_growth` - Revenue/earnings growth
4. ✅ `get_stock_price_summary` - Price, volume, changes
5. ✅ `get_analyst_recommendations` - Buy/sell ratings
6. ✅ `compare_key_metrics` - Side-by-side comparison

### News Tools (3 tools)
7. ✅ `get_stock_news` - **PRIMARY** for real-time company news
8. ✅ `get_market_news` - **PRIMARY** for general market headlines
9. ✅ `get_full_article_content` - Extract full article text

### SEC Filing Tools (3 tools)
10. ✅ `get_sec_filing_summary` - Quick overview (first 5K chars)
11. ✅ `get_sec_financial_data` - XBRL financial statements
12. ✅ `compare_sec_filings` - Compare multiple years

### RAG-Enhanced Tools (5 tools) ⭐ PRIMARY FOR DEEP ANALYSIS
13. ✅ `semantic_search_sec_filing` - **PRIMARY** SEC filing search (RAG)
14. ✅ `semantic_search_news` - Historical news themes (RAG)
15. ✅ `multi_document_analysis` - **MOST COMPREHENSIVE** (SEC + news)
16. ✅ `index_news_for_ticker` - Prepare news for semantic search
17. ✅ `rag_system_status` - Check RAG system health

### Web Search Tools (4 tools)
18. ✅ `web_search` - General real-time web search
19. ✅ `financial_web_search` - Company-specific real-time search
20. ✅ `real_time_market_search` - Breaking market news
21. ✅ `search_and_summarize` - Deep web research with content extraction

### Deprecated Tools (1 tool) ❌
22. ❌ `search_sec_filing` - **REMOVED** (use semantic_search_sec_filing instead)

---

## RAG vs Non-RAG Decision Matrix

| Question Type | Use RAG? | Tool | Why |
|---------------|----------|------|-----|
| "What are Apple's risks in their 10-K?" | ✅ YES | `semantic_search_sec_filing` | SEC filing content - semantic understanding needed |
| "Latest Apple news" | ❌ NO | `get_stock_news` | Real-time API - already fresh |
| "Comprehensive Apple analysis" | ✅ YES | `multi_document_analysis` | Multi-source synthesis - RAG combines SEC + news |
| "Apple stock price today" | ❌ NO | `web_search` | Real-time data - web search faster |
| "Historical news themes about AI" | ✅ YES | `semantic_search_news` | Historical analysis - semantic search needed |
| "Market news today" | ❌ NO | `get_market_news` | Real-time headlines - API faster |

---

## Keywords That Trigger Specific Tools

### RAG Tools (semantic_search_sec_filing)
- "what", "how", "why", "describe", "explain"
- "risks", "challenges", "strategy", "competitive advantages"
- "according to 10-K", "in their filing"

### Multi-Document Analysis
- "comprehensive", "overall", "complete", "all sources"
- "compare official vs media", "due diligence"
- "from multiple perspectives"

### Real-Time Tools (web_search, get_stock_news)
- "latest", "recent", "current", "today", "now"
- "breaking", "just announced", "this week"

### Historical RAG (semantic_search_news)
- "historical", "trends", "patterns", "themes"
- "over time", "past coverage"

---

## Performance Characteristics

| Tool | Speed | Coverage | Use Case |
|------|-------|----------|----------|
| `semantic_search_sec_filing` | First: 30-60s<br>After: 2-3s | 100% of filing | Deep SEC analysis |
| `search_sec_filing` (deprecated) | 2-3s | 30-50% of filing | Exact phrase only |
| `get_stock_news` | 2-3s | Last 30 days | Real-time news |
| `semantic_search_news` | 2-3s | Indexed articles | Historical themes |
| `multi_document_analysis` | 5-10s | SEC + news | Comprehensive |
| `web_search` | 3-5s | Entire web | Real-time info |

---

## Testing Your Agent's Tool Selection

Run these test queries to verify correct tool selection:

```bash
# Should use semantic_search_sec_filing (RAG)
python agent/app.py "What are Apple's main risks according to their 10-K?"

# Should use get_stock_news (real-time)
python agent/app.py "What's the latest news about Apple?"

# Should use web_search (real-time)
python agent/app.py "What is Apple's stock price right now?"

# Should use multi_document_analysis (comprehensive RAG)
python agent/app.py "Give me a comprehensive analysis of Microsoft's cloud strategy"

# Should use get_valuation_metrics (quantitative)
python agent/app.py "What is Tesla's P/E ratio?"

# Should use get_market_news (general headlines)
python agent/app.py "What's the market news today?"
```

---

## Summary: When to Use RAG

### ✅ Use RAG When:
1. **Large documents** - SEC filings (50-500 pages)
2. **Semantic understanding needed** - "What are the risks?" (finds synonyms)
3. **Historical analysis** - Themes over time in news coverage
4. **Multi-source synthesis** - Combining SEC + news
5. **Static content** - Documents don't change (perfect for caching)

### ❌ Don't Use RAG When:
1. **Real-time data** - Stock prices, breaking news
2. **Small, fresh content** - Recent news articles (API is faster)
3. **Exact matching** - Looking for specific product names
4. **Quantitative data** - Financial metrics from databases
5. **Constantly changing** - Web search results

---

## Key Principle

**The agent automatically selects tools based on docstrings. Your job is to write clear, distinct tool descriptions that guide the LLM to the right choice.**

**Default hierarchy:**
1. RAG tools for SEC filing content (`semantic_search_sec_filing`)
2. Real-time APIs for current news (`get_stock_news`)
3. Web search for very recent info (`web_search`)
4. Multi-document RAG for comprehensive analysis (`multi_document_analysis`)

This ensures the agent uses the most appropriate tool for each type of query.
