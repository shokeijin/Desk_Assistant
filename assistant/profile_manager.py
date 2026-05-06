"""
Profil-Manager
==============
Verwaltet das aktuell aktive Nutzerprofil für die laufende Sitzung.
Das aktive Profil wird beim Start gesetzt und von allen Store-Modulen
verwendet, um die korrekten Datenpfade zu ermitteln.
"""

# Interner Speicher für den aktuell aktiven Profilnamen
_active_profile: str | None = None


def set_active_profile(profile_name: str) -> None:
    """
    Setzt das aktive Profil für die aktuelle Sitzung.
    Muss vor dem ersten Zugriff auf Store-Funktionen aufgerufen werden.
    """
    global _active_profile
    _active_profile = profile_name
    print(f"✅ Profil '{profile_name}' ist jetzt aktiv.")


def get_active_profile() -> str:
    """
    Gibt den Namen des aktuell aktiven Profils zurück.
    Wirft einen ValueError wenn noch kein Profil gesetzt wurde.
    """
    if _active_profile is None:
        raise ValueError("Es wurde kein aktives Profil gesetzt!")
    return _active_profile