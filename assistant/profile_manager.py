# --- NEUE DATEI: assistant/profile_manager.py ---

# Diese Variable speichert den Namen des aktuell aktiven Profils.
_active_profile = None

def set_active_profile(profile_name: str):
    """Setzt das globale aktive Profil für die Sitzung."""
    global _active_profile
    print(f"✅ Profil '{profile_name}' ist jetzt aktiv.")
    _active_profile = profile_name

def get_active_profile() -> str:
    """Gibt den Namen des aktiven Profils zurück."""
    if _active_profile is None:
        raise ValueError("Es wurde kein aktives Profil gesetzt!")
    return _active_profile