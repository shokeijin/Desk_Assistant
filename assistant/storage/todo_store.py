"""
Todo-Store
==========
Lese- und Schreibzugriff auf die Todo-Liste des aktiven Profils.
Daten werden als JSON-Datei pro Nutzerprofil gespeichert.
"""

import json
from pathlib import Path

from assistant.profile_manager import get_active_profile

# Basispfad zum Profil-Verzeichnis, relativ zu dieser Datei
PROFILES_DIR = Path(__file__).parent / "profiles"


def _get_data_file_path() -> Path:
    """Ermittelt den Pfad zur todos.json des aktiven Profils."""
    profile_path = PROFILES_DIR / get_active_profile()
    profile_path.mkdir(exist_ok=True)
    return profile_path / "todos.json"


def load_todos() -> list[str]:
    """Lädt die Todo-Liste aus der JSON-Datei des aktiven Profils."""
    data_file = _get_data_file_path()

    if not data_file.exists():
        return []

    try:
        content = data_file.read_text(encoding="utf-8").strip()
        return json.loads(content) if content else []
    except (json.JSONDecodeError, IOError):
        return []


def save_todos(todos: list[str]) -> None:
    """Speichert die Todo-Liste in der JSON-Datei des aktiven Profils."""
    data_file = _get_data_file_path()
    data_file.write_text(
        json.dumps(todos, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )