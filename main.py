import time
import threading
import speech_recognition as sr
import pyttsx3
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification
from pathlib import Path

# Umgebungsvariablen so früh wie möglich laden
load_dotenv()

# Eigene Module importieren
from assistant.agent import create_assistant
from assistant.storage.reminder_store import load_reminders, save_reminders
from assistant.storage.settings_store import load_settings, save_settings
from assistant import profile_manager

# --- Setup für TTS und STT ---
tts_engine = pyttsx3.init()


def speak(text):
    settings = load_settings()
    if settings.get("use_speech_output", True):
        tts_engine.say(text)
        tts_engine.runAndWait()


recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.0
microphone = sr.Microphone()


# --- MODIFIZIERTE LISTEN-FUNKTION ---
def listen(prompt="", show_feedback=True):
    """
    Nimmt Audio auf und wandelt es in Text um.
    Die Feedback-Ausgaben können jetzt abgeschaltet werden.
    """
    with microphone as source:
        if prompt:
            print(prompt)

        try:
            # Nur Feedback anzeigen, wenn gewünscht
            if show_feedback:
                print("Höre zu...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            if show_feedback:
                print("Erkenne Sprache...")
            text = recognizer.recognize_google(audio, language="de-DE")
            return text.lower()
        except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError):
            return ""


# --- Vollständige Hilfsfunktionen (unverändert) ---
def check_reminders():
    """Diese Funktion läuft endlos im Hintergrund und prüft Erinnerungen."""
    while True:
        try:
            profile_manager.get_active_profile()
        except ValueError:
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
                save_settings({})
                return
            else:
                print("Bitte wähle ein existierendes Profil.")
                continue


# --- Hauptprogramm ---
if __name__ == "__main__":
    setup_profile()
    settings = load_settings()
    wake_word = settings.get("agent_name", "melvin").lower()
    reminder_thread = threading.Thread(target=check_reminders, daemon=True)
    reminder_thread.start()
    ki_assistant = create_assistant()

    # ✅ FIX: Kalibrierung in eigenem with-Block durchführen.
    # Das Mikrofon wird danach wieder freigegeben, sodass listen() es nutzen kann.
    with microphone as source:
        print("Kalibriere Mikrofon für Umgebungsgeräusche...")
        recognizer.adjust_for_ambient_noise(source, duration=2)
    # ↑ Einzug entfernt – print ist jetzt AUSSERHALB des with-Blocks
    print("Kalibrierung abgeschlossen.")

    speak(f"Assistent für Profil {profile_manager.get_active_profile()} ist bereit. Ich höre auf den Namen {wake_word}.")
    print(f"Assistent bereit. Sage '{wake_word}', um einen Befehl zu starten.")
    print("--------------------------------------------------")

    while True:
        # Wir lauschen jetzt still im Hintergrund (show_feedback=False)
        heard_text = listen(show_feedback=False)

        if wake_word in heard_text:
            speak("Ja?")
            # Für den Befehl wollen wir das Feedback wieder sehen
            command = listen(prompt="\nIch höre... was ist Ihr Befehl?", show_feedback=True)

            if not command:
                speak("Ich habe nichts verstanden.")
                continue

            if command.lower() == 'exit':
                speak("Auf Wiedersehen!")
                break

            print(f"-> Befehl: '{command}'")
            result = ki_assistant.invoke({"input": command})

            output = result.get('output', 'Ich habe leider keine Antwort darauf.')
            print(f"<- Antwort: {output}")
            speak(output)
'''
#Debug Version
while True:
    heard_text = listen(show_feedback=False)

    # 🔍 DEBUG: Zeigt was erkannt wurde
    if heard_text:
        print(f"[DEBUG] Gehört: '{heard_text}' | Wake-Word: '{wake_word}'")

    if wake_word in heard_text:
        speak("Ja?")
        command = listen(prompt="\nIch höre... was ist Ihr Befehl?", show_feedback=True)

        if not command:
            speak("Ich habe nichts verstanden.")
            continue

        if command.lower() == 'exit':
            speak("Auf Wiedersehen!")
            break

        print(f"-> Befehl: '{command}'")
        result = ki_assistant.invoke({"input": command})

        output = result.get('output', 'Ich habe leider keine Antwort darauf.')
        print(f"<- Antwort: {output}")
        speak(output)
'''