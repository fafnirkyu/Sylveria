from datetime import datetime

class InternalClock:
    def __init__(self):
        self.start = datetime.now()

    def now(self) -> str:
        """Returns the current time (HH:MM format)."""
        return datetime.now().strftime("%H:%M")

    def today(self) -> str:
        """Returns the current date (YYYY-MM-DD)."""
        return datetime.now().strftime("%Y-%m-%d")

    def elapsed(self) -> str:
        """Returns the elapsed time since assistant started."""
        return str(datetime.now() - self.start)

    def get_timestamp(self) -> str:
        """Returns a full timestamp (ISO format)."""
        return datetime.now().isoformat()

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