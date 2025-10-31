# Web Search Tools for Real-Time Information

## Overview

The web search tools provide real-time information gathering capabilities using DuckDuckGo search (no API key required). These tools fill the gap for current information that isn't available in historical documents like SEC filings or indexed news articles.

## Why Web Search?

**The Problem:**
- SEC filings are historical (filed quarterly/annually)
- News APIs have limited coverage and recency
- RAG system indexes documents but doesn't have real-time market data
- Need current stock prices, breaking news, and today's events

**The Solution:**
Web search tools that can:
- Find current stock prices and market data
- Get breaking news from the last 24 hours
- Research any topic with real-time web results
- Extract full content from web pages for deep analysis

## Tools Available (4 Total)

### 1. `web_search` - General Web Search

**Best for:** General queries, company information, current events

```python
web_search(query: str, max_results: int = 10) -> str
```

**Use cases:**
- "Latest news about Apple stock price today"
- "Current interest rates Federal Reserve 2025"
- "Microsoft earnings call date Q4 2024"
- "Recent merger activity in tech sector"

**Features:**
- Up to 20 results
- Returns titles, URLs, and snippets
- Timestamp included
- Fast (~2-3 seconds)

---

### 2. `financial_web_search` - Company-Specific Financial Search

**Best for:** Financial information about specific companies

```python
financial_web_search(ticker: str, query: str, max_results: int = 8) -> str
```

**Automatically enhances query with financial context!**

**Use cases:**
```python
# ticker="AAPL", query="current stock price"
# Searches: "AAPL current stock price stock financial market"

# ticker="TSLA", query="latest delivery numbers"
# Searches: "TSLA latest delivery numbers stock financial market"
```

**Features:**
- Ticker-focused results
- Financial context automatically added
- Optimized for market data
- Returns 8 most relevant results

---

### 3. `real_time_market_search` - Breaking Market News

**Best for:** Recent market movements, breaking news, economic data

```python
real_time_market_search(query: str, time_filter: str = "day") -> str
```

**Time filters:**
- `"day"` - Last 24 hours (default)
- `"week"` - Last 7 days
- `"month"` - Last 30 days

**Use cases:**
- "S&P 500 today market movement"
- "Federal Reserve interest rate decision"
- "Tech stocks performance this week"
- "Oil prices latest update"

**Features:**
- News-specific search (DuckDuckGo News)
- Time-filtered results
- Source and date attribution
- Perfect for market-moving events

---

### 4. `search_and_summarize` - Deep Research Tool

**Best for:** In-depth research requiring full page content

```python
search_and_summarize(query: str, num_sources: int = 3) -> str
```

**WARNING:** Slower (10-15 seconds) - fetches and extracts full web pages

**Use cases:**
- "Comprehensive analysis of semiconductor shortage impact"
- "Detailed explanation of recent banking crisis"
- "In-depth review of Apple Vision Pro market reception"

**Features:**
- Extracts full content from top results
- Returns 3000+ characters per source
- Multiple sources synthesized
- Most comprehensive search option

---

## Architecture

### Technology Stack

**Search Provider: DuckDuckGo**
- **Why?** No API key required (zero cost!)
- **Coverage:** Comprehensive web and news search
- **Privacy:** Doesn't track users
- **Reliability:** Well-maintained Python library

**Web Scraping:**
- `requests` for HTTP
- `BeautifulSoup` for HTML parsing
- Content extraction from main article/body
- Automatic cleanup of navigation/ads

### Components

```
agent/tools/search/
├── __init__.py          # Module exports
├── search.py            # Main implementation
└── README.md            # This file
```

**Class: `WebSearchEngine`**
- `search_duckduckgo()` - General web search
- `search_duckduckgo_news()` - News-specific search
- `extract_page_content()` - Full page content extraction
- `search_and_extract()` - Combined search + extraction

---

## Usage Examples

### Example 1: Current Stock Price

```
User: "What's Apple's stock price right now?"

Agent: [Calls financial_web_search("AAPL", "current stock price")]

Returns: Recent articles with current AAPL price, market cap, and trading info
```

### Example 2: Breaking Market News

```
User: "What happened in the market today?"

Agent: [Calls real_time_market_search("S&P 500 Dow Jones today", "day")]

Returns: News articles from last 24 hours about market movements
```

### Example 3: Deep Research

```
User: "Give me a comprehensive analysis of the AI chip shortage"

Agent: [Calls search_and_summarize("AI chip shortage analysis", 3)]

Returns: Full content extracted from 3 authoritative sources
```

