"""
Web Search Tools for Real-Time Information

Provides multiple search strategies optimized for financial queries.
Uses DuckDuckGo as primary search provider (no API key required).
"""

import os
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from functools import lru_cache
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from duckduckgo_search import DDGS


class WebSearchEngine:
    """
    Unified web search engine with multiple providers.
    Falls back gracefully if one provider fails.
    """

    def __init__(self):
        """Initialize search engine."""
        self.ddg = DDGS()
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

    def search_duckduckgo(self, query: str, max_results: int = 10,
                         region: str = "us-en") -> List[Dict]:
        """
        Search using DuckDuckGo (no API key required).

        Args:
            query: Search query
            max_results: Maximum number of results
            region: Search region

        Returns:
            List of search result dictionaries
        """
        try:
            results = []
            ddg_results = self.ddg.text(
                keywords=query,
                region=region,
                max_results=max_results
            )

            for result in ddg_results:
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', ''),
                    'source': 'duckduckgo'
                })

            return results

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []

    def search_duckduckgo_news(self, query: str, max_results: int = 10,
                              timelimit: str = "w") -> List[Dict]:
        """
        Search news using DuckDuckGo News.

        Args:
            query: Search query
            max_results: Maximum number of results
            timelimit: Time limit (d=day, w=week, m=month)

        Returns:
            List of news result dictionaries
        """
        try:
            results = []
            news_results = self.ddg.news(
                keywords=query,
                max_results=max_results,
                timelimit=timelimit
            )

            for result in news_results:
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('body', ''),
                    'date': result.get('date', ''),
                    'source': result.get('source', 'unknown'),
                    'type': 'news'
                })

            return results

        except Exception as e:
            print(f"DuckDuckGo news search error: {e}")
            return []

    def extract_page_content(self, url: str, max_length: int = 5000) -> Optional[str]:
        """
        Extract main content from a webpage.

        Args:
            url: URL to extract content from
            max_length: Maximum content length

        Returns:
            Extracted text content or None if failed
        """
        try:
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'aside']):
                script.decompose()

            # Try to find main content
            main_content = soup.find('main') or soup.find('article') or soup.find('body')

            if main_content:
                text = main_content.get_text(separator='\n', strip=True)

                # Clean up whitespace
                text = re.sub(r'\n\s*\n', '\n\n', text)
                text = re.sub(r' +', ' ', text)

                # Truncate if too long
                if len(text) > max_length:
                    text = text[:max_length] + "\n\n... [Content truncated]"

                return text

        except Exception as e:
            print(f"Error extracting content from {url}: {e}")

        return None

    def search_and_extract(self, query: str, max_results: int = 5,
                          extract_content: bool = True) -> List[Dict]:
        """
        Search and optionally extract full content from results.

        Args:
            query: Search query
            max_results: Maximum results to return
            extract_content: Whether to extract full page content

        Returns:
            List of results with optional full content
        """
        # Perform search
        results = self.search_duckduckgo(query, max_results=max_results * 2)

        if not results:
            return []

        enriched_results = []

        for result in results[:max_results]:
            enriched = result.copy()

            if extract_content and result.get('url'):
                content = self.extract_page_content(result['url'])
                if content:
                    enriched['full_content'] = content

            enriched_results.append(enriched)

        return enriched_results


# Global search engine instance
_search_engine = None


def get_search_engine() -> WebSearchEngine:
    """Get or create global search engine instance."""
    global _search_engine

    if _search_engine is None:
        _search_engine = WebSearchEngine()

    return _search_engine


