import os
import json
import requests

HISTORY_FILE = "assistant/memory/assistant_journal.json"
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "sylveria"

class AiWrapper:
    def __init__(self, assistant):
        self.assistant = assistant
        os.makedirs("assistant/memory", exist_ok=True)
        self.history = self._load_history()

    def _load_history(self):
        if not os.path.exists(HISTORY_FILE):
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Memory Load Error] {e}")
            return []

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history[-100:], f, indent=2)
        except Exception as e:
            print(f"[Memory Save Error] {e}")

    def _clean_response(self, text: str):
        if not text:
            return ""
        text = text.strip()
        words = text.split()
        return " ".join(words[:60]) + "..." if len(words) > 60 else text

    def generate(self, user_input: str):
        try:
            system_prompt, user_prompt = self._get_built_prompt(user_input)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            payload = {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.6,
                    "num_ctx": 2048,
                    "top_p": 0.9,
                    "stop": [
                        "Fafnir:", "User:", "Assistant:", "System:",
                        "Sylveria:", "You say", "Fafnir said", "Your response", "You reply",
                        "\nFafnir", "\nUser", "\nSylveria"
                    ]
                }
            }

            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()

            result = response.json()["message"]["content"].strip()
            cleaned = self._clean_response(result)

            self.history.append({"role": "user", "parts": [user_input]})
            self.history.append({"role": "sylveria", "parts": [cleaned]})
            self._save_history()

            return cleaned

        except Exception as e:
            import traceback
            print(f"[Ollama Error] {e}")
            traceback.print_exc()
            return "Sylveria hesitated — the words did not come this time."

    def _get_built_prompt(self, user_input):
        return self.assistant.prompt_builder.get_system_and_user_prompt(user_input)
