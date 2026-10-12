import json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

class Settings:
    def __init__(self):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.settings = self.data
    def get(self, key):
        return self.data.get(key)
    def set(self, key, value):
        self.data[key] = value
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)
