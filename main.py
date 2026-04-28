import time
import threading
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification  # --- NEUER IMPORT

# Umgebungsvariablen so früh wie möglich laden
load_dotenv()

from assistant.agent import create_assistant
# --- NEUE IMPORTS für die Überwachung ---
from assistant.storage.reminder_store import load_reminders, save_reminders


# --- NEUE FUNKTION: Der Hintergrund-Wächter ---
def check_reminders():
    """Diese Funktion läuft endlos im Hintergrund."""
    while True:
        reminders = load_reminders()
        now = datetime.now()
        something_changed = False

        for reminder in reminders:
            # Prüfen, ob eine Erinnerung fällig und noch nicht erledigt ist
            reminder_time = datetime.fromisoformat(reminder["time"])
            if not reminder.get("done", False) and now >= reminder_time:
                print(f"\n🔔 ERINNERUNG WIRD AUSGELÖST: {reminder['text']}\n")

                # Desktop-Benachrichtigung senden
                notification.notify(
                    title='Erinnerung',
                    message=reminder['text'],
                    app_name='Desktop Assistant',
                    timeout=15  # Benachrichtigung bleibt 15 Sek. sichtbar
                )

                # Erinnerung als erledigt markieren
                reminder["done"] = True
                something_changed = True

        # Nur speichern, wenn sich etwas geändert hat, um unnötige Schreibzugriffe zu vermeiden
        if something_changed:
            save_reminders(reminders)

        # 60 Sekunden warten bis zur nächsten Prüfung
        time.sleep(60)


if __name__ == "__main__":
    # --- NEU: Starten des Hintergrund-Threads ---
    # daemon=True sorgt dafür, dass der Thread sich beendet, wenn das Hauptprogramm schließt
    reminder_thread = threading.Thread(target=check_reminders, daemon=True)
    reminder_thread.start()

    # Ab hier der bekannte Teil für die Benutzereingabe
    ki_assistant = create_assistant()
    print("KI Desktop Assistant ist bereit. Hintergrund-Überwachung ist aktiv.")
    print("Stellen Sie Ihre Frage (beenden mit 'exit').")

    while True:
        user_input = input("Ihre Frage: ")
        if user_input.lower() == 'exit':
            print("Auf Wiedersehen!")
            break

        result = ki_assistant.invoke({"input": user_input})
        print("\nAntwort des Assistenten:")
        print(result['output'])
        print("-" * 20)