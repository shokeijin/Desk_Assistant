import re
import time
import threading
import speech_recognition as sr
import edge_tts
import asyncio
import pygame
import keyboard
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification
from pathlib import Path



load_dotenv()

from assistant.agent import create_assistant
from assistant.storage.reminder_store import load_reminders, save_reminders
from assistant.storage.settings_store import load_settings, save_settings
from assistant import profile_manager
from websocket_bridge import start_bridge, set_state
from admin_store import admin_exists, set_admin_pin, verify_admin_pin
from admin_panel import run_admin_panel

# ==================================================
# 🔧 DEBUG & TEST EINSTELLUNGEN
# ==================================================
DEBUG_MODE = True
TEST_MODE  = False
# ==================================================

TTS_VOICE = "de-DE-ConradNeural"
_admin_triggered = False


def clean_for_speech(text: str) -> str:
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'[^\x00-\x7FäöüÄÖÜß\s.,!?:;()\-]', '', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()


def speak(text: str):
    try:
        settings = load_settings()
        if not settings.get("use_speech_output", True):
            return
    except ValueError:
        pass

    cleaned = clean_for_speech(text)
    if not cleaned:
        return

    if DEBUG_MODE:
        print(f"[DEBUG] TTS: '{cleaned[:80]}...'")

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

    set_state("idle")


recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.5
microphone = sr.Microphone()


def listen(prompt="", show_feedback=True):
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


def listen_for_name() -> str:
    with microphone as source:
        try:
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=5)
            text = recognizer.recognize_google(audio, language="de-DE")
            name = text.strip().split()[0].capitalize()
            return name
        except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError):
            return ""


# =====================
# ✅ ADMIN HOTKEY (F12)
# =====================

def _on_f12():
    """Wird aufgerufen wenn F12 gedrückt wird."""
    global _admin_triggered
    _admin_triggered = True


def _setup_admin_pin():
    """Einmalige PIN-Einrichtung beim ersten Start."""
    print("\n🔐 Kein Admin-Account gefunden.")
    print("Bitte richte jetzt eine 6-stellige Admin-PIN ein.")
    while True:
        pin = input("Neue PIN (6 Ziffern): ").strip()
        if len(pin) != 6 or not pin.isdigit():
            print("❌ Bitte genau 6 Ziffern eingeben.")
            continue
        confirm = input("PIN bestätigen: ").strip()
        if pin != confirm:
            print("❌ PINs stimmen nicht überein.")
            continue
        set_admin_pin(pin)
        print("✅ Admin-PIN wurde gesetzt.\n")
        return


def _check_admin_trigger():
    """Prüft ob F12 gedrückt wurde und startet Admin-Panel."""
    global _admin_triggered
    if not _admin_triggered:
        return
    _admin_triggered = False

    print("\n🔐 Admin-Modus: PIN eingeben")
    pin = input("PIN: ").strip()

    if verify_admin_pin(pin):
        print("✅ Zugriff gewährt.")
        run_admin_panel()
    else:
        print("❌ Falsche PIN. Zugriff verweigert.")


def check_reminders():
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
    profiles_path = Path(__file__).parent / "assistant" / "storage" / "profiles"
    profiles_path.mkdir(exist_ok=True)
    existing_profiles = [p.name for p in profiles_path.iterdir() if p.is_dir()]

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    while True:
        if existing_profiles:
            profiles_str = ", ".join(existing_profiles)
            speak(f"Willkommen! Bekannte Profile sind: {profiles_str}. Wer bist du?")
        else:
            speak("Willkommen! Ich kenne dich noch nicht. Wie heißt du?")

        print("👂 Warte auf Namenseingabe (Sprache oder Tastatur)...")
        profile_name = listen_for_name()

        if not profile_name:
            speak("Ich habe dich nicht verstanden. Bitte tippe deinen Namen ein.")
            profile_name = input("Name: ").strip().capitalize()

        if not profile_name:
            speak("Der Name darf nicht leer sein. Bitte versuche es nochmal.")
            continue

        print(f"[DEBUG] Erkannter Name: '{profile_name}'")

        # Fuzzy-Matching
        for existing in existing_profiles:
            if existing.lower() == profile_name.lower():
                profile_name = existing
                break
            if len(existing) >= 3 and len(profile_name) >= 3:
                if existing.lower()[:3] == profile_name.lower()[:3]:
                    print(f"[DEBUG] Fuzzy Match: '{profile_name}' → '{existing}'")
                    profile_name = existing
                    break

        if profile_name in existing_profiles:
            profile_manager.set_active_profile(profile_name)
            speak(f"Schön dich wiederzusehen, {profile_name}!")
            return
        else:
            speak(f"Ich kenne {profile_name} noch nicht. Soll ich ein neues Profil erstellen?")
            print("Neues Profil erstellen? (ja/nein)")
            answer = listen_for_name().lower()
            if not answer:
                answer = input("(ja/nein): ").strip().lower()

            if answer in ["ja", "j", "yes"]:
                (profiles_path / profile_name).mkdir()
                profile_manager.set_active_profile(profile_name)
                save_settings({})
                speak(f"Perfekt! Ich habe ein Profil für {profile_name} erstellt. Schön dich kennenzulernen!")
                return
            else:
                speak("Okay, lass es uns nochmal versuchen.")
                continue


# --- Hauptprogramm ---
if __name__ == "__main__":
    start_bridge()
    time.sleep(0.5)

    # ✅ Admin PIN einrichten falls noch nicht vorhanden
    if not admin_exists():
        _setup_admin_pin()

    # ✅ F12 Hotkey registrieren
    keyboard.on_press_key("f12", lambda _: _on_f12())
    print("[ADMIN] F12 registriert – Admin-Panel jederzeit erreichbar.")

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
    speak(f"Alles bereit. Ich höre auf den Namen {wake_word}.")

    print(f"Assistent bereit. Sage '{wake_word}', um einen Befehl zu starten.")
    print("--------------------------------------------------")

    while True:
        # ✅ Admin-Trigger prüfen
        _check_admin_trigger()

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