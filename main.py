import os, json

creds = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

import requests

SERP_API_KEY = "YOUR_KEY"

def google_search(query):
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google"
    }
    return requests.get(url, params=params).json()


def get_emails_from_results(results):
    emails = set()
    for r in results.get("organic_results", []):
        snippet = r.get("snippet", "")
        emails |= extract_emails(snippet)
    return emails


import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

sheet = client.open("RPA_Leads").sheet1

existing = set(sheet.col_values(1))

def add_new_emails(emails):
    for e in emails:
        if e not in existing:
            sheet.append_row([e])

queries = [
    "RPA automation consultant email",
    "Robotic Process Automation services contact"
]

for q in queries:
    res = google_search(q)
    emails = get_emails_from_results(res)
    add_new_emails(emails)

