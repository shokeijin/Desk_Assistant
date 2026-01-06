import os
from langchain.tools import tool
from assistant.storage.user_profile_store import (
    load_user_profile,
    save_user_profile
)


@tool
def show_user_profile(dummy: str = "") -> str:
    """Zeigt das aktuelle Benutzerprofil."""
    profile = load_user_profile()
    if not profile:
        return "👤 Noch kein Benutzerprofil gespeichert."
    return "👤 Dein Profil:\n" + "\n".join(
        f"- {k}: {v}" for k, v in profile.items()
    )


@tool
def update_user_profile(input_text: str) -> str:
    """
    Aktualisiert das Benutzerprofil.
    Format: key=value
    Beispiel: name=Andi
    """
    if "=" not in input_text:
        return "❌ Format: key=value (z.B. name=Andi)"

    key, value = input_text.split("=", 1)
    key = key.strip()
    value = value.strip()

    profile = load_user_profile()
    profile[key] = value
    save_user_profile(profile)

    return f"✅ Profil aktualisiert: {key} = {value}"
