import json
from pathlib import Path

# --- NEU: Importieren des Profil-Managers ---
from assistant.profile_manager import get_active_profile

# Der Basispfad, der zum Ordner "storage" führt
BASE_STORAGE_DIR = Path(__file__).parent
PROFILES_DIR = BASE_STORAGE_DIR / "profiles"


def _get_data_file_path() -> Path:
    """Ermittelt den Pfad zur JSON-Datei des aktiven Profils."""
    active_user = get_active_profile()
    profile_path = PROFILES_DIR / active_user

    # Sicherstellen, dass der Ordner für das Profil existiert
    profile_path.mkdir(exist_ok=True)

    return profile_path / "user_profile.json"


def load_user_profile() -> dict:
    data_file = _get_data_file_path()
    if not data_file.exists():
        return {}

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return {}


def save_user_profile(profile: dict) -> None:
    data_file = _get_data_file_path()
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)