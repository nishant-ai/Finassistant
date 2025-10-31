"""
SEC Filing Tool for Finassistant Agent

Provides functionality to retrieve and analyze SEC filings (10-K, 10-Q, 8-K, etc.)
for publicly traded companies. Integrates with LangGraph agent via LangChain tools.

Dependencies:
    - sec-edgar-downloader: For downloading SEC filings
    - beautifulsoup4: For XML/HTML parsing and cleaning
    - lxml: XML parser backend
"""

import os
import re
from typing import Optional, Dict
from functools import lru_cache
from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup
from langchain_core.tools import tool


class SECFilingsTool:
    """
    Core class for downloading and processing SEC filings.
    Supports multiple filing types: 10-K, 10-Q, 8-K, etc.
    """

    def __init__(self,
                 company_name: str = "FinassistantAgent",
                 email: str = "agent@finassistant.com"):
        """
        Initialize SEC filings downloader.

        Args:
            company_name: Your company/app name (required by SEC)
            email: Contact email (required by SEC)
        """
        self.downloader = Downloader(company_name, email)
        self.base_download_path = "sec-edgar-filings"

    def download_filing(self, ticker: str, filing_type: str = "10-K", limit: int = 1) -> Optional[str]:
        """
        Download SEC filing and return the file path.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")
            filing_type: Type of filing ("10-K", "10-Q", "8-K", etc.)
            limit: Number of filings to download (default: 1 - most recent)

        Returns:
            Path to the downloaded filing or None if failed
        """
        try:
            # Download the filing
            self.downloader.get(filing_type, ticker, limit=limit)

            # Construct path to the downloaded filing
            base_path = os.path.join(self.base_download_path, ticker, filing_type)

            # Get list of accession folders (excluding hidden files)
            all_items = os.listdir(base_path)
            accession_folders = [
                item for item in all_items
                if not item.startswith('.') and os.path.isdir(os.path.join(base_path, item))
            ]

            if not accession_folders:
                return None

            # Return path to most recent filing
            accession_number = accession_folders[0]
            file_path = os.path.join(base_path, accession_number, "full-submission.txt")

            if os.path.exists(file_path):
                return file_path
            else:
                return None

        except Exception as e:
            print(f"Error downloading {filing_type} for {ticker}: {e}")
            return None

    def read_filing_content(self, file_path: str) -> Optional[str]:
        """
        Read the content of a downloaded filing.

        Args:
            file_path: Path to the filing file

        Returns:
            File content as string or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading filing: {e}")
            return None

    def get_filing_content(self, ticker: str, filing_type: str = "10-K") -> Optional[str]:
        """
        Download and return the raw content of a SEC filing.

        Args:
            ticker: Stock ticker symbol
            filing_type: Type of filing (default: "10-K")

        Returns:
            Filing content as string or None if failed
        """
        file_path = self.download_filing(ticker, filing_type)
        if file_path:
            return self.read_filing_content(file_path)
        return None


class SECFilingProcessor:
    """
    Processes and cleans SEC filings for LLM consumption.
    Removes unnecessary sections and extracts key financial data.
    """

    @staticmethod
    def remove_zip_and_header(raw_content: str) -> str:
        """
        Remove ZIP document blocks and SEC-HEADER from filing.

        Args:
            raw_content: Raw filing content

        Returns:
            Cleaned content without ZIP blocks and headers
        """
        # Remove ZIP document blocks
        zip_pattern = re.compile(r'<DOCUMENT>.*?<TYPE>ZIP.*?</DOCUMENT>', re.DOTALL | re.IGNORECASE)
        content = re.sub(zip_pattern, '', raw_content)

        # Remove the SEC-HEADER block
        header_pattern = re.compile(r'<SEC-HEADER>.*?</SEC-HEADER>', re.DOTALL | re.IGNORECASE)
        content = re.sub(header_pattern, '', content)

        return content

    @staticmethod
    def extract_xbrl_data(content: str) -> Optional[str]:
        """
        Extract and clean XBRL/XML financial data from filing.

        Args:
            content: Pre-processed filing content

        Returns:
            Cleaned XBRL data as pretty-printed XML string or None if not found
        """
        # Find the main XML block
        xml_match = re.search(r'<XML>.*?</XML>', content, re.DOTALL)
        if not xml_match:
            return None

        xml_content = xml_match.group(0)

        # Remove inline styles
        style_pattern = re.compile(r'\s+style=".*?"', re.DOTALL | re.IGNORECASE)
        xml_content = re.sub(style_pattern, '', xml_content)

        # Parse with BeautifulSoup
        soup = BeautifulSoup(xml_content, 'lxml-xml')

        # Remove entity information from context tags (reduces noise)
        for context in soup.find_all('context'):
            entity_tag = context.find('entity')
            if entity_tag:
                entity_tag.decompose()

        # Clean HTML embedded within text content
        for tag in soup.find_all(True):
            if tag.string and ('<' in tag.string or '>' in tag.string):
                text_soup = BeautifulSoup(tag.string, 'html.parser')
                cleaned_text = text_soup.get_text(separator=' ', strip=True)
                tag.string.replace_with(cleaned_text)

        return soup.prettify()

    @staticmethod
    def extract_text_sections(raw_content: str, max_length: int = 50000) -> str:
        """
        Extract main text sections from filing (for narrative analysis).

        Args:
            raw_content: Raw filing content
            max_length: Maximum length of extracted text (to avoid overwhelming LLM)

        Returns:
            Extracted text content
        """
        # Remove headers and metadata
        content = SECFilingProcessor.remove_zip_and_header(raw_content)

        # Try to find the main HTML document section
        html_pattern = re.compile(r'<DOCUMENT>.*?<TYPE>10-K.*?<TEXT>(.*?)</TEXT>.*?</DOCUMENT>',
                                 re.DOTALL | re.IGNORECASE)
        html_match = html_pattern.search(content)

        if html_match:
            html_content = html_match.group(1)
            # Parse HTML and extract text
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)

            # Limit length
            if len(text) > max_length:
                text = text[:max_length] + "\n\n... [Content truncated for length]"

            return text

        # Fallback: return cleaned content
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)

        if len(text) > max_length:
            text = text[:max_length] + "\n\n... [Content truncated for length]"

        return text

    @classmethod
    def get_clean_financial_data(cls, ticker: str, filing_type: str = "10-K") -> Optional[str]:
        """
        Complete pipeline: download, extract, and clean financial data.

        Args:
            ticker: Stock ticker symbol
            filing_type: Type of filing

        Returns:
            Cleaned financial data (XBRL) or None if failed
        """
        tool = SECFilingsTool()
        raw_content = tool.get_filing_content(ticker, filing_type)

        if not raw_content:
            return None

        # Pre-process
        preprocessed = cls.remove_zip_and_header(raw_content)

        # Extract XBRL data
        clean_data = cls.extract_xbrl_data(preprocessed)

        return clean_data


# ============================================================================
# LangChain Tool Functions (Agent Integration)
# ============================================================================

@lru_cache(maxsize=32)
def _cached_filing_download(ticker: str, filing_type: str) -> Optional[str]:
    """
    Internal cached function to avoid re-downloading same filing.
    Cache size of 32 should handle typical session queries.
    """
    tool = SECFilingsTool()
    return tool.get_filing_content(ticker, filing_type)


@tool
def get_sec_filing_summary(ticker: str, filing_type: str = "10-K") -> str:
    """
    Get a quick overview/preview of a SEC filing (first 5000 characters).

    **When to use:**
    - User wants a QUICK PREVIEW or OVERVIEW of a filing
    - Need to check if a filing exists and is available
    - Want to see the general structure before deep searching
    - Looking for metadata (filing date, company info)

    **When NOT to use:**
    - User asks specific questions about content → Use semantic_search_sec_filing instead
    - Need comprehensive search → Use semantic_search_sec_filing
    - Analytical questions → Use semantic_search_sec_filing

    **Note:** Returns only first ~5000 characters (2-3% of full filing).
    For searching or analyzing content, use semantic_search_sec_filing.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")
        filing_type: Type of SEC filing - "10-K" (annual), "10-Q" (quarterly), or "8-K" (current events)

    Returns:
        Brief preview of filing (first 5000 characters) with metadata

    Example queries:
        - "Show me an overview of Apple's latest 10-K"
        - "Give me a preview of Tesla's quarterly report"
        - "Is Microsoft's 8-K available?"

    **For content questions, use semantic_search_sec_filing instead.**
    """
    try:
        # Download filing (cached)
        raw_content = _cached_filing_download(ticker.upper(), filing_type)

        if not raw_content:
            return f"Error: Could not retrieve {filing_type} filing for {ticker}. The ticker may be incorrect or the filing may not be available."

        # Extract text sections for summary
        processor = SECFilingProcessor()
        text_content = processor.extract_text_sections(raw_content, max_length=30000)

        # Create summary response
        response = f"**SEC {filing_type} Filing - {ticker.upper()}**\n\n"
        response += f"Filing Type: {filing_type}\n"
        response += f"Ticker: {ticker.upper()}\n\n"
        response += "**Content Preview:**\n"
        response += text_content[:5000]  # First 5000 chars for LLM context
        response += "\n\n... [Additional content available but truncated for summary]"

        return response

    except Exception as e:
        return f"Error retrieving SEC filing for {ticker}: {str(e)}"


@tool
def get_sec_financial_data(ticker: str, filing_type: str = "10-K") -> str:
    """
    Extract structured financial data (XBRL) from SEC filings.

    Use this tool when users need:
    - Detailed financial statements (balance sheet, income statement, cash flow)
    - XBRL/XML formatted financial data
    - Specific accounting figures and metrics from official filings
    - Historical financial data from annual/quarterly reports

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")
        filing_type: Type of SEC filing - "10-K" (annual) or "10-Q" (quarterly)

    Returns:
        Structured financial data in XBRL format, cleaned for analysis

    Example queries:
        - "Get Apple's balance sheet from their 10-K"
        - "Show me the financial statements for Microsoft"
        - "What are Tesla's reported revenues in their latest quarterly filing?"
    """
    try:
        # Use processor to get clean financial data
        clean_data = SECFilingProcessor.get_clean_financial_data(ticker.upper(), filing_type)

        if not clean_data:
            return f"Error: Could not extract financial data from {filing_type} for {ticker}. XBRL data may not be available in this filing."

        # Truncate if too large (XBRL can be massive)
        max_length = 40000
        if len(clean_data) > max_length:
            clean_data = clean_data[:max_length] + "\n\n... [Data truncated - full XBRL available but exceeds display limit]"

        response = f"**SEC {filing_type} Financial Data (XBRL) - {ticker.upper()}**\n\n"
        response += "The following structured financial data has been extracted and cleaned:\n\n"
        response += clean_data

        return response

    except Exception as e:
        return f"Error extracting financial data for {ticker}: {str(e)}"


@tool
def search_sec_filing(ticker: str, search_term: str, filing_type: str = "10-K") -> str:
    """
    **LEGACY KEYWORD SEARCH - Prefer semantic_search_sec_filing for better results.**

    Simple regex keyword search within SEC filings (searches first ~100K characters only).

    **LIMITATIONS - This tool has significant constraints:**
    - Only searches first 30-50% of document (rest is truncated)
    - Exact keyword matching only (no synonyms or semantic understanding)
    - May miss relevant information if exact keywords don't match
    - Returns text fragments without relevance ranking
    - No context or hierarchical understanding

    **When to use (RARE CASES ONLY):**
    - Looking for EXACT phrases or product names (e.g., "iPhone 15", "Model 3")
    - Searching for specific acronyms (e.g., "GDPR", "CCPA", "FDA")
    - Quick yes/no check if a specific term appears
    - Fallback if semantic_search_sec_filing times out or fails

    **For 95% of queries, use semantic_search_sec_filing instead.**

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")
        search_term: EXACT term or phrase to search for (case-insensitive)
        filing_type: Type of SEC filing - "10-K" (annual) or "10-Q" (quarterly)

    Returns:
        Text excerpts containing the exact search term (max 5 matches, with context)

    Example queries where this might be appropriate:
        - "Does Apple's 10-K mention 'iPhone 15' exactly?" (exact product name check)
        - "Find exact mentions of 'GDPR' in Meta's filing" (specific acronym)
        - "Search for 'Cybertruck' in Tesla's 10-K" (specific product name)

    **Better alternative: Use semantic_search_sec_filing with natural language queries.**
    """
    try:
        # Download filing (cached)
        raw_content = _cached_filing_download(ticker.upper(), filing_type)

        if not raw_content:
            return f"Error: Could not retrieve {filing_type} filing for {ticker}."

        # Extract text content
        processor = SECFilingProcessor()
        text_content = processor.extract_text_sections(raw_content, max_length=100000)

        # Search for term (case-insensitive)
        search_pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        matches = list(search_pattern.finditer(text_content))

        if not matches:
            return f"No matches found for '{search_term}' in {ticker}'s {filing_type} filing."

        # Extract context around matches (500 chars before/after)
        results = []
        context_length = 500

        for i, match in enumerate(matches[:5], 1):  # Limit to 5 matches
            start = max(0, match.start() - context_length)
            end = min(len(text_content), match.end() + context_length)
            context = text_content[start:end]

            results.append(f"**Match {i}:**\n{context}\n")

        response = f"**Search Results for '{search_term}' in {ticker.upper()} {filing_type}**\n\n"
        response += f"Found {len(matches)} total match(es). Showing top {min(5, len(matches))}:\n\n"
        response += "\n".join(results)

        if len(matches) > 5:
            response += f"\n\n... {len(matches) - 5} additional match(es) not shown."

        return response

    except Exception as e:
        return f"Error searching filing for {ticker}: {str(e)}"


@tool
def compare_sec_filings(ticker: str, filing_type: str = "10-K", num_filings: int = 2) -> str:
    """
    Compare multiple years of SEC filings to identify trends and changes.

    Use this tool when users want to:
    - Track changes over time in annual or quarterly reports
    - Compare year-over-year disclosures
    - Identify new risk factors or business changes
    - Analyze historical reporting trends

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")
        filing_type: Type of SEC filing - "10-K" (annual) or "10-Q" (quarterly)
        num_filings: Number of recent filings to compare (2-3 recommended)

    Returns:
        Comparison of recent filings with key differences highlighted

    Example queries:
        - "Compare Apple's last two annual reports"
        - "How has Microsoft's risk disclosure changed over the past 3 years?"
        - "Show me trends in Tesla's quarterly filings"
    """
    try:
        tool = SECFilingsTool()

        # Limit to reasonable number
        num_filings = min(num_filings, 3)

        # Download multiple filings
        file_path = tool.download_filing(ticker.upper(), filing_type, limit=num_filings)

        if not file_path:
            return f"Error: Could not download {filing_type} filings for {ticker}."

        # Get all filing folders
        base_path = os.path.join(tool.base_download_path, ticker.upper(), filing_type)
        all_items = os.listdir(base_path)
        accession_folders = sorted([
            item for item in all_items
            if not item.startswith('.') and os.path.isdir(os.path.join(base_path, item))
        ], reverse=True)

        # Read each filing
        filings_data = []
        for folder in accession_folders[:num_filings]:
            file_path = os.path.join(base_path, folder, "full-submission.txt")
            if os.path.exists(file_path):
                content = tool.read_filing_content(file_path)
                if content:
                    # Get brief preview
                    processor = SECFilingProcessor()
                    preview = processor.extract_text_sections(content, max_length=3000)
                    filings_data.append({
                        'accession': folder,
                        'preview': preview[:1500]
                    })

        if len(filings_data) < 2:
            return f"Error: Could not retrieve enough {filing_type} filings for comparison (need at least 2)."

        # Format comparison
        response = f"**{filing_type} Comparison for {ticker.upper()}**\n\n"
        response += f"Comparing {len(filings_data)} recent {filing_type} filing(s):\n\n"

        for i, filing in enumerate(filings_data, 1):
            response += f"**Filing {i} (Accession: {filing['accession']})**\n"
            response += f"{filing['preview']}\n\n"
            response += "---\n\n"

        response += "**Analysis Note:** Review the previews above to identify key changes in language, risk factors, or financial disclosures between filings."

        return response

    except Exception as e:
        return f"Error comparing filings for {ticker}: {str(e)}"


if __name__ == "__main__":
    # Test the tool
    sec_tool = SECFilingsTool()
    content = sec_tool.get_filing_content(ticker="AAPL", filing_type="10-K")

    if content:
        print("Successfully downloaded filing!")
        print(f"Content length: {len(content)} characters")
        print(f"Preview: {content[:500]}...")
    else:
        print("Failed to download filing")
