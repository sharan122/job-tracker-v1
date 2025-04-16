import requests
import psycopg2
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from urllib.parse import urljoin, urlparse
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import undetected_chromedriver as uc
from serpapi import GoogleSearch
from flask import Flask, jsonify

app = Flask(__name__)


# ========== DATABASE CONFIG ==========

DB_CONFIG = {
    "dbname": "job_db",
    "user": "postgres",
    "password": "sharan123",
    "host": "localhost",
    "port": "5432"
}

# ========== EMAIL CONFIG ==========

SMTP_CONFIG = {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "rambogaming121@gmail.com",
    "password": "fhql prbn vjqj kvyv",
    "receiver": "sharanraj037840@gmail.com"
}


SERPAPI_KEY  = '490d1d035bc657aad2cf585f9bc68cab94044ef7c5e13e9111b59cee6106e3e8'

# ========== DB HELPERS ==========

def get_db_connection():
    """Connect to PostgreSQL and return the connection object."""
    return psycopg2.connect(**DB_CONFIG)

def fetch_funded_companies():
    """Fetch (company_name, website) from DB."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, website FROM api_fundedcompany")
            return cur.fetchall()  # list of (company_name, company_website)

# ========== HELPER TO NORMALIZE LINKS ==========

def normalize_link(link):
    """
    Removes query parameters/fragments and normalizes scheme/netloc/path.
    This helps avoid duplicates if LinkedIn adds query params.
    """
    parsed = urlparse(link)
    # Rebuild URL without query or fragment
    link_no_query = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return link_no_query.lower().rstrip("/")



# ========== 2) Crunchbase: Newly Funded Companies ==========
def find_comapany_details():
    """
    Scrapes the Crunchbase 'funding_rounds' page to get newly funded company names.
    Then for each company, calls 'search_company_with_serpapi' to find the Crunchbase link,
    then parses that link with Selenium to extract details.
    Returns a list of dictionaries with extracted info.
    """
    url = "https://www.crunchbase.com/discover/funding_rounds/e1ffaf87fcd0f9fa6d6ab9347cb8f379"
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    driver.get(url)
    time.sleep(15)  # Wait for JavaScript to load

    cells = driver.find_elements(By.CSS_SELECTOR, "grid-cell.column-id-funded_organization_identifier")
    company_names = []
    for cell in cells:
        try:
            name_elem = cell.find_element(By.CSS_SELECTOR, "div.identifier-label")
            if name_elem:
                company_names.append(name_elem.text.strip())
        except:
            continue

    driver.quit()

    # For each company, find Crunchbase link + parse details
    results = []
    for name in company_names:
        link = search_company_with_serpapi(name)
        if link:
            data = parse_company_details_selenium(link)
            data["company_name"] = name
            results.append(data)
        else:
            print(f"[WARN] No SerpAPI result for {name}")
        print(results)
    return results

def search_company_with_serpapi(company_name):
    """
    Uses SerpAPI to search Google for '{company_name} funding details crunchbase'.
    Returns the first organic result link, or None if no result.
    """
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
            link = organic_results[0].get("link")
            return link
    except Exception as e:
        print(f"Error using SerpAPI for {company_name}: {e}")
    return None

def parse_company_details_selenium(page_url):
    details = {
        "company_name": None,
        "website": None,
        "industry": [],
        "funding_round": None
    }

    if not page_url:
        return details

    # 1. Set up undetected-chromedriver
    options = uc.ChromeOptions()
    options.add_argument("--headless")  # Uncomment if you want headless mode
    driver = uc.Chrome(options=options)

    try:
        # 2. Navigate to the Crunchbase company page
        driver.get(page_url)
        print("[INFO] Navigating to:", page_url)
        time.sleep(20)

        # 3. Wait for Cloudflare challenge to finish + page to load
        #    We wait up to 30s for a known element that appears AFTER the challenge is done
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.profile-layout"))
            )
            print("[INFO] Cloudflare challenge bypassed, page loaded!")
        except:
            print("[WARN] Timed out waiting for Cloudflare or main page element. Possibly blocked or still verifying.")

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 1) Extract Website
        website_elem = soup.find("a", class_="component--field-formatter accent ng-star-inserted")
        if website_elem and website_elem.get("href"):
            details["website"] = website_elem["href"]

        # 2) Extract Funding Round
        
        funding_elem = soup.find("a", class_="component--field-formatter field-type-enum accent highlight-color-contrast-light ng-star-inserted")
        if funding_elem:
            details["funding_round"] = funding_elem.get_text(strip=True)

        # 3) Extract Industries (Multiple Values)
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
    

# ========== SCRAPING FUNCTIONS ==========

def find_career_page(company_website):
    """Try direct paths + parse homepage for 'career' links."""
    company_website = company_website.strip()
    if not company_website.startswith(("http://", "https://")):
        company_website = "https://" + company_website

    # 1. Try known paths
    possible_paths = ["/careers", "/jobs", "/join-us", "/work-with-us", "/hiring"]
    for path in possible_paths:
        url = urljoin(company_website, path)
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return url
        except:
            pass

    # 2. Parse homepage
    try:
        homepage_resp = requests.get(company_website, timeout=5)
        soup = BeautifulSoup(homepage_resp.text, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].lower()
            if any(kw in href for kw in ["career", "jobs", "hiring", "work-with"]):
                return urljoin(company_website, a_tag["href"])
    except:
        pass

    return None

def scrape_jobs_from_career_page(career_page, company_name):
    """Scrape job listings from the discovered career page."""
    job_listings = []
    try:
        resp = requests.get(career_page, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Adjust the selector based on actual structure
        job_divs = soup.find_all("div", class_="job-listing")
        for div in job_divs:
            title = div.find("h2")
            title_text = title.get_text(strip=True) if title else "No Title"

            link = div.find("a")
            link_url = urljoin(career_page, link["href"]) if link else "No Link"

            job_listings.append({
                "title": title_text,
                "link": link_url,
                "location": "Unknown",
                "job_type": "Unknown"
            })
    except:
        pass
    return job_listings

def scrape_jobs_from_linkedin(company_name):
    """Scrape job listings from LinkedIn using undetected ChromeDriver."""
    options = uc.ChromeOptions()
    options.add_argument("--disable-webrtc")
    # options.add_argument("--headless=new")  # Run in headless mode

    job_listings = []
    driver = None
    try:
        driver = uc.Chrome(options=options)
        linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={company_name}&location=worldwide"
        driver.get(linkedin_url)

        # Close login modal if present
        try:
            close_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "artdeco-button--muted")]'))
            )
            close_btn.click()
        except:
            pass  # No login modal

        # Check if job not found message appears
        no_jobs_msg = driver.find_elements(By.XPATH, "//h2[contains(text(), 'We couldn’t find a match')]")
        if no_jobs_msg:
            print(f"No jobs found for {company_name}. Skipping...")
            return []  # Return empty list

        # Wait for job cards
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list li"))
        )

        job_cards = driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li")

        for card in job_cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title").text.strip()
            except:
                title = "No Title"

            try:
                link_url = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute("href")
            except:
                link_url = "No Link"

            try:
                loc = card.find_element(By.CSS_SELECTOR, "span.job-search-card__location").text.strip()
            except:
                loc = "No Location"

            try:
                jt = card.find_element(By.CSS_SELECTOR, "span.job-search-card__employment-status").text.strip()
            except:
                jt = "Unknown"

            job_listings.append({
                "title": title,
                "link": link_url,
                "location": loc,
                "job_type": jt
            })

        print(f"Scraped {len(job_listings)} jobs from LinkedIn for {company_name}")

    except Exception as e:
        print(f"Unexpected error for {company_name}: {e}")
    finally:
        if driver:
            driver.quit()

    return job_listings


# ========== DATABASE LOGIC ==========
def save_company_details_to_db(company_data_list):
    """
    Saves company details to the database, avoiding duplicates.
    Returns the newly inserted companies (if any).
    """
    new_inserts = []

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for data in company_data_list:
                # Get values safely with defaults
                company_name = (data.get("company_name") or "").strip() or "Unknown Company"
                website = (data.get("website") or "").strip() or "N/A"
                
                # Convert industry list to a string
                industry = data.get("industry") or []
                if isinstance(industry, list):
                    industry = ", ".join(industry)  # Convert list to comma-separated string
                industry = industry.strip() or "Unknown"

                # Ensure funding_round is a string before stripping
                funding_round = (data.get("funding_round") or "").strip() or "Not Disclosed"

                # Check if the company already exists in DB
                cur.execute("SELECT id FROM api_fundedcompany WHERE name = %s", (company_name,))
                existing_row = cur.fetchone()

                if existing_row:
                    continue  # Skip if already exists
                else:
                    # Insert into 'companies_fundedcompany'
                    cur.execute("""
                        INSERT INTO api_fundedcompany (name, website, industry, funding_round, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        RETURNING id
                    """, (company_name, website, industry, funding_round))
                    new_company_id = cur.fetchone()[0]

                    new_inserts.append(data)

        conn.commit()
    return new_inserts



def save_jobs_to_db(company_name, job_listings):
    """
    Save job listings to the DB, skipping duplicates.
    Returns a list of newly inserted job dictionaries.
    """
    new_inserted_jobs = []

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Find company ID
            cur.execute("SELECT id FROM api_fundedcompany WHERE name = %s", (company_name,))
            row = cur.fetchone()
            if not row:
                return []  # If no company found

            company_id = row[0]

            # Fetch existing job links from DB, normalized
            cur.execute("SELECT job_link FROM api_joblisting WHERE company_id = %s", (company_id,))
            existing_links = {normalize_link(r[0]) for r in cur.fetchall()}

            for job in job_listings:
                norm_link = normalize_link(job["link"])
                if norm_link not in existing_links:
                    # Insert into DB
                    cur.execute("""
                        INSERT INTO api_joblisting (company_id, title, job_link, location, job_type)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        company_id,
                        job["title"],
                        job["link"],  # store original link
                        job.get("location", ""),
                        job.get("job_type", "")
                    ))
                    existing_links.add(norm_link)
                    new_inserted_jobs.append(job)

        conn.commit()
    return new_inserted_jobs

# ========== EMAIL LOGIC ==========

def send_email(new_jobs):
    """Send an email summary of newly found jobs."""
    if not new_jobs:
        print("No new jobs found. Skipping email.")
        return

    subject = f"🚀 Found {len(new_jobs)} new jobs!"
    body = f"<h2>{subject}</h2><br>"
    body += "<h3>💼 New Jobs:</h3><ul>"
    for job in new_jobs:
        body += f"<li><a href='{job['link']}'>{job['title']}</a>"
        if 'company' in job:
            body += f" at {job['company']}"
        body += "</li>"
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
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

# ========== MAIN WORKFLOW ==========

def main():
    
    company_data_list = find_comapany_details()  
   
    save_company_details_to_db(company_data_list)
    
    companies = fetch_funded_companies()
    all_new_jobs = []

    for (company_name, company_website) in companies:
        print(f"Processing {company_name} ({company_website}) ...")

        # 1. Attempt to find a career page
        career_page = find_career_page(company_website)
        if career_page:
            job_listings = scrape_jobs_from_career_page(career_page, company_name)
            if not job_listings:
                # If no jobs from career page, fallback to LinkedIn
                job_listings = scrape_jobs_from_linkedin(company_name)
        else:
            # No career page found, fallback to LinkedIn
            job_listings = scrape_jobs_from_linkedin(company_name)

        # 2. Insert only truly new jobs
        newly_inserted = save_jobs_to_db(company_name, job_listings)

        # 3. Label new jobs with company for the email
        for job in newly_inserted:
            job["company"] = company_name

        all_new_jobs.extend(newly_inserted)

    # 4. Send email only if new jobs exist
    # send_email(all_new_jobs)

if __name__ == "__main__":
    main()
