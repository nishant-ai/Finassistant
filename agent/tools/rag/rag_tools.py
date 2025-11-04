"""
RAG Tools for LangChain Agent Integration

Provides semantic search tools for SEC filings and multi-document synthesis.
"""

from datetime import datetime
from langchain_core.tools import tool

from agent.tools.sec_filing.sec_filing import SECFilingsTool, SECFilingProcessor
from .chunking import SECFilingChunker, Chunk
from .vector_store import get_vector_store
from .embeddings import get_embedding_service


# Initialize global instances
_vector_store = None
_embedding_service = None


def get_rag_instances():
    """Get or create RAG service instances."""
    global _vector_store, _embedding_service

    if _vector_store is None:
        _vector_store = get_vector_store()

    if _embedding_service is None:
        _embedding_service = get_embedding_service()

    return _vector_store, _embedding_service


def index_sec_filing(ticker: str, filing_type: str = "10-K") -> bool:
    """
    Index a SEC filing into the vector store if not already indexed.

    Args:
        ticker: Stock ticker symbol
        filing_type: Type of filing (10-K, 10-Q, etc.)

    Returns:
        True if indexed successfully, False otherwise
    """
    vector_store, _ = get_rag_instances()

    # Extract year from current date (filings are typically from previous year)
    current_year = datetime.now().year

    # Check if already indexed
    if vector_store.check_filing_indexed(ticker, filing_type, current_year):
        print(f"{ticker} {filing_type} {current_year} already indexed")
        return True

    # Download filing
    sec_tool = SECFilingsTool()
    raw_content = sec_tool.get_filing_content(ticker, filing_type)

    if not raw_content:
        print(f"Failed to download {ticker} {filing_type}")
        return False

    # Clean content
    processor = SECFilingProcessor()
    clean_content = processor.remove_zip_and_header(raw_content)
    text_content = processor.extract_text_sections(clean_content, max_length=500000)  # Get full content

    # Chunk the document
    chunker = SECFilingChunker()
    metadata = {
        'ticker': ticker.upper(),
        'filing_type': filing_type,
        'filing_year': current_year,
        'indexed_date': datetime.now().isoformat()
    }

    chunks = chunker.chunk_document(text_content, metadata)

    if not chunks:
        print(f"Failed to chunk {ticker} {filing_type}")
        return False

    # Add to vector store
    vector_store.add_chunks(chunks, collection_name="sec_filings")

    print(f"Successfully indexed {ticker} {filing_type} with {len(chunks)} chunks")
    return True


@tool
def semantic_search_sec_filing(ticker: str, query: str, filing_type: str = "10-K") -> str:
    """
    **PRIMARY SEC FILING SEARCH TOOL - Use this by default for ALL SEC filing questions.**

    Advanced semantic search across ENTIRE SEC filings using RAG and vector embeddings.
    This is the most powerful and comprehensive way to search SEC filings.

    When to use (DEFAULT CHOICE):
    - ANY question about SEC filing content
    - Questions requiring understanding of concepts, themes, or context
    - When you need comprehensive, ranked results from the entire document
    - Analysis of risks, strategies, competitive advantages, challenges, etc.

    Key advantages:
    - Searches 100% of filing (not truncated like basic search)
    - Understands synonyms and context ("risks" finds "uncertainties", "challenges", "threats")
    - Returns sections ranked by semantic relevance
    - Provides both section summaries and detailed content
    - Hierarchical retrieval for better context

    Performance:
    - First query per company: 30-60 seconds (one-time indexing)
    - All subsequent queries: 2-3 seconds (instant from vector DB)

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")
        query: Natural language question (e.g., "What are the main competitive advantages?")
        filing_type: Type of SEC filing - "10-K" (annual) or "10-Q" (quarterly)

    Returns:
        Ranked, relevant sections from the filing with context and metadata

    Example queries:
        - "What are Apple's main competitive advantages according to their 10-K?"
        - "How does Microsoft describe their AI strategy?"
        - "What supply chain risks does Tesla face?"
        - "Find information about cybersecurity in Meta's filing"
        - "What does Amazon say about AWS competition?"
        - "Describe the company's research and development efforts"
    """
    try:
        vector_store, _ = get_rag_instances()

        # Ensure filing is indexed
        print(f"Ensuring {ticker} {filing_type} is indexed...")
        if not index_sec_filing(ticker.upper(), filing_type):
            return f"Error: Could not index {filing_type} for {ticker}. The ticker may be incorrect or filing may not be available."

        # Perform hierarchical semantic search
        results = vector_store.query_sec_filing_hierarchical(
            query=query,
            ticker=ticker.upper(),
            filing_type=filing_type,
            n_results=10
        )

        if not results:
            return f"No relevant information found for query '{query}' in {ticker}'s {filing_type}."

        # Format response
        response = f"**Semantic Search Results: {ticker.upper()} {filing_type}**\n\n"
        response += f"Query: *{query}*\n\n"
        response += f"Found {len(results)} relevant sections:\n\n"
        response += "---\n\n"

        for i, result in enumerate(results, 1):
            section = result['metadata'].get('section', 'Unknown Section')
            chunk_type = result['chunk_type']
            relevance_score = 1 - result['distance']  # Convert distance to similarity

            response += f"**Result {i}** - {section} ({chunk_type.upper()}) [Relevance: {relevance_score:.2f}]\n\n"
            response += f"{result['text']}\n\n"
            response += "---\n\n"

        response += f"\n*Searched using RAG across entire {filing_type} filing with semantic understanding.*"

        return response

    except Exception as e:
        return f"Error performing semantic search for {ticker}: {str(e)}"


@tool
def multi_document_analysis(ticker: str, query: str) -> str:
    """
    **COMPREHENSIVE SEC FILING ANALYSIS - Deep search across multiple filing types.**

    Performs comprehensive semantic search across SEC filings (10-K and 10-Q) to provide
    a complete picture from official company disclosures.

    **When to use:**
    - Questions requiring COMPREHENSIVE analysis from SEC filings
    - Investment due diligence requiring thorough research
    - Risk assessment from official company statements
    - Strategic analysis of company disclosures
    - Questions with words like "comprehensive", "overall", "complete picture"

    **What it does:**
    1. Searches SEC 10-K filings (annual reports)
    2. Can be extended to search 10-Q (quarterly reports) as well
    3. Synthesizes information from multiple sections
    4. Provides ranked results by relevance

    Performance: 30-60s first time (indexing), then 3-5s

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")
        query: Comprehensive analysis question (e.g., "Analyze Apple's AI strategy")

    Returns:
        Comprehensive analysis with multiple relevant sections from SEC filings

    Example queries:
        - "Give me a comprehensive analysis of Microsoft's cloud strategy"
        - "Analyze Tesla's competitive position from SEC filings"
        - "What are Apple's main risks according to their filings?"
        - "Evaluate Amazon's growth drivers from official disclosures"

    **For basic queries, use semantic_search_sec_filing instead.**
    """
    try:
        vector_store, _ = get_rag_instances()

        # Index SEC filing
        print(f"Ensuring {ticker} filings are indexed...")
        if not index_sec_filing(ticker.upper(), "10-K"):
            return f"Error: Could not index SEC filings for {ticker}."

        # Query SEC filings with higher result count for comprehensive analysis
        results = vector_store.query_sec_filing_hierarchical(
            query=query,
            ticker=ticker.upper(),
            filing_type="10-K",
            n_results=15  # More results for comprehensive view
        )

        if not results:
            return f"No relevant information found for query '{query}' in {ticker}'s SEC filings."

        # Format comprehensive response
        response = f"**Comprehensive SEC Filing Analysis: {ticker.upper()}**\n\n"
        response += f"Query: *{query}*\n\n"
        response += f"Found {len(results)} relevant sections from 10-K filing:\n\n"
        response += "=" * 60 + "\n\n"

        # Group by section for better organization
        sections_covered = set()
        for i, result in enumerate(results, 1):
            section = result['metadata'].get('section', 'Unknown')
            chunk_type = result['chunk_type']
            relevance = 1 - result['distance']

            # Add section header if new section
            if section not in sections_covered:
                response += f"\n### {section}\n\n"
                sections_covered.add(section)

            response += f"**Result {i}** ({chunk_type}) [Relevance: {relevance:.2f}]\n\n"
            response += f"{result['text'][:600]}\n\n"
            response += "---\n\n"

        # Summary
        response += "\n## ANALYSIS SUMMARY\n\n"
        response += f"This comprehensive analysis searched {len(results)} sections across {len(sections_covered)} different parts of the SEC 10-K filing. "
        response += "Results are ranked by semantic relevance to your query.\n\n"
        response += f"**Sections covered:** {', '.join(sorted(sections_covered))}\n\n"
        response += "*Note: This represents a deep analysis across the entire SEC filing using advanced RAG technology.*"

        return response

    except Exception as e:
        return f"Error performing comprehensive analysis: {str(e)}"


@tool
def rag_system_status() -> str:
    """
    Get status and statistics about the RAG system.

    Shows how many documents are indexed and available for semantic search.

    Returns:
        System status information
    """
    try:
        vector_store, _ = get_rag_instances()

        stats = vector_store.get_collection_stats()

        response = "**RAG System Status**\n\n"
        response += f"SEC Filings Indexed: {stats.get('sec_filings', 0)} chunks\n\n"

        response += "**Capabilities:**\n"
        response += "- Semantic search across SEC 10-K and 10-Q filings\n"
        response += "- Comprehensive analysis of company disclosures\n"
        response += "- Hierarchical retrieval for complete context\n\n"

        response += "*Note: SEC filings are automatically indexed on first access.*"

        return response

    except Exception as e:
        return f"Error getting RAG system status: {str(e)}"
