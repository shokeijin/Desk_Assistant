import re
import time
import threading
import speech_recognition as sr
import edge_tts
import asyncio
import pygame
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification
from pathlib import Path

load_dotenv()

from assistant.agent import create_assistant
from assistant.storage.reminder_store import load_reminders, save_reminders
from assistant.storage.settings_store import load_settings, save_settings
from assistant import profile_manager

# ✅ WebSocket Bridge importieren
from websocket_bridge import start_bridge, set_state

# ==================================================
# 🔧 DEBUG & TEST EINSTELLUNGEN
# ==================================================
DEBUG_MODE = False
TEST_MODE  = False
# ==================================================

TTS_VOICE = "de-DE-ConradNeural"


def clean_for_speech(text: str) -> str:
    """Bereinigt Markdown damit Conrad sauber vorlesen kann."""
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'[^\x00-\x7FäöüÄÖÜß\s.,!?:;()\-]', '', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()


def speak(text: str):
    """Spricht Text mit Conrad vor und informiert die UI."""
    settings = load_settings()
    if not settings.get("use_speech_output", True):
        return

    cleaned = clean_for_speech(text)
    if not cleaned:
        return

    if DEBUG_MODE:
        print(f"[DEBUG] TTS: '{cleaned[:80]}...'")

    # ✅ UI: Sprechen-Zustand + Text anzeigen
    set_state("speaking", text=text)

    async def _speak():
        communicate = edge_tts.Communicate(cleaned, TTS_VOICE)
        tmp_file = Path("_tts_output.mp3")
        await communicate.save(str(tmp_file))
        pygame.mixer.init()
        pygame.mixer.music.load(str(tmp_file))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.quit()
        tmp_file.unlink(missing_ok=True)

    try:
        asyncio.run(_speak())
    except Exception as e:
        print(f"[FEHLER] Sprachausgabe fehlgeschlagen: {e}")

    # ✅ UI: Nach dem Sprechen zurück zu Idle
    set_state("idle")


recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.5
microphone = sr.Microphone()


def listen(prompt="", show_feedback=True):
    """Nimmt Audio auf und wandelt es in Text um."""
    if TEST_MODE:
        if prompt:
            print(prompt)
        return input("  [TEST] Eingabe: ").lower()

    with microphone as source:
        if prompt:
            print(prompt)
        try:
            if show_feedback:
                print("Höre zu...")
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=30)
            if show_feedback:
                print("Erkenne Sprache...")
            text = recognizer.recognize_google(audio, language="de-DE")
            return text.lower()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            print("[FEHLER] Spracherkennung nicht erreichbar.")
            return ""


def check_reminders():
    """Läuft im Hintergrund und prüft Erinnerungen."""
    while True:
        try:
            profile_manager.get_active_profile()
        except ValueError:
            time.sleep(10)
            continue
        try:
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
                    print(f"[REMINDER] {notification_text}")
                    reminder["done"] = True
                    something_changed = True
            if something_changed:
                save_reminders(reminders)
        except Exception as e:
            print(f"[FEHLER] Reminder-Prüfung fehlgeschlagen: {e}")
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
    # ✅ WebSocket Bridge starten (vor allem anderen)
    start_bridge()
    time.sleep(0.5)

    setup_profile()
    settings = load_settings()
    wake_word = settings.get("agent_name", "melvin").lower()

    reminder_thread = threading.Thread(target=check_reminders, daemon=True)
    reminder_thread.start()

    try:
        ki_assistant = create_assistant()
    except Exception as e:
        print(f"[KRITISCHER FEHLER] Assistent konnte nicht gestartet werden: {e}")
        print("Bitte prüfe deine .env Datei und API-Keys.")
        exit(1)

    if not TEST_MODE:
        with microphone as source:
            print("Kalibriere Mikrofon für Umgebungsgeräusche...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Kalibrierung abgeschlossen.")

    set_state("idle")

    if TEST_MODE:
        print("⚠️  TEST MODE AKTIV – Tastatur wird genutzt.")
    else:
        speak(f"Assistent für Profil {profile_manager.get_active_profile()} ist bereit. Ich höre auf den Namen {wake_word}.")

    print(f"Assistent bereit. Sage '{wake_word}', um einen Befehl zu starten.")
    print("--------------------------------------------------")

    while True:
        heard_text = listen(show_feedback=False)

        if DEBUG_MODE and heard_text:
            print(f"[DEBUG] Gehört: '{heard_text}' | Wake-Word: '{wake_word}'")

        if wake_word in heard_text:
            command = heard_text.replace(wake_word, "").strip()

            if command:
                print(f"-> Befehl: '{command}'")
            else:
                speak("Ja?")
                time.sleep(0.8)
                set_state("listening")
                command = listen(prompt="\nIch höre... was ist Ihr Befehl?", show_feedback=True)

            if not command:
                set_state("idle")
                speak("Ich habe nichts verstanden.")
                continue

            if command.lower() == 'exit':
                speak("Auf Wiedersehen!")
                break

            # ✅ UI: Denken
            set_state("thinking")

            try:
                result = ki_assistant.invoke({"input": command})
                output = result.get('output', 'Ich habe leider keine Antwort darauf.')
            except ConnectionError:
                output = "Ich habe gerade keine Internetverbindung."
                print("[FEHLER] Keine Verbindung zur API.")
            except TimeoutError:
                output = "Die Anfrage hat zu lange gedauert."
                print("[FEHLER] API Timeout.")
            except Exception as e:
                output = "Es ist ein Fehler aufgetreten. Bitte versuche es erneut."
                print(f"[FEHLER] Unbekannter Fehler: {e}")

            print(f"<- Antwort: {output}")
            speak(output)