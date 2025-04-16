# Job Tracker V1

A comprehensive application for tracking job applications and managing your job search process.

## Features

- Track job applications status
- Store company details
- Monitor application progress
- Automated web scraping for company information
- User-friendly interface

## Installation Options

### Django App Installation

1. Clone the Repository
   ```
   https://github.com/sharan122/job-tracker-v1.git
   cd Backend
   ```

2. Set Up Virtual Environment
   ```
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate  # On Windows
   ```

3. Install Dependencies
   ```
   pip install -r requirements.txt
   ```

4. Run the Server
   ```
   cd AI_Email_Portal
   python manage.py migrate
   python manage.py runserver
   ```

### Flask App Installation

1. Set Up Virtual Environment
   ```
   cd job_listing_tracker
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate  # On Windows
   ```

3. Install Dependencies
   ```
   pip install -r requirements.txt
   ```

4. Run the Application
   ```
   cd job_listing_tracker\main
   python main.py
   ```

## Important Note

Currently, Cloudflare bot verification is not handled automatically. You may need to manually pass the test and wait for approximately 15 minutes to scrape all company details.

## Requirements

- Python 3.8 or higher
- Django/Flask (depending on which version you use)
- Internet connection for web scraping features

