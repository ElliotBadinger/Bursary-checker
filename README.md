## How to Run the Bursary Checker

This program scrapes a website for bursary information, determines the status of each bursary (open or closed), and generates visualizations of the data.

**1. Installation:**

Make sure you have Python 3 installed. Then, install the required libraries using pip:

```bash
pip install -r requirements.txt
```

**2. Running the script:**

Save the code as a Python file (e.g., `bursary_checker.py`) and run it from your terminal:

```bash
python bursary_checker.py
```

**3. Output:**

The program will print the status, closing date (if available), and details for each bursary it finds.  It will then generate the following visualizations in the same directory as the script:

* **`bursary_status_distribution.png`**: A pie chart showing the distribution of bursary application statuses (Open, Closed, Unknown).
* **`bursary_timeline.png`**: A timeline of open bursaries, sorted by their closing dates.
* **`bursary_report.html`**: An HTML report containing a table with details of all bursaries, including links to apply, and the generated visualizations.


**4. Customization:**

* **`base_url`**:  You can change the `base_url` variable in the `main()` function to scrape a different page on the website or even a different website altogether.  However, you may need to adjust the `extract_bursary_links` and `check_bursary_status` methods to correctly parse the new HTML structure.
* **Date Parsing**: The date parsing logic attempts to handle various date formats.  If the website changes its date format, you might need to update the regular expressions (`date_patterns`) in `check_bursary_status`.
* **Keywords**: The `extract_bursary_links` method uses keywords like "bursary," "scholarship," and "fellowship" to identify relevant links. You can modify these keywords to target specific types of opportunities.
* **Headers**: The `headers` attribute in the `BursaryChecker` class mimics a web browser.  It's a good practice to keep these updated.  You might want to rotate user agents occasionally to avoid being blocked.
* **Error Handling**: The `get_page_content` method includes a retry mechanism.  You can adjust the number of retries and the delay between attempts.


**5. Notes:**

* Web scraping is fragile. Websites can change their structure, which might break the script.  Regular maintenance and updates might be required.
* Be respectful of the website's terms of service and robots.txt. Avoid overloading the server with requests by implementing appropriate delays.
