import os
import json
import re
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# =========================
# CONFIG
# =========================

SERP_API_KEY = os.environ.get("SERP_API_KEY")  # set this also as GitHub secret
SHEET_NAME = "RPA_Leads"

SEARCH_QUERIES = [
    "RPA automation consultant email",
    "Robotic Process Automation services contact",
    "RPA services company contact email",
    "business process automation consultant email"
]


# =========================
# GOOGLE SHEETS AUTH
# =========================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sheet = client.open(SHEET_NAME).sheet1
existing_emails = set(sheet.col_values(1))


# =========================
# UTIL FUNCTIONS
# =========================

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

def extract_emails(text):
    return set(re.findall(EMAIL_REGEX, text))


def google_search(query):
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google",
        "num": 10
    }
    return requests.get(url, params=params, timeout=30).json()


def collect_emails_from_results(results):
    emails = set()

    for r in results.get("organic_results", []):
        snippet = r.get("snippet", "")
        title = r.get("title", "")
        emails |= extract_emails(snippet)
        emails |= extract_emails(title)

    return emails


def add_new_emails(emails):
    new_rows = []
    for email in emails:
        if email not in existing_emails:
            new_rows.append([email])
            existing_emails.add(email)

    if new_rows:
        sheet.append_rows(new_rows)
        print(f"Added {len(new_rows)} new emails")
    else:
        print("No new emails found")


# =========================
# MAIN
# =========================

def main():
    for query in SEARCH_QUERIES:
        print(f"Searching: {query}")
        results = google_search(query)
        emails = collect_emails_from_results(results)
        add_new_emails(emails)


if __name__ == "__main__":
    main()