### Example 4: General Company Info

```
User: "Tell me about SpaceX's recent launches"

Agent: [Calls web_search("SpaceX recent launches 2025")]

Returns: Recent news, press releases, and updates about SpaceX
```

---

## Comparison with Other Tools

### Web Search vs. News API Tools

| Feature | `get_stock_news` (NewsAPI) | `real_time_market_search` (Web) |
|---------|---------------------------|--------------------------------|
| **API Key** | Required (News API key) | None required |
| **Coverage** | Limited sources | All web sources |
| **Recency** | Up to 7 days back | Real-time + customizable |
| **Cost** | API limits apply | Free |
| **Results** | 10 max | Up to 20 |

**Recommendation:** Use web search for broader coverage and breaking news

### Web Search vs. RAG Semantic Search

| Feature | RAG Semantic Search | Web Search |
|---------|-------------------|------------|
| **Data Source** | Indexed documents (SEC, news) | Live web |
| **Latency** | 2-3s (if indexed) | 2-3s |
| **Coverage** | Historical documents | Real-time web |
| **Accuracy** | Very high (semantic) | Good (keyword-based) |
| **Best For** | Deep document analysis | Current information |

**Recommendation:** Use both! Web search for current data, RAG for historical analysis

---

## Performance

### Latency

| Tool | Average Time |
|------|-------------|
| `web_search` | 2-3 seconds |
| `financial_web_search` | 2-3 seconds |
| `real_time_market_search` | 2-4 seconds |
| `search_and_summarize` | 10-15 seconds |

### Cost

**Total Cost: $0/month**

- DuckDuckGo API: Free
- No API keys required
- No rate limits (reasonable use)
- No subscription fees

Compare to:
- Google Custom Search: $5/1000 queries
- Bing Search API: $7/1000 queries
- Serp API: $50+/month

---

## Integration with Agent

The agent **automatically** chooses the right search tool based on the query:

```
User Query Analysis:
├─ Contains company ticker + "price/stock" → financial_web_search
├─ Contains "today/now/current/latest" → real_time_market_search
├─ Request for "detailed/comprehensive" → search_and_summarize
└─ General query → web_search
```

**You don't need to specify which tool to use** - the agent is smart enough to pick!

---

## Best Practices

### 1. Be Specific in Queries

```python
# ❌ Too vague
"Apple news"

# ✅ Specific
"Apple iPhone 16 sales numbers Q1 2025"
```

### 2. Use Time Filters for Market News

```python
# For breaking news
real_time_market_search("Fed rate decision", time_filter="day")

# For trend analysis
real_time_market_search("Tesla stock performance", time_filter="week")
```

### 3. Combine with Other Tools

```python
# Step 1: Get real-time price
financial_web_search("AAPL", "current stock price")

# Step 2: Get fundamentals
get_valuation_metrics("AAPL")

# Step 3: Get official filings
semantic_search_sec_filing("AAPL", "business strategy", "10-K")

# = Comprehensive analysis!
```

### 4. Use Deep Search Sparingly

`search_and_summarize` is powerful but slow (10-15s). Use it only when you need full article content, not for quick lookups.

---

## Configuration

### Adjust Results Count

Edit `agent/tools/search/search.py`:

```python
# Return more results
results = search_engine.search_duckduckgo(query, max_results=20)

# Return fewer results (faster)
results = search_engine.search_duckduckgo(query, max_results=5)
```

### Adjust Content Extraction Length

```python
# Extract longer content
content = search_engine.extract_page_content(url, max_length=10000)

# Extract shorter snippets
content = search_engine.extract_page_content(url, max_length=2000)
```

### Change Search Region

```python
# US English (default)
results = search_engine.search_duckduckgo(query, region="us-en")

# UK English
results = search_engine.search_duckduckgo(query, region="uk-en")

# Other regions: de-de, fr-fr, ja-jp, etc.
```

---

## Troubleshooting

### Issue: "No results found"

**Causes:**
- Query too specific
- DuckDuckGo temporarily unavailable
- Network issues

**Solutions:**
- Broaden your query
- Try different keywords
- Check internet connection
- Wait a few seconds and retry

### Issue: "Slow performance"

**Causes:**
- Using `search_and_summarize` (expected - fetches full pages)
- Slow websites being scraped
- Network latency

**Solutions:**
- Use faster tools (`web_search`, `financial_web_search`)
- Reduce `num_sources` in `search_and_summarize`
- Check network speed

