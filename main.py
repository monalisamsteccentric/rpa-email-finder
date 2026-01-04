import os, json, re, requests, time
from urllib.parse import urlparse, urljoin
import gspread
from google.oauth2.service_account import Credentials

# ================= CONFIG =================
DAILY_EMAIL_LIMIT = 10
MAX_PAGE = 100

# ================= GOOGLE SHEET =================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

sheet = client.open("RPA_Leads").sheet1

existing_emails = set(sheet.col_values(1))
existing_domains = set(sheet.col_values(5))   # DOMAIN LAST COLUMN

# ================= SERP API =================
SERP_API_KEY = os.environ.get("SERP_API_KEY")

def google_search(query, start):
    return requests.get(
        "https://serpapi.com/search",
        params={
            "q": query,
            "engine": "google",
            "api_key": SERP_API_KEY,
            "num": 10,
            "start": start
        },
        timeout=15
    ).json()

# ================= EMAIL FILTER =================
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

INVALID_EXT = (
    ".png",".jpg",".jpeg",".svg",".webp",".gif",
    ".css",".js",".woff",".woff2",".ttf",".ico"
)

def clean_emails(emails):
    valid = set()
    for e in emails:
        el = e.lower()
        if el.endswith(INVALID_EXT):
            continue
        if "@2x." in el or "@32px." in el:
            continue
        valid.add(e)
    return valid

def extract_emails(url):
    try:
        html = requests.get(url, timeout=10).text
        return clean_emails(set(EMAIL_REGEX.findall(html)))
    except:
        return set()

# ================= HELPERS =================
def domain(url):
    return urlparse(url).netloc.lower()

def crawl_site(url):
    emails = set()
    for p in [url, urljoin(url, "/contact"), urljoin(url, "/about")]:
        emails |= extract_emails(p)
        time.sleep(1)
    return emails

# ================= KEYWORD PAGE STATE =================
def get_keyword_page(keyword):
    keywords = sheet.col_values(3)   # Column C
    pages = sheet.col_values(4)      # Column D

    max_page = 0
    for k, p in zip(keywords, pages):
        if k == keyword:
            try:
                max_page = max(max_page, int(p))
            except:
                pass

    return max_page


def save_row(email, keyword, page, domain):
    sheet.append_row([email, "", keyword, page, domain])

# ================= MAIN =================
queries = [
    "RPA automation company",
    "Robotic Process Automation consulting",
    "UiPath partner",
    "Automation services provider",
    "Business process automation services"
]

emails_collected = 0

for query in queries:
    if emails_collected >= DAILY_EMAIL_LIMIT:
        break

    last_page = get_keyword_page(query)
    next_page = last_page + 1
    if next_page > MAX_PAGE:
        continue

    print(f"\n🔍 {query} → Page {next_page}")
    start = (next_page - 1) * 10
    results = google_search(query, start)

    for r in results.get("organic_results", []):
        if emails_collected >= DAILY_EMAIL_LIMIT:
            break

        link = r.get("link")
        if not link:
            continue

        d = domain(link)
        if d in existing_domains:
            continue

        print(f"🌐 Crawling: {d}")
        emails = crawl_site(link)

        for e in emails:
            if emails_collected >= DAILY_EMAIL_LIMIT:
                break
            if e in existing_emails:
                continue

            save_row(e, query, next_page, d)
            existing_emails.add(e)
            existing_domains.add(d)
            emails_collected += 1

        time.sleep(2)

print(f"\n✅ Done. {emails_collected} emails collected today.")
