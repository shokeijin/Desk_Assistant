"""
Melvin – Hauptprogramm
======================
Einstiegspunkt des Assistenten. Koordiniert alle Komponenten:
  - WebSocket-Bridge zur Electron-UI
  - Spracheingabe (Google Speech-to-Text)
  - Sprachausgabe (Microsoft edge-tts, Conrad Neural)
  - Wake-Word-Erkennung und Befehlsverarbeitung
  - Profilverwaltung mit Sprach- und UI-Eingabe
  - Admin-Panel (F12 + 6-stellige PIN)
  - Hintergrund-Thread für fällige Erinnerungen

Starten: python main.py
Beenden: "Melvin, exit" sprechen
"""

import asyncio
import re
import threading
import time
from datetime import datetime
from pathlib import Path

import edge_tts
import keyboard
import pygame
import speech_recognition as sr
from dotenv import load_dotenv
from plyer import notification

# Umgebungsvariablen (API-Keys) so früh wie möglich laden
load_dotenv()

from admin_panel import run_admin_panel
from admin_store import admin_exists, set_admin_pin, verify_admin_pin
from assistant import profile_manager
from assistant.agent import create_assistant
from assistant.storage.reminder_store import load_reminders, save_reminders
from assistant.storage.settings_store import load_settings, save_settings
from websocket_bridge import _send, request_input, set_state, start_bridge

# ---------------------------------------------------------------------------
# Einstellungen – hier können Debug- und Testmodus umgeschaltet werden
# ---------------------------------------------------------------------------

# True: Zeigt erkannte Sprache und TTS-Ausgaben im Terminal an
DEBUG_MODE: bool = True

# True: Ersetzt das Mikrofon durch Tastatureingabe (nützlich zum Testen)
TEST_MODE: bool = False

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

# Microsoft Neural Voice für die Sprachausgabe (männlich, Deutsch)
TTS_VOICE: str = "de-DE-ConradNeural"

# Internes Flag das gesetzt wird wenn F12 gedrückt wurde
_admin_triggered: bool = False

# ---------------------------------------------------------------------------
# Sprach-Setup
# ---------------------------------------------------------------------------

recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True  # Passt sich automatisch an Umgebungslärm an
recognizer.pause_threshold = 1.5            # Sekunden Stille bis eine Aussage als beendet gilt
microphone = sr.Microphone()


# ---------------------------------------------------------------------------
# Sprachausgabe
# ---------------------------------------------------------------------------

def clean_for_speech(text: str) -> str:
    """
    Bereinigt einen Text von Markdown-Formatierung und Sonderzeichen,
    damit Conrad ihn flüssig vorlesen kann.
    """
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)   # Links: [Text](URL) → Text
    text = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', text)   # Fett/Kursiv: **Text** → Text
    text = re.sub(r'#+\s*', '', text)                         # Überschriften: ### → entfernen
    text = re.sub(r'[^\x00-\x7FäöüÄÖÜß\s.,!?:;()\-]', '', text)  # Emojis entfernen
    text = re.sub(r'\n{2,}', '\n', text)                      # Mehrfach-Leerzeilen reduzieren
    return text.strip()


def speak(text: str) -> None:
    """
    Liest einen Text mit der Conrad Neural Voice vor.
    Informiert gleichzeitig die UI über den Sprechen-Zustand.
    Funktioniert auch wenn noch kein Profil aktiv ist (z.B. beim Start).
    """
    # Sprachausgabe kann über die Einstellungen deaktiviert werden
    try:
        settings = load_settings()
        if not settings.get("use_speech_output", True):
            return
    except ValueError:
        pass  # Kein Profil gesetzt – trotzdem sprechen

    cleaned = clean_for_speech(text)
    if not cleaned:
        return

    if DEBUG_MODE:
        print(f"[DEBUG] TTS: '{cleaned[:80]}...'")

    # UI in den Sprechen-Zustand versetzen und Text anzeigen
    set_state("speaking", text=text)

    async def _generate_and_play() -> None:
        """Generiert die Audiodatei und spielt sie ab."""
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
        asyncio.run(_generate_and_play())
    except Exception as e:
        print(f"[FEHLER] Sprachausgabe fehlgeschlagen: {e}")

    set_state("idle")


# ---------------------------------------------------------------------------
# Spracheingabe
# ---------------------------------------------------------------------------

def listen(prompt: str = "", show_feedback: bool = True) -> str:
    """
    Nimmt eine Spracheingabe auf und gibt den erkannten Text zurück.
    Im TEST_MODE wird stattdessen eine Tastatureingabe verwendet.
    Gibt einen leeren String zurück wenn nichts erkannt wurde.
    """
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
            return recognizer.recognize_google(audio, language="de-DE").lower()
        except sr.WaitTimeoutError:
            return ""   # Keine Sprache innerhalb des Timeouts erkannt
        except sr.UnknownValueError:
            return ""   # Sprache erkannt aber nicht verstanden
        except sr.RequestError:
            print("[FEHLER] Google Spracherkennung nicht erreichbar.")
            return ""


