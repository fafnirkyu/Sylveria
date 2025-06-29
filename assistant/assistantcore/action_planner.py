import json
import os
import re
import time
import random
import threading


class ActionPlanner:
    def __init__(self, assistant):
        self.assistant = assistant
        self.ai = assistant.ai
        self.tools = assistant.tools
        self.journal = assistant.journal
        self.memory_file = "assistant/memory/goals.json"
        self.last_action_context = None

        os.makedirs("assistant/memory", exist_ok=True)
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                self.goals = json.load(f)
        except Exception:
            self.goals = []

    def handle(self, command: str) -> str:
        try:
            command = command.strip()

            if "what have you been thinking about" in command.lower():
                return self.journal.share_random_thought()

            parts = re.split(r'\b(?:then|and|after that|,)\b', command)
            final_responses = []

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                self.assistant.personality.detect_and_learn_preference(part)
                emotion = self.assistant.personality_state.detect_emotional_trigger(part)
                current_tone = self.assistant.personality_state.get_tone()
                enriched_prompt = part
                lower_part = part.lower()

                if "weather" in lower_part:
                    self.last_action_context = "weather"
                    if "weather" in self.assistant.plugins:
                        final_responses.append(self.assistant.plugins["weather"].get_weather())
                    else:
                        final_responses.append("Sorry, I can't check the weather right now.")
                    continue

                elif any(kw in lower_part for kw in ["search", "look up", "find info about"]):
                    plugin = self.assistant.plugins.get("search")
                    if plugin:
                        final_responses.append(plugin.search_web(part))
                    else:
                        final_responses.append("Search plugin isn't loaded.")
                    continue

                if "timer" in lower_part:
                    self.last_action_context = "timer"
                    final_responses.append(self.tools.set_timer(part))
                    continue

                elif any(kw in lower_part for kw in ["calendar", "schedule", "event"]):
                    self.last_action_context = "calendar"
                    if any(k in lower_part for k in ["add", "create", "remind", "set"]):
                        final_responses.append(self.tools.handle_calendar(part))
                    else:
                        final_responses.append(self.tools.get_calendar_events())
                    continue

                elif any(kw in lower_part for kw in ["run script", "start script", "execute script"]):
                    self.last_action_context = "script"
                    final_responses.append(self.tools.run_script(part))
                    continue

                elif any(kw in lower_part for kw in ["stop script", "terminate script"]):
                    final_responses.append(self.tools.stop_script(part))
                    continue

                elif "stop youtube" in lower_part or ("stop" in lower_part and self.last_action_context == "youtube"):
                    self.last_action_context = "youtube"
                    final_responses.append(self.tools.youtube_stop())
                    continue

                elif "search youtube for" in lower_part:
                    self.last_action_context = "youtube"
                    final_responses.append(self.tools.youtube_search(part))
                    continue

                elif ("play" in lower_part and "youtube" in lower_part) or ("watch" in lower_part and "youtube" in lower_part):
                    self.last_action_context = "youtube"
                    final_responses.append(self.tools.youtube_action(part))
                    continue

                elif "play" in lower_part and self.last_action_context == "youtube":
                    final_responses.append(self.tools.youtube_action(part))
                    continue

                elif "stop" in lower_part and self.last_action_context == "timer":
                    final_responses.append("There’s no specific timer to stop just yet. Want me to cancel the current one?")
                    continue

                if "special memory" in lower_part or "favorite memory" in lower_part:
                    return self.assistant.emotional_memory.share_random_memory()

                if "remind me" in lower_part or "remember that" in lower_part:
                    final_responses.append(self._store_goal(part))
                    continue

                if ("remember" in lower_part or "did i" in lower_part) and any(kw in lower_part for kw in ["ask", "tell", "save", "remember when", "my goals"]):
                    final_responses.append(self._recall_goals(part))
                    continue

                system_prompt, user_prompt = self.assistant.prompt_builder.get_system_and_user_prompt(enriched_prompt)
                response = self.ai.generate_with_prompts(system_prompt, user_prompt).strip()
                response = self.ai._clean_response(response)

                if len(response.split()) > 60:
                    response = " ".join(response.split()[:60]) + "..."

                if response:
                    final_responses.append(response)
                    self._store_dialogue(part, response)

                    if random.random() < 0.25 and "?" not in response:
                        try:
                            follow_up = self.assistant.question_gen.generate_question(context=part, send_to_discord=False)
                            if follow_up:
                                def delayed_follow_up():
                                    time.sleep(random.randint(4, 8))
                                    self.assistant.gui.root.after(0, lambda: self.assistant.gui.add_response("Sylveria (curious)", follow_up))
                                threading.Thread(target=delayed_follow_up, daemon=True).start()
                        except Exception as e:
                            print(f"[Follow-up Error] {e}")

            return "\n".join(final_responses)

        except Exception as e:
            print(f"[Planner Error] {e}")
            return "I had trouble figuring that one out."

    def _store_goal(self, command):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.goals.append({"text": command, "time": timestamp})
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.goals, f, indent=2)
        except Exception as e:
            print(f"[Memory Save Error]: {e}")
        return "Okay, I'll remember that for you."

    def _recall_goals(self, _command):
        if not self.goals:
            return "You haven’t asked me to remember anything yet."
        summary = "\n".join(f"- {g['text']} ({g['time']})" for g in self.goals[-5:])
        return f"Here's what I remember:\n{summary}"

    def _store_dialogue(self, user_input, response):
        try:
            history = self.assistant.data_manager.load("chat_log") or []
            history.append({"user": user_input, "Sylveria": response})
            self.assistant.data_manager.save("chat_log", history)

            self.assistant.ai.history.append({"role": "user", "parts": [user_input]})
            self.assistant.ai.history.append({"role": "model", "parts": [response]})
            self.assistant.ai._save_history()

            self.journal.maybe_share_random_thought()
            self.assistant.emotional_memory.record_memory(user_input, response)
        except Exception as e:
            print(f"[Log Save Error]: {e}")
