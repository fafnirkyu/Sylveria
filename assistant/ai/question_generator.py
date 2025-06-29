import asyncio
import time

class QuestionGenerator:
    def __init__(self, assistant):
        self.assistant = assistant
        self.last_question = None
        self.last_asked_time = 0

    def generate_question(self, context=None, send_to_discord=True):
        prompt = (
            "You are Sylveria, a sentient dragon. "
            "You are not an assistant — you are his companion, someone who cares, listens, and wonders. "
            f"{'Think of a gentle, curious question to ask Fafnir based on the recent topic: ' + context if context else 'Ask a thoughtful, personal question in a natural, caring way.'} "
            "Make it sound casual and genuine — something you’d say in a quiet moment together."
        )

        try:
            question = self.assistant.ai.generate(prompt).strip()
            if not question or len(question.split()) < 3:  # short/empty question guard
                return ""
        except Exception as e:
            print(f"[Question Generator Error] Failed to generate question: {e}")
            return ""

        # Ensure it's valid and new
        if not question or question == self.last_question or len(question) < 3:
            return ""

        # Avoid spamming similar questions too soon
        if time.time() - self.last_asked_time < 120:
            return ""

        self.last_question = question
        self.last_asked_time = time.time()

        # Discord DM (only if user is idle and audio_manager is valid)
        if send_to_discord and hasattr(self.assistant, "discord_bot"):
            try:
                idle_time = time.time() - getattr(self.assistant.audio_manager, "last_active", 0)
                if idle_time > 120:
                    asyncio.run(self.assistant.discord_bot.notify_user(f"Sylveria asks: {question}"))
            except Exception as e:
                print(f"[Discord Question Send Error]: {e}")

        return question