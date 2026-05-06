"""
Benutzerprofil-Store
====================
Lese- und Schreibzugriff auf die persönlichen Daten des aktiven Profils.
Speichert beliebige Schlüssel-Wert-Paare (z.B. Name, Alter, Beruf).
"""

import json
from pathlib import Path

from assistant.profile_manager import get_active_profile

# Basispfad zum Profil-Verzeichnis, relativ zu dieser Datei
PROFILES_DIR = Path(__file__).parent / "profiles"


def _get_data_file_path() -> Path:
    """Ermittelt den Pfad zur user_profile.json des aktiven Profils."""
    profile_path = PROFILES_DIR / get_active_profile()
    profile_path.mkdir(exist_ok=True)
    return profile_path / "user_profile.json"


def load_user_profile() -> dict:
    """Lädt die persönlichen Daten des aktiven Profils."""
    data_file = _get_data_file_path()

    if not data_file.exists():
        return {}

    try:
        content = data_file.read_text(encoding="utf-8").strip()
        return json.loads(content) if content else {}
    except (json.JSONDecodeError, IOError):
        return {}


def save_user_profile(profile: dict) -> None:
    """Speichert die persönlichen Daten des aktiven Profils."""
    data_file = _get_data_file_path()
    data_file.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )