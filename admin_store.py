"""
Admin-Store
===========
Verwaltung der Admin-PIN für das Admin-Panel.
Die PIN wird ausschließlich als SHA-256-Hash gespeichert –
der Klartext verlässt niemals den Arbeitsspeicher.
"""

import hashlib
import json
from pathlib import Path

# Speicherort der gehashten Admin-PIN, relativ zu dieser Datei
ADMIN_FILE = Path(__file__).parent / "assistant" / "storage" / "admin.json"


def _hash_pin(pin: str) -> str:
    """Gibt den SHA-256-Hash der PIN als Hex-String zurück."""
    return hashlib.sha256(pin.encode()).hexdigest()


def admin_exists() -> bool:
    """Gibt True zurück wenn bereits ein Admin-Account angelegt wurde."""
    if not ADMIN_FILE.exists():
        return False
    try:
        data = json.loads(ADMIN_FILE.read_text(encoding="utf-8"))
        return "pin_hash" in data
    except (json.JSONDecodeError, IOError):
        return False


def set_admin_pin(pin: str) -> None:
    """
    Speichert eine neue Admin-PIN als SHA-256-Hash.
    Überschreibt eine vorhandene PIN ohne Rückfrage.
    """
    ADMIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"pin_hash": _hash_pin(pin)}
    ADMIN_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def verify_admin_pin(pin: str) -> bool:
    """Gibt True zurück wenn die eingegebene PIN mit dem gespeicherten Hash übereinstimmt."""
    if not admin_exists():
        return False
    try:
        data = json.loads(ADMIN_FILE.read_text(encoding="utf-8"))
        return data.get("pin_hash") == _hash_pin(pin)
    except (json.JSONDecodeError, IOError):
        return False