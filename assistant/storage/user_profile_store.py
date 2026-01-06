import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "user_profile.json"


def load_user_profile() -> dict:
    if not DATA_FILE.exists():
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        # Bei Fehler leeres Dictionary zurückgeben
        return {}


def save_user_profile(profile: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)