
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
