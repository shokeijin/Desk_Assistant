from langchain.tools import tool
from assistant.storage.settings_store import load_settings, save_settings


@tool
def change_agent_name(new_name: str) -> str:
    """
    Ändert den Namen (Wake Word), auf den der Assistent hört.
    Der Nutzer muss den Assistenten danach mit dem neuen Namen ansprechen.
    """
    if not new_name:
        return "❌ Bitte gib einen gültigen Namen an."

    settings = load_settings()
    old_name = settings.get("agent_name", "Malvin")
    settings["agent_name"] = new_name
    save_settings(settings)

    return f"✅ Okay, ab jetzt höre ich auf den Namen '{new_name}'. Mein alter Name war '{old_name}'."