@tool
def web_search(query: str, max_results: int = 10) -> str:
    """
    **REAL-TIME WEB SEARCH for current information not in databases.**

    Performs live web search using DuckDuckGo for the most up-to-date information.
    Use when you need information that's VERY RECENT or constantly changing.

    **When to use:**
    - Real-time/current information not available in historical data
    - Very recent events (last few hours/days)
    - Information that changes frequently (prices, dates, schedules)
    - General web research on any topic
    - "Google this for me" type queries

    **When NOT to use:**
    - SEC filing questions → Use semantic_search_sec_filing
    - Company news (last 7-30 days) → Use get_stock_news (faster, structured)
    - Market headlines → Use get_market_news or real_time_market_search
    - Historical analysis → Use RAG tools

    Data source: DuckDuckGo (real-time web index)
    Speed: 3-5 seconds
    No RAG needed: Results are already fresh from the web

    Args:
        query: Search query in natural language
        max_results: Number of results to return (default: 10, max: 20)

    Returns:
        Formatted search results with titles, URLs, and snippets

    Example queries:
        - "Apple stock price right now"
        - "Current Federal Reserve interest rate 2025"
        - "When is NVIDIA earnings call Q1 2025"
        - "Latest developments in AI chip manufacturing"
        - "Who is the current CEO of Tesla"
    """
    try:
        search_engine = get_search_engine()

        # Limit max results
        max_results = min(max_results, 20)

        results = search_engine.search_duckduckgo(query, max_results=max_results)

        if not results:
            return f"No search results found for query: '{query}'"

        # Format response
        response = f"**Web Search Results for: '{query}'**\n\n"
        response += f"Found {len(results)} results:\n\n"
        response += "---\n\n"

        for i, result in enumerate(results, 1):
            response += f"**{i}. {result['title']}**\n"
            response += f"URL: {result['url']}\n\n"
            response += f"{result['snippet']}\n\n"
            response += "---\n\n"

        response += f"\n*Search performed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        return response

    except Exception as e:
        return f"Error performing web search: {str(e)}"


@tool
def financial_web_search(ticker: str, query: str, max_results: int = 8) -> str:
    """
    **REAL-TIME FINANCIAL WEB SEARCH for company-specific current information.**

    Web search optimized for financial queries - automatically adds financial context.
    Use for VERY RECENT financial information about a specific company.

    **When to use:**
    - Current stock price or real-time market data
    - Very recent company announcements (today/this week)
    - Latest analyst ratings or upgrades
    - Breaking financial news about a company
    - Real-time earnings or revenue data

    **When NOT to use:**
    - General company news → Use get_stock_news (faster, better structured)
    - SEC filing questions → Use semantic_search_sec_filing
    - Historical data → Use quantitative tools (get_valuation_metrics, etc.)
    - Comprehensive analysis → Use multi_document_analysis

    Data source: DuckDuckGo with financial keywords added
    Speed: 3-5 seconds
    No RAG needed: Real-time web results

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")
        query: What you want to know about the company
        max_results: Number of results to return (default: 8)

    Returns:
        Formatted search results focused on financial information

    Example queries:
        - ticker="AAPL", query="stock price right now"
        - ticker="TSLA", query="delivery numbers announced today"
        - ticker="NVDA", query="analyst upgrade today"
        - ticker="AMZN", query="AWS revenue this quarter"
    """
    try:
        search_engine = get_search_engine()

        # Enhance query with financial context
        enhanced_query = f"{ticker} {query} stock financial market"

        results = search_engine.search_duckduckgo(enhanced_query, max_results=max_results)

        if not results:
            return f"No financial information found for {ticker} matching: '{query}'"

        # Format response
        response = f"**Financial Search: {ticker.upper()}**\n\n"
        response += f"Query: *{query}*\n\n"
        response += f"Found {len(results)} results:\n\n"
        response += "---\n\n"

        for i, result in enumerate(results, 1):
            response += f"**{i}. {result['title']}**\n"
            response += f"Source: {result['url']}\n\n"
            response += f"{result['snippet']}\n\n"
            response += "---\n\n"

        response += f"\n*Financial search for {ticker.upper()} performed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        return response

    except Exception as e:
        return f"Error performing financial search for {ticker}: {str(e)}"


