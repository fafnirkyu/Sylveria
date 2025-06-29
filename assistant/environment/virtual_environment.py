import random
from datetime import datetime

class VirtualEnvironment:
    def __init__(self):
        self.time = self.get_time_of_day()
        self.weather = self._random_weather()
        self.wind = self._random_wind()
        self.last_refresh = datetime.now().hour

    def get_time_of_day(self):
        hour = datetime.now().hour
        if 5 <= hour < 11:
            return "morning"
        elif 11 <= hour < 14:
            return "midday"
        elif 14 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"

    def _random_weather(self):
        return random.choice(["clear", "cloudy", "light rain", "storm", "fog", "snow"])

    def _random_wind(self):
        return random.choice(["still", "breeze", "gusty", "howling"])

    def refresh(self):
        """Refreshes the environmental state periodically."""
        current_hour = datetime.now().hour
        if current_hour != self.last_refresh:
            self.time = self.get_time_of_day()
            self.weather = self._random_weather()
            self.wind = self._random_wind()
            self.last_refresh = current_hour

    def describe(self):
        return f"It is {self.time}, the sky is {self.weather}, and the wind is {self.wind}."

    def get_context_dict(self):
        return {
            "time_of_day": self.time,
            "weather": self.weather,
            "wind": self.wind,
        }
