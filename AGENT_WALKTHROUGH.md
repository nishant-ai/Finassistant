# Finassistant Project Walkthrough

> **A comprehensive guide to understanding every file and component in the Finassistant multi-agent financial analysis system.**

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Quick Start](#quick-start)
3. [Project Structure](#project-structure)
4. [Core Application Files](#core-application-files)
5. [Graph & Orchestration System](#graph--orchestration-system)
6. [Tools Ecosystem (23 Tools)](#tools-ecosystem-23-tools)
7. [Configuration & Dependencies](#configuration--dependencies)
8. [Documentation Files](#documentation-files)
9. [Data & Persistence](#data--persistence)
10. [Execution Flows](#execution-flows)
11. [Development Guide](#development-guide)

---

## Project Overview

**Finassistant** is an AI-powered financial analysis system built with **LangGraph** and **Google Gemini**. It uses a **three-agent architecture** to intelligently analyze companies, markets, and financial data.

### Key Features
- 🤖 **Three specialized agents**: Planner → Financial Executor → Publisher
- 🔧 **23+ financial tools**: SEC filings, news, quantitative metrics, RAG, web search
- 📝 **Two output modes**: [Chat] for quick answers, [Report] for comprehensive analysis
- ⚡ **Optimized workflows**: 5-15 seconds for Chat, 30-90 seconds for Reports
- 💾 **RAG system**: Semantic search over SEC filings and news articles

### Tech Stack
- **LangGraph**: Workflow orchestration
- **Google Gemini 2.0 Flash**: LLM provider
- **ChromaDB**: Vector database
- **yfinance**: Stock market data
- **NewsAPI**: Real-time news
- **SEC Edgar**: Filing downloads

---

## Quick Start

### Installation
```bash
# Clone and setup
cd /Users/nishant/Desktop/Finassistant
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure API keys in .env
# Required: GOOGLE_API_KEY, NEWS_API_KEY
```

### Run Examples
```bash
# Interactive mode
python agent/app_multi_agent.py

# Example queries
[Chat] What's Apple's P/E ratio?
[Report] Analyze Tesla's financial health comprehensively
```

---

## Project Structure

```
Finassistant/
├── agent/                          # Core application code
│   ├── app_multi_agent.py          # Main entry point (3-agent system)
│   ├── app.py                      # Legacy single-agent system
│   ├── graph/                      # LangGraph workflow definitions
│   │   ├── multi_agent_state.py    # State management
│   │   ├── multi_agent_graph.py    # Workflow orchestration
│   │   ├── request_parser.py       # [Chat]/[Report] parsing
│   │   ├── planner_agent.py        # Planning agent
│   │   ├── financial_agent.py      # Execution agent
│   │   └── publisher_agent.py      # Output formatting agent
│   └── tools/                      # 23 financial analysis tools
│       ├── quant/                  # 6 quantitative tools
│       ├── news/                   # 3 news tools
│       ├── sec_filing/             # 3 SEC tools
│       ├── rag/                    # 5 RAG tools
│       └── search/                 # 4 web search tools
├── examples/                       # Example usage and outputs
├── chroma_db/                      # Vector database (persistent)
├── sec-edgar-filings/              # Downloaded SEC filings cache
├── .env                            # API keys (not in git)
├── requirements.txt                # Python dependencies
├── README.md                       # Project overview
├── ARCHITECTURE_DIAGRAM.md         # System architecture
├── MULTI_AGENT_README.md          # Complete documentation
└── QUICKSTART_MULTI_AGENT.md      # Getting started guide
```

---

## Core Application Files

### 1. [agent/app_multi_agent.py](agent/app_multi_agent.py) (184 lines)

**Purpose**: Main entry point for the multi-agent system.

**Key Functions**:
- `main()` - Interactive CLI loop
- Handles user input parsing
- Executes the three-agent workflow
- Displays execution summaries

**Usage**:
```python
# Interactive mode
python agent/app_multi_agent.py

# Programmatic usage
from agent.app_multi_agent import main
main()
```

**Architecture**:
```
User Input → Parser → Planner → Financial Executor → Publisher → Output
```

**Features**:
- Supports [Chat] and [Report] modes
- Interactive mode with real-time feedback
- Execution time tracking
- Pretty-printed summaries

---

### 2. [agent/app.py](agent/app.py) (96 lines)

**Purpose**: Legacy single-agent system (simpler architecture).

**Key Functions**:
- `main()` - CLI interface
- Uses all 23 tools in a single agent
- More basic workflow (no planning/publishing phases)

**When to Use**:
- Quick prototyping
- Simple queries that don't need multi-agent coordination
- Testing individual tools

**Differences from Multi-Agent**:
| Feature | Single-Agent | Multi-Agent |
|---------|--------------|-------------|
| Agents | 1 (does everything) | 3 (specialized) |
| Planning | None | Explicit planning phase |
| Tool Selection | LLM decides | Strategic planner |
| Output | Raw LLM response | Professionally formatted |
| Speed | Unpredictable | Optimized per mode |

---

## Graph & Orchestration System

The `agent/graph/` directory contains the orchestration logic for the multi-agent system.

### 3. [agent/graph/multi_agent_state.py](agent/graph/multi_agent_state.py) (70 lines)

**Purpose**: Defines the shared state structure used by all agents.

**Key Components**:

```python
class MultiAgentState(TypedDict):
    # User input
    messages: Annotated[list, add_messages]
    user_query: str

    # Mode configuration
    output_mode: Literal["chat", "report"]
    desired_length: Optional[str]

    # Planning phase
    plan: Optional[str]  # JSON execution plan
    plan_summary: Optional[str]
    planner_reasoning: Optional[str]

    # Execution phase
    execution_results: list[ExecutionResult]
    current_step: int
    all_tool_outputs: dict

    # Publishing phase
    final_output: Optional[str]
    output_format: Literal["markdown", "html", "text"]

    # Metadata
    execution_time: Optional[float]
    total_cost_estimate: Optional[float]
```

**State Flow**:
1. **Parse Phase**: Populates `user_query`, `output_mode`, `desired_length`
2. **Planning Phase**: Creates `plan`, `plan_summary`, `planner_reasoning`
3. **Execution Phase**: Updates `execution_results`, `all_tool_outputs`
4. **Publishing Phase**: Generates `final_output`

**Sub-Types**:
- `PlanStep`: Individual step in execution plan
- `ExecutionResult`: Result from executing a plan step

---

### 4. [agent/graph/multi_agent_graph.py](agent/graph/multi_agent_graph.py) (80+ lines)

**Purpose**: Builds the complete multi-agent workflow graph.

**Key Function**:
```python
def create_multi_agent_graph() -> StateGraph:
    """Creates the three-agent workflow."""
```

**Graph Structure**:
```
START
  ↓
parse_user_request
  ↓
planner_agent
  ↓
financial_execution_agent (loops until all steps complete)
  ↓
publisher_agent
  ↓
END
```

**Node Functions**:
- `parse_node()` - Extracts [Chat]/[Report] tags
- `planner_node()` - Creates execution plan
- `financial_node()` - Executes tools
- `publisher_node()` - Formats output

**Helper Functions**:
- `print_execution_summary()` - Displays execution metrics
- `should_continue_execution()` - Determines if more steps needed

**Visualization**:
The graph is compiled with `StateGraph(MultiAgentState)` and uses conditional edges for the execution loop.

---

### 5. [agent/graph/request_parser.py](agent/graph/request_parser.py) (151 lines)

**Purpose**: Parses user input to extract mode and configuration.

**Key Functions**:

#### `parse_user_request(query: str) -> dict`
Extracts [Chat] or [Report] tags from user input.

**Examples**:
```python
parse_user_request("[Chat] What's Apple's P/E?")
# → {"output_mode": "chat", "user_query": "What's Apple's P/E?"}

parse_user_request("[Report] Analyze Tesla comprehensively")
# → {"output_mode": "report", "user_query": "Analyze Tesla comprehensively"}

parse_user_request("Compare Apple and Microsoft")
# → {"output_mode": "chat", "user_query": "Compare Apple and Microsoft"}  # Default
```

**Features**:
- Case-insensitive tag detection
- Supports tags at start or end of query
- Extracts desired length (e.g., "5 paragraphs", "brief")
- Defaults to Chat mode if no tag found

#### `get_plan_complexity(mode: str) -> str`
Determines plan complexity based on mode.

**Returns**:
- `"minimal"` - Chat mode (1-3 tools)
- `"exhaustive"` - Report mode (5-10+ tools)

#### `format_mode_description(mode: str) -> str`
Returns human-readable mode description.

---

### 6. [agent/graph/planner_agent.py](agent/graph/planner_agent.py) (80+ lines)

**Purpose**: Strategic planning agent that creates tool execution plans.

**Key Components**:

#### `TOOL_CATALOG`
Comprehensive documentation of all 23 tools with:
- Tool names and descriptions
- When to use each tool
- Parameter requirements
- Expected outputs

#### `create_planner_agent() -> Runnable`
Creates the planning agent with Google Gemini.

**Configuration**:
- Model: `google-gemini-2.0-flash-exp`
- Temperature: `0` (deterministic)
- Output: JSON execution plan

**System Prompt**:
```
You are a strategic financial analysis planner.
Given a user query and output mode (chat/report),
create an optimal execution plan using available tools.

For [Chat]: Use 1-3 tools for quick answers
For [Report]: Use 5-10+ tools for comprehensive analysis
```

**Output Format**:
```json
{
  "steps": [
    {
      "step_number": 1,
      "tool_name": "get_valuation_metrics",
      "parameters": {"ticker": "AAPL"},
      "reasoning": "Get P/E ratio data"
    }
  ],
  "summary": "Retrieve Apple's valuation metrics",
  "reasoning": "User needs P/E ratio specifically"
}
```

**Adaptation Strategy**:
- **Chat Mode**: Minimal plan, focus on most relevant tools
- **Report Mode**: Exhaustive plan, cover all aspects

---

### 7. [agent/graph/financial_agent.py](agent/graph/financial_agent.py) (80+ lines)

**Purpose**: Tool execution agent (no LLM, direct tool calls).

**Key Function**:
```python
def create_financial_execution_agent(tools: list) -> Callable:
    """Creates agent that executes plan steps."""
```

**Execution Logic**:
1. Parse JSON plan from Planner
2. For each step:
   - Look up tool by name
   - Execute with specified parameters
   - Capture output or error
   - Store in `execution_results`
3. Aggregate all results in `all_tool_outputs`
4. Continue until all steps complete

**Error Handling**:
- Graceful failures (doesn't stop on error)
- Captures error messages in results
- Continues to next step even if one fails

**No LLM**: This agent is purely deterministic and doesn't make decisions.

**Performance**:
- Fast execution (no LLM latency)
- Parallel tool calls (where possible)
- Efficient result aggregation

---

### 8. [agent/graph/publisher_agent.py](agent/graph/publisher_agent.py) (80+ lines)

**Purpose**: Output formatting agent that creates human-readable reports.

**Key Components**:

#### `CHAT_PUBLISHER_PROMPT`
System prompt for Chat mode output.

**Guidelines**:
- 3-4 paragraphs
- Conversational tone
- Key insights highlighted
- No excessive formatting
- Web-friendly Markdown

#### `REPORT_PUBLISHER_PROMPT`
System prompt for Report mode output.

**Guidelines**:
- 8-15 sections
- Professional structure
- Executive summary
- Detailed analysis
- Tables and lists
- Comprehensive coverage
- Web-friendly Markdown

#### `create_publisher_agent() -> Runnable`
Creates the publishing agent with Google Gemini.

**Configuration**:
- Model: `google-gemini-2.0-flash-exp`
- Temperature: `0.3` (slightly creative for natural language)
- Output: Markdown formatted text

**Input**: All tool outputs from Financial Agent
**Output**: Final formatted response

**Customization**:
- Respects `desired_length` parameter
- Adapts tone to mode
- Ensures web-readability

---

### 9. [agent/graph/nodes.py](agent/graph/nodes.py) (50+ lines)

**Purpose**: Legacy node creation for single-agent system.

**Key Functions**:
- `create_agent_node()` - Builds LLM with all 23 tools
- `should_continue()` - Router function (continue to tools or end)

**System Prompt**:
```
You are an expert financial analyst with access to 23+ tools.
Analyze companies, markets, and investments using available data.
Be thorough but concise.
```

**Note**: Used by [agent/app.py](agent/app.py), not the multi-agent system.

---

### 10. [agent/graph/graph.py](agent/graph/graph.py) (67 lines)

**Purpose**: Legacy graph builder for single-agent system.

**Architecture**:
```
agent → should_continue? → tools → agent (loop)
                        ↓
                       end
```

**Performance**:
- Efficient: 2-4 LLM calls per query
- Uses Google Gemini 2.0 Flash
- All 23 tools available

**Note**: Simpler than multi-agent, but less strategic.

---

### 11. [agent/graph/state.py](agent/graph/state.py) (6 lines)

**Purpose**: Basic state for single-agent system.

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
```

**Note**: Much simpler than `MultiAgentState`.

---

## Tools Ecosystem (23 Tools)

The `agent/tools/` directory contains all financial analysis tools organized by category.

### Tool Registry: [agent/tools/__init__.py](agent/tools/__init__.py) (62 lines)

**Purpose**: Central export point for all tools.

**Exports**:
```python
# Quantitative (6)
from agent.tools.quant.quant import (
    get_valuation_metrics,
    get_profitability_metrics,
    get_historical_growth,
    get_stock_price_summary,
    get_analyst_recommendations,
    compare_key_metrics,
)

# News (3)
from agent.tools.news.news import (
    get_stock_news,
    get_market_news,
    get_full_article_content,
)

# SEC (3)
from agent.tools.sec_filing.sec_filing import (
    get_sec_filing_summary,
    get_sec_financial_data,
    compare_sec_filings,
)

# RAG (5)
from agent.tools.rag.rag_tools import (
    semantic_search_sec_filing,
    semantic_search_news,
    multi_document_analysis,
    index_news_for_ticker,
    rag_system_status,
)

# Web Search (4)
from agent.tools.search.search import (
    web_search,
    financial_web_search,
    real_time_market_search,
    search_and_summarize,
)
```

---

## Quantitative Tools (6 Tools)

### [agent/tools/quant/quant.py](agent/tools/quant/quant.py)

**Purpose**: Stock market data and quantitative analysis using yfinance.

**Tools**:

#### 1. `get_valuation_metrics(ticker: str) -> dict`
Retrieves valuation ratios.

**Returns**:
- P/E Ratio
- P/S Ratio
- PEG Ratio
- EV/EBITDA
- Price/Book

**Example**:
```python
get_valuation_metrics("AAPL")
# → {"pe_ratio": 28.5, "ps_ratio": 7.2, "peg_ratio": 2.3, ...}
```

#### 2. `get_profitability_metrics(ticker: str) -> dict`
Retrieves profitability metrics.

**Returns**:
- Gross Margin
- Operating Margin
- Net Margin
- ROA (Return on Assets)
- ROE (Return on Equity)

**Example**:
```python
get_profitability_metrics("MSFT")
# → {"gross_margin": 0.68, "operating_margin": 0.42, ...}
```

#### 3. `get_historical_growth(ticker: str, years: int = 5) -> dict`
Calculates YoY growth trends.

**Returns**:
- Revenue growth
- Earnings growth
- Average growth rate

**Example**:
```python
get_historical_growth("TSLA", years=3)
# → {"revenue_growth": [0.45, 0.51, 0.37], ...}
```

#### 4. `get_stock_price_summary(ticker: str) -> dict`
Current price and trading data.

**Returns**:
- Current price
- 52-week high/low
- Beta
- Market cap
- Volume

**Example**:
```python
get_stock_price_summary("GOOGL")
# → {"current_price": 142.50, "52_week_high": 155.30, ...}
```

#### 5. `get_analyst_recommendations(ticker: str) -> dict`
Analyst ratings and targets.

**Returns**:
- Buy/Hold/Sell counts
- Target price
- Recommendation trend

**Example**:
```python
get_analyst_recommendations("NVDA")
# → {"strong_buy": 15, "buy": 8, "hold": 2, ...}
```

#### 6. `compare_key_metrics(tickers: List[str]) -> dict`
Multi-company comparison.

**Returns**:
- Side-by-side comparison of all metrics
- Relative performance rankings

**Example**:
```python
compare_key_metrics(["AAPL", "MSFT", "GOOGL"])
# → {"AAPL": {...}, "MSFT": {...}, "GOOGL": {...}}
```

**Features**:
- LRU caching for performance
- Error handling for missing data
- Supports all major stock symbols

---

## News Tools (3 Tools)

### [agent/tools/news/news.py](agent/tools/news/news.py)

**Purpose**: Real-time news and sentiment analysis using NewsAPI.

**Tools**:

#### 1. `get_stock_news(ticker: str, days: int = 7) -> list`
Recent company-specific news.

**Parameters**:
- `ticker`: Stock symbol
- `days`: Lookback period (default 7)

**Returns**:
```python
[
    {
        "title": "Apple Announces New iPhone",
        "source": "TechCrunch",
        "published_at": "2025-11-01T10:00:00Z",
        "url": "https://...",
        "description": "...",
        "sentiment": "positive"  # If available
    }
]
```

**Example**:
```python
get_stock_news("AAPL", days=3)
```

#### 2. `get_market_news(category: str = "business", max_articles: int = 10) -> list`
General market news.

**Categories**:
- `"business"` (default)
- `"technology"`
- `"finance"`
- `"general"`

**Example**:
```python
get_market_news("technology", max_articles=5)
```

#### 3. `get_full_article_content(url: str) -> dict`
Extracts full article text.

**Uses**: newspaper3k library for parsing

**Returns**:
```python
{
    "title": "Full article title",
    "text": "Complete article content...",
    "authors": ["Author Name"],
    "publish_date": "2025-11-01",
    "summary": "Auto-generated summary"
}
```

**Example**:
```python
article = get_full_article_content("https://techcrunch.com/...")
```

**Requirements**:
- `NEWS_API_KEY` in `.env`
- Internet connection
- NewsAPI free tier: 100 requests/day

---

## SEC Filing Tools (3 Tools)

### [agent/tools/sec_filing/sec_filing.py](agent/tools/sec_filing/sec_filing.py)

**Purpose**: Download and parse SEC filings (10-K, 10-Q, 8-K).

**Classes**:

#### `SECFilingsTool`
Core downloader using sec-edgar-downloader.

**Key Methods**:
```python
def download_filing(ticker: str, filing_type: str, num_filings: int = 1):
    """Downloads SEC filings to ./sec-edgar-filings/"""
```

**Supported Filing Types**:
- `"10-K"` - Annual reports
- `"10-Q"` - Quarterly reports
- `"8-K"` - Current events

**Download Location**:
```
sec-edgar-filings/{TICKER}/{FILING_TYPE}/{ACCESSION_NUMBER}/full-submission.txt
```

#### `SECFilingProcessor`
Parser for XML/HTML filings.

**Key Methods**:
```python
def extract_financial_statements(filing_path: str) -> dict:
    """Extracts balance sheet, income statement, cash flow"""
```

**Tools**:

#### 1. `get_sec_filing_summary(ticker: str, filing_type: str = "10-K") -> dict`
Download and summarize filing.

**Returns**:
```python
{
    "ticker": "AAPL",
    "filing_type": "10-K",
    "filing_date": "2024-10-31",
    "fiscal_year": "2024",
    "summary": "Key highlights and sections",
    "file_path": "./sec-edgar-filings/AAPL/10-K/..."
}
```

**Example**:
```python
summary = get_sec_filing_summary("AAPL", "10-K")
```

#### 2. `get_sec_financial_data(ticker: str, filing_type: str = "10-K") -> dict`
Extract financial statements.

**Returns**:
```python
{
    "balance_sheet": {...},
    "income_statement": {...},
    "cash_flow_statement": {...},
    "key_metrics": {
        "total_revenue": 123456789,
        "net_income": 12345678,
        "total_assets": 987654321
    }
}
```

**Example**:
```python
financials = get_sec_financial_data("TSLA", "10-Q")
```

#### 3. `compare_sec_filings(ticker: str, years: int = 3) -> dict`
Multi-year comparison.

**Returns**:
- YoY changes in key metrics
- Trend analysis
- Growth rates

**Example**:
```python
comparison = compare_sec_filings("MSFT", years=5)
```

**Caching**:
- Downloaded filings are cached locally
- Subsequent requests use cached files
- Saves bandwidth and time

---

## RAG Tools (5 Tools)

### RAG System Components

The RAG (Retrieval-Augmented Generation) system consists of 4 files:

1. [agent/tools/rag/rag_tools.py](agent/tools/rag/rag_tools.py) - Tool definitions
2. [agent/tools/rag/vector_store.py](agent/tools/rag/vector_store.py) - ChromaDB manager
3. [agent/tools/rag/chunking.py](agent/tools/rag/chunking.py) - Document chunking
4. [agent/tools/rag/embeddings.py](agent/tools/rag/embeddings.py) - Embedding service

---

### [agent/tools/rag/rag_tools.py](agent/tools/rag/rag_tools.py)

**Purpose**: Semantic search over SEC filings and news articles.

**Tools**:

#### 1. `semantic_search_sec_filing(ticker: str, query: str, top_k: int = 5) -> list`
Search SEC filings semantically.

**Example**:
```python
results = semantic_search_sec_filing(
    ticker="AAPL",
    query="What are the main risk factors?",
    top_k=5
)
# Returns most relevant sections from 10-K
```

**Returns**:
```python
[
    {
        "text": "Risk factor section content...",
        "metadata": {"filing_type": "10-K", "section": "Risk Factors"},
        "similarity_score": 0.92
    }
]
```

#### 2. `semantic_search_news(ticker: str, query: str, days: int = 30) -> list`
Search news articles semantically.

**Example**:
```python
results = semantic_search_news(
    ticker="TSLA",
    query="production challenges",
    days=30
)
```

#### 3. `multi_document_analysis(ticker: str, query: str) -> dict`
Combined SEC + news analysis.

**Example**:
```python
analysis = multi_document_analysis(
    ticker="NVDA",
    query="AI chip demand outlook"
)
# Synthesizes info from SEC filings AND recent news
```

#### 4. `index_news_for_ticker(ticker: str, days: int = 30) -> dict`
Prepare news for semantic search.

**Process**:
1. Fetch news from NewsAPI
2. Chunk articles
3. Generate embeddings
4. Store in ChromaDB

**Example**:
```python
status = index_news_for_ticker("AAPL", days=30)
# → {"indexed_articles": 25, "total_chunks": 150}
```

#### 5. `rag_system_status() -> dict`
Check RAG system health.

**Returns**:
```python
{
    "sec_filings_indexed": 12,
    "news_articles_indexed": 150,
    "total_chunks": 2500,
    "collections": ["sec_filings", "news_articles"]
}
```

---

### [agent/tools/rag/vector_store.py](agent/tools/rag/vector_store.py)

**Purpose**: Manages ChromaDB vector database.

**Class**: `VectorStoreManager`

**Collections**:
- `sec_filings` - SEC filing chunks
- `news_articles` - News article chunks

**Key Methods**:

```python
class VectorStoreManager:
    def store_documents(self, collection_name: str, documents: list):
        """Store documents with embeddings."""

    def query(self, collection_name: str, query_text: str, n_results: int = 5):
        """Semantic search."""

    def get_collection_stats(self, collection_name: str) -> dict:
        """Get collection info."""

    def clear_collection(self, collection_name: str):
        """Delete all documents."""
```

**Storage Location**: `./chroma_db/`

**Persistence**: Automatic (survives restarts)

---

### [agent/tools/rag/chunking.py](agent/tools/rag/chunking.py)

**Purpose**: Intelligently chunk documents for embedding.

**Classes**:

#### `SECFilingChunker`
Hierarchical chunking for SEC filings.

**Strategy**:
- Respects document structure
- Preserves context
- Optimal chunk size: 500-1000 tokens
- Overlapping windows for continuity

#### `NewsArticleChunker`
Article chunking.

**Strategy**:
- Paragraph-based
- Preserves metadata
- Smaller chunks (200-500 tokens)

**Data Structure**:
```python
class Chunk(TypedDict):
    text: str
    metadata: dict
    chunk_id: str
```

---

### [agent/tools/rag/embeddings.py](agent/tools/rag/embeddings.py)

**Purpose**: Embedding generation service.

**Function**:
```python
def get_embedding_service():
    """Returns Google embedding model via LangChain."""
```

**Model**: Google's embedding models (compatible with Gemini)

**Integration**: Works seamlessly with ChromaDB

---

## Web Search Tools (4 Tools)

### [agent/tools/search/search.py](agent/tools/search/search.py)

**Purpose**: Web search using DuckDuckGo (no API key required).

**Class**: `WebSearchEngine`

**Tools**:

#### 1. `web_search(query: str, max_results: int = 5) -> list`
General web search.

**Example**:
```python
results = web_search("Tesla earnings report Q3 2024", max_results=5)
```

**Returns**:
```python
[
    {
        "title": "Tesla Q3 Earnings Beat Expectations",
        "url": "https://...",
        "snippet": "Tesla reported...",
        "source": "Reuters"
    }
]
```

#### 2. `financial_web_search(company_name: str, query: str) -> list`
Company-specific financial search.

**Example**:
```python
results = financial_web_search(
    company_name="Apple",
    query="quarterly revenue growth"
)
```

#### 3. `real_time_market_search(topic: str) -> list`
Breaking market news.

**Example**:
```python
results = real_time_market_search("Federal Reserve interest rate decision")
```

#### 4. `search_and_summarize(query: str, extract_content: bool = True) -> dict`
Deep research with content extraction.

**Process**:
1. Perform web search
2. Extract full content from top results
3. Return comprehensive data

**Example**:
```python
research = search_and_summarize(
    query="Impact of AI on semiconductor industry",
    extract_content=True
)
# Returns search results + full article contents
```

**Features**:
- No API key required
- Rate limiting built-in
- Content extraction with BeautifulSoup
- Error handling for failed extractions

---

## Configuration & Dependencies

### [requirements.txt](requirements.txt)

**Core Dependencies**:

```txt
# AI & LLM
langchain>=0.1.0
langchain-core>=0.1.0
langchain-google-genai>=0.0.5
langgraph>=0.0.20
google-generativeai>=0.3.0

# Financial Data
yfinance>=0.2.30
pandas>=2.0.0

# News
newsapi-python>=0.2.7
newspaper3k>=0.2.8

# Web Scraping
beautifulsoup4>=4.12.0
lxml>=4.9.0

# SEC Filings
sec-edgar-downloader>=5.0.0

# Vector Database
chromadb>=0.4.0

# Web Search
duckduckgo-search>=3.9.0
requests>=2.31.0

# Configuration
python-dotenv>=1.0.0
```

**Installation**:
```bash
pip install -r requirements.txt
```

---

### [.env](.env)

**Required API Keys**:

```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here  # For Gemini
NEWS_API_KEY=your_newsapi_key_here       # For NewsAPI

# Optional (legacy/fallback)
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here
PINECONE_API_KEY=your_pinecone_key_here
ALPHA_VANTAGE_API_KEY=your_alphavantage_key_here
```

**Getting API Keys**:

1. **Google Gemini**: https://makersuite.google.com/app/apikey
2. **NewsAPI**: https://newsapi.org/register (Free tier: 100 requests/day)

**Security**:
- `.env` is in `.gitignore` (never committed)
- Store securely, never share

---

### [.gitignore](.gitignore)

**Ignored Items**:

```gitignore
# Environment
.venv/
.env

# API Keys
.openai_api_key
.pinecone_api_key

# Data
chroma_db/
sec-edgar-filings/

# Python
__pycache__/
*.pyc
*.pyo

# IDE
.vscode/
.idea/
```

---

## Documentation Files

### 1. [README.md](README.md) (121 lines)

**Purpose**: Project overview and quick start guide.

**Contents**:
- What is Finassistant
- Key features
- Architecture overview
- Tech stack
- Installation instructions
- Basic usage
- Directory structure

**Audience**: New users, GitHub visitors

---

### 2. [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) (342 lines)

**Purpose**: Complete system architecture documentation.

**Contents**:
- ASCII workflow diagrams
- State management details
- Component relationships
- Data flow diagrams
- Performance characteristics
- Tool selection logic
- Output format comparisons

**Highlights**:
```
User Input
    ↓
┌─────────────────────────────────────┐
│  Request Parser                     │
│  [Chat]/[Report] detection          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Planner Agent (Gemini)             │
│  Creates tool execution plan        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Financial Agent (No LLM)           │
│  Executes tools sequentially        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Publisher Agent (Gemini)           │
│  Formats final output               │
└─────────────────────────────────────┘
    ↓
Final Output (Markdown)
```

**Audience**: Developers, architects

---

### 3. [MULTI_AGENT_README.md](MULTI_AGENT_README.md) (408 lines)

**Purpose**: Comprehensive system documentation.

**Contents**:
- Three-agent architecture explained
- Agent responsibilities
- All 23 tools documented
- Output mode comparisons
- Usage examples
- API reference
- Configuration options
- Performance metrics
- Design principles
- Future enhancements

**Highlights**:

**Agent Responsibilities**:
- **Planner**: Strategic planning, tool selection
- **Financial**: Tool execution, data gathering
- **Publisher**: Output formatting, presentation

**Performance Metrics**:
- Chat: 5-15 seconds, $0.001-0.005
- Report: 30-90 seconds, $0.01-0.05

**Audience**: All users (comprehensive reference)

---

### 4. [QUICKSTART_MULTI_AGENT.md](QUICKSTART_MULTI_AGENT.md) (240 lines)

**Purpose**: Get started in 5 minutes.

**Contents**:
- Installation steps
- Quick test examples
- Basic usage patterns
- Interactive mode guide
- Tag syntax (`[Chat]` and `[Report]`)
- Length customization
- Example outputs
- Common mistakes
- Troubleshooting
- Pro tips

**Example Queries**:
```
# Chat mode (quick answers)
[Chat] What's Apple's current P/E ratio?
[Chat] Is Tesla profitable?
[Chat] Compare revenue growth: AAPL vs MSFT

# Report mode (comprehensive analysis)
[Report] Analyze Amazon's financial health
[Report] What are NVIDIA's growth prospects in AI?
[Report] Compare cloud providers: AWS, Azure, GCP

# Length customization
[Report, 10 paragraphs] Deep dive into Tesla's business model
[Chat, brief] Quick update on Apple stock
```

**Audience**: New users, quick reference

---

## Data & Persistence

### 1. ChromaDB Vector Store

**Location**: `./chroma_db/`

**Collections**:
- `sec_filings` - SEC filing embeddings
- `news_articles` - News article embeddings

**Persistence**: Automatic

**Management**:
```python
from agent.tools.rag.vector_store import VectorStoreManager

manager = VectorStoreManager()
stats = manager.get_collection_stats("sec_filings")
print(stats)  # → {"count": 1250, "size_mb": 45.2}
```

**Cleanup**:
```python
# Clear all news articles
manager.clear_collection("news_articles")

# Or delete entire database
import shutil
shutil.rmtree("./chroma_db")
```

---

### 2. SEC Filing Cache

**Location**: `./sec-edgar-filings/`

**Structure**:
```
sec-edgar-filings/
├── AAPL/
│   ├── 10-K/
│   │   └── 0001018724-25-000004/
│   │       └── full-submission.txt
│   └── 10-Q/
│       └── 0001018724-24-000123/
│           └── full-submission.txt
├── TSLA/
│   └── 10-K/
│       └── ...
```

**Caching Benefits**:
- Faster subsequent queries
- Saves bandwidth
- Offline access
- SEC rate limit compliance

**Cleanup**:
```bash
# Remove all cached filings
rm -rf ./sec-edgar-filings

# Or remove specific company
rm -rf ./sec-edgar-filings/AAPL
```

---

### 3. Example Outputs

**Location**: `./examples/outputs/`

**Files**:
- `output_market_news.md` - Market news example
- `output_growth_analysis.md` - Growth analysis example

**Purpose**: Reference examples for expected output quality.

---

## Execution Flows

### Chat Mode Flow

**User Input**:
```
[Chat] What's Apple's P/E ratio?
```

**Execution**:

1. **Parse** (< 1ms):
   ```python
   {
       "output_mode": "chat",
       "user_query": "What's Apple's P/E ratio?",
       "desired_length": None  # Default 3-4 paragraphs
   }
   ```

2. **Plan** (~1-2 seconds):
   ```json
   {
       "steps": [
           {
               "step_number": 1,
               "tool_name": "get_valuation_metrics",
               "parameters": {"ticker": "AAPL"},
               "reasoning": "Get P/E ratio directly"
           }
       ],
       "summary": "Retrieve Apple's valuation metrics",
       "reasoning": "Minimal plan for quick answer"
   }
   ```

3. **Execute** (~1-2 seconds):
   ```python
   {
       "pe_ratio": 28.5,
       "ps_ratio": 7.2,
       "peg_ratio": 2.3,
       ...
   }
   ```

4. **Publish** (~2-3 seconds):
   ```markdown
   Apple (AAPL) currently has a P/E ratio of 28.5, which is above the
   technology sector average of 25.2. This suggests the market has high
   expectations for Apple's future earnings growth.

   The P/E ratio of 28.5 means investors are willing to pay $28.50 for
   every dollar of Apple's earnings. This premium valuation reflects
   Apple's strong brand, loyal customer base, and consistent profitability.

   Compared to other tech giants like Microsoft (P/E: 32.1) and Google
   (P/E: 24.3), Apple sits in the middle range, indicating balanced
   market sentiment.
   ```

**Total Time**: 5-8 seconds
**Cost**: ~$0.002

---

### Report Mode Flow

**User Input**:
```
[Report] Analyze Tesla's financial health comprehensively
```

**Execution**:

1. **Parse** (< 1ms):
   ```python
   {
       "output_mode": "report",
       "user_query": "Analyze Tesla's financial health comprehensively"
   }
   ```

2. **Plan** (~2-3 seconds):
   ```json
   {
       "steps": [
           {"tool": "get_valuation_metrics", "params": {"ticker": "TSLA"}},
           {"tool": "get_profitability_metrics", "params": {"ticker": "TSLA"}},
           {"tool": "get_historical_growth", "params": {"ticker": "TSLA", "years": 5}},
           {"tool": "get_stock_price_summary", "params": {"ticker": "TSLA"}},
           {"tool": "get_sec_filing_summary", "params": {"ticker": "TSLA", "filing_type": "10-K"}},
           {"tool": "get_sec_financial_data", "params": {"ticker": "TSLA", "filing_type": "10-K"}},
           {"tool": "get_stock_news", "params": {"ticker": "TSLA", "days": 30}},
           {"tool": "get_analyst_recommendations", "params": {"ticker": "TSLA"}},
           {"tool": "semantic_search_sec_filing", "params": {"ticker": "TSLA", "query": "financial risks"}},
           {"tool": "real_time_market_search", "params": {"topic": "Tesla financial performance"}}
       ],
       "summary": "Comprehensive financial health analysis using 10+ tools"
   }
   ```

3. **Execute** (~15-25 seconds):
   - Runs all 10 tools sequentially
   - Aggregates results

4. **Publish** (~10-15 seconds):
   - Creates 12-section comprehensive report
   - Includes executive summary, detailed analysis, risk assessment, outlook

**Total Time**: 30-45 seconds
**Cost**: ~$0.02

---

## Development Guide

### Adding a New Tool

**Step 1**: Create tool file

```python
# agent/tools/your_category/your_tool.py

from langchain.tools import tool

@tool
def your_new_tool(param1: str, param2: int = 10) -> dict:
    """
    Brief description of what this tool does.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)

    Returns:
        dict: Description of return value
    """
    # Implementation
    result = do_something(param1, param2)
    return result
```

**Step 2**: Export from category `__init__.py`

```python
# agent/tools/your_category/__init__.py

from .your_tool import your_new_tool

__all__ = ["your_new_tool"]
```

**Step 3**: Add to main tool registry

```python
# agent/tools/__init__.py

from agent.tools.your_category import your_new_tool

# Add to __all__ list
```

**Step 4**: Update Planner's TOOL_CATALOG

```python
# agent/graph/planner_agent.py

TOOL_CATALOG = """
...
- your_new_tool(param1, param2): Description and when to use
...
"""
```

**Step 5**: Test

```python
# Test standalone
from agent.tools import your_new_tool
result = your_new_tool("test", 5)
print(result)

# Test in system
python agent/app_multi_agent.py
# Then: [Chat] Use your_new_tool to...
```

---

### Modifying Agent Behavior

**Planner Agent**:
- Edit system prompt in [agent/graph/planner_agent.py](agent/graph/planner_agent.py)
- Adjust planning logic (e.g., change tool count for Chat vs Report)
- Modify temperature for more/less creative plans

**Financial Agent**:
- Edit execution logic in [agent/graph/financial_agent.py](agent/graph/financial_agent.py)
- Add parallel execution
- Implement retry logic
- Add result validation

**Publisher Agent**:
- Edit prompts in [agent/graph/publisher_agent.py](agent/graph/publisher_agent.py)
- Change output format (e.g., HTML instead of Markdown)
- Adjust length guidelines
- Modify tone/style

---

### Running Tests

**Current State**: Tests were deleted (see git status)

**To Add Tests**:

```python
# agent/tests/test_tools.py

import pytest
from agent.tools import get_valuation_metrics

def test_get_valuation_metrics():
    result = get_valuation_metrics("AAPL")
    assert "pe_ratio" in result
    assert result["pe_ratio"] > 0

# Run with:
# pytest agent/tests/
```

---

### Debugging

**Enable Verbose Logging**:

```python
# agent/app_multi_agent.py

import os
os.environ["LANGCHAIN_VERBOSE"] = "true"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
```

**Inspect State**:

```python
# In any agent node
def planner_node(state: MultiAgentState):
    print("Current state:", state)
    # ... rest of implementation
```

**Check LLM Calls**:

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Summary

This walkthrough has covered:

1. **Project Structure**: Complete directory organization
2. **Core Application**: Entry points and main workflows
3. **Graph System**: 8 orchestration files managing the three-agent workflow
4. **Tools**: All 23 tools across 5 categories (Quant, News, SEC, RAG, Search)
5. **Configuration**: Dependencies, API keys, environment setup
6. **Documentation**: 4 comprehensive guides
7. **Data**: Vector store, SEC cache, example outputs
8. **Execution**: Chat and Report mode flows
9. **Development**: Adding tools, modifying agents, testing

**Key Files to Remember**:

- **Main Entry**: [agent/app_multi_agent.py](agent/app_multi_agent.py)
- **State Definition**: [agent/graph/multi_agent_state.py](agent/graph/multi_agent_state.py)
- **Orchestration**: [agent/graph/multi_agent_graph.py](agent/graph/multi_agent_graph.py)
- **Tool Registry**: [agent/tools/__init__.py](agent/tools/__init__.py)
- **Complete Docs**: [MULTI_AGENT_README.md](MULTI_AGENT_README.md)

**Next Steps**:

1. Read [QUICKSTART_MULTI_AGENT.md](QUICKSTART_MULTI_AGENT.md)
2. Run example queries
3. Explore individual tools
4. Customize agents for your use case
5. Add new tools as needed

---

**Questions or Issues?**

- Check [MULTI_AGENT_README.md](MULTI_AGENT_README.md) for detailed documentation
- Review [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) for system design
- Examine tool source code for implementation details

Happy analyzing! 🚀
