"""
Web Search Tools for Real-Time Information

Provides web search capabilities for real-time market data,
current events, and information not available in historical documents.
"""

from .search import (
    web_search,
    financial_web_search,
    real_time_market_search,
    search_and_summarize
)

__all__ = [
    'web_search',
    'financial_web_search',
    'real_time_market_search',
    'search_and_summarize'
]
