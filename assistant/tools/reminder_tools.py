"""
Reminder-Tools
==============
LangChain-Tools für die Verwaltung von Erinnerungen.
Werden vom KI-Agenten aufgerufen wenn der Nutzer Erinnerungen
setzen, anzeigen oder löschen möchte.

Datumsformat für neue Erinnerungen: "Text | YYYY-MM-DD HH:MM"
"""

from datetime import datetime

from langchain.tools import tool

from assistant.storage.reminder_store import load_reminders, save_reminders


@tool
def add_reminder(input_text: str) -> str:
    """
    Erstellt eine neue Erinnerung mit Datum und Uhrzeit.
    Erwartetes Format: "<Text> | YYYY-MM-DD HH:MM"
    Beispiel: "Arzttermin | 2026-06-15 09:30"
    """
    try:
        text, datetime_str = input_text.split("|")
        text = text.strip()
        datetime_str = datetime_str.strip()
        remind_at = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return (
            "❌ Formatfehler. Bitte so angeben:\n"
            "Text | YYYY-MM-DD HH:MM\n"
            "Beispiel: Arzttermin | 2026-06-15 09:30"
        )

    reminders = load_reminders()
    reminders.append({
        "text": text,
        "time": remind_at.isoformat(),
        "done": False,
    })
    save_reminders(reminders)
    return f"⏰ Erinnerung gesetzt: {text} am {datetime_str}"


@tool
def list_reminders(dummy: str = "") -> str:
    """Zeigt alle Erinnerungen mit Status und Zeitpunkt an."""
    reminders = load_reminders()

    if not reminders:
        return "📭 Keine Erinnerungen vorhanden."

    now = datetime.now()
    lines = []

    for i, reminder in enumerate(reminders):
        time_obj = datetime.fromisoformat(reminder["time"])
        time_str = time_obj.strftime("%d.%m.%Y %H:%M")

        if reminder.get("done", False):
            status = "✅ (Erledigt)"
        elif time_obj < now:
            status = "🕒 (Vergangenheit)"
        else:
            status = ""

        lines.append(f"{i + 1}. {time_str} – {reminder['text']} {status}".strip())

    return "⏰ Deine Erinnerungen:\n" + "\n".join(lines)


@tool
def delete_reminder(input_text: str) -> str:
    """
    Löscht eine Erinnerung anhand ihrer Nummer in der Liste.
    Erwartet eine einzelne Zahl als Eingabe, z.B. "1".
    """
    reminders = load_reminders()

    try:
        index = int(input_text.strip()) - 1
        removed = reminders.pop(index)
        save_reminders(reminders)
        return f"🗑️ Erinnerung gelöscht: {removed['text']}"
    except (ValueError, IndexError):
        return "❌ Bitte gib eine gültige Nummer der Erinnerung an."