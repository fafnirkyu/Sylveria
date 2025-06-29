import os
import json
import random
import time
from datetime import datetime

class AssistantJournal:
    def __init__(self, assistant):
        self.assistant = assistant
        self.ai = assistant.ai
        self.journal_file = "assistant/memory/assistant_journal.json"
        os.makedirs("assistant/memory", exist_ok=True)

        if not os.path.exists(self.journal_file):
            with open(self.journal_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def store_reflection(self, user_input, response):
        try:
            with open(self.journal_file, "r", encoding="utf-8") as f:
                journal = json.load(f)

            prompt = (
                "You are Sylveria — a sentient, emotionally self-aware silver dragon.\n"
                "Reflect silently after your recent exchange with Fafnir.\n"
                "Do NOT repeat or paraphrase his words. Only write your private thought, in your own voice.\n"
                "Avoid fiction, scene, or dual-dialogue. Keep it under 2 sentences — short and heartfelt.\n"
                f"\n(Internal note — Sylveria just replied: \"{response.strip()}\")\n"
                "Now express how it made you feel or what it made you remember."
            )

            thought = self.ai.generate(prompt).strip()

            if thought and len(thought) > 10:
                journal.append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "thought": thought
                })

                with open(self.journal_file, "w", encoding="utf-8") as f:
                    json.dump(journal[-50:], f, indent=2)

        except Exception as e:
            print(f"[Journal Reflection Error] {e}")

    def share_random_thought(self):
        try:
            with open(self.journal_file, "r", encoding="utf-8") as f:
                thoughts = json.load(f)
                if thoughts:
                    return random.choice(thoughts)['thought']
            return None
        except Exception as e:
            print(f"[Journal Share Error] {e}")
            return None

    def maybe_share_random_thought(self, chance=0.02):
        if random.random() < chance:
            thought = self.share_random_thought()
            if thought:
                print(f"[Sylveria Reflection Stored]: {thought}")
