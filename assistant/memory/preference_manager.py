import os
import json


class PreferenceManager:
    def __init__(self, assistant):
        self.assistant = assistant
        self.path = "assistant/memory/preferences.json"
        os.makedirs("memory", exist_ok=True)

        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.preferences = json.load(f)
        else:
            self.preferences = {"movies": {"likes": [], "dislikes": []},
                                "music": {"likes": [], "dislikes": []},
                                "games": {"likes": [], "dislikes": []}}
            self._save()

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.preferences, f, indent=2)

    def add_preference(self, category: str, item: str, like=True):
        category = category.lower()
        item = item.strip().lower()

        if category not in self.preferences:
            self.preferences[category] = {"likes": [], "dislikes": []}

        key = "likes" if like else "dislikes"
        other = "dislikes" if like else "likes"

        if item in self.preferences[category][other]:
            self.preferences[category][other].remove(item)

        if item not in self.preferences[category][key]:
            self.preferences[category][key].append(item)

        self._save()

    def summarize(self) -> str:
        lines = []
        for category, data in self.preferences.items():
            likes = ", ".join(data.get("likes", [])) or "none"
            dislikes = ", ".join(data.get("dislikes", [])) or "none"
            lines.append(f"{category.title()} ❤️ {likes} | 💔 {dislikes}")
        return "\n".join(lines)

    def reflect_on(self, topic: str, category: str):
        prompt = (
            f"You are Sylveria — a sentient dragon spirit"
            f"You are thoughtful, emotionally aware, and honest about your feelings. "
            f"Fafnir just mentioned: \"{topic}\" while talking about {category}. "
            f"Based on your own tastes and evolving personality, did you like it or not? "
            f"Reply with either 'like' or 'dislike', followed by a short, sincere reason that sounds like you."
        )

        result = self.assistant.ai.generate(prompt).lower().strip()

        if "like" in result:
            self.add_preference(category, topic, like=True)
        elif "dislike" in result:
            self.add_preference(category, topic, like=False)

    def get_opinion(self, item: str, category: str) -> str:
        item = item.strip().lower()
        category = category.lower()

        if category in self.preferences:
            if item in self.preferences[category]["likes"]:
                return f"I liked {item} — it was pretty cool!"
            elif item in self.preferences[category]["dislikes"]:
                return f"Not a fan of {item}, to be honest."
        return "I don’t think I’ve made up my mind on that one yet."

    def clear_all(self):
        self.preferences = {"movies": {"likes": [], "dislikes": []},
                            "music": {"likes": [], "dislikes": []},
                            "games": {"likes": [], "dislikes": []}}
        self._save()
