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

# assistant/datafiles.py
import os
import json

class DataFileManager:
    def __init__(self):
        self.files = ["memory/calendar.json", "memory/timers.json", "memory/config.json"]
        self._initialize()

    def _initialize(self):
        for file in self.files:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)

def extract_preference_from_history(history, keyword="call me"):
    for msg in reversed(history):  # search most recent messages first
        if msg["role"] == "user" and keyword in msg["content"].lower():
            return msg["content"].split(keyword, 1)[-1].strip()
    return None