import os, json, re, requests, time
import gspread
from google.oauth2.service_account import Credentials

# ---------- GOOGLE SHEET ----------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

SHEET_NAME = "RPA_Leads"
sheet = client.open(SHEET_NAME).sheet1
existing = set(sheet.col_values(1))

# ---------- SERP API ----------
SERP_API_KEY = os.environ.get("SERP_API_KEY")

def google_search(query):
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "engine": "google",
        "api_key": SERP_API_KEY,
        "num": 5
    }
    return requests.get(url, params=params).json()

# ---------- EMAIL EXTRACTION ----------
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

def extract_emails_from_url(url):
    try:
        html = requests.get(url, timeout=10).text
        return set(EMAIL_REGEX.findall(html))
    except:
        return set()

def add_new_emails(emails):
    for e in emails:
        if e not in existing:
            sheet.append_row([e])
            existing.add(e)

# ---------- MAIN ----------
queries = [
    "RPA automation services",
    "Robotic Process Automation consulting"
]

for q in queries:
    print(f"Searching: {q}")
    results = google_search(q)

    for r in results.get("organic_results", []):
        link = r.get("link")
        if link:
            emails = extract_emails_from_url(link)
            if emails:
                add_new_emails(emails)
            time.sleep(2)  # polite scraping
