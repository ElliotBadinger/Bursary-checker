# Bursary Checker

This tool helps you find open bursaries in South Africa based on your field of study.

## Installation

This project requires Python 3.7 or higher.

1. **Install Git (if not already installed):**

   - **Windows:** Download and install Git for Windows from [https://git-scm.com/download/win](https://git-scm.com/download/win).
   - **macOS:**  Install Git using Homebrew: `brew install git`
   - **Linux:** Use your distribution's package manager (e.g., `apt-get install git` on Debian/Ubuntu, `dnf install git` on Fedora).

2. **Clone the repository:**

   Open your terminal or command prompt and run:

   ```bash
   git clone https://github.com/ElliotBadinger/Bursary-checker.git
   cd Bursary-checker
   ```



3. **Run the installer:**

   ```bash
   python installer.py
   ```

   The installer will:

   - Check your Python version.
   - Install `rich` (for colorful output) and `pip` (if needed).
   - Create a virtual environment named `bursary_env`.
   - Install the necessary Python packages within the virtual environment.
   - Offer to run the Bursary Checker after installation.


## Usage

1. **Activate the virtual environment:**

   ```bash
   # Windows:
   bursary_env\Scripts\activate

   # macOS/Linux:
   source bursary_env/bin/activate
   ```

2. **Run the script:**

   ```bash
   python bursary_checker.py
   ```

   Choose your field of study from the provided list.  The script will fetch bursary information, generate a PDF report named `[field_of_study]_bursaries_report.pdf` (e.g., `accounting_bursaries_report.pdf`) in the project directory, and display a summary table in the console.

## Troubleshooting

* **`ModuleNotFoundError`:** If you encounter errors like `ModuleNotFoundError: No module named 'requests'`, ensure you have activated the virtual environment before running `bursary_checker.py`.
* **PDF Generation Issues:** If the PDF report is not generated, check the `bursary_checker.log` file for any error messages. Ensure you have write permissions in the project directory.
* **Network Problems:**  If the script fails to fetch data from the website, check your internet connection.  The script has retry logic, but persistent network issues might prevent it from working correctly.

## Contributing

Contributions are welcome! Fork the repository, make your changes, and submit a pull request.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.  (Add a LICENSE file if you haven't already - MIT is a good choice for open-source projects).
```


