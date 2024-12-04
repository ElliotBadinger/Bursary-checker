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
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn, BarColumn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table as RichTable
from rich import print as rprint
import time
import logging
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class BursaryReportGenerator:
    def __init__(self, base_url):
        self.base_url = base_url
        self.console = Console()
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
        self.progress = None
    
    def _display_console_summary(self, bursaries):
        """Display a summary of bursaries in a rich formatted table."""
        table = RichTable(title="Open Bursaries Summary", show_header=True, header_style="bold magenta")
        
        # Add columns
        table.add_column("Bursary Name", style="cyan", no_wrap=False)
        table.add_column("Closing Date", style="green")
        table.add_column("Status", style="yellow")
        
        # Add rows
        for bursary in bursaries:
            closing_date = (bursary['closing_date'].strftime('%d %B %Y') 
                          if bursary['closing_date'] else 'Not specified')
            table.add_row(
                bursary['name'],
                closing_date,
                bursary['status']
            )
        
        self.console.print("\n[bold]Summary of Open Bursaries[/bold]")
        self.console.print(table)
        self.console.print(f"\nTotal open bursaries found: [green]{len(bursaries)}[/green]")    
    def _generate_pdf_report(self, field, bursaries):
        """Generate PDF report for bursaries."""
        try:
            filename = f"{field.lower().replace(' ', '_')}_bursaries_report.pdf"
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Add title
            title = Paragraph(f"Bursary Report - {field}", styles['Heading1'])
            elements.append(title)

            # Prepare table data
            data = [['Bursary Name', 'Closing Date', 'Status', 'Details']]
            for bursary in bursaries:
                closing_date = (bursary['closing_date'].strftime('%d %B %Y') 
                              if bursary['closing_date'] else 'Not specified')
                data.append([
                    bursary['name'],
                    closing_date,
                    bursary['status'],
                    bursary['details']
                ])

            # Create and style table
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))

            elements.append(table)
            doc.build(elements)
            
            self.console.print(f"[green]Report generated successfully: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {e}")
            self.console.print("[red]Error generating PDF report. Check the log file for details.")

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
        """Enhanced date parsing to handle more formats."""
        try:
            # Remove any ordinal indicators and extra whitespace
            date_str = re.sub(r'(?:st|nd|rd|th)', '', date_str).strip()
            
            # Try parsing common formats
            formats = [
                '%d %B %Y',
                '%d-%B-%Y',
                '%d %b %Y',
                '%Y/%m/%d',
                '%d/%m/%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
                    
            # If standard formats fail, try regex patterns
            patterns = [
                r'(\d{1,2})\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s*(202[45])',
                r'(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(202[45])'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_str, re.IGNORECASE)
                if match:
                    day, month, year = match.groups()
                    month = month[:3].title()
                    return datetime.strptime(f"{day} {month} {year}", "%d %b %Y")
                    
            return None
        except Exception as e:
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
        
    def check_bursary_status(self, url, name, task):
        """Modified to use the task directly instead of progress object."""
        try:
            content = self.get_page_content(url)
            if not content:
                self.progress.update(task, advance=1)
                return None

            soup = BeautifulSoup(content, 'html.parser')
            text_content = soup.get_text().lower()

            # Look for closing date section more precisely
            closing_date = None
            closing_date_patterns = [
                r'closing date[:\s]*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+202[45])',
                r'deadline[:\s]*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+202[45])',
                r'applications? close[:\s]*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+202[45])',
                r'due date[:\s]*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s+202[45])'
            ]

            # First try to find an explicit closing date section
            closing_date_section = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4', 'strong'] and 
                                          re.search(r'closing date|deadline', tag.get_text().lower()))
            
            if closing_date_section:
                next_element = closing_date_section.find_next()
                if next_element:
                    date_text = next_element.get_text().strip()
                    closing_date = self.parse_date(date_text)

            # If no closing date found in sections, try regex patterns
            if not closing_date:
                for pattern in closing_date_patterns:
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        date_str = match.group(1)
                        closing_date = self.parse_date(date_str)
                        if closing_date:
                            break

            # Determine status
            status = "Open"
            if closing_date:
                if closing_date < datetime.now():
                    status = "Closed"
            elif not any(str(year) in text_content for year in [2024, 2025]):
                status = "Closed"

            # Extract requirements
            requirements = "No specific requirements listed"
            requirements_section = soup.find(lambda tag: tag.name in ['div', 'section'] and 
                                          re.search(r'requirements|eligibility|criteria', 
                                                  tag.get_text().lower()))
            if requirements_section:
                requirements = ' '.join(requirements_section.get_text().split()[:50]) + "..."

            result = {
                'name': name,
                'url': url,
                'status': status,
                'closing_date': closing_date,
                'details': f"Requirements: {requirements}",
                'last_updated': datetime.now()
            }

            self.bursary_data.append(result)
            self.progress.update(task, advance=1)
            return result

        except Exception as e:
            self.logger.error(f"Error processing {name} at {url}: {e}")
            self.progress.update(task, advance=1)
            return None

