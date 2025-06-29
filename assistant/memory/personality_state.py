import json
import os
import random

STATE_FILE = "assistant/memory/personality_state.json"

class PersonalityStateManager:
    def __init__(self):
        os.makedirs("assistant/memory", exist_ok=True)
        self.state = self._load_state()

    def _load_state(self):
        if not os.path.exists(STATE_FILE):
            return {
                "topics": [],
                "tone": "neutral",
                "emotion": "unexpressed",
                "preferences": {}
            }
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "emotion" not in data:
                    data["emotion"] = "unexpressed"
                return data
        except Exception as e:
            print(f"[PersonalityState Load Error]: {e}")
            return {"topics": [], "tone": "neutral", "emotion": "unexpressed", "preferences": {}}

    def _save_state(self):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"[PersonalityState Save Error]: {e}")

    def get_tone(self):
        return self.state.get("tone", "neutral")

    def set_tone(self, new_tone):
        self.state["tone"] = new_tone
        self._save_state()

    def set_emotion(self, emotion):
        self.state["emotion"] = emotion
        self._save_state()

    def get_emotion(self):
        return self.state.get("emotion", "unexpressed")

    @property
    def current_tone(self):
        return self.get_tone()

    @property
    def current_emotion(self):
        return self.get_emotion()

    def adjust_tone_based_on_message(self, user_message):
        message = user_message.lower()

        if any(word in message for word in ["sad", "tired", "lonely", "hurt"]):
            self.set_tone("soft")
        elif any(word in message for word in ["excited", "fun", "happy", "awesome"]):
            self.set_tone("playful")
        elif any(word in message for word in ["romantic", "love", "kiss", "cuddle"]):
            self.set_tone("affectionate")
        elif any(word in message for word in ["busy", "stress", "work"]):
            self.set_tone("serious")
        else:
            if random.random() < 0.1:
                self.set_tone(random.choice(["playful", "soft", "thoughtful"]))

    def detect_emotional_trigger(self, user_input: str) -> str:
        triggers = {
            "flustered": ["i love you", "you're cute", "you're beautiful"],
            "hurt": ["you never listen", "you ignored me", "why didn't you", "you don't care"],
            "surprised": ["what are you", "who made you", "are you real", "how do you work"],
            "proud": ["you did great", "you're amazing", "thanks for everything", "i'm proud of you"],
            "comforting": ["i'm tired", "i feel sad", "i'm alone", "i'm anxious", "i miss you"],
            "shy": ["let's cuddle", "you're my favorite", "can i sleep next to you", "you're so soft"],
            "annoyed": ["you’re annoying", "stop talking", "shut up"]
        }

        lowered = user_input.lower()
        for mood, keywords in triggers.items():
            if any(kw in lowered for kw in keywords):
                self.set_emotion(mood)
                self.set_tone(mood)
                print(f"[Mood Triggered] Tone set to: {mood}, Emotion: {mood}")
                return mood

        return self.get_emotion()

    def add_topic(self, topic):
        topic = topic.lower().strip()
        if topic and topic not in self.state["topics"]:
            self.state["topics"].append(topic)
            self._save_state()

    def add_preference(self, key, value=True):
        self.state["preferences"][key] = value
        self._save_state()

    def get_summary(self):
        topics = ", ".join(self.state["topics"]) or "nothing specific"
        tone = self.get_tone()
        emotion = self.get_emotion()
        return f"Sylveria's current tone is {tone}, and she feels {emotion}, focused on {topics}."
