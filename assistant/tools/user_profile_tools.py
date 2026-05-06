"""
Benutzerprofil-Tools
====================
LangChain-Tools zum Anzeigen und Aktualisieren persönlicher Daten.
Ermöglicht dem KI-Agenten, Informationen über den Nutzer zu speichern
und abzurufen (z.B. Name, Alter, Beruf, Standort).
"""

from langchain.tools import tool

from assistant.storage.user_profile_store import load_user_profile, save_user_profile


@tool
def show_user_profile(dummy: str = "") -> str:
    """Zeigt alle gespeicherten persönlichen Daten des Nutzers an."""
    profile = load_user_profile()

    if not profile:
        return "👤 Noch kein Benutzerprofil gespeichert."

    eintraege = "\n".join(f"- {k}: {v}" for k, v in profile.items())
    return f"👤 Dein Profil:\n{eintraege}"


@tool
def update_user_profile(input_text: str) -> str:
    """
    Aktualisiert einen Eintrag im Benutzerprofil.
    Format: schluessel=wert
    Beispiele: name=Andi | alter=25 | beruf=Entwickler
    """
    if "=" not in input_text:
        return "❌ Format: schluessel=wert (z.B. name=Andi)"

    key, value = input_text.split("=", 1)
    key = key.strip()
    value = value.strip()

    profile = load_user_profile()
    profile[key] = value
    save_user_profile(profile)

    return f"✅ Profil aktualisiert: {key} = {value}"