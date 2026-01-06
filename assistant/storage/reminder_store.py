import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "reminders.json"

def load_reminders() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content: return [] # Falls Datei leer ist
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return []

def save_reminders(reminders: list[dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)