@tool
def real_time_market_search(query: str, time_filter: str = "day") -> str:
    """
    **BREAKING MARKET NEWS - Real-time news search for market-wide events.**

    Uses DuckDuckGo news search for the most recent market information and news.
    Focus on market-wide events, not company-specific news.

    **When to use:**
    - Breaking market news or major market events
    - Today's market movements (indices, sectors)
    - Recent economic data releases (GDP, inflation, jobs)
    - Current market sentiment or trends
    - Real-time trading information or alerts
    - Market-wide topics (not company-specific)

    **When NOT to use:**
    - Company-specific news → Use get_stock_news
    - General market headlines → Use get_market_news
    - Company financial data → Use quantitative tools or SEC filing tools
    - Comprehensive analysis → Use multi_document_analysis

    Data source: DuckDuckGo news (filtered by time)
    Speed: 3-5 seconds
    No RAG needed: Real-time news results

    Args:
        query: Market-related query (market-wide, not company-specific)
        time_filter: Time filter - "day" (last 24h), "week" (last 7 days), or "month" (last 30 days)

    Returns:
        Recent news articles and market updates with timestamps

    Example queries:
        - "S&P 500 movement today"
        - "Federal Reserve interest rate decision today"
        - "Tech sector performance this week"
        - "Oil prices latest update"
        - "Market reaction to inflation data"
    """
    try:
        search_engine = get_search_engine()

        # Map time filter to DuckDuckGo format
        timelimit_map = {
            "day": "d",
            "week": "w",
            "month": "m"
        }
        timelimit = timelimit_map.get(time_filter.lower(), "d")

        # Search news
        results = search_engine.search_duckduckgo_news(
            query,
            max_results=10,
            timelimit=timelimit
        )

        if not results:
            return f"No recent market news found for: '{query}'"

        # Format response
        response = f"**Real-Time Market News: '{query}'**\n\n"
        response += f"Time filter: Last {time_filter}\n"
        response += f"Found {len(results)} recent articles:\n\n"
        response += "---\n\n"

        for i, result in enumerate(results, 1):
            source = result.get('source', 'Unknown')
            date = result.get('date', 'Unknown date')

            response += f"**{i}. {result['title']}**\n"
            response += f"*Source: {source} | Date: {date}*\n"
            response += f"URL: {result['url']}\n\n"
            response += f"{result['snippet']}\n\n"
            response += "---\n\n"

        response += f"\n*Market news search performed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        return response

    except Exception as e:
        return f"Error searching market news: {str(e)}"


@tool
def search_and_summarize(query: str, num_sources: int = 3) -> str:
    """
    Deep search that extracts and summarizes content from multiple sources.

    This is the MOST COMPREHENSIVE search tool. It:
    1. Searches the web
    2. Extracts full content from top results
    3. Provides detailed information for analysis

    Use this tool when you need:
    - In-depth research on a topic
    - Detailed information from multiple sources
    - Comprehensive analysis of current events
    - Full context, not just snippets

    WARNING: This tool is slower (10-15 seconds) because it fetches full pages.

    Args:
        query: Research query
        num_sources: Number of sources to extract and analyze (1-5, default: 3)

    Returns:
        Detailed content from multiple web sources

    Example queries:
        - "Comprehensive analysis of semiconductor shortage impact"
        - "Detailed explanation of recent banking crisis"
        - "In-depth review of Apple Vision Pro market reception"
    """
    try:
        search_engine = get_search_engine()

        # Limit sources
        num_sources = min(max(num_sources, 1), 5)

        print(f"Searching and extracting content from {num_sources} sources...")

        results = search_engine.search_and_extract(
            query,
            max_results=num_sources,
            extract_content=True
        )

        if not results:
            return f"No results found for: '{query}'"

        # Count successful extractions
        extracted_count = sum(1 for r in results if r.get('full_content'))

        # Format response
        response = f"**Deep Search & Analysis: '{query}'**\n\n"
        response += f"Extracted content from {extracted_count} of {num_sources} sources:\n\n"
        response += "=" * 60 + "\n\n"

        for i, result in enumerate(results, 1):
            response += f"## SOURCE {i}: {result['title']}\n\n"
            response += f"**URL:** {result['url']}\n\n"

            if result.get('full_content'):
                response += "**Full Content:**\n\n"
                response += result['full_content'][:3000]  # First 3000 chars

                if len(result.get('full_content', '')) > 3000:
                    response += "\n\n... [Content continues but truncated for length]"
            else:
                response += "**Snippet (full content not available):**\n\n"
                response += result['snippet']

            response += "\n\n" + "=" * 60 + "\n\n"

        response += f"\n*Deep search completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        response += f"\n*Note: Full page content extracted from {extracted_count} sources for comprehensive analysis.*"

        return response

    except Exception as e:
        return f"Error in deep search: {str(e)}"


if __name__ == "__main__":
    # Test search tools
    from dotenv import load_dotenv
    load_dotenv()

    print("Testing web search tools...\n")

    # Test basic search
    print("1. Testing web_search...")
    result = web_search.invoke({"query": "Apple stock price today", "max_results": 3})
    print(result[:500])
