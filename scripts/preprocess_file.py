import re
import sys
from bs4 import BeautifulSoup
from sec_filings import SECFilings

def get_raw_filing(ticker: str) -> str:
    """Fetches the latest 10-K filing for a given ticker."""
    print(f"Fetching 10-K for {ticker}...")
    try:
        sec = SECFilings(filing_type="10-K")
        raw_content = sec.get_content(ticker=ticker)
        if not raw_content:
            print(f"Error: Failed to retrieve content for {ticker}. The ticker might be incorrect or the service is unavailable.")
            return None
        return raw_content
    except Exception as e:
        print(f"An error occurred during fetching: {e}")
        return None

def remove_zip_and_header(raw_content: str) -> str:
    """
    Removes any <DOCUMENT> blocks of type ZIP and the <SEC-HEADER> block.
    """
    # Remove ZIP document blocks
    zip_pattern = re.compile(r'<DOCUMENT>.*?<TYPE>ZIP.*?</DOCUMENT>', re.DOTALL | re.IGNORECASE)
    content = re.sub(zip_pattern, '', raw_content)
    
    # Remove the SEC-HEADER block
    header_pattern = re.compile(r'<SEC-HEADER>.*?</SEC-HEADER>', re.DOTALL | re.IGNORECASE)
    content = re.sub(header_pattern, '', content)
    
    return content

def extract_and_clean_xbrl(full_content: str) -> str:
    """
    Isolates the primary XBRL/XML data block and cleans it for LLM readability.
    This is the key step that removes the narrative sections.
    """
    xml_match = re.search(r'<XML>.*?</XML>', full_content, re.DOTALL)
    if not xml_match:
        print("Error: Could not find the main <XML> data block in the document.")
        return None
    
    xml_content = xml_match.group(0)

    style_pattern = re.compile(r'\s+style=".*?"', re.DOTALL | re.IGNORECASE)
    xml_content = re.sub(style_pattern, '', xml_content)

    soup = BeautifulSoup(xml_content, 'lxml-xml')

    for context in soup.find_all('context'):
        entity_tag = context.find('entity')
        if entity_tag:
            entity_tag.decompose()

    # --- ID REMOVAL BLOCK IS NOW GONE ---

    # Clean HTML embedded within the text content of a tag
    for tag in soup.find_all(True):
        if tag.string and ('<' in tag.string or '>' in tag.string):
            text_soup = BeautifulSoup(tag.string, 'html.parser')
            cleaned_text = text_soup.get_text(separator=' ', strip=True)
            tag.string.replace_with(cleaned_text)

    return soup.prettify()

# --- Main Execution ---
if __name__ == '__main__':
    TICKER = "AAPL"
    OUTPUT_FILENAME = "cleaned_financial_data.xml"

    # Step 1: Get the full filing
    full_filing_text = get_raw_filing(TICKER)
    
    if full_filing_text:
        # Step 2: Perform initial cleanup
        pre_processed_content = remove_zip_and_header(full_filing_text)
        
        # Step 3: Extract and clean the financial data block, now including style removal
        cleaned_xml = extract_and_clean_xbrl(pre_processed_content)

        if cleaned_xml:
            # Step 4: Save the final, data-only file
            with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
                f.write(cleaned_xml)
            print(f"✅ Success! All narrative text and inline styles were removed.")
            print(f"Clean financial data has been saved to '{OUTPUT_FILENAME}'")