def generate_report(self, field):
    """Enhanced report generation with Rich formatting and better error handling."""
    try:
        category_url = self.get_category_url(field)
        self.console.print(Panel(f"[bold]Checking bursaries for: [cyan]{field}"))
        self.console.print(f"Category URL: [link={category_url}]{category_url}[/link]")
        
        bursary_links = self.extract_bursary_links(category_url)
        
        if not bursary_links:
            self.console.print("[red]No bursary links found. Please check if the category exists.")
            return
            
        self.console.print(f"Found [green]{len(bursary_links)}[/green] potential bursary links")
        
        # Clear previous data
        self.bursary_data = []
        
        # Create a single Progress instance
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            self.progress = progress
            task = progress.add_task("[cyan]Processing bursaries...", total=len(bursary_links))
            
            # Process bursaries with improved error handling
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for name, url in bursary_links:
                    future = executor.submit(self.check_bursary_status, url, name, task)
                    futures.append(future)
                
                # Handle results as they complete
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            self.bursary_data.append(result)
                    except Exception as e:
                        self.logger.error(f"Error processing bursary: {str(e)}")
        
        # Filter valid and open bursaries
        open_bursaries = [b for b in self.bursary_data if b and b['status'] == 'Open']
        
        if not open_bursaries:
            self.console.print("[yellow]No open bursaries found for this category.")
            return

        # Generate PDF report
        self._generate_pdf_report(field, open_bursaries)
        
        # Save to cache
        self.save_cached_data()
        
        # Display console summary
        self._display_console_summary(open_bursaries)

    except Exception as e:
        self.logger.error(f"Error in generate_report: {str(e)}")
        self.console.print(f"[red]An error occurred: {str(e)}")
        self.console.print("[red]Please check the log file for details.")
    

def main():
    try:
        base_url = "https://www.zabursaries.co.za"
        generator = BursaryReportGenerator(base_url)
        console = Console()  # Initialize console for main function

        console.print("[bold cyan]Select a field of study:")
        fields = ["Accounting", "Arts", "Commerce", "Computer Science & IT", 
                 "Construction & Built Environment", "Education", "Engineering", 
                 "General", "Government", "International", "Law", "Medical", 
                 "Postgraduate", "Science"]
        
        for i, field in enumerate(fields, start=1):
            console.print(f"{i}. {field}")

        while True:
            try:
                choice = input("\nEnter the number of your field of study (1-14): ")
                choice = int(choice)
                if 1 <= choice <= len(fields):
                    break
                console.print("[red]Please enter a number between 1 and {len(fields)}")
            except ValueError:
                console.print("[red]Please enter a valid number")

        field_of_study = fields[choice - 1]
        generator.generate_report(field_of_study)

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        console.print("[red]An error occurred. Please check the log file for details.")

if __name__ == "__main__":
    main()