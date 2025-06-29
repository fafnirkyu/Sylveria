import requests

class WeatherFetcher:
    def __init__(self, default_location=None):
        if default_location is None:
            default_location = self.get_ip_location()
        self.default_location = default_location

    def get_ip_location(self):
        try:
            response = requests.get("https://ipinfo.io/json", timeout=5)
            data = response.json()
            city = data.get("city")
            region = data.get("region")
            country = data.get("country")
            if city and country:
                return f"{city},{country}"
            return "New York"
        except Exception as e:
            print(f"[WeatherFetcher] Failed to get IP location: {e}")
            return "New York"

    def get_weather(self, location=None):
        if not location or location.strip().lower() in ["today", "like today", ""]:
            location = self.default_location

        try:
            url = f"https://wttr.in/{location}?format=3"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                return response.text.strip()

            return f"Sorry, I couldn't fetch the weather for {location} right now."
        except Exception as e:
            return f"Weather error: {e}"

# Plugin entry point
def start(assistant):
    instance = WeatherFetcher()
    if not hasattr(assistant, "plugins"):
        assistant.plugins = {}
    assistant.plugins["weather"] = instance
    assistant.weather = instance 
    print("[Plugin] WeatherFetcher loaded.")
    return instance