def listen_for_name() -> str:
    """
    Spezialisierte Variante von listen() für die Profil-Auswahl beim Start.
    Gibt nur das erste Wort der Eingabe zurück, kapitalisiert als Eigenname.
    """
    with microphone as source:
        try:
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=5)
            text = recognizer.recognize_google(audio, language="de-DE")
            return text.strip().split()[0].capitalize()
        except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError):
            return ""


# ---------------------------------------------------------------------------
# Admin-Panel
# ---------------------------------------------------------------------------

def _on_f12(_event) -> None:
    """Callback für den F12-Hotkey – setzt das Admin-Trigger-Flag."""
    global _admin_triggered
    _admin_triggered = True


def _setup_admin_pin() -> None:
    """
    Führt die einmalige PIN-Einrichtung beim ersten Start durch.
    Der Nutzer gibt die PIN direkt in der UI ein.
    """
    speak("Kein Admin-Account gefunden. Bitte richte jetzt eine sechsstellige PIN ein.")

    while True:
        pin = request_input("Neue PIN (6 Ziffern):", input_type="pin", masked=True)

        if len(pin) != 6 or not pin.isdigit():
            set_state("idle", text="❌ Bitte genau 6 Ziffern eingeben.")
            time.sleep(1.5)
            continue

        confirm = request_input("PIN bestätigen:", input_type="pin", masked=True)

        if pin != confirm:
            set_state("idle", text="❌ PINs stimmen nicht überein. Nochmal versuchen.")
            time.sleep(1.5)
            continue

        set_admin_pin(pin)
        speak("Admin-PIN wurde erfolgreich gesetzt.")
        return


def _check_admin_trigger() -> None:
    """
    Prüft ob F12 gedrückt wurde und öffnet bei korrekter PIN das Admin-Panel.
    Wird in jedem Durchlauf der Hauptschleife aufgerufen.
    """
    global _admin_triggered

    if not _admin_triggered:
        return

    _admin_triggered = False

    set_state("idle", text="🔐 Admin-Modus – PIN eingeben:")
    pin = request_input("Admin PIN:", input_type="pin", masked=True)

    if verify_admin_pin(pin):
        speak("Zugriff gewährt. Admin Panel wird im Terminal geöffnet.")
        set_state("idle", text="✅ Admin Panel läuft im Terminal.")
        run_admin_panel()
        set_state("idle", text="Admin Panel geschlossen.")
    else:
        speak("Falsche PIN. Zugriff verweigert.")
        set_state("idle", text="❌ Falsche PIN. Zugriff verweigert.")


# ---------------------------------------------------------------------------
# Reminder-Überwachung
# ---------------------------------------------------------------------------

def check_reminders() -> None:
    """
    Hintergrund-Thread der jede Minute prüft ob eine Erinnerung fällig ist.
    Fällige Erinnerungen werden als Desktop-Benachrichtigung und per Sprache ausgegeben.
    """
    while True:
        # Warten bis ein Profil aktiv ist
        try:
            profile_manager.get_active_profile()
        except ValueError:
            time.sleep(10)
            continue

        try:
            reminders = load_reminders()
            now = datetime.now()
            changed = False

            for reminder in reminders:
                reminder_time = datetime.fromisoformat(reminder["time"])
                is_due = not reminder.get("done", False) and now >= reminder_time

                if is_due:
                    message = f"Erinnerung: {reminder['text']}"
                    print(f"\n🔔 {message}\n")

                    notification.notify(
                        title="Melvin – Erinnerung",
                        message=reminder["text"],
                        app_name="Melvin Desktop Assistant",
                        timeout=15,
                    )
                    speak(message)

                    reminder["done"] = True
                    changed = True

            if changed:
                save_reminders(reminders)

        except Exception as e:
            print(f"[FEHLER] Reminder-Prüfung fehlgeschlagen: {e}")

        time.sleep(60)


# ---------------------------------------------------------------------------
# Profil-Setup
# ---------------------------------------------------------------------------

