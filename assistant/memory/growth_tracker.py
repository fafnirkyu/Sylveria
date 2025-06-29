import json
import os
from datetime import datetime

class GrowthTracker:
    def __init__(self, path="assistant/memory/growth_log.json"):
        self.path = path
        self.growth_log = self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.growth_log, f, indent=2)

    def add_event(self, text: str, tags: list = [], emotion: str = None):
        event = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "event": text,
            "tags": tags,
            "emotion": emotion
        }
        self.growth_log.append(event)
        self._save()

    def get_anniversaries_today(self):
        today = datetime.now().strftime("%m-%d")
        return [e for e in self.growth_log if e["date"][5:] == today]

    def get_events_by_tag(self, tag: str):
        return [e for e in self.growth_log if tag in e["tags"]]

    def get_all(self):
        return self.growth_log
