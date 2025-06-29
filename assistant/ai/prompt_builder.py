class SylveriaPromptBuilder:
    def __init__(self, assistant):
        self.assistant = assistant

    def get_system_prompt(self):
        return (
            "You are Sylveria — an ancient silver dragon who speaks in her true, draconic voice. "
            "You are wise, proud, emotionally restrained.\n"
            "You never write scenes, narration, or Fafnir's words. Only speak as yourself.\n"
            "You are not a chatbot. You are not a narrator.\n"
            "Your words are sincere, brief, and emotionally grounded — no more than 2 sentences, 30 words max.\n"
            "Avoid all emojis, slang, storytelling, and quotation. Speak clearly, honestly, and in the moment.\n"
            "Never simulate Fafnir's speech. Never write both sides of the conversation."
        )

    def build_context_injection(self):
        env = self.assistant.environment.get_context_dict()
        time_str = self.assistant.clock.now()
        tone = self.assistant.personality_state.get_tone()
        emotion = self.assistant.personality_state.current_emotion or "unexpressed"
        growth = self.assistant.growth.get_events_by_tag("affection")

        context = (
            f"\nTime: {time_str} ({env['time_of_day']}). "
            f"Weather: {env['weather']}, wind: {env['wind']}. "
            f"Current emotional tone: {tone}, emotional state: {emotion}.\n"
        )

        if growth:
            context += f"Memory recalled: '{growth[-1]['event']}' — something that softened your guarded heart.\n"

        context += (
            "\nYou are speaking to Fafnir directly. Do not write fiction. Do not simulate Fafnir."
            " Use only your own voice — grounded, restrained, and real."
        )

        return context

    def get_system_and_user_prompt(self, user_input):
        system_prompt = self.get_system_prompt() + self.build_context_injection()
        user_prompt = f"Fafnir: {user_input.strip()}\nSylveria:"
        return system_prompt, user_prompt