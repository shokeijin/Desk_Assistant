import time
import threading  # Der korrigierte Import
import speech_recognition as sr
import pyttsx3
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification
from pathlib import Path

# Umgebungsvariablen so früh wie möglich laden
load_dotenv()

# Eigene Module importieren, nachdem dotenv geladen wurde
from assistant.agent import create_assistant
from assistant.storage.reminder_store import load_reminders, save_reminders
from assistant import profile_manager

# --- SETUP FÜR SPRACHAUSGABE (TTS) ---
tts_engine = pyttsx3.init()


def speak(text):
    """Liest einen Text vor."""
    tts_engine.say(text)
    tts_engine.runAndWait()


# --- SETUP FÜR SPRACHERKENNUNG (STT) ---
recognizer = sr.Recognizer()
microphone = sr.Microphone()


def listen_for_command():
    """Hört auf einen Befehl über das Mikrofon und gibt ihn als Text zurück."""
    with microphone as source:
        print("\nKalibriere für Umgebungsgeräusche...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Höre zu...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Erkenne Sprache...")
            text = recognizer.recognize_google(audio, language="de-DE")
            print(f"Du hast gesagt: {text}")
            return text
        except sr.WaitTimeoutError:
            print("Keine Spracheingabe erkannt. Bitte erneut versuchen.")
            return None
        except sr.UnknownValueError:
            print("Konnte dich leider nicht verstehen.")
            return None
        except sr.RequestError as e:
            print(f"Fehler bei der Anfrage an Google Speech Recognition; {e}")
            return None


def check_reminders():
    """Diese Funktion läuft endlos im Hintergrund."""
    while True:
        try:
            # Dieser Block stellt sicher, dass die Funktion erst startet,
            # nachdem ein Profil geladen wurde.
            profile_manager.get_active_profile()
        except ValueError:
            # Noch kein Profil aktiv, 10 Sekunden warten und erneut versuchen
            time.sleep(10)
            continue

        reminders = load_reminders()
        now = datetime.now()
        something_changed = False

        for reminder in reminders:
            reminder_time = datetime.fromisoformat(reminder["time"])
            if not reminder.get("done", False) and now >= reminder_time:
                notification_text = f"Erinnerung: {reminder['text']}"
                print(f"\n🔔 {notification_text}\n")
                notification.notify(
                    title='Desktop Assistant',
                    message=reminder['text'],
                    app_name='Desktop Assistant',
                    timeout=15
                )
                speak(notification_text)
                reminder["done"] = True
                something_changed = True

        if something_changed:
            save_reminders(reminders)
        time.sleep(60)


def setup_profile():
    """Fragt den Benutzer nach seinem Profil und erstellt es ggf."""
    profiles_path = Path(__file__).parent / "assistant" / "storage" / "profiles"
    profiles_path.mkdir(exist_ok=True)

    existing_profiles = [p.name for p in profiles_path.iterdir() if p.is_dir()]

    if existing_profiles:
        print("Verfügbare Profile: " + ", ".join(existing_profiles))

    while True:
        profile_name = input("Bitte gib deinen Profilnamen ein: ").strip()
        if not profile_name:
            print("Der Name darf nicht leer sein.")
            continue

        if profile_name in existing_profiles:
            profile_manager.set_active_profile(profile_name)
            return
        else:
            create_new = input(f"Profil '{profile_name}' nicht gefunden. Möchtest du es erstellen? (j/n): ").lower()
            if create_new == 'j':
                (profiles_path / profile_name).mkdir()
                profile_manager.set_active_profile(profile_name)
                return
            else:
                print("Bitte wähle ein existierendes Profil.")
                continue


if __name__ == "__main__":
    setup_profile()

    reminder_thread = threading.Thread(target=check_reminders, daemon=True)
    reminder_thread.start()

    ki_assistant = create_assistant()

    use_speech_input = input("Spracheingabe aktivieren? (j/n): ").lower() == 'j'

    if use_speech_input:
        speak("Desktop Assistent ist bereit und hört zu.")
        print("Desktop Assistent ist bereit und hört zu.")
    else:
        speak("Desktop Assistent ist bereit.")
        print("Desktop Assistent ist bereit. Hintergrund-Überwachung ist aktiv.")

    print("Beenden mit 'exit' (getippt oder gesprochen).")

    while True:
        user_input = None
        if use_speech_input:
            user_input = listen_for_command()
        else:
            user_input = input("\nIhre Frage: ")

        if user_input is None:
            continue

        if user_input.lower() == 'exit':
            speak("Auf Wiedersehen!")
            print("Auf Wiedersehen!")
            break

        result = ki_assistant.invoke({"input": user_input})

        print("\nAntwort des Assistenten:")
        print(result['output'])

        speak(result['output'])

        print("-" * 20)