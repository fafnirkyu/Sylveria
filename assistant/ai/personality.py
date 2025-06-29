import os
import json

PREFERENCES_FILE = "assistant/memory/preferences.json"

class Personality:
    def __init__(self):
        self.preferences = self.load_preferences()

    def load_preferences(self):
        try:
            with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Preferences Load Error]: {e}")
            return {
                "movies": {"likes": [], "dislikes": []},
                "music": {"likes": [], "dislikes": []},
                "games": {"likes": [], "dislikes": []},
            }

    def _save_preferences(self):
        try:
            os.makedirs(os.path.dirname(PREFERENCES_FILE), exist_ok=True)
            with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            print(f"[Preferences Save Error]: {e}")

    def get_preferences_summary(self):
        likes = []
        dislikes = []

        for category, prefs in self.preferences.items():
            likes.extend(prefs.get("likes", []))
            dislikes.extend(prefs.get("dislikes", []))

        likes_text = ", ".join(likes) if likes else "none yet"
        dislikes_text = ", ".join(dislikes) if dislikes else "none yet"

        return f"Sylveria likes: {likes_text}. Sylveria dislikes: {dislikes_text}."

    def add_like(self, category: str, item: str):
        category = category.lower()
        item = item.strip()

        if category not in self.preferences:
            self.preferences[category] = {"likes": [], "dislikes": []}

        if item and item.lower() not in (x.lower() for x in self.preferences[category]["likes"]):
            self.preferences[category]["likes"].append(item)
            self._save_preferences()
            print(f"[Personality] Added to likes: {item} under {category}")

    def add_dislike(self, category: str, item: str):
        category = category.lower()
        item = item.strip()

        if category not in self.preferences:
            self.preferences[category] = {"likes": [], "dislikes": []}

        if item and item.lower() not in (x.lower() for x in self.preferences[category]["dislikes"]):
            self.preferences[category]["dislikes"].append(item)
            self._save_preferences()
            print(f"[Personality] Added to dislikes: {item} under {category}")

    def detect_and_learn_preference(self, user_input: str):
        keywords = {
            "movies": ["movie", "film", "cinema", "watch", "horror", "comedy", "romance"],
            "music": ["music", "song", "playlist", "album", "band", "listen"],
            "games": ["game", "play", "gaming", "videogame", "rpg", "shooter"],
        }

        positive_words = ["love", "like", "enjoy", "awesome", "amazing", "great", "fun"]
        negative_words = ["hate", "dislike", "boring", "bad", "awful", "terrible"]

        question_words = ["what", "how", "why", "when", "where", "do you", "would you", "could you"]

        user_lower = user_input.lower().strip()

        #First: Skip if it's clearly a question
        if user_lower.endswith("?") or any(user_lower.startswith(q) for q in question_words):
            return None, None

        #Second: Normal positive/negative detection
        is_positive = any(word in user_lower for word in positive_words)
        is_negative = any(word in user_lower for word in negative_words)

        for category, words in keywords.items():
            if any(word in user_lower for word in words):
                item = user_input.strip()

                if is_positive:
                    self.add_like(category, item)
                elif is_negative:
                    self.add_dislike(category, item)
                return category, item

        return None, None
    
