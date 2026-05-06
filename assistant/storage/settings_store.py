"""
Einstellungs-Store
==================
Lese- und Schreibzugriff auf die Einstellungen des aktiven Profils.
Fehlende Einstellungen werden durch Standardwerte ersetzt, sodass
das System auch bei einer leeren oder neuen settings.json funktioniert.
"""

import json
from pathlib import Path

from assistant.profile_manager import get_active_profile

# Basispfad zum Profil-Verzeichnis, relativ zu dieser Datei
PROFILES_DIR = Path(__file__).parent / "profiles"

# Standardwerte – werden verwendet wenn keine Einstellungen existieren
# oder wenn einzelne Schlüssel in der Datei fehlen
DEFAULT_SETTINGS: dict = {
    "agent_name": "melvin",
    "use_speech_output": True,
}


def _get_settings_file_path() -> Path:
    """Ermittelt den Pfad zur settings.json des aktiven Profils."""
    profile_path = PROFILES_DIR / get_active_profile()
    profile_path.mkdir(exist_ok=True)
    return profile_path / "settings.json"


def load_settings() -> dict:
    """
    Lädt die Einstellungen des aktiven Profils.
    Fehlende Schlüssel werden mit Standardwerten aufgefüllt.
    """
    settings_file = _get_settings_file_path()

    # Kopie der Standardwerte als Basis
    settings = DEFAULT_SETTINGS.copy()

    if not settings_file.exists():
        return settings

    try:
        content = settings_file.read_text(encoding="utf-8").strip()
        if content:
            # Geladene Werte überschreiben die Standardwerte
            settings.update(json.loads(content))
    except (json.JSONDecodeError, IOError):
        pass

    return settings


def save_settings(settings: dict) -> None:
    """Speichert die Einstellungen für das aktive Profil."""
    settings_file = _get_settings_file_path()
    settings_file.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )