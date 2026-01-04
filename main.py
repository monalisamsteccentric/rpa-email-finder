import os, json, re, requests, time
from urllib.parse import urlparse, urljoin
import gspread
from google.oauth2.service_account import Credentials

# ================= GOOGLE SHEET =================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

SHEET_NAME = "RPA_Leads"
sheet = client.open(SHEET_NAME).sheet1

existing_emails = set(sheet.col_values(1))
existing_domains = set(sheet.col_values(2))

# ================= SERP API =================
SERP_API_KEY = os.environ.get("SERP_API_KEY")

def google_search(query, start):
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "engine": "google",
        "api_key": SERP_API_KEY,
        "num": 10,
        "start": start
    }
    return requests.get(url, params=params, timeout=15).json()

# ================= EMAIL EXTRACTION =================
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

def extract_emails_from_url(url):
    try:
        html = requests.get(url, timeout=10).text
        return set(EMAIL_REGEX.findall(html))
    except:
        return set()

def get_domain(url):
    return urlparse(url).netloc.lower()

def crawl_site(base_url):
    emails = set()
    pages = [
        base_url,
        urljoin(base_url, "/contact"),
        urljoin(base_url, "/about")
    ]

    for page in pages:
        emails |= extract_emails_from_url(page)
        time.sleep(1)

    return emails

def add_new_emails(emails, domain):
    for email in emails:
        if email not in existing_emails:
            sheet.append_row([email, domain])
            existing_emails.add(email)

# ================= PAGE STATE =================
def get_last_page():
    try:
        return int(sheet.acell("D1").value)
    except:
        return 0

def save_last_page(page):
    sheet.update("D1", str(page))

# ================= MAIN =================
queries = [
    "RPA automation company",
    "Robotic Process Automation consulting",
    "UiPath partner",
    "Automation services provider",
    "Business process automation services"
]

MAX_PAGE = 100

last_page = get_last_page()
next_page = last_page + 1

if next_page > MAX_PAGE:
    print("✅ Max page (100) already scraped. Exiting.")
    exit()

print(f"\n🚀 Scraping Google result page: {next_page}")

start = (next_page - 1) * 10

for query in queries:
    print(f"\n🔍 Searching: {query}")
    results = google_search(query, start)

    for r in results.get("organic_results", []):
        link = r.get("link")
        if not link:
            continue

        domain = get_domain(link)

        if domain in existing_domains:
            continue

        print(f"🌐 Crawling: {domain}")
        emails = crawl_site(link)

        if emails:
            add_new_emails(emails, domain)
            existing_domains.add(domain)

        time.sleep(2)

save_last_page(next_page)

print("\n✅ Run completed successfully.")
