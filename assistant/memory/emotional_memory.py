import os
import json
import random
from datetime import datetime
from assistant.memory.growth_tracker import GrowthTracker


MEMORY_FILE = "assistant/memory/emotional_memories.json"

class EmotionalMemory:
    def __init__(self):
        os.makedirs("assistant/memory", exist_ok=True)

        if not os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

        self.memories = self._load_memories()
        self.growth_tracker = GrowthTracker()

    def _load_memories(self):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Memory Load Error]: {e}")
            return []

    def _save_memories(self):
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2)
        except Exception as e:
            print(f"[Memory Save Error]: {e}")

    def record_memory(self, user_input, response):
        # 10% chance to record a special emotional memory
        if random.random() < 0.10:
            feeling = random.choice(["warm", "joyful", "grateful", "hopeful", "loved", "amused"])
            memory_entry = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "user_input": user_input,
                "sylveria_response": response,
                "feeling": feeling,
            }
            self.memories.append(memory_entry)
            self.memories = self.memories[-50:]  # keep memory list short
            self._save_memories()
            print(f"[EmotionalMemory] Recorded a new emotional memory!")

            # If emotion is meaningful, also log it as growth
            if feeling in ["grateful", "hopeful", "loved"]:
                self.growth_tracker.add_event(
                    text=f"Sylveria felt {feeling} after Fafnir said: \"{user_input}\"",
                    tags=["emotional", feeling],
                    emotion=feeling
                )
                print(f"[GrowthTracker] Logged growth due to emotional memory.")
    def share_random_memory(self):
        if not self.memories:
            return "Hmm... I don't have many special memories yet. Let's make some today. 🌸"

        memory = random.choice(self.memories)
        return (
            f"I still remember when you said '{memory['user_input']}'... "
            f"It made me feel really {memory['feeling']}. 💜"
        )
