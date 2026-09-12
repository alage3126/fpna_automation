FP&A Automation Framework
Automated testing framework built with Python, Pytest, and Allure, featuring unified HTML email reporting with detailed API request/response trace data across local and CI/CD environments.

Tech Stack
Language: Python

Testing Framework: Pytest

Reporting: Allure Reports

Notifications: Custom SMTP HTML reporter (smtplib)

CI/CD: GitHub Actions

Project Structure
Plaintext
fpna_automation/
├── .github/
│   └── workflows/
│       └── test.yml
├── utils/
│   └── notifier.py
├── tests/
│   ├── conftest.py
│   └── test_db_api.py
├── requirements.txt
└── allure-results/
Setup & Installation
Clone the repository:

Bash
git clone <repository-url>
cd fpna_automation
Install dependencies:

Bash
pip install -r requirements.txt
Running Tests Locally
To run the test suite locally and trigger the automated HTML email report, define your email environment variables and execute pytest:

PowerShell:

PowerShell
$env:MAIL_USERNAME="your-email@gmail.com"
$env:MAIL_PASSWORD="your-app-password"
pytest --alluredir=allure-results
Bash (Linux/macOS):

Bash
export MAIL_USERNAME="your-email@gmail.com"
export MAIL_PASSWORD="your-app-password"
pytest --alluredir=allure-results
CI/CD Pipeline
The framework executes automatically via GitHub Actions on every push or pull request to main/master.

Required Repository Secrets
Configure the following secrets under Settings > Secrets and variables > Actions in your GitHub repository:

MAIL_USERNAME: Your sender email address.

MAIL_PASSWORD: Your Gmail App Password.