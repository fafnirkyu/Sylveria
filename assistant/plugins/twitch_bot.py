import asyncio
import random
from twitchio.ext import commands
from config.secrets import TWITCH_TOKEN, TWITCH_NICK, TWITCH_CHANNEL


class TwitchBot(commands.Bot):
    def __init__(self, assistant, token, nick, prefix, initial_channels):
        super().__init__(token=token, prefix=prefix, initial_channels=initial_channels)
        self.assistant = assistant

    async def event_ready(self):
        print(f"[Twitch] Logged in as | {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return

        if "@mal0v10" not in message.content.lower():
            return

        user_input = message.content.strip()
        username = message.author.name
        print(f"[Twitch Chat] {username}: {user_input}")

        if user_input.lower().startswith("!shoutout"):
            parts = user_input.split()
            if len(parts) >= 2:
                target_user = parts[1].lstrip("@")
                await self.shoutout(target_user)
            else:
                await message.channel.send("Who should I shout out?")
            return

        try:
            # Append to conversation history
            if not hasattr(self.assistant, "conversation_history"):
                self.assistant.conversation_history = []

            self.assistant.conversation_history.append({
                "role": "user",
                "content": f"{username}: {user_input}"
            })

            # Build prompt with system prompt as context
            chat_context = "\n".join(
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in self.assistant.conversation_history[-8:]
            )

            full_prompt = f"{self.assistant.system_prompt_twitch.strip()}\n\n{chat_context}"

            # Generate response
            response = self.assistant.ai.generate(prompt=full_prompt)
            response = self.assistant.command_processor._clean_response(response)

            if not response.strip():
                print("[Twitch Warning] Empty response from LLM.")
                response = "Sorry, I blanked out for a sec 😅"

            response = self.shorten_response(response, word_limit=60)

            if len(response) > 500:
                response = response[:497].rstrip() + "..."

            response = response[0].upper() + response[1:]
            await message.channel.send(response)
            self.assistant.audio_manager.speech_queue.put(response)

        except Exception as e:
            print(f"[Twitch LLM Error] {e}")
            await message.channel.send("Oops! I had a brain freeze. 🧊")

    async def shoutout(self, username):
        chat_templates = [
            "Huge shoutout to @{name}! A true legend.",
            "Go follow @{name} — they’re absolute fire 🔥",
            "Don’t walk — RUN to check out @{name}'s stream!",
            "It's @{name}! Drop them a follow or face my wrath 🐉"
        ]
        tts_templates = [
            "Hey everyone, big love to {name}!",
            "You rock, {name}. Keep shining!",
            "Shoutout activated. I approve of {name}!"
        ]

        chat_msg = random.choice(chat_templates).format(name=username)
        tts_msg = random.choice(tts_templates).format(name=username)

        try:
            for channel in self.connected_channels:
                await channel.send(chat_msg)
        except Exception as e:
            print(f"[Shoutout Error] Failed to send Twitch message: {e}")

        self.assistant.audio_manager.speech_queue.put(tts_msg)

    def shorten_response(self, text, word_limit=40):
        words = text.split()
        return " ".join(words[:word_limit]) + "..." if len(words) > word_limit else text


#Plugin interface
def start(assistant):
    token = TWITCH_TOKEN
    nick = TWITCH_NICK
    prefix = "!"
    channels = TWITCH_CHANNEL if isinstance(TWITCH_CHANNEL, list) else [TWITCH_CHANNEL]

    if not token:
        print("[TwitchBot] No token provided. Plugin will not start.")
        return

    bot = TwitchBot(assistant, token, nick, prefix, channels)

    def run_bot():
        asyncio.run(bot.run())

    asyncio.get_event_loop().run_in_executor(None, run_bot)
    print("[Plugin] TwitchBot loaded and running.")
