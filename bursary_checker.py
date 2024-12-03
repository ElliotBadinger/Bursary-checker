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
        self.bursary_data = self.load_cached_data() or []
        self.total_links = 0
        self.processed_links = 0

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
            status_forcelist=[500, 502, 503, 504]  # Removed 404 from retry list
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

    def get_page_content(self, url, timeout=15):
        try:
            response = self.session.get(url, headers=self.headers, timeout=timeout)
            if response.status_code == 404:
                self.logger.warning(f"Page not found: {url}")
                return None
            response.raise_for_status()
            time.sleep(0.5)  # Rate limiting
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def check_bursary_status(self, url, name, pbar):
        try:
            content = self.get_page_content(url)
            if not content:
                pbar.update(1)
                return {"name": name, "status": "Error", "closing_date": None, "details": "Failed to fetch page"}

            # Fixed BeautifulSoup parser initialization
            soup = BeautifulSoup(content, 'html.parser')
            text_content = soup.get_text().lower()

            status_map = {
                'open': ['applications are open', 'apply now', 'how to apply'],
                'closed': ['application closed', 'not accepting', 'applications ended']
            }

            status = "Unknown"
            details = ""
            closing_date = None

            for key, indicators in status_map.items():
                if any(ind in text_content for ind in indicators):
                    status = key.capitalize()
                    break

            date_patterns = [
                r'(\d{1,2}\s+[a-z]+\s+202[45])',
                r'closing\s*date[:\s]*(\d{1,2}\s+[a-z]+\s+202[45])'
            ]

            for pattern in date_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(1)
                        closing_date = datetime.strptime(date_str, '%d %B %Y')
                        if closing_date < datetime.now():
                            status = "Closed"
                        details = f"Closing date: {closing_date.strftime('%d %B %Y')}"
                        break
                    except ValueError:
                        self.logger.warning(f"Invalid date format found in {url}: {date_str}")

            result = {
                'name': name,
                'url': url,
                'status': status,
                'closing_date': closing_date,
                'details': details,
                'last_updated': datetime.now()
            }

            self.bursary_data.append(result)
            self.save_cached_data()
            pbar.update(1)
            return result

        except Exception as e:
            self.logger.error(f"Error processing {name} at {url}: {e}")
            pbar.update(1)
            return {"name": name, "status": "Error", "closing_date": None, "details": str(e)}

    def extract_bursary_links(self, category_url):
        content = self.get_page_content(category_url)
        if not content:
            return []

        # Fixed BeautifulSoup parser initialization
        soup = BeautifulSoup(content, 'html.parser')
        links = []

        # Updated URL handling
        category_base = self.base_url.rstrip('/') + '/bursaries-south-africa/'
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.text.strip()
            if any(keyword in (href.lower() + text.lower()) 
                   for keyword in ['bursary', 'scholarship', 'fellowship']):
                if href.startswith('/'):
                    href = f'{self.base_url.rstrip("/")}{href}'
                elif not href.startswith(('http://', 'https://')):
                    href = f'{self.base_url.rstrip("/")}/{href}'
                if href.startswith(self.base_url) and text:
                    links.append((text, href))
        
        return list(set(links))  # Remove duplicates

    def check_bursaries_concurrent(self, links, max_workers=5):
        self.total_links = len(links)
        with tqdm(total=self.total_links, desc="Processing bursaries") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.check_bursary_status, url, name, pbar): (name, url) 
                    for name, url in links
                }
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as exc:
                        name, url = futures[future]
                        self.logger.error(f'Error processing {name} at {url}: {exc}')

    def load_cached_data(self):
        try:
            if os.path.exists('bursary_data.pkl'):
                with open('bursary_data.pkl', 'rb') as f:
                    data = pickle.load(f)
                current_time = datetime.now()
                data = [entry for entry in data if 
                       'last_updated' in entry and 
                       (current_time - entry['last_updated']).total_seconds() < 86400]
                return data
        except Exception as e:
            self.logger.error(f"Error loading cached data: {e}")
        return None

    def save_cached_data(self):
        try:
            with open('bursary_data.pkl', 'wb') as f:
                pickle.dump(self.bursary_data, f)
        except Exception as e:
            self.logger.error(f"Error saving cached data: {e}")

    def generate_report(self, field):
        print(f"\nGenerating report for {field} bursaries...")
        
        # Updated URL construction
        category_url = f"{self.base_url.rstrip('/')}/{field.lower().replace(' ', '-')}-bursaries-south-africa/"
        bursary_links = self.extract_bursary_links(category_url)
        
        if not bursary_links:
            print(f"No bursary links found for {field}. Please check if the category exists.")
            return
            
        print(f"Found {len(bursary_links)} potential bursary links")

        self.check_bursaries_concurrent(bursary_links)

        open_bursaries = [b for b in self.bursary_data if b['status'] == 'Open']
        
        if not open_bursaries:
            print("No open bursaries found.")
            return

        pdf_filename = f"bursary_report_{field.lower().replace(' ', '_')}.pdf"
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        styles = getSampleStyleSheet()

        elements = []
        elements.append(Paragraph(f"Open Bursary Report for {field}", styles["Heading1"]))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["BodyText"]))
        elements.append(Paragraph(f"Total bursaries found: {len(open_bursaries)}", styles["BodyText"]))
        elements.append(Paragraph("", styles["BodyText"]))

        data = [['Bursary Name', 'Closing Date', 'Details', 'Link']]
        
        for bursary in open_bursaries:
            try:
                safe_url = bursary['url'].replace('&', '&amp;')
                data.append([
                    Paragraph(bursary['name'], styles["BodyText"]),
                    Paragraph(bursary['closing_date'].strftime('%d %B %Y') if bursary['closing_date'] else 'Not specified', styles["BodyText"]),
                    Paragraph(bursary['details'], styles["BodyText"]),
                    Paragraph(f'<link href="{safe_url}">Apply</link>', styles["BodyText"])
                ])
            except Exception as e:
                self.logger.error(f"Error processing bursary {bursary['name']}: {e}")

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
        base_url = "https://www.zabursaries.co.za/"
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