"""
Melvin Admin Store
------------------
Speichert die Admin-PIN sicher als SHA-256 Hash.
Die PIN wird NIE im Klartext gespeichert.
"""

import json
import hashlib
from pathlib import Path

ADMIN_FILE = Path(__file__).parent / "assistant" / "storage" / "admin.json"


def _hash_pin(pin: str) -> str:
    """Hasht die PIN mit SHA-256."""
    return hashlib.sha256(pin.encode()).hexdigest()


def admin_exists() -> bool:
    """Prüft ob bereits ein Admin-Account existiert."""
    if not ADMIN_FILE.exists():
        return False
    try:
        data = json.loads(ADMIN_FILE.read_text(encoding="utf-8"))
        return "pin_hash" in data
    except:
        return False


def set_admin_pin(pin: str) -> None:
    """Setzt eine neue Admin-PIN (gehasht gespeichert)."""
    ADMIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"pin_hash": _hash_pin(pin)}
    ADMIN_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def verify_admin_pin(pin: str) -> bool:
    """Prüft ob die eingegebene PIN korrekt ist."""
    if not admin_exists():
        return False
    try:
        data = json.loads(ADMIN_FILE.read_text(encoding="utf-8"))
        return data.get("pin_hash") == _hash_pin(pin)
    except:
        return False