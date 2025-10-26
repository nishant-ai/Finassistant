import os
from typing import Optional, List
from sec_edgar_downloader import Downloader

class SECFilings:
    def __init__(self, filing_type: str = "10-K"):
        self.filing_type=filing_type
    
    def get_content(self, ticker: str):
        try:
            self.ticker = ticker
            dl = Downloader("MyCompanyName", "my.email@domain.com") # random info as of now
            dl.get(self.filing_type, self.ticker, limit=1)

            base_path = os.path.join("sec-edgar-filings", self.ticker, self.filing_type)
            
            all_items = os.listdir(base_path)
            accession_folders = [
                item for item in all_items 
                if not item.startswith('.') and os.path.isdir(os.path.join(base_path, item))
            ]

            if not accession_folders:
                print("No Accession Directory Found")
                return None
            
            accession_number = accession_folders[0]
            file_path = os.path.join(base_path, accession_number, "full-submission.txt")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content
        
        except FileNotFoundError:
            # This catches the error if the directory was not created
            print(f"Error: Directory not found. The download likely failed for ticker '{self.ticker}'.")
            return None

        except Exception as e:
            print("Unexpected Exception: ", e)
            return None


if __name__ == "__main__":
    sec10k = SECFilings(filing_type="8-K")
    content = sec10k.get_content(ticker="MSFT")

    print(content[1:1000], "...")