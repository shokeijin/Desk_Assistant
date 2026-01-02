import json
from pathlib import Path
from datetime import datetime

DATA_FILE = Path(__file__).parent / "reminders.json"


def load_reminders() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_reminders(reminders: list[dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)
