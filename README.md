# Bursary Checker

This tool helps you find open bursaries in South Africa based on your field of study.

## Installation

This project requires Python 3.7 or higher.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ElliotBadinger/Bursary-checker.git
   cd Bursary-checker
   ```

2. **Run the installer:**

   ```bash
   python installer.py
   ```

   The installer will:

   - Check your Python version.
   - Install `rich` (for colorful output) and `pip` (if needed).
   - Create a virtual environment.
   - Install the necessary Python packages.
   - Offer to run the Bursary Checker after installation.

## Usage

After installation (or if you chose to run it later), activate the virtual environment and run the Bursary Checker:

```bash
# Activate the virtual environment (the installer will print the correct command):
# Windows:
bursary_env\Scripts\activate

# macOS/Linux:
source bursary_env/bin/activate

# Run the script:
python bursary_checker.py
```

Choose your field of study, and the script will generate a PDF report named `bursary_report_[field_of_study].pdf` with a list of open bursaries.

## Contributing

Contributions are welcome! Fork the repository and submit a pull request.