def setup_profile() -> None:
    """
    Interaktive Profil-Auswahl beim Programmstart.
    Melvin fragt per Sprache nach dem Namen. Bei Misserfolg wird ein
    Eingabefeld in der UI geöffnet. Neue Profile können direkt angelegt werden.
    Fuzzy-Matching gleicht ähnliche Namen ab (z.B. "Andy" → "Andi").
    """
    profiles_path = (
        Path(__file__).parent / "assistant" / "storage" / "profiles"
    )
    profiles_path.mkdir(exist_ok=True)
    existing = [p.name for p in profiles_path.iterdir() if p.is_dir()]

    # Mikrofon einmalig kalibrieren bevor wir mit dem Nutzer sprechen
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    while True:
        # Begrüßung je nachdem ob bereits Profile existieren
        if existing:
            speak(f"Willkommen! Bekannte Profile: {', '.join(existing)}. Wer bist du?")
        else:
            speak("Willkommen! Ich kenne dich noch nicht. Wie heißt du?")

        set_state("listening")
        print("👂 Warte auf Namenseingabe...")
        name = listen_for_name()

        # Fallback auf UI-Eingabe wenn Sprache nicht erkannt wurde
        if not name:
            speak("Ich habe dich nicht verstanden.")
            name = request_input(
                "Bitte gib deinen Namen ein:", input_type="text"
            ).strip().capitalize()

        if not name:
            speak("Der Name darf nicht leer sein.")
            continue

        set_state("thinking")

        if DEBUG_MODE:
            print(f"[DEBUG] Erkannter Name: '{name}'")

        # Fuzzy-Matching: ersten 3 Buchstaben mit vorhandenen Profilen vergleichen
        # Verhindert Fehlerkennungen wie "Andy" statt "Andi"
        for existing_name in existing:
            if existing_name.lower() == name.lower():
                name = existing_name
                break
            if len(existing_name) >= 3 and len(name) >= 3:
                if existing_name.lower()[:3] == name.lower()[:3]:
                    if DEBUG_MODE:
                        print(f"[DEBUG] Fuzzy Match: '{name}' → '{existing_name}'")
                    name = existing_name
                    break

        if name in existing:
            profile_manager.set_active_profile(name)
            speak(f"Schön dich wiederzusehen, {name}!")
            return

        # Unbekanntes Profil – Nutzer fragen ob es angelegt werden soll
        speak(f"Ich kenne {name} noch nicht. Soll ich ein neues Profil erstellen?")
        answer = request_input(
            f"Profil '{name}' erstellen?", input_type="confirm"
        ).lower()

        if answer in ("ja", "j", "yes"):
            (profiles_path / name).mkdir()
            profile_manager.set_active_profile(name)
            save_settings({})
            speak(f"Perfekt! Profil für {name} erstellt. Schön dich kennenzulernen!")
            return

        speak("Okay, lass es uns nochmal versuchen.")


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # WebSocket-Server starten damit die UI sich verbinden kann
    start_bridge()
    time.sleep(0.5)

    # Admin-PIN beim ersten Start einrichten
    if not admin_exists():
        _setup_admin_pin()

    # F12-Hotkey für Admin-Panel registrieren
    keyboard.on_press_key("f12", _on_f12)
    print("[ADMIN] F12-Hotkey registriert – Admin-Panel jederzeit erreichbar.")

    # Profil auswählen oder neu anlegen
    setup_profile()

    settings = load_settings()
    wake_word = settings.get("agent_name", "melvin").lower()

    # Reminder-Überwachung im Hintergrund starten
    reminder_thread = threading.Thread(target=check_reminders, daemon=True)
    reminder_thread.start()

    # KI-Agenten initialisieren
    try:
        ki_assistant = create_assistant()
    except Exception as e:
        print(f"[KRITISCHER FEHLER] Assistent konnte nicht gestartet werden: {e}")
        print("Bitte prüfe deine .env-Datei und API-Keys.")
        raise SystemExit(1)

    # Mikrofon für den Betrieb kalibrieren
    if not TEST_MODE:
        with microphone as source:
            print("Kalibriere Mikrofon für Umgebungsgeräusche...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Kalibrierung abgeschlossen.")

    set_state("idle")
    speak(f"Alles bereit. Ich höre auf den Namen {wake_word}.")
    print(f"Assistent bereit. Sage '{wake_word}' um einen Befehl zu starten.")
    print("-" * 50)

    # Hauptschleife – wartet auf das Wake-Word
    while True:
        _check_admin_trigger()

        heard = listen(show_feedback=False)

        if DEBUG_MODE and heard:
            print(f"[DEBUG] Gehört: '{heard}' | Wake-Word: '{wake_word}'")

        if wake_word not in heard:
            continue

        # Wake-Word erkannt – Befehl extrahieren oder neu abhören
        command = heard.replace(wake_word, "").strip()

        if command:
            print(f"-> Befehl: '{command}'")
        else:
            # Nur Wake-Word gesagt – auf Befehl warten
            speak("Ja?")
            time.sleep(0.8)  # Warten bis Conrad fertig gesprochen hat
            set_state("listening")
            command = listen(prompt="\nIch höre...", show_feedback=True)

        if not command:
            set_state("idle")
            speak("Ich habe nichts verstanden.")
            continue

        if command.lower() == "exit":
            speak("Auf Wiedersehen!")
            _send({"type": "quit"})   # UI schließen
            time.sleep(1.5)           # Warten bis Conrad fertig ist
            break

        # Befehl verarbeiten
        set_state("thinking")

        try:
            result = ki_assistant.invoke({"input": command})
            output = result.get("output", "Ich habe leider keine Antwort darauf.")
        except ConnectionError:
            output = "Ich habe gerade keine Internetverbindung."
            print("[FEHLER] Keine Verbindung zur API.")
        except TimeoutError:
            output = "Die Anfrage hat zu lange gedauert. Bitte nochmal versuchen."
            print("[FEHLER] API Timeout.")
        except Exception as e:
            output = "Es ist ein Fehler aufgetreten. Bitte versuche es erneut."
            print(f"[FEHLER] Unbekannter Fehler: {e}")

        print(f"<- Antwort: {output}")
        speak(output)