"""
Einstellungs-Tools
==================
LangChain-Tool zum Ändern der Assistent-Einstellungen per Sprache.
Ermöglicht dem Nutzer z.B. das Wake-Word während der Laufzeit zu ändern.
"""

from langchain.tools import tool

from assistant.storage.settings_store import load_settings, save_settings


@tool
def change_agent_name(new_name: str) -> str:
    """
    Ändert das Wake-Word auf das der Assistent hört.
    Der neue Name wird lowercase gespeichert und gilt ab dem nächsten Start.
    Beispiel: "Jarvis" → Melvin hört ab sofort auf "jarvis".
    """
    if not new_name:
        return "❌ Bitte gib einen gültigen Namen an."

    settings = load_settings()
    old_name = settings.get("agent_name", "melvin")
    settings["agent_name"] = new_name.lower().strip()
    save_settings(settings)

    return (
        f"✅ Okay, ab jetzt höre ich auf den Namen '{new_name}'. "
        f"Mein alter Name war '{old_name}'."
    )