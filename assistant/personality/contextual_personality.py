import os
import json
import time

STATE_FILE = "assistant/memory/personality_state.json"

class ContextualPersonality:
    def __init__(self):
        os.makedirs("memory", exist_ok=True)
        self.state = {
            "topics": [],
            "tone": "neutral",
            "preferences": {}
        }
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
            except Exception:
                pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"[Personality Save Error] {e}")

    def update_from_input(self, text):
        lowered = text.lower()

        if "horror" in lowered:
            self._add_topic("horror")
            self.state["preferences"]["likes_horror"] = True

        if "speedrun" in lowered or "split" in lowered:
            self._add_topic("speedrunning")
            self.state["preferences"]["loves_speedrunning"] = True

        if any(word in lowered for word in ["tired", "burnt out", "sad", "lonely"]):
            self.state["tone"] = "soft"

        self.save_state()

    def _add_topic(self, topic):
        if topic not in self.state["topics"]:
            self.state["topics"].append(topic)

    def inject_context(self, base_prompt):
        additions = []

        if self.state["preferences"].get("likes_horror"):
            additions.append("You know Fafnir loves horror — you might reference scary stuff casually.")

        if self.state["tone"] == "soft":
            additions.append("Use a softer, more caring tone today.")

        if additions:
            base_prompt += "\n\Sylveria's current context:\n" + "\n".join(f"- {line}" for line in additions)

        return base_prompt
