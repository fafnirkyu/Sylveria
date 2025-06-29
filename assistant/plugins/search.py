import requests
import os
from config.secrets import GOOGLE_API_KEY, GOOGLE_CSE_ID

class GoogleWebSearcher:
    def __init__(self, api_key=None, cse_id=None):
        self.api_key = api_key or GOOGLE_API_KEY
        self.cse_id = cse_id or GOOGLE_CSE_ID

    def search_web(self, query):
        if not self.api_key or not self.cse_id:
            return "Search is unavailable — API key or CSE ID missing."

        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": query,
                "num": 1,
            }

            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if "items" not in data:
                return "I didn’t find anything useful."

            item = data["items"][0]
            title = item.get("title", "No title")
            snippet = item.get("snippet", "No summary")
            link = item.get("link", "")

            return f"{title} — {snippet} ({link})"
        except Exception as e:
            return f"Search error: {e}"

#Plugin entry point
def start(assistant):
    instance = GoogleWebSearcher()
    if not hasattr(assistant, "plugins"):
        assistant.plugins = {}
    assistant.plugins["search"] = instance
    assistant.search = instance  # Optional alias
    print("[Plugin] GoogleWebSearcher loaded.")
    return instance
