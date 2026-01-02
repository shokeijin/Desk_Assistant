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
    reminders.append({
        "text": text,
        "time": remind_at.isoformat(),
        "done": False
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
    for i, r in enumerate(reminders):
        time = datetime.fromisoformat(r["time"]).strftime("%d.%m.%Y %H:%M")
        lines.append(f"{i+1}. {time} – {r['text']}")

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
        return f"🗑️ Erinnerung gelöscht: {removed}"
    except ValueError:
        return "❌ Bitte gib eine gültige Nummer an (z.B. 1)."
    except IndexError:
        return "❌ Diese Aufgabe existiert nicht."
