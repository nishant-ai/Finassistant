from newsapi import NewsApiClient
from langchain_core.tools import tool
from datetime import datetime, timedelta
import os
from typing import Optional
from newspaper import Article

def get_newsapi_client():
    """
    Returns a NewsAPI client instance using the API key from environment variables.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise ValueError("NEWS_API_KEY environment variable not set")
    return NewsApiClient(api_key=api_key)


@tool
def get_stock_news(ticker: str, days: Optional[int] = 7) -> str:
    """
    Fetches recent news articles related to a specific stock or company.
    Use this tool when a user asks about news, recent developments, or
    current events related to a company or stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        days: Number of days to look back for news (default: 7, max: 30)

    Returns:
        Formatted string containing news articles with titles, sources,
        publication dates, and descriptions.
    """
    try:
        newsapi = get_newsapi_client()

        # Limit days to reasonable range
        days = min(max(days, 1), 30)

        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)

        # Format dates for API
        from_param = from_date.strftime('%Y-%m-%d')
        to_param = to_date.strftime('%Y-%m-%d')

        # Search for news using the ticker symbol and common company variations
        query = f"{ticker} OR ${ticker}"

        # Fetch news articles
        response = newsapi.get_everything(
            q=query,
            from_param=from_param,
            to=to_param,
            language='en',
            sort_by='publishedAt',
            page_size=10
        )

        articles = response.get('articles', [])

        if not articles:
            return f"No recent news found for {ticker.upper()} in the last {days} days."

        # Format the response
        output = f"**Recent News for {ticker.upper()}** (Last {days} days)\n\n"
        output += f"Found {len(articles)} article(s):\n\n"

        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No title')
            source = article.get('source', {}).get('name', 'Unknown source')
            published_at = article.get('publishedAt', 'Unknown date')
            description = article.get('description', 'No description available')
            url = article.get('url', '')

            # Parse and format the date
            try:
                pub_date = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
                formatted_date = pub_date.strftime('%B %d, %Y at %I:%M %p')
            except:
                formatted_date = published_at

            output += f"**{i}. {title}**\n"
            output += f"   - Source: {source}\n"
            output += f"   - Published: {formatted_date}\n"
            output += f"   - Summary: {description}\n"
            if url:
                output += f"   - URL: {url}\n"
            output += "\n"

        return output

    except ValueError as ve:
        return f"Configuration Error: {str(ve)}. Please set NEWS_API_KEY in your environment variables."
    except Exception as e:
        return f"Error fetching news for {ticker.upper()}: {str(e)}"


@tool
def get_market_news(category: Optional[str] = "business", max_articles: Optional[int] = 10) -> str:
    """
    Fetches general market news and headlines from top financial news sources.
    Use this tool when a user asks about overall market news, financial headlines,
    or general business news (not specific to a single company).

    Args:
        category: News category ('business', 'technology', or 'general')
        max_articles: Maximum number of articles to return (default: 10)

    Returns:
        Formatted string containing top news headlines with sources and descriptions.
    """
    try:
        newsapi = get_newsapi_client()

        # Validate category
        valid_categories = ['business', 'technology', 'general']
        if category not in valid_categories:
            category = 'business'

        # Limit articles to reasonable range
        max_articles = min(max(max_articles, 5), 20)

        # Fetch top headlines
        response = newsapi.get_top_headlines(
            category=category,
            language='en',
            country='us',
            page_size=max_articles
        )

        articles = response.get('articles', [])

        if not articles:
            return f"No recent {category} news found."

        # Format the response
        output = f"**Top {category.title()} News Headlines**\n\n"
        output += f"Found {len(articles)} headline(s):\n\n"

        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No title')
            source = article.get('source', {}).get('name', 'Unknown source')
            published_at = article.get('publishedAt', 'Unknown date')
            description = article.get('description', 'No description available')
            url = article.get('url', '')

            # Parse and format the date
            try:
                pub_date = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
                formatted_date = pub_date.strftime('%B %d, %Y at %I:%M %p')
            except:
                formatted_date = published_at

            output += f"**{i}. {title}**\n"
            output += f"   - Source: {source}\n"
            output += f"   - Published: {formatted_date}\n"
            output += f"   - Summary: {description}\n"
            if url:
                output += f"   - URL: {url}\n"
            output += "\n"

        return output

    except ValueError as ve:
        return f"Configuration Error: {str(ve)}. Please set NEWS_API_KEY in your environment variables."
    except Exception as e:
        return f"Error fetching market news: {str(e)}"


@tool
def get_full_article_content(url: str) -> str:
    """
    Extracts and returns the full text content from a news article URL.
    Use this tool when a user asks for the full article, complete details,
    or wants to read the entire content of a specific news article.

    This tool legally scrapes publicly available news articles.
    Note: May not work with paywalled content or sites that block scraping.

    Args:
        url: The full URL of the news article to extract

    Returns:
        Formatted string containing the article title, author, publish date,
        and full text content. Returns error message if extraction fails.
    """
    try:
        # Create Article object
        article = Article(url)

        # Download and parse the article
        article.download()
        article.parse()

        # Extract metadata
        title = article.title or "No title available"
        authors = ", ".join(article.authors) if article.authors else "Unknown author"
        publish_date = article.publish_date.strftime('%B %d, %Y') if article.publish_date else "Unknown date"
        text = article.text or "No content could be extracted."

        # Format the output
        output = f"**{title}**\n\n"
        output += f"**Author(s):** {authors}\n"
        output += f"**Published:** {publish_date}\n"
        output += f"**Source URL:** {url}\n\n"
        output += "---\n\n"
        output += f"**Full Article Content:**\n\n{text}\n"

        # Add word count for context
        word_count = len(text.split())
        output += f"\n---\n*Article length: ~{word_count} words*"

        return output

    except Exception as e:
        error_msg = str(e)

        # Provide helpful error messages
        if "404" in error_msg:
            return f"Error: Article not found at {url}. The URL may be invalid or the article may have been removed."
        elif "403" in error_msg or "blocked" in error_msg.lower():
            return f"Error: Access denied to {url}. This site may block automated access or require a subscription."
        elif "timeout" in error_msg.lower():
            return f"Error: Connection timeout while accessing {url}. Please try again later."
        else:
            return f"Error extracting article from {url}: {error_msg}. The site may be using anti-scraping measures or the content may be behind a paywall."
