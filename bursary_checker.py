import requests
from bs4 import BeautifulSoup
from datetime import datetime

# URL of the bursaries page
url = 'https://www.zabursaries.co.za/computer-science-it-bursaries-south-africa/'

# Fetch the page content
response = requests.get(url)
if response.status_code != 200:
    print(f"Failed to fetch the page. Status code: {response.status_code}")
    exit()

# Parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')

# Find all bursary listings
bursary_listings = soup.find_all('div', class_='bursary-listing')

# Current date
current_date = datetime.now().date()

# List to store open bursaries
open_bursaries = []

# Iterate through each bursary listing
for listing in bursary_listings:
    # Extract the closing date
    closing_date_str = listing.find('span', class_='closing-date').text.strip()
    
    # Convert the closing date to a datetime object
    try:
        closing_date = datetime.strptime(closing_date_str, '%d %B %Y').date()
    except ValueError:
        print(f"Could not parse date: {closing_date_str}")
        continue
    
    # Check if the closing date is in the future
    if closing_date > current_date:
        # Extract the bursary title and link
        title = listing.find('h2', class_='bursary-title').text.strip()
        link = listing.find('a')['href']
        
        # Add the open bursary to the list
        open_bursaries.append((title, link, closing_date_str))

# Write the open bursaries to a file
with open('open_bursaries.txt', 'w') as file:
    for title, link, closing_date in open_bursaries:
        file.write(f"Title: {title}\n")
        file.write(f"Link: {link}\n")
        file.write(f"Closing Date: {closing_date}\n")
        file.write("\n")

print(f"Found {len(open_bursaries)} open bursaries. Details written to open_bursaries.txt")
