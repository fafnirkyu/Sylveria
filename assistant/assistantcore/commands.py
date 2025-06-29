import re
import time
import threading
import random
from dateutil.parser import parse
from assistant.utils.assistant_utils import words_to_numbers
from assistant.plugins.google_calendar import create_event, get_upcoming_events, find_event_by_title, update_event
import datetime
import asyncio
import os
import subprocess

class CommandProcessor:
    def __init__(self, assistant):
        self.assistant = assistant
        self.script_process = None

    def process(self, command, source="assistant"):
        # Detect and adjust tone based on emotional trigger
        mood = self.assistant.personality_state.detect_emotional_trigger(command)
        self.assistant.personality_state.adjust_tone_based_on_message(command)
        print(f"[Mood Detection] Tone set to: {mood}")

        response = self.assistant.planner.handle(command)
        response = self.assistant.ai._clean_response(response)

        if not response or not response.strip():
            print("[CommandProcessor] Empty or invalid response after cleaning.")
            return self.fallback_response()

        return response

    def fallback_response(self):
        options = [
            "Hmm... I’d love to, but I’m still learning 🎤",
            "I'd try, but my code is feeling shy today!",
            "Not sure how to help with that yet 😅",
            "Still working on that skill! Ask me again later."
        ]
        return random.choice(options)

    def set_timer(self, command, discord_notify=False):
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

        if is_recurring:
            threading.Thread(target=self._recurring_timer_thread, args=(label, total_seconds), daemon=True).start()
            return f"Recurring timer set: I'll remind you every {label}."

        else:
            end_time = time.time() + total_seconds
            timers = self.assistant.data_manager.load('timers') or {}
            timers[label] = end_time
            self.assistant.data_manager.save('timers', timers)

            threading.Thread(target=self._timer_thread, args=(label, total_seconds, discord_notify), daemon=True).start()
            return f"Timer set for {label}."

    def _timer_thread(self, label, seconds, discord_notify=False):
        time.sleep(seconds)
        message = f"Timer for {label} is up!"
        self.assistant.gui.add_response("Sylveria", message)

        if discord_notify and hasattr(self.assistant, "discord_bot"):
            try:
                asyncio.run(self.assistant.discord_bot.notify_user(message))
            except Exception as e:
                print(f"[Discord DM Error] {e}")

    def _recurring_timer_thread(self, label, interval):
        while True:
            time.sleep(interval)
            message = f"Reminder: It's time for your {label}!"
            print(f"[Recurring Timer] {message}")

    def handle_calendar(self, command):
        try:
            is_recurring = "every" in command

            cleaned = re.sub(
                r'\b(add|set|schedule|remind|calendar|event|to|on|at|for|every|called|name|a|an|the)\b',
                '', command, flags=re.IGNORECASE
            )
            event_name = re.sub(r'\s+', ' ', cleaned).strip()

            if not event_name:
                return "What should I call this event?"

            if is_recurring:
                weekday_match = re.search(r'every\s+(\w+)', command)
                time_match = re.search(r'at\s+(\d+)(?::(\d+))?\s*(am|pm)?', command)

                if not weekday_match or not time_match:
                    return "Sorry, I couldn't understand the recurring schedule."

                day_name = weekday_match.group(1).capitalize()
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                am_pm = time_match.group(3)

                if am_pm and am_pm.lower() == 'pm' and hour < 12:
                    hour += 12
                elif am_pm and am_pm.lower() == 'am' and hour == 12:
                    hour = 0

                today = datetime.datetime.now()
                weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                if day_name not in weekdays:
                    return f"'{day_name}' doesn't look like a valid weekday."

                target_day = weekdays.index(day_name)
                days_ahead = (target_day - today.weekday()) % 7
                if days_ahead == 0 and datetime.datetime.now().time() > datetime.time(hour, minute):
                    days_ahead += 7

                next_occurrence = today + datetime.timedelta(days=days_ahead)
                start_time = next_occurrence.replace(hour=hour, minute=minute, second=0, microsecond=0)

                create_event(event_name, start_time, recurring=True)
                return f"Recurring event '{event_name}' set for every {day_name} at {start_time.strftime('%I:%M %p')}."

            else:
                dt = parse(command, fuzzy=True, default=datetime.datetime.now())
                create_event(event_name, dt)
                return f"Event '{event_name}' added to your Google Calendar for {dt.strftime('%A at %I:%M %p')}."

        except Exception as e:
            print(f"[Calendar Error] {e}")
            return f"Sorry, I couldn't schedule that: {e}"

    def read_calendar(self, command):
        try:
            if "week" in command:
                days = 7
            elif "tomorrow" in command:
                days = 2
            else:
                days = 1

            events = get_upcoming_events(days_ahead=days)

            if not events:
                return "You have no upcoming events."

            lines = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                date = datetime.datetime.fromisoformat(start.replace("Z", "+00:00")).strftime('%A at %I:%M %p')
                lines.append(f"{event['summary']} on {date}")

            return "Here's what's coming up: " + "; ".join(lines)

        except Exception as e:
            print(f"[Read Calendar Error] {e}")
            return "Something went wrong trying to read your calendar."

    def edit_calendar_event(self, command):
        try:
            new_time = parse(command, fuzzy=True, default=datetime.datetime.now())

            cleaned = re.sub(r'\b(change|edit|move|reschedule|my|event|to|at|on|for)\b', '', command, flags=re.IGNORECASE)
            event_title = re.sub(r'\s+', ' ', cleaned).strip()

            if not event_title:
                return "What event should I update?"

            event = find_event_by_title(event_title)
            if not event:
                return f"I couldn't find an event called '{event_title}'."

            start = new_time
            end = start + datetime.timedelta(hours=1)

            update_event(event['id'], {
                'start': {'dateTime': start.isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': end.isoformat(), 'timeZone': 'UTC'}
            })

            return f"'{event['summary']}' has been rescheduled to {start.strftime('%A at %I:%M %p')}."

        except Exception as e:
            print(f"[Calendar Edit Error] {e}")
            return f"Sorry, I couldn't update that: {e}"

    def list_files(self, command):
        try:
            path = os.path.expanduser("~/Downloads")
            files = os.listdir(path)
            if not files:
                return "The folder is empty."
            return "Here's what I found:\n" + "\n".join(files)
        except Exception as e:
            return f"Error listing files: {e}"

    def read_file(self, command):
        try:
            filename = self._extract_filename(command)
            if not filename:
                return "What file do you want me to read?"

            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()

            if len(content) > 800:
                return f"Contents of {filename} (truncated):\n\n{content[:800]}..."
            else:
                return f"Here's what's in {filename}:\n\n{content}"

        except Exception as e:
            return f"Sorry, I couldn't read the file: {e}"

    def write_file(self, command):
        try:
            match = re.search(r'write to (\S+)\s*[:\-]*\s*(.*)', command, re.IGNORECASE)
            if not match:
                return "Please tell me what file to write to, and what to write."

            filename, content = match.groups()

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content.strip())

            return f"I've written your message to {filename}."

        except Exception as e:
            return f"Sorry, I couldn't write to the file: {e}"

    def _extract_filename(self, command):
        match = re.search(r'(?:read|open) (?:file )?(\S+\.\w+)', command, re.IGNORECASE)
        return match.group(1) if match else None

    def run_script(self, command):
        try:
            match = re.search(r'(?:run|start|execute)\s+script\s+([\w\-\.]+)', command)
            if not match:
                return "Which script should I run?"

            script_name = match.group(1).strip()
            script_path = os.path.join("scripts", script_name)

            if not os.path.exists(script_path):
                return f"I couldn't find a script named {script_name} in your scripts folder."

            self.stop_script()

            self.script_process = subprocess.Popen(["python", script_path])
            return f"Running `{script_name}` now!"

        except Exception as e:
            print(f"[Script Error] {e}")
            return "Something went wrong trying to run the script."

    def stop_script(self, *args):
        if hasattr(self, "script_process") and self.script_process:
            self.script_process.terminate()
            self.script_process = None
            return "Stopped the script."
        return "No script was running."

    def handle_script_generation(self, command):
        try:
            match = re.search(r'call it ([\w\-]+\.py)', command)
            if match:
                filename = match.group(1)
            else:
                filename = f"generated_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.py"

            cleaned_command = re.sub(r'call it [\w\-]+\.py', '', command, flags=re.IGNORECASE).strip()

            system_prompt = (
                "You are a helpful coding assistant. "
                "Write valid and complete Python code only. "
                "Do not include explanation, just return the code."
            )

            response = self.assistant.ai.generate(prompt=cleaned_command, system_prompt=system_prompt)

            code = self._extract_python_code(response)

            os.makedirs("scripts", exist_ok=True)
            with open(f"scripts/{filename}", "w", encoding="utf-8") as f:
                f.write(code)

            return f"Script saved as {filename}. Let me know when to run it."

        except Exception as e:
            print(f"[Script Gen Error] {e}")
            return "Something went wrong while generating the script."

    def _extract_python_code(self, text):
        code_block = re.sub(r"```(?:python)?", "", text, flags=re.IGNORECASE).strip()
        return code_block.replace("```", "").strip()
