import discord
import asyncio
import threading
import random
from config.secrets import DISCORD_USER_ID, DISCORD_TOKEN

class DiscordBot(discord.Client):
    def __init__(self, assistant):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.assistant = assistant
        self.prefix = "!"
        self.loop_reference = None

    async def on_ready(self):
        print(f"[Discord] Logged in as {self.user}")
        self.loop_reference = asyncio.get_running_loop()

    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip()

        #Direct Message (Private DM)
        if isinstance(message.channel, discord.DMChannel):
            user_input = content
            async with message.channel.typing():
                response = self.assistant.command_processor.process(user_input)
                await asyncio.sleep(random.uniform(1.0, 2.0))  # natural typing delay
                await message.channel.send(response)
            return

        #Prefixed command
        if content.startswith(self.prefix):
            await self.handle_command(message, content[len(self.prefix):])

        #Mention fallback
        elif self.user in message.mentions:
            cleaned = content.replace(f"<@{self.user.id}>", "").strip()
            if cleaned:
                response = self.assistant.command_processor.process(cleaned)
                await message.channel.send(response)

    async def handle_command(self, message, command):
        try:
            response = self.assistant.command_processor.process(command)
            await message.channel.send(response)
        except Exception as e:
            print(f"[DiscordBot Error] {e}")
            await message.channel.send("Oops, something went wrong.")

    async def _send_dm(self, message: str):
        try:
            user = await self.fetch_user(DISCORD_USER_ID)
            if user:
                async with user.typing():
                    await asyncio.sleep(random.uniform(0.8, 2.0))
                    await user.send(message)
                    print(f"[Discord] Sent DM: {message}")
        except Exception as e:
            print(f"[Discord DM Error]: {e}")

    def notify_user(self, message: str):
        if self.loop_reference and self.loop_reference.is_running():
            asyncio.run_coroutine_threadsafe(
                self._send_dm(message),
                self.loop_reference
            )
        else:
            print("[DiscordBot] Event loop not ready; cannot send DM.")

    def send_ping(self, message: str):
        self.notify_user(message)

    async def _send_gui_response(self, response: str):
        try:
            user = await self.fetch_user(DISCORD_USER_ID)
            if user:
                async with user.typing():
                    await asyncio.sleep(random.uniform(0.8, 2.0))
                    await user.send(response)
        except Exception as e:
            print(f"[Discord GUI Response Error]: {e}")

    def send_gui_response_to_dm(self, response: str):
        if self.loop_reference and self.loop_reference.is_running():
            asyncio.run_coroutine_threadsafe(
                self._send_gui_response(response),
                self.loop_reference
            )
        else:
            print("[DiscordBot] Event loop not ready; cannot send GUI response.")

#Plugin entry point
def start(assistant):
    def run_discord_bot():
        bot = DiscordBot(assistant)
        assistant.discord_bot = bot  # Make accessible externally
        bot.run(DISCORD_TOKEN)

    threading.Thread(target=run_discord_bot, daemon=True).start()
    print("[Plugin] Discord bot is starting in background.")
