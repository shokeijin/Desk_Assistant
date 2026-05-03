import json
from pathlib import Path
from assistant.profile_manager import get_active_profile

PROFILES_DIR = Path(__file__).parent / "profiles"


def _get_settings_file_path() -> Path:
    """Ermittelt den Pfad zur settings.json des aktiven Profils."""
    active_user = get_active_profile()
    profile_path = PROFILES_DIR / active_user
    profile_path.mkdir(exist_ok=True)
    return profile_path / "settings.json"


def load_settings() -> dict:
    """Lädt die Einstellungen und gibt Standardwerte zurück, wenn keine vorhanden sind."""
    settings_file = _get_settings_file_path()

    # Standard-Einstellungen, falls die Datei nicht existiert
    defaults = {
        "agent_name": "Melvin",
        "use_speech_output": True
    }

    if not settings_file.exists():
        return defaults

    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return defaults
            # Geladene Einstellungen mit den Defaults zusammenführen
            # (falls später neue Einstellungen hinzukommen)
            loaded_settings = json.loads(content)
            defaults.update(loaded_settings)
            return defaults
    except (json.JSONDecodeError, IOError):
        return defaults


def save_settings(settings: dict) -> None:
    """Speichert die Einstellungen für das aktive Profil."""
    settings_file = _get_settings_file_path()
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)