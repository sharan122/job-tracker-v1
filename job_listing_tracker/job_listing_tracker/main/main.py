import os
import time
import asyncio
import argparse
import re
import requests
import psycopg2
import smtplib
from urllib.parse import urljoin, urlparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from serpapi import GoogleSearch
from flask import Flask
from dotenv import load_dotenv
import openai
from crawl4ai import AsyncWebCrawler

# ========== INITIAL SETUP ==========

app = Flask(__name__)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ========== CONFIGS ==========

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "job_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "your_db_password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

SMTP_CONFIG = {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": os.getenv("SMTP_USER", "your_email@gmail.com"),
    "password": os.getenv("SMTP_PASS", "your_email_app_password"),
    "receiver": os.getenv("RECEIVER_EMAIL", "recipient_email@gmail.com")
}

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# ========== DATABASE HELPERS ==========

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def save_company_details_to_db(company_data_list):
    new_inserts = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for data in company_data_list:
                name = (data.get("company_name") or "").strip() or "Unknown Company"
                website = (data.get("website") or "").strip() or "N/A"
                industry = ", ".join(data.get("industry") or []) or "Unknown"
                funding = (data.get("funding_round") or "").strip() or "Not Disclosed"
               
                cur.execute("SELECT id FROM api_fundedcompany WHERE name = %s", (name,))
                if cur.fetchone():
                    continue
                cur.execute("""
                    INSERT INTO api_fundedcompany (name, website, industry, funding_round, created_at)
                    VALUES (%s, %s, %s, %s, NOW()) RETURNING id
                """, (name, website, industry, funding))
                new_inserts.append(data)
        conn.commit()
    return new_inserts

def fetch_funded_companies():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, website, careers_url FROM api_fundedcompany")
            return cur.fetchall()

def save_job_listings_to_db(company_id, job_listings):
    """
    Insert job listings into the job table while avoiding duplicates based on normalized job_link.
    Now includes saving job_description.
    """
    new_inserts = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Fetch existing normalized job links for this company
            cur.execute("SELECT job_link FROM api_joblisting WHERE company_id = %s", (company_id,))
            existing_links = {normalize_link(row[0]) for row in cur.fetchall()}

            for job in job_listings:
                norm_link = normalize_link(job["link"])
                # Skip if link already exists or appears invalid
                if norm_link in existing_links or norm_link == "http://":
                    continue
                cur.execute("""
                    INSERT INTO api_joblisting (company_id, title, job_link, location, job_type, job_description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    company_id,
                    job["title"],
                    job["link"],
                    job.get("location", ""),
                    job.get("job_type", ""),
                    job.get("description", "")
                ))
                existing_links.add(norm_link)
                new_inserts.append(job)
        conn.commit()
    return new_inserts

def save_career_url(company_id, career_url):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE api_fundedcompany SET careers_url = %s WHERE id = %s", (career_url, company_id))
            conn.commit()
        print(f"[DB] Saved career URL for company ID {company_id}")
    except Exception as e:
        print(f"[DB ERROR] Could not save career URL for {company_id}: {e}")

def normalize_link(link):
    try:
        parsed = urlparse(link)
        norm = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".lower().rstrip("/")
        return norm
    except Exception:
        return link

# ========== SCRAPING FUNCTIONS ==========

def find_comapany_details():
    """
    Scrapes Crunchbase for company names from the funding rounds page.
    Uses SerpAPI and Selenium to extract details.
    Returns a list of dictionaries.
    """
    url = "https://www.crunchbase.com/discover/funding_rounds/e1ffaf87fcd0f9fa6d6ab9347cb8f379"
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    driver.get(url)
    time.sleep(30)  

    cells = driver.find_elements(By.CSS_SELECTOR, "grid-cell.column-id-funded_organization_identifier")
    company_names = []
    for cell in cells:
        try:
            name_elem = cell.find_element(By.CSS_SELECTOR, "div.identifier-label")
            if name_elem:
                company_names.append(name_elem.text.strip())
        except Exception:
            continue
    driver.quit()

    results = []
    for name in company_names:
        link = search_company_with_serpapi(name)
        if link:
            data = parse_company_details_selenium(link)
            data["company_name"] = name
            results.append(data)
        else:
            print(f"[WARN] No SerpAPI result for {name}")
    return results

def search_company_with_serpapi(company_name):
    query = f"{company_name} funding details crunchbase"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "gl": "us",
        "num": 1
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])
        if organic_results:
            return organic_results[0].get("link")
    except Exception as e:
        print(f"Error using SerpAPI for {company_name}: {e}")
    return None

def parse_company_details_selenium(page_url):
    details = {"company_name": None, "website": None, "industry": [], "funding_round": None}
    if not page_url:
        return details

    options = uc.ChromeOptions()
    # options.add_argument("--headless")
    driver = uc.Chrome(options=options)
    try:
        driver.get(page_url)
        print("[INFO] Navigating to:", page_url)
        time.sleep(20)
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.profile-layout"))
            )
            print("[INFO] Page loaded!")
        except Exception:
            print("[WARN] Timed out waiting for page elements.")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        website_elem = soup.find("a", class_="component--field-formatter accent ng-star-inserted")
        if website_elem and website_elem.get("href"):
            details["website"] = website_elem["href"]
        funding_elem = soup.find("a", class_="component--field-formatter field-type-enum accent highlight-color-contrast-light ng-star-inserted")
        if funding_elem:
            details["funding_round"] = funding_elem.get_text(strip=True)
        industry_elems = soup.find_all("chip", class_="success")
        for industry in industry_elems:
            industry_text = industry.find("div", class_="chip-text")
            if industry_text:
                details["industry"].append(industry_text.get_text(strip=True))
    except Exception as e:
        print(f"[ERROR] Parsing {page_url} with Selenium: {e}")
    finally:
        driver.quit()
    return details

# ========== CAREER PAGE / JOB LISTING FUNCTIONS ==========

def find_career_page_direct(base_url):
    if not base_url.startswith("http"):
        base_url = "https://" + base_url
    for path in ["/careers", "/jobs", "/join-us", "/hiring", "/work-with-us"]:
        url = urljoin(base_url, path)
        try:
            if requests.get(url, timeout=5).status_code == 200:
                return url
        except Exception:
            continue
    try:
        resp = requests.get(base_url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if any(keyword in href for keyword in ["career", "job", "hiring"]):
                return urljoin(base_url, a["href"])
    except Exception:
        pass
    return None

def scrape_job_listings(career_page):
    job_listings = []
    try:
        resp = requests.get(career_page, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = soup.find_all("div", class_="job-listing")
        for job in jobs:
            title_elem = job.find("h2")
            title = title_elem.get_text(strip=True) if title_elem else "No Title"
            link_elem = job.find("a", href=True)
            link = urljoin(career_page, link_elem["href"]) if link_elem else "No Link"
            job_listings.append({
                "title": title,
                "link": link,
                "location": "Unknown",
                "job_type": "Unknown",
                "description": ""
            })
    except Exception as e:
        print(f"[Job Scrape Error] {career_page}: {e}")
    return job_listings

def extract_career_link_with_gpt(markdown, original_url):
    prompt = f"""
You are an assistant. From the following markdown content from {original_url}, extract the best careers page URL.
Reply with the URL only, or "None" if not found.

Markdown:
{markdown}
"""
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[GPT Error - Careers] {e}")
        return "None"

def extract_jobs_with_gpt(markdown, career_url):
    prompt = f"""
        Extract job listings related to Software Engineering or AI/ML from this markdown page ({career_url}).
        For each job, list:
        1. Job Title
        2. Job URL
        3. Location (City/Country or Remote)
        4. Date Posted
        5. Job Type (Remote, Hybrid, Onsite)
        6. A short description (one-two sentences)

        Format the results as markdown like this:
        ### [Job Title]
        - **URL**: [Job URL]
        - **Location**: [Location]
        - **Date Posted**: [Date]
        - **Job Type**: [Remote/Hybrid/Onsite]
        - **Description**: [Summary]

        If no jobs are found, return "None".

        Markdown:
        {markdown}
        """
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[GPT Error - Jobs] {e}")
        return "None"

def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"]
    except Exception:
        return False

# ========== JOB PARSING HELPER ==========

def parse_gpt_jobs_output(gpt_output: str) -> list:
    """
    Parse GPT's markdown output into a list of job dictionaries.
    Expected GPT format:
      ### [Job Title](Job URL)    -- The title line may include a Markdown link.
      - **URL**: [Job Title](Job URL)  (optional if already extracted in title)
      - **Location**: [Location]
      - **Date Posted**: [Date]
      - **Job Type**: [Remote/Hybrid/Onsite]
      - **Description**: [Summary]
    Returns a list of dictionaries.
    """
    if not gpt_output or gpt_output.strip().lower() == "none":
        return []

    jobs = []
    current_job = {}
    # Regex pattern to extract markdown links: [text](url)
    md_link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    lines = gpt_output.strip().splitlines()
    for line in lines:
        if line.startswith("### "):
            if current_job:
                jobs.append(current_job)
            # Remove "### " and attempt to extract markdown link
            title_line = line[4:].strip()
            match = md_link_pattern.search(title_line)
            if match:
                current_job = {"title": match.group(1), "link": match.group(2)}
            else:
                current_job = {"title": title_line}
        elif "**URL**:" in line:
            match = md_link_pattern.search(line)
            if match:
                current_job["link"] = match.group(2)
            else:
                current_job["link"] = line.split("**URL**:")[-1].strip()
        elif "**Location**:" in line:
            current_job["location"] = line.split("**Location**:")[-1].strip()
        elif "**Date Posted**:" in line:
            current_job["date_posted"] = line.split("**Date Posted**:")[-1].strip()
        elif "**Job Type**:" in line:
            current_job["job_type"] = line.split("**Job Type**:")[-1].strip()
        elif "**Description**:" in line:
            current_job["description"] = line.split("**Description**:")[-1].strip()
    if current_job:
        jobs.append(current_job)
    return jobs

# ========== COMBINED CAREER AND JOB EXTRACTION ==========

async def process_career_and_jobs(company_id, homepage, max_retries=3):
    if not is_valid_url(homepage):
        print(f"[Skip] Invalid homepage URL for company ID {company_id}")
        return

    attempt = 0
    while attempt < max_retries:
        try:
            print(f"[Pipeline] Processing company ID {company_id} from {homepage} (Attempt {attempt+1})")
            async with AsyncWebCrawler() as crawler:
                # Retrieve homepage content
                result = await crawler.arun(url=homepage)
                homepage_markdown = result.markdown

                # Use GPT to extract the career page URL
                career_url = extract_career_link_with_gpt(homepage_markdown, homepage)
                if not career_url or career_url == "None" or not is_valid_url(career_url):
                    # Fallback: try known career paths
                    career_url = find_career_page_direct(homepage)
                    if career_url:
                        print(f"[Fallback] Company ID {company_id}: Using direct career URL: {career_url}")
                    else:
                        print(f"[Career] Company ID {company_id}: No valid career URL extracted.")
                        return
                else:
                    print(f"[Career] Company ID {company_id}: Found career URL: {career_url}")
                    save_career_url(company_id, career_url)

                # Extract job listings from the career page
                result = await crawler.arun(url=career_url)
                career_markdown = result.markdown
                jobs_output = extract_jobs_with_gpt(career_markdown, career_url)
                print(f"[Jobs] Company ID {company_id} from {career_url}:\n{jobs_output}")
                
                # Parse GPT output into structured jobs
                job_list = parse_gpt_jobs_output(jobs_output)
                if not job_list:
                    print(f"[Jobs] No jobs found or unable to parse for {career_url}")
                else:
                    newly_inserted = save_job_listings_to_db(company_id, job_list)
                    print(f"[Jobs] Inserted {len(newly_inserted)} new jobs for company ID {company_id}.")
                return  # Success; exit loop.
        except Exception as e:
            attempt += 1
            print(f"[Async Pipeline Error] Company ID {company_id} on attempt {attempt}: {e}")
            await asyncio.sleep(1)
    print(f"[Async Pipeline Error] Company ID {company_id}: Failed after {max_retries} attempts.")

async def process_all_career_and_jobs():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Process companies that have a non-null website.
            cur.execute("SELECT id, website FROM api_fundedcompany WHERE website IS NOT NULL")
            companies = cur.fetchall()

    if not companies:
        print("[Pipeline] No companies found with a valid homepage.")
        return

    tasks = []
    for company_id, homepage in companies:
        if is_valid_url(homepage):
            tasks.append(process_career_and_jobs(company_id, homepage))
            await asyncio.sleep(0.2)
    if tasks:
        await asyncio.gather(*tasks)

# ========== EMAIL FUNCTION (OPTIONAL) ==========

def send_email(new_jobs):
    if not new_jobs:
        print("[Email] No new jobs to send.")
        return

    subject = f"🚀 Found {len(new_jobs)} new jobs!"
    body = f"<h2>{subject}</h2><br><h3>New Jobs:</h3><ul>"
    for job in new_jobs:
        body += f"<li><a href='{job['link']}'>{job['title']}</a> at {job.get('company', '')}</li>"
    body += "</ul>"

    msg = MIMEMultipart()
    msg["From"] = SMTP_CONFIG["username"]
    msg["To"] = SMTP_CONFIG["receiver"]
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"])
        server.starttls()
        server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
        server.sendmail(SMTP_CONFIG["username"], SMTP_CONFIG["receiver"], msg.as_string())
        server.quit()
        print("[Email] Summary email sent successfully!")
    except Exception as e:
        print(f"[Email Error] {e}")

# ========== FULL PIPELINE FUNCTIONS ==========

def run_full_pipeline():
    print("===== STEP 1: Crunchbase Scraping & Company Details =====")
    companies = find_comapany_details()
    if companies:
        save_company_details_to_db(companies)
    else:
        print("[Pipeline] No company details scraped.")

    # Direct lookup for career pages if none exists (optional)
    all_companies = fetch_funded_companies()
    for comp in all_companies:
        company_id, name, website, career_url = comp
        if not career_url and website and is_valid_url(website):
            direct_url = find_career_page_direct(website)
            if direct_url:
                print(f"[Direct Career] {name}: {direct_url}")
                save_career_url(company_id, direct_url)
            else:
                print(f"[Direct Career] {name}: No direct career URL found.")

    print("\n===== STEP: Combined Asynchronous Career & Job Extraction =====")
    asyncio.run(process_all_career_and_jobs())

    # Optionally send an email summary if needed
    # new_jobs = [...]  # Build this list from the job extraction process
    # send_email(new_jobs)

    print("\n===== Pipeline Completed =====")

# ========== ARGUMENT PARSING & ENTRY POINT ==========

def main():
    parser = argparse.ArgumentParser(description="Modular Pipeline for Crunchbase -> Career -> Jobs")
    parser.add_argument("--phase", type=str, default="all",
                        help="Run specific phase: 'crunchbase', 'career', 'jobs', 'combined', or 'all' for full pipeline")
    args = parser.parse_args()

    phase = args.phase.lower()
    if phase == "crunchbase":
        print("Running Crunchbase scraping only...")
        companies = find_comapany_details()
        save_company_details_to_db(companies)
    elif phase == "career":
        print("Running Career page extraction only...")
        asyncio.run(process_all_career_and_jobs())
    elif phase == "jobs":
        print("Running Job listings extraction only...")
        asyncio.run(process_all_career_and_jobs())
    elif phase == "combined":
        print("Running combined Career and Job extraction...")
        asyncio.run(process_all_career_and_jobs())
    elif phase == "all":
        print("Running full pipeline...")
        run_full_pipeline()
    else:
        print("Invalid phase. Use --phase crunchbase | career | jobs | combined | all")

if __name__ == "__main__":
    main()
