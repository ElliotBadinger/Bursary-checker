## How to Check for Bursaries (No Programming Experience Needed!)

This guide will show you how to use a program that automatically checks for available bursaries and tells you if they are open or closed, even if you have no programming experience.

**1. What you'll need:**

* **A computer:**  Windows, Mac, or Linux will work.
* **Internet connection:**  You'll need to be online to use this program.
* **Python:** This is a free programming language. Don't worry, you won't have to write any code!

**2. Installing Python:**

* **Windows:**
    1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/) and download the latest version for Windows.
    2. Run the downloaded installer.  Make sure to check the box that says "Add Python to PATH" during the installation. This is very important!
* **Mac:** Python is often already installed on Macs. Open the "Terminal" application (search for it using Spotlight) and type `python3 --version`. If you see a version number (like `Python 3.9.x`), you're good to go.  If not, download the Mac installer from [https://www.python.org/downloads/mac-osx/](https://www.python.org/downloads/mac-osx/).
* **Linux:** Python is usually pre-installed on Linux. Open your terminal and type `python3 --version`.  If it's not installed, use your distribution's package manager (like `apt-get` on Debian/Ubuntu or `yum` on Fedora/CentOS) to install it (e.g., `sudo apt-get install python3`).

**3. Downloading the Bursary Checker:**

1. Download the files `requirements.txt` and `bursary_checker.py` (ask the person who provided this guide how to get these files).
2. Put both files in the **same folder** on your computer. Remember where you put this folder.

**4. Installing the required libraries:**

1. Open your terminal or command prompt.
2. Navigate to the folder where you saved the files.  You can do this using the `cd` command. For example, if the files are in `Downloads/bursary_checker`, you would type:
   ```bash
   cd Downloads/bursary_checker
   ```
3. Once you're in the correct folder, run the following command:
   ```bash
   pip install -r requirements.txt 
   ```

**5. Running the Bursary Checker:**

Still in the same terminal window, run this command:

```bash
python bursary_checker.py
```


**6. Viewing the results:**

The program will print information to the terminal as it runs. Once it's finished, you'll find new files in the same folder:

* **`bursary_status_distribution.png`:** A pie chart showing how many bursaries are open, closed, or unknown. Open this file with any image viewer.
* **`bursary_timeline.png`:** A timeline showing when open bursaries close. Open this with an image viewer.
* **`bursary_report.html`:** This file contains a complete report with all the details and the visualizations. Open this file with your web browser (like Chrome, Firefox, or Safari). This is the most important file!


**7. If something goes wrong:**

* **`pip` is not recognized:** Make sure you added Python to your PATH during installation (step 2).  You might need to restart your computer.
* **Other errors:** Contact the person who provided this guide for assistance.



