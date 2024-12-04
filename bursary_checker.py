import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import os
import pickle
import concurrent.futures
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from tqdm import tqdm
import time
import logging
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class BursaryReportGenerator:
    def __init__(self, base_url):
        self.base_url = base_url
        self.setup_session()
        self.setup_logging()
        self.cache_file = 'bursary_data_cache.pkl'
        self.bursary_data = self.load_cached_data() or []
        self.total_links = 0
        self.processed_links = 0
        # Updated excluded terms to be more specific
        self.excluded_terms = [
            'sassa payment dates',
            'srd grant payment',
            'post office payment',
            'cash point location'
        ]
        self.category_mapping = {
            'arts': 'music-and-performing-arts',
            'computer science & it': 'computer-science-it',
            'construction & built environment': 'built-environment'
        }

    def load_cached_data(self):
        """Load cached bursary data from file if it exists and is not expired."""
        try:
            if os.path.exists(self.cache_file):
                # Check if cache is older than 24 hours
                if time.time() - os.path.getmtime(self.cache_file) < 86400:  # 24 hours in seconds
                    with open(self.cache_file, 'rb') as f:
                        return pickle.load(f)
                else:
                    self.logger.info("Cache expired, will fetch fresh data")
            return []
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}")
            return []

    def save_cached_data(self):
        """Save current bursary data to cache file."""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.bursary_data, f)
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")

    def get_page_content(self, url):
        """Fetch page content with retry logic."""
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def check_bursaries_concurrent(self, bursary_links):
        """Process bursary links concurrently using ThreadPoolExecutor."""
        self.total_links = len(bursary_links)
        with tqdm(total=self.total_links, desc="Processing bursaries") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(self.check_bursary_status, url, name, pbar)
                    for name, url in bursary_links
                ]
                concurrent.futures.wait(futures)

    def setup_logging(self):
        logging.basicConfig(
            filename='bursary_checker.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_session(self):
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

    def is_valid_bursary_link(self, href, text):
        # Check if the link contains excluded terms
        if any(term in (href + text).lower() for term in self.excluded_terms):
            return False
        
        # Verify it's a bursary/scholarship link
        if not any(keyword in (href.lower() + text.lower()) 
                  for keyword in ['bursary', 'scholarship', 'fellowship']):
            return False
            
        # Additional validation
        if 'view-all' in href.lower() or 'news' in href.lower():
            return False
            
        return True

    def parse_date(self, date_str):
        try:
            # Handle various date formats
            patterns = [
                r'(\d{1,2})\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s*(202[45])',
                r'(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(202[45])',
                r'(202[45])/(\d{1,2})/(\d{1,2})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_str, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 3:
                        if '/' in date_str:
                            year, month, day = match.groups()
                            # Convert month number to month name
                            month = datetime(2000, int(month), 1).strftime('%B')
                        else:
                            day, month, year = match.groups()
                        # Standardize month name
                        month = month[:3].title()
                        return datetime.strptime(f"{day} {month} {year}", "%d %b %Y")
            return None
        except ValueError as e:
            self.logger.warning(f"Date parsing error: {date_str} - {str(e)}")
            return None

    def get_category_url(self, field):
        # Handle special category mappings
        field_lower = field.lower()
        if field_lower in self.category_mapping:
            category_slug = self.category_mapping[field_lower]
        else:
            category_slug = field_lower.replace(' & ', '-').replace(' ', '-')
        
        return f"{self.base_url.rstrip('/')}/{category_slug}-bursaries-south-africa/"

    def extract_bursary_links(self, category_url):
        """Extracts bursary links from the category page."""
        try:
            content = self.get_page_content(category_url)
            if not content:
                return []

            soup = BeautifulSoup(content, 'html.parser')
            bursary_links = []

            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.text.strip()
                if self.is_valid_bursary_link(href, text):
                    full_url = href if href.startswith('http') else self.base_url + href
                    bursary_links.append((text, full_url))

            return bursary_links
        except Exception as e:
            self.logger.error(f"Error extracting bursary links from {category_url}: {e}")
            return []
        
    def check_bursary_status(self, url, name, pbar):
        try:
            content = self.get_page_content(url)
            if not content:
                pbar.update(1)
                return None

            soup = BeautifulSoup(content, 'html.parser')
            text_content = soup.get_text().lower()

            # Skip if content contains excluded terms
            if any(term in text_content for term in self.excluded_terms):
                pbar.update(1)
                return None

            # Improved status detection patterns
            status = "Open"  # Default to Open unless explicitly found to be closed
            closed_patterns = [
                r'applications?\s+(?:are\s+)?closed\s+for\s+202[45]',
                r'deadline\s+has\s+passed\s+for\s+202[45]',
                r'applications?\s+(?:has|have)\s+ended\s+for\s+202[45]',
                r'no\s+longer\s+accepting\s+applications?\s+for\s+202[45]'
            ]

            # Check for explicit closure statements
            for pattern in closed_patterns:
                if re.search(pattern, text_content):
                    status = "Closed"
                    break

            # Enhanced date extraction
            date_patterns = [
                r'closing date[:\s]*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+202[45])',
                r'deadline[:\s]*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+202[45])',
                r'applications? close[:\s]*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+202[45])',
                r'due date[:\s]*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+202[45])',
                r'submit before[:\s]*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+202[45])',
                r'last day to apply[:\s]*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+202[45])'
            ]

            closing_date = None
            details = ""

            for pattern in date_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    # Remove ordinal indicators before parsing
                    date_str = re.sub(r'(?:st|nd|rd|th)', '', date_str)
                    closing_date = self.parse_date(date_str)
                    if closing_date:
                        if closing_date < datetime.now():
                            status = "Closed"
                        details = f"Closing date: {closing_date.strftime('%d %B %Y')}"
                        break

            # Look for current year references to determine if bursary is current
            current_year = datetime.now().year
            next_year = current_year + 1
            year_pattern = f"202[45]|{current_year}|{next_year}"
            
            if not re.search(year_pattern, text_content):
                status = "Closed"  # Mark as closed if no recent year references found

            # Extract requirements
            requirements_section = soup.find(lambda tag: tag.name in ['div', 'section', 'p'] and 
                                          any(keyword in tag.get_text().lower() 
                                              for keyword in ['requirements', 'eligibility', 'criteria']))
            if requirements_section:
                details += "\nKey requirements: " + ' '.join(requirements_section.get_text().split()[:50]) + "..."

            result = {
                'name': name,
                'url': url,
                'status': status,
                'closing_date': closing_date,
                'details': details.strip(),
                'last_updated': datetime.now()
            }

            self.bursary_data.append(result)
            self.save_cached_data()
            pbar.update(1)
            return result

        except Exception as e:
            self.logger.error(f"Error processing {name} at {url}: {e}")
            pbar.update(1)
            return None

    def generate_report(self, field):
        print(f"\nGenerating report for {field} bursaries...")
        
        # Clear previous data before generating new report
        self.bursary_data = []
        
        category_url = self.get_category_url(field)
        print(f"Checking category URL: {category_url}")
        
        bursary_links = self.extract_bursary_links(category_url)
        
        if not bursary_links:
            print(f"No bursary links found for {field}. Please check if the category exists.")
            return
            
        print(f"Found {len(bursary_links)} potential bursary links")

        self.check_bursaries_concurrent(bursary_links)

        # Filter out None values and get only open bursaries
        open_bursaries = [b for b in self.bursary_data if b and b['status'] == 'Open']
        
        if not open_bursaries:
            print("No open bursaries found. This might be an error - please check the website manually.")
            return

        pdf_filename = f"bursary_report_{field.lower().replace(' ', '_')}.pdf"
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        styles = getSampleStyleSheet()

        elements = []
        elements.append(Paragraph(f"Open Bursary Report for {field}", styles["Heading1"]))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["BodyText"]))
        elements.append(Paragraph(f"Total bursaries found: {len(open_bursaries)}", styles["BodyText"]))
        elements.append(Paragraph("", styles["BodyText"]))

        # Sort bursaries by closing date
        open_bursaries.sort(key=lambda x: (x['closing_date'] or datetime.max))

        data = [['Bursary Name', 'Closing Date', 'Details', 'Link']]
        
        for bursary in open_bursaries:
            safe_url = bursary['url'].replace('&', '&amp;')
            closing_date_str = (bursary['closing_date'].strftime('%d %B %Y') 
                              if bursary['closing_date'] else 'Not specified')
            
            data.append([
                Paragraph(bursary['name'], styles["BodyText"]),
                Paragraph(closing_date_str, styles["BodyText"]),
                Paragraph(bursary['details'], styles["BodyText"]),
                Paragraph(f'<link href="{safe_url}">Apply</link>', styles["BodyText"])
            ])

        table = Table(data, colWidths=[2.5*inch, 1.5*inch, 2*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 14),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('WORDWRAP', (0,0), (-1,-1), True),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))

        elements.append(table)
        doc.build(elements)
        print(f"\nReport generated successfully: {pdf_filename}")

def main():
    try:
        base_url = "https://www.zabursaries.co.za"
        generator = BursaryReportGenerator(base_url)

        print("Select a field of study:")
        fields = ["Accounting", "Arts", "Commerce", "Computer Science & IT", 
                 "Construction & Built Environment", "Education", "Engineering", 
                 "General", "Government", "International", "Law", "Medical", 
                 "Postgraduate", "Science"]
        
        for i, field in enumerate(fields, start=1):
            print(f"{i}. {field}")

        while True:
            try:
                choice = input("\nEnter the number of your field of study (1-14): ")
                choice = int(choice)
                if 1 <= choice <= len(fields):
                    break
                print(f"Please enter a number between 1 and {len(fields)}")
            except ValueError:
                print("Please enter a valid number")

        field_of_study = fields[choice - 1]
        generator.generate_report(field_of_study)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"\nAn error occurred. Please check the log file for details.")

if __name__ == "__main__":
    main()