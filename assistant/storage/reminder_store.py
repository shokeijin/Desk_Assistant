"""
Reminder-Store
==============
Lese- und Schreibzugriff auf die Erinnerungsliste des aktiven Profils.
Jeder Reminder ist ein Dictionary mit den Feldern:
  - text:  Beschreibung der Erinnerung
  - time:  ISO-Zeitstempel (z.B. "2026-05-01T09:30:00")
  - done:  True wenn die Erinnerung bereits ausgelöst wurde
"""

import json
from pathlib import Path

from assistant.profile_manager import get_active_profile

# Basispfad zum Profil-Verzeichnis, relativ zu dieser Datei
PROFILES_DIR = Path(__file__).parent / "profiles"


def _get_data_file_path() -> Path:
    """Ermittelt den Pfad zur reminders.json des aktiven Profils."""
    profile_path = PROFILES_DIR / get_active_profile()
    profile_path.mkdir(exist_ok=True)
    return profile_path / "reminders.json"


def load_reminders() -> list[dict]:
    """Lädt alle Erinnerungen aus der JSON-Datei des aktiven Profils."""
    data_file = _get_data_file_path()

    if not data_file.exists():
        return []

    try:
        content = data_file.read_text(encoding="utf-8").strip()
        return json.loads(content) if content else []
    except (json.JSONDecodeError, IOError):
        return []


def save_reminders(reminders: list[dict]) -> None:
    """Speichert alle Erinnerungen in der JSON-Datei des aktiven Profils."""
    data_file = _get_data_file_path()
    data_file.write_text(
        json.dumps(reminders, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )