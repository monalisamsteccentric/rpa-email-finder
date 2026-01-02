import os
import json
import re
import requests
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# ========================
# CONFIG
# ========================
SHEET_NAME = "RPA_Leads"
SERP_API_KEY = os.environ.get("SERP_API_KEY")

PROVIDER_QUERIES = [
    "RPA automation services contact",
    "Zapier automation consultant",
    "workflow automation agency",
    "CRM automation services"
]

PROBLEM_QUERIES = [
    "missed follow ups operations",
    "manual reporting is painful",
    "everything is done manually operations",
    "CRM follow up nightmare",
    "manual invoicing workflow problem"
]

ALLOWED_KEYWORDS = [
    "automation", "workflow", "rpa", "zapier", "crm",
    "operations", "manual", "integration", "process"
]

FREE_EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com"
]

# ========================
# GOOGLE SHEETS AUTH
# ========================
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(credentials)

sheet = client.open(SHEET_NAME).sheet1

existing_provider_emails = set(sheet.col_values(1))
existing_problem_emails = set(sheet.col_values(2))

# ========================
# UTILS
# ========================
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

def google_search(query):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY,
        "num": 10
    }
    return requests.get(url, params=params, timeout=30).json()

def extract_emails(text):
    return set(re.findall(EMAIL_REGEX, text or ""))

def is_business_email(email):
    domain = email.split("@")[-1].lower()
    return domain not in FREE_EMAIL_DOMAINS

def has_relevant_keywords(text):
    text = (text or "").lower()
    return any(k in text for k in ALLOWED_KEYWORDS)

# ========================
# CORE LOGIC
# ========================
def process_queries(queries, column_index, existing_set):
    new_rows = []

    for query in queries:
        results = google_search(query)

        for r in results.get("organic_results", []):
            snippet = r.get("snippet", "")
            title = r.get("title", "")
            combined_text = f"{title} {snippet}"

            if not has_relevant_keywords(combined_text):
                continue

            emails = extract_emails(combined_text)

            for email in emails:
                if not is_business_email(email):
                    continue
                if email in existing_set:
                    continue

                new_rows.append((email, datetime.utcnow().isoformat()))
                existing_set.add(email)

    # write to sheet
    for email, _ in new_rows:
        if column_index == 1:
            sheet.append_row([email, ""])
        else:
            sheet.append_row(["", email])

# ========================
# RUN
# ========================
if not SERP_API_KEY:
    raise Exception("SERP_API_KEY missing")

process_queries(PROVIDER_QUERIES, column_index=1, existing_set=existing_provider_emails)
process_queries(PROBLEM_QUERIES, column_index=2, existing_set=existing_problem_emails)

print("✅ Email collection completed")
