import re
from bs4 import BeautifulSoup
from sec import SECFilings

class SECFilingCleaner:
    """
    A class to fetch, clean, and process the latest 10-K filing for a given stock ticker.

    This class encapsulates the entire workflow:
    1. Fetches the raw filing text from the SEC.
    2. Removes irrelevant headers and ZIP file data.
    3. Isolates and cleans the core XBRL/XML financial data block.
    """
    def __init__(self, ticker: str):
        """
        Initializes the cleaner for a specific ticker.

        Args:
            ticker (str): The stock ticker symbol (e.g., "AAPL", "TSLA").
        """
        self.ticker = ticker.upper()
        self.raw_content: str | None = None
        self.cleaned_xml: str | None = None
        print(f"Initialized cleaner for ticker: {self.ticker}")

    def _fetch_filing(self) -> None:
        """[Internal] Fetches the latest 10-K filing and stores it."""
        print(f"Fetching 10-K for {self.ticker}...")
        try:
            sec = SECFilings(filing_type="10-K")
            content = sec.get_content(ticker=self.ticker)
            if not content:
                print(f"Error: Failed to retrieve content for {self.ticker}. The ticker might be incorrect or the service is unavailable.")
                self.raw_content = None
            else:
                self.raw_content = content
        except Exception as e:
            print(f"An error occurred during fetching: {e}")
            self.raw_content = None

    def _preprocess_content(self, raw_content: str) -> str:
        """[Internal] Removes SEC headers and ZIP document blocks."""
        # Remove ZIP document blocks
        zip_pattern = re.compile(r'<DOCUMENT>.*?<TYPE>ZIP.*?</DOCUMENT>', re.DOTALL | re.IGNORECASE)
        content = re.sub(zip_pattern, '', raw_content)
        
        # Remove the SEC-HEADER block
        header_pattern = re.compile(r'<SEC-HEADER>.*?</SEC-HEADER>', re.DOTALL | re.IGNORECASE)
        content = re.sub(header_pattern, '', content)
        
        return content

    def _extract_and_clean_xbrl(self, preprocessed_content: str) -> str | None:
        """[Internal] Isolates and cleans the primary XBRL/XML data block."""
        xml_match = re.search(r'<XML>.*?</XML>', preprocessed_content, re.DOTALL)
        if not xml_match:
            print("Error: Could not find the main <XML> data block in the document.")
            return None
        
        xml_content = xml_match.group(0)

        # Remove all inline style attributes for better LLM readability
        style_pattern = re.compile(r'\s+style=".*?"', re.DOTALL | re.IGNORECASE)
        xml_content = re.sub(style_pattern, '', xml_content)

        soup = BeautifulSoup(xml_content, 'lxml-xml')

        # Remove context tags which contain redundant entity information
        for context in soup.find_all('context'):
            entity_tag = context.find('entity')
            if entity_tag:
                entity_tag.decompose()

        # Clean HTML embedded within the text content of tags
        for tag in soup.find_all(True):
            if tag.string and ('<' in tag.string or '>' in tag.string):
                text_soup = BeautifulSoup(tag.string, 'html.parser')
                cleaned_text = text_soup.get_text(separator=' ', strip=True)
                tag.string.replace_with(cleaned_text)

        return soup.prettify()

    def process_and_save(self, output_filename: str) -> bool:
        """
        Executes the full fetch and clean workflow and saves the result to a file.

        Args:
            output_filename (str): The path to save the cleaned XML file.

        Returns:
            bool: True if successful, False otherwise.
        """
        # Step 1: Fetch the filing
        self._fetch_filing()
        if not self.raw_content:
            return False

        # Step 2: Perform initial cleanup
        preprocessed = self._preprocess_content(self.raw_content)
        
        # Step 3: Extract and clean the financial data block
        self.cleaned_xml = self._extract_and_clean_xbrl(preprocessed)

        if not self.cleaned_xml:
            return False

        # Step 4: Save the final, data-only file
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(self.cleaned_xml)
            print(f"✅ Success! Clean financial data saved to '{output_filename}'")
            return True
        except IOError as e:
            print(f"Error: Could not write to file '{output_filename}'. Reason: {e}")
            return False

# --- Main Execution ---
if __name__ == '__main__':
    TICKER = "AAPL"
    OUTPUT_FILENAME = f"cleaned_{TICKER}_financial_data.xml"

    # Instantiate the cleaner for a specific ticker
    cleaner = SECFilingCleaner(ticker=TICKER)

    # Call the single function to run the entire process
    cleaner.process_and_save(output_filename=OUTPUT_FILENAME)