### Issue: "Content extraction failed"

**Causes:**
- Website blocks scraping
- JavaScript-heavy site
- Paywall or login required

**Solutions:**
- Fallback to snippet (automatically handled)
- Try different sources
- Use direct URL access tools if available

---

## Privacy & Ethics

### Responsible Use

✅ **Do:**
- Use for research and analysis
- Respect website terms of service
- Attribute sources properly
- Use reasonable rate limits

❌ **Don't:**
- Scrape excessively from single site
- Bypass paywalls
- Violate copyright
- Use for spam or malicious purposes

### Data Handling

- No personal data collected
- Search queries not logged
- Results not stored (unless in RAG)
- Privacy-first design with DuckDuckGo

---

## Future Enhancements

### Planned Features

- [ ] **Multi-provider fallback** - Try Bing/Google if DDG fails
- [ ] **Result caching** - Cache recent searches (1-hour TTL)
- [ ] **Sentiment analysis** - Analyze sentiment of search results
- [ ] **Auto-summarization** - LLM-based summarization of results
- [ ] **Image search** - Find charts, graphs, infographics
- [ ] **Advanced filtering** - By date, source, content type

### Optimization Opportunities

- [ ] Parallel page scraping (fetch multiple URLs simultaneously)
- [ ] Smart result ranking (relevance scoring)
- [ ] Duplicate detection and dedup
- [ ] Auto-retry with exponential backoff

---

## API Reference

### WebSearchEngine Class

```python
from agent.tools.search.search import WebSearchEngine, get_search_engine

# Get singleton instance
engine = get_search_engine()

# General search
results = engine.search_duckduckgo(
    query="Apple stock price",
    max_results=10,
    region="us-en"
)

# News search
news = engine.search_duckduckgo_news(
    query="Fed rate decision",
    max_results=10,
    timelimit="d"  # d=day, w=week, m=month
)

# Extract page content
content = engine.extract_page_content(
    url="https://example.com/article",
    max_length=5000
)

# Search and extract
enriched = engine.search_and_extract(
    query="AI chip shortage",
    max_results=3,
    extract_content=True
)
```

---

## Examples in Action

### Investment Research Workflow

```
1. User: "Should I invest in NVIDIA?"

2. Agent uses multiple tools:

   a) financial_web_search("NVDA", "current price analyst ratings")
      → Get current market perception

   b) get_valuation_metrics("NVDA")
      → Get P/E, growth metrics

   c) semantic_search_sec_filing("NVDA", "business strategy risks", "10-K")
      → Get official strategy and risks

   d) real_time_market_search("NVIDIA AI chip demand", "week")
      → Get recent market developments

3. Agent synthesizes all sources:
   → Comprehensive investment analysis
```

### Breaking News Analysis

```
1. User: "What's happening with banks today?"

2. Agent:
   a) real_time_market_search("bank stocks today", "day")
      → Get today's news

   b) search_and_summarize("banking sector analysis", 2)
      → Get detailed analysis from expert sources

3. Returns: Comprehensive view of current banking situation
```

---

## Dependencies

```
# requirements.txt
duckduckgo-search>=5.0.0   # Free web search
requests>=2.31.0            # HTTP requests
beautifulsoup4>=4.12.0      # HTML parsing (already installed for RAG)
```

**Total added dependencies: 2** (beautifulsoup4 already installed)

---

## Summary

### What You Get

✅ Real-time web search (no API key needed)
✅ Financial-optimized search for companies
✅ Breaking news with time filtering
✅ Deep research with full content extraction
✅ Free forever (DuckDuckGo)
✅ Fast (2-3 seconds typical)
✅ Privacy-respecting

### Agent Capabilities

**Now the agent can answer:**
- "What's Apple's stock price right now?"
- "What happened in the market today?"
- "Latest news about Tesla deliveries"
- "Current interest rates"
- "Breaking news about [any topic]"
- "Comprehensive analysis of [any topic]"

### Total Agent Tools

**Before:** 18 tools
**After:** 22 tools

**Complete toolkit:**
- 6 Quantitative tools
- 3 News API tools
- 4 SEC filing tools
- 5 RAG tools
- **4 Web search tools (NEW!)**

---

**You're all set!** The agent now has comprehensive real-time information gathering capabilities.

Try queries like:
- "What's the current price of Apple stock?"
- "What happened in the tech sector today?"
- "Give me a comprehensive analysis of the chip shortage"

The agent will automatically use the most appropriate web search tool!
