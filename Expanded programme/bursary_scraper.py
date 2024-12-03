import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict

class BursaryScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

    def get_page_content(self, url):
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {str(e)}")
            return None

    def extract_bursary_links(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.text.strip()
            if any(keyword in href.lower() or keyword in text.lower() for keyword in ['bursary', 'scholarship', 'fellowship']):
                if href.startswith('/'):
                    href = f"{self.base_url}{href}"
                elif not href.startswith(('http://', 'https://')):
                    href = f"{self.base_url}/{href}"
                if text and href.startswith(self.base_url):
                    links.append((text, href))
        return links

    def extract_bursary_details(self, url):
        content = self.get_page_content(url)
        if not content:
            return None

        soup = BeautifulSoup(content, 'html.parser')
        details = defaultdict(lambda: 'Unknown')

        # Extract bursary name
        name_element = soup.find('h1')
        if name_element:
            details['name'] = name_element.text.strip()

        # Extract eligibility requirements
        eligibility_section = soup.find(string='ELIGIBILITY REQUIREMENTS FOR')
        if eligibility_section:
            eligibility_text = eligibility_section.find_next('p').get_text(strip=True)
            details['eligibility'] = eligibility_text

        # Extract field of study
        about_section = soup.find(string='ABOUT THE BASF BURSARY PROGRAMME – FIELDS COVERED')
        if about_section:
            fields_text = about_section.find_next('p').get_text(strip=True)
            details['fields'] = fields_text

        # Extract closing date
        closing_date_section = soup.find(string=lambda text: 'CLOSING DATE' in text)
        if closing_date_section:
            closing_date_text = closing_date_section.find_next(lambda tag: tag.name == 'p' or tag.name == 'span').get_text(strip=True)
            details['closing_date'] = closing_date_text

        return details