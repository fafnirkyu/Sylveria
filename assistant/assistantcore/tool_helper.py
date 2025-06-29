import re
import threading
import time
import asyncio
from assistant.plugins.spotify import SpotifyHelper

def words_to_numbers(text):
    word_map = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
        'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
        'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
        'eighteen': 18, 'nineteen': 19, 'twenty': 20
    }
    words = text.lower().split()
    for i, word in enumerate(words):
        if word in word_map:
            words[i] = str(word_map[word])
    return ' '.join(words)

class ToolHelper:
    def __init__(self, assistant):
        self.assistant = assistant
        self.command = assistant.command_processor
        self.youtube = assistant.youtube_player
        self.spotify = SpotifyHelper()
        self.weather = getattr(assistant, "weather", None)
        
    def _get_plugin(self, name):
        return self.assistant.plugins.get(name)

    def set_timer(self, command):
        command = words_to_numbers(command.lower())
        is_recurring = "every" in command

        matches = re.findall(r'(\d+)\s*(second|seconds|minute|minutes|hour|hours)', command)
        if not matches:
            return "Sorry, I didn't catch the timer duration."

        total_seconds = 0
        label_parts = []

        for amount, unit in matches:
            amount = int(amount)
            unit = unit.rstrip('s')
            seconds = amount * {'second': 1, 'minute': 60, 'hour': 3600}[unit]
            total_seconds += seconds
            label_parts.append(f"{amount} {unit}{'s' if amount > 1 else ''}")

        label = " and ".join(label_parts)

        def notify_timer_done():
            message = f"Time's up for: {label}!"
            self.assistant.gui.add_response("Sylveria", message)
            if hasattr(self.assistant, "discord_bot"):
                try:
                    asyncio.run(self.assistant.discord_bot.notify_user(message))
                except Exception as e:
                    print(f"[Discord Ping Error] {e}")

        if is_recurring:
            def recurring():
                while True:
                    time.sleep(total_seconds)
                    notify_timer_done()
            threading.Thread(target=recurring, daemon=True).start()
            return f"Recurring timer set: I'll remind you every {label}."

        threading.Thread(target=lambda: (time.sleep(total_seconds), notify_timer_done()), daemon=True).start()
        return f"Timer set for {label}."

    def run_script(self, command):
        return self.command.run_script(command)

    def stop_script(self, command):
        return self.command.stop_script(command)

    # ─── Plugin-aware Methods ───────────────────────

    def check_weather(self, location=None):
        if "weather" in self.assistant.plugins:
            return self.assistant.plugins["weather"].get_weather(location)
        return "Weather plugin is not available."

    def handle_calendar(self, command):
        calendar = self._get_plugin("google_calendar")
        if calendar:
            try:
                return calendar.handle_command(command)
            except Exception as e:
                return f"Calendar error: {e}"
        return "Calendar plugin is not loaded."

    def get_calendar_events(self):
        calendar = self._get_plugin("google_calendar")
        if calendar:
            try:
                return calendar.get_upcoming_events()
            except Exception as e:
                return f"Calendar error: {e}"
        return "Calendar plugin is not available."

    # ─── Built-in Tools ─────────────────────────────

    def youtube_action(self, command):
        query = command.lower().replace("play", "").replace("on youtube", "").strip()
        if not query:
            return "What would you like me to play?"
        self.youtube.play(query)
        return f"Playing '{query}' on YouTube!"

    def youtube_stop(self):
        self.youtube.stop()
        return "Stopped YouTube playback."

    def youtube_search(self, command):
        search_term = command.lower().split("search youtube for", 1)[-1].strip()
        results = self.youtube.search(search_term)
        if results:
            response = "YouTube results:\n" + "\n".join([f"- {title} ({url})" for title, url in results])
            return response
        return "I couldn't find anything on YouTube for that."

    # ─── Spotify ────────────────────────────────────

    def spotify_play(self, command):
        query = command.lower().replace("play", "").replace("on spotify", "").strip()
        return self.spotify.play_song(query)

    def spotify_pause(self):
        return self.spotify.pause()

    def spotify_resume(self):
        return self.spotify.resume()

    def spotify_now_playing(self):
        return self.spotify.now_playing()
