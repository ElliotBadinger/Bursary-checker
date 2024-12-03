import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from urllib.parse import urljoin
import time
import random
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict
import seaborn as sns
from datetime import datetime, timedelta

class BursaryChecker:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1'
        }
        self.results = []  # Store results for visualization

    def get_page_content(self, url, retries=3):
        """
        Get page content with retry mechanism and random delays
        """
        for attempt in range(retries):
            try:
                time.sleep(random.uniform(1, 3))
                response = self.session.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == retries - 1:
                    print(f"Failed to fetch {url} after {retries} attempts: {str(e)}")
                    return None
                time.sleep(random.uniform(2, 5))
        return None

    def check_bursary_status(self, url, name):
        """
        Check the status of a bursary application and store results
        """
        content = self.get_page_content(url)
        if not content:
            return "Error", None, "Failed to fetch page content"

        soup = BeautifulSoup(content, 'html.parser')
        
        closing_date = None
        status = "Unknown"
        details = ""
        
        date_patterns = [
            r'CLOSING DATE[:\s]*([^\.]*)',
            r'Applications close[:\s]*([^\.]*)',
            r'Closing date[:\s]*([^\.]*)',
            r'(\d{1,2}\s+[A-Za-z]+\s+202\d)',
            r'(\d{1,2}\s+[A-Za-z]+)',
        ]
        
        text_content = soup.get_text()
        
        for pattern in date_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                closing_date = match.group(1).strip()
                break

        closed_indicators = [
            'application has closed',
            'applications are closed',
            'bursary has closed',
            'applications closed',
            'closing date has passed'
        ]
        
        open_indicators = [
            'applications are open',
            'applications now open',
            'apply now',
            'how to apply'
        ]
        
        text_lower = text_content.lower()
        
        if any(indicator in text_lower for indicator in closed_indicators):
            status = "Closed"
            details = "Application period has ended"
        elif any(indicator in text_lower for indicator in open_indicators):
            status = "Open"
            if closing_date:
                details = f"Applications are open until {closing_date}"
            else:
                details = "Applications are currently open"
        elif closing_date:
            try:
                if '2024' not in closing_date and '2025' not in closing_date:
                    closing_date += ' 2024'
                date_obj = datetime.strptime(closing_date, '%d %B %Y')
                if date_obj < datetime.now():
                    status = "Closed"
                    details = "Closing date has passed"
                else:
                    status = "Open"
                    details = f"Applications are open until {closing_date}"
            except ValueError:
                status = "Unknown"
                details = f"Found closing date: {closing_date} (format unclear)"
        
        # Store result for visualization
        self.results.append({
            'name': name,
            'status': status,
            'closing_date': closing_date,
            'details': details,
            'url': url
        })
        
        return status, closing_date, details

    def extract_bursary_links(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.text.strip()
            
            if any(keyword in href.lower() or keyword in text.lower() 
                  for keyword in ['bursary', 'scholarship', 'fellowship']):
                if href.startswith('/'):
                    href = 'https://www.zabursaries.co.za' + href
                elif not href.startswith(('http://', 'https://')):
                    href = 'https://www.zabursaries.co.za/' + href
                
                if text and href.startswith('https://www.zabursaries.co.za'):
                    links.append((text, href))
        
        return links

    def create_visualizations(self):
        """
        Create visualizations of the bursary data
        """
        if not self.results:
            print("No data available for visualization")
            return

        df = pd.DataFrame(self.results)
        
        # Set up the plotting style
        plt.style.use('seaborn')
        
        # 1. Status Distribution Pie Chart
        plt.figure(figsize=(10, 6))
        status_counts = df['status'].value_counts()
        plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%',
                colors=sns.color_palette("husl", len(status_counts)))
        plt.title('Distribution of Bursary Application Statuses')
        plt.savefig('bursary_status_distribution.png')
        plt.close()

        # 2. Timeline of Open Bursaries
        open_bursaries = df[df['status'] == 'Open'].copy()
        if not open_bursaries.empty and 'closing_date' in open_bursaries.columns:
            try:
                plt.figure(figsize=(12, 6))
                
                # Convert closing dates to datetime
                open_bursaries['closing_date_dt'] = pd.to_datetime(
                    open_bursaries['closing_date'].apply(
                        lambda x: x + ' 2024' if x and '202' not in str(x) else x
                    ),
                    format='%d %B %Y',
                    errors='coerce'
                )
                
                # Sort by closing date
                open_bursaries = open_bursaries.sort_values('closing_date_dt')
                
                # Create timeline
                plt.figure(figsize=(12, 6))
                plt.scatter(open_bursaries['closing_date_dt'], 
                          range(len(open_bursaries)),
                          s=100)
                
                # Add bursary names
                for idx, row in enumerate(open_bursaries.itertuples()):
                    plt.text(row.closing_date_dt, idx, 
                            f"  {row.name}",
                            verticalalignment='center')
                
                plt.yticks([])
                plt.xticks(rotation=45)
                plt.title('Timeline of Open Bursary Deadlines')
                plt.xlabel('Closing Date')
                plt.tight_layout()
                plt.savefig('bursary_timeline.png')
                plt.close()

            except Exception as e:
                print(f"Error creating timeline visualization: {str(e)}")

        # 3. Create an HTML report
        html_content = """
        <html>
        <head>
            <title>Bursary Application Status Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .open { color: green; }
                .closed { color: red; }
                .unknown { color: gray; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
            </style>
        </head>
        <body>
            <h1>Bursary Application Status Report</h1>
            <h2>Generated on: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</h2>
            
            <h2>Open Bursaries:</h2>
            <table>
                <tr>
                    <th>Bursary Name</th>
                    <th>Closing Date</th>
                    <th>Details</th>
                    <th>Link</th>
                </tr>
        """
        
        # Add open bursaries to the report
        for result in self.results:
            if result['status'] == 'Open':
                html_content += f"""
                <tr>
                    <td>{result['name']}</td>
                    <td>{result['closing_date'] or 'Not specified'}</td>
                    <td>{result['details']}</td>
                    <td><a href="{result['url']}" target="_blank">Apply</a></td>
                </tr>
                """
        
        html_content += """
            </table>
            <h2>Visualizations:</h2>
            <img src="bursary_status_distribution.png" alt="Status Distribution">
            <img src="bursary_timeline.png" alt="Timeline of Open Bursaries">
        </body>
        </html>
        """
        
        with open('bursary_report.html', 'w') as f:
            f.write(html_content)

def main():
    checker = BursaryChecker()
    base_url = "https://www.zabursaries.co.za/computer-science-it-bursaries-south-africa/"
    
    print("Fetching main page...")
    content = checker.get_page_content(base_url)
    
    if content:
        bursary_links = checker.extract_bursary_links(content)
        print(f"\nFound {len(bursary_links)} bursary links")
        
        if bursary_links:
            print("\nChecking application statuses...\n")
            for name, url in bursary_links:
                print(f"\nChecking: {name}")
                status, closing_date, details = checker.check_bursary_status(url, name)
                print(f"Status: {status}")
                if closing_date:
                    print(f"Closing Date: {closing_date}")
                print(f"Details: {details}")
                print("-" * 80)
            
            print("\nCreating visualizations...")
            checker.create_visualizations()
            print("\nVisualizations have been created:")
            print("1. bursary_status_distribution.png - Pie chart of status distribution")
            print("2. bursary_timeline.png - Timeline of open bursaries")
            print("3. bursary_report.html - Complete report with details and visualizations")
        else:
            print("No bursary links found. The page structure might have changed.")
    else:
        print("Failed to fetch the main page. Please check your internet connection or try again later.")

if __name__ == "__main__":
    main()