# assistant/datafiles.py
import os
import json
import time
import shutil

class DataFileManager:
    def __init__(self):
        self.data_files = {
            'timers': "assistant/memory/timers.json",
        }
        self._initialize()
        self.validate_files()
        self.backup_files()

    def _initialize(self):
        for key, file in self.data_files.items():
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)

    def validate_files(self):
        for file in self.data_files.values():
            try:
                with open(file, 'r') as f:
                    if f.read().strip():
                        f.seek(0)
                        json.load(f)
            except Exception as e:
                with open(file, 'w') as f:
                    json.dump({}, f)

    def backup_files(self):
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)

        for file in self.data_files.values():
            if os.path.exists(file):
                timestamp = int(time.time())
                backup_name = os.path.join(backup_dir, f"{os.path.basename(file)}.bak.{timestamp}")
                shutil.copyfile(file, backup_name)
                self._clean_old_backups(file, backup_dir)

    def _clean_old_backups(self, filename, backup_dir, keep=5):
        base = os.path.basename(filename)
        backups = sorted(
            [f for f in os.listdir(backup_dir) if f.startswith(base)],
            key=lambda x: os.path.getctime(os.path.join(backup_dir, x))
        )
        for old in backups[:-keep]:
            os.remove(os.path.join(backup_dir, old))

    def load(self, key):
        path = self.data_files.get(key)
        if path and os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        return {}

    def save(self, key, data):
        path = self.data_files.get(key)
        if path:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)