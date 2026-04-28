from langchain.tools import tool
from datetime import datetime
from assistant.storage.reminder_store import load_reminders, save_reminders


@tool
def add_reminder(input_text: str) -> str:
    """
    Erstellt eine Erinnerung.
    Erwartetes Format:
    "<Text> | YYYY-MM-DD HH:MM"
    """
    try:
        text, datetime_str = input_text.split("|")
        text = text.strip()
        datetime_str = datetime_str.strip()
        remind_at = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return (
            "❌ Formatfehler.\n"
            "Bitte so angeben:\n"
            "Text | YYYY-MM-DD HH:MM\n"
            "Beispiel:\n"
            "Arzttermin | 2026-01-12 09:30"
        )

    reminders = load_reminders()

    # --- ÄNDERUNG HIER: 'done' Flag hinzufügen ---
    reminders.append({
        "text": text,
        "time": remind_at.isoformat(),
        "done": False  # Wichtig für den neuen Überwachungsprozess
    })

    save_reminders(reminders)
    return f"⏰ Erinnerung gesetzt: {text} am {datetime_str}"


@tool
def list_reminders(dummy: str = "") -> str:
    """Listet alle Erinnerungen auf."""
    reminders = load_reminders()
    if not reminders:
        return "📭 Keine Erinnerungen vorhanden."

    lines = []
    now = datetime.now()
    for i, r in enumerate(reminders):
        time_obj = datetime.fromisoformat(r["time"])
        time_str = time_obj.strftime("%d.%m.%Y %H:%M")

        # --- ÄNDERUNG HIER: Visueller Hinweis für den Status ---
        status = ""
        if r.get("done", False):
            status = "✅ (Erledigt)"
        elif time_obj < now:
            status = "🕒 (Vergangenheit)"

        lines.append(f"{i + 1}. {time_str} – {r['text']} {status}")

    return "⏰ Deine Erinnerungen:\n" + "\n".join(lines)


@tool
def delete_reminder(input_text: str) -> str:
    """
    Löscht eine Aufgabe anhand ihrer Nummer.
    Erwartet eine Zahl, z.B. "1"
    """
    reminders = load_reminders()
    try:
        index = int(input_text.strip())
        removed = reminders.pop(index - 1)
        save_reminders(reminders)
        return f"🗑️ Erinnerung gelöscht: {removed['text']}"
    except (ValueError, IndexError):
        return "❌ Bitte gib eine gültige Nummer der Erinnerung an."