import pandas as pd
from bursary_scraper import BursaryScraper

class BursaryManager:
    def __init__(self, base_url):
        self.scraper = BursaryScraper(base_url)
        self.bursary_data = pd.DataFrame()

    def scrape_bursaries(self):
        print("Fetching main page...")
        content = self.scraper.get_page_content(self.scraper.base_url)
        if content:
            print("Extracting bursary links...")
            bursary_links = self.scraper.extract_bursary_links(content)
            print(f"Found {len(bursary_links)} bursary links")

            print("Extracting bursary details...")
            bursary_data = []
            for name, url in bursary_links:
                print(f"Checking: {name}")
                details = self.scraper.extract_bursary_details(url)
                if details:
                    details['url'] = url
                    bursary_data.append(details)

            self.bursary_data = pd.DataFrame(bursary_data)
            print(f"Extracted data for {len(self.bursary_data)} bursaries")
        else:
            print("Failed to fetch the main page. Please check your internet connection or try again later.")

    def save_data(self, filename='bursary_data.csv'):
        self.bursary_data.to_csv(filename, index=False)
        print(f"Bursary data saved to {filename}")