# Bursary Checker

This simple Python application helps you find open bursaries in South Africa based on your field of study. It scrapes a website for bursary information and generates a PDF report with open bursaries, their closing dates, and application links.

## Setup Instructions

This guide assumes you have a basic understanding of using the command line/terminal. If you are completely new to this, you may want to search for tutorials on using the command line for your operating system (Windows, macOS, or Linux).

1. **Install Python:** If you don't have Python installed, download it from [https://www.python.org/downloads/](https://www.python.org/downloads/). Make sure to add Python to your system's PATH during installation.

2. **Clone the repository:** Open your terminal or command prompt and navigate to the directory where you want to save the project.  Then run:
   ```bash
   git clone https://github.com/ElliotBadinger/Bursary-checker.git
   ```

3. **Navigate to the project directory:**
   ```bash
   cd Bursary-checker
   ```

4. **Create a virtual environment (recommended):**  This isolates the project's dependencies.
   ```bash
   python3 -m venv .venv  # For Windows/macOS/Linux
   ```
   or try ```bash
      python -m venv .venv
      ```
   if the first one fails
   
5. **Activate the virtual environment:**
   - **Windows:** `.venv\Scripts\activate`
   - **macOS/Linux:** `source .venv/bin/activate`


6. **Install required libraries:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the script:** After activating the virtual environment, run the following command in your terminal:

   ```bash
   python main.py
   ```

2. **Select your field of study:** The script will present a list of fields of study. Enter the corresponding number to select your field.

3. **Report generation:** The script will scrape the website, check the status of bursaries, and generate a PDF report named `bursary_report_<your_field_of_study>.pdf` in the project directory.  The progress will be displayed on the terminal.

## How it Works

The script uses several Python libraries:

- **`requests`:** To fetch the HTML content of web pages.
- **`BeautifulSoup`:** To parse the HTML and extract relevant information.
- **`re` (regular expressions):** To find patterns in text, such as dates.
- **`datetime`:** To work with dates and times.
- **`os`:** For file system operations.
- **`pickle`:** To save and load data to avoid repeated web scraping.
- **`concurrent.futures`:** To speed up processing by checking multiple bursaries concurrently.
- **`reportlab`:** To generate the PDF report.
- **`tqdm`:** To display a progress bar.
- **`logging`:** To record errors and other information.


The script first retrieves a list of bursary links from the target website. Then, it checks each link to determine the bursary's status (open or closed) and extracts details like the closing date. Finally, it generates a PDF report containing information about the open bursaries.  The results are cached for 24 hours to avoid repeated scraping of the same data.


## Troubleshooting

- **Errors during installation:** Ensure you have a stable internet connection and that your Python installation is configured correctly.  Try updating `pip`: `pip install --upgrade pip`

- **Script errors:** Check the `bursary_checker.log` file for detailed error messages.

- **Website changes:** The script relies on the structure of the target website.  If the website changes, the script may need to be updated.  Create an issue on GitHub if this happens.


## Contributing

Contributions are welcome! Feel free to create pull requests with bug fixes, improvements, or new features.
