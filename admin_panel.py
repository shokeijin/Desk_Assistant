"""
Melvin Admin Panel
------------------
Vollständige Admin-Konsole mit Zugriff auf alle Profil-Daten.
Wird über F12 + 6-stellige PIN aktiviert.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

PROFILES_DIR = Path(__file__).parent / "assistant" / "storage" / "profiles"


def _get_profiles() -> list[str]:
    """Gibt alle vorhandenen Profile zurück."""
    if not PROFILES_DIR.exists():
        return []
    return [p.name for p in PROFILES_DIR.iterdir() if p.is_dir()]


def _load_json(path: Path) -> list | dict:
    """Lädt eine JSON Datei sicher."""
    if not path.exists():
        return []
    try:
        content = path.read_text(encoding="utf-8").strip()
        return json.loads(content) if content else []
    except:
        return []


def _save_json(path: Path, data) -> None:
    """Speichert Daten als JSON."""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_admin_panel():
    """Startet die Admin-Konsole."""
    print("\n" + "="*50)
    print("  🔐 MELVIN ADMIN PANEL")
    print("="*50)

    while True:
        print("\n📋 HAUPTMENÜ:")
        print("  [1] Profile anzeigen")
        print("  [2] Profil löschen")
        print("  [3] Profil umbenennen")
        print("  [4] Todos eines Profils anzeigen")
        print("  [5] Todos eines Profils bearbeiten")
        print("  [6] Reminder eines Profils anzeigen")
        print("  [7] Reminder eines Profils bearbeiten")
        print("  [8] Benutzerprofil anzeigen/bearbeiten")
        print("  [9] Einstellungen eines Profils anzeigen/bearbeiten")
        print("  [0] Admin Panel beenden")
        print()

        choice = input("Auswahl: ").strip()

        if choice == "0":
            print("\n✅ Admin Panel beendet.\n")
            break

        elif choice == "1":
            _show_profiles()

        elif choice == "2":
            _delete_profile()

        elif choice == "3":
            _rename_profile()

        elif choice == "4":
            _show_todos()

        elif choice == "5":
            _edit_todos()

        elif choice == "6":
            _show_reminders()

        elif choice == "7":
            _edit_reminders()

        elif choice == "8":
            _edit_user_profile()

        elif choice == "9":
            _edit_settings()

        else:
            print("❌ Ungültige Auswahl.")


# =====================
# PROFIL FUNKTIONEN
# =====================

def _show_profiles():
    profiles = _get_profiles()
    if not profiles:
        print("\n📭 Keine Profile vorhanden.")
        return
    print(f"\n👤 Vorhandene Profile ({len(profiles)}):")
    for i, p in enumerate(profiles, 1):
        todos = _load_json(PROFILES_DIR / p / "todos.json")
        reminders = _load_json(PROFILES_DIR / p / "reminders.json")
        print(f"  [{i}] {p} – {len(todos)} Todos, {len(reminders)} Reminder")


def _select_profile(action="auswählen") -> str | None:
    profiles = _get_profiles()
    if not profiles:
        print("\n📭 Keine Profile vorhanden.")
        return None
    _show_profiles()
    name = input(f"\nProfil zum {action} (Name eingeben): ").strip()
    if name not in profiles:
        print(f"❌ Profil '{name}' nicht gefunden.")
        return None
    return name


def _delete_profile():
    profile = _select_profile("Löschen")
    if not profile:
        return
    confirm = input(f"⚠️  Profil '{profile}' wirklich löschen? Alle Daten gehen verloren! (ja/nein): ").strip().lower()
    if confirm in ["ja", "j"]:
        shutil.rmtree(PROFILES_DIR / profile)
        print(f"✅ Profil '{profile}' wurde gelöscht.")
    else:
        print("Abgebrochen.")


def _rename_profile():
    profile = _select_profile("Umbenennen")
    if not profile:
        return
    new_name = input(f"Neuer Name für '{profile}': ").strip().capitalize()
    if not new_name:
        print("❌ Name darf nicht leer sein.")
        return
    profiles = _get_profiles()
    if new_name in profiles:
        print(f"❌ Profil '{new_name}' existiert bereits.")
        return
    (PROFILES_DIR / profile).rename(PROFILES_DIR / new_name)
    print(f"✅ Profil '{profile}' → '{new_name}' umbenannt.")


# =====================
# TODOS
# =====================

def _show_todos():
    profile = _select_profile("anzeigen")
    if not profile:
        return
    todos = _load_json(PROFILES_DIR / profile / "todos.json")
    if not todos:
        print(f"\n📭 Keine Todos für '{profile}'.")
        return
    print(f"\n📝 Todos von '{profile}':")
    for i, t in enumerate(todos, 1):
        print(f"  [{i}] {t}")


def _edit_todos():
    profile = _select_profile("bearbeiten")
    if not profile:
        return
    todos_file = PROFILES_DIR / profile / "todos.json"
    todos = _load_json(todos_file)

    while True:
        print(f"\n📝 Todos von '{profile}':")
        if not todos:
            print("  (leer)")
        for i, t in enumerate(todos, 1):
            print(f"  [{i}] {t}")

        print("\n  [a] Todo hinzufügen")
        print("  [d] Todo löschen")
        print("  [0] Zurück")
        action = input("Auswahl: ").strip().lower()

        if action == "0":
            break
        elif action == "a":
            text = input("Neues Todo: ").strip()
            if text:
                todos.append(text)
                _save_json(todos_file, todos)
                print(f"✅ Todo hinzugefügt.")
        elif action == "d":
            try:
                idx = int(input("Nummer löschen: ")) - 1
                removed = todos.pop(idx)
                _save_json(todos_file, todos)
                print(f"✅ '{removed}' gelöscht.")
            except (ValueError, IndexError):
                print("❌ Ungültige Nummer.")


# =====================
# REMINDER
# =====================

def _show_reminders():
    profile = _select_profile("anzeigen")
    if not profile:
        return
    reminders = _load_json(PROFILES_DIR / profile / "reminders.json")
    if not reminders:
        print(f"\n📭 Keine Reminder für '{profile}'.")
        return
    print(f"\n⏰ Reminder von '{profile}':")
    for i, r in enumerate(reminders, 1):
        status = "✅" if r.get("done") else "🔔"
        print(f"  [{i}] {status} {r.get('time', '?')} – {r.get('text', '?')}")


def _edit_reminders():
    profile = _select_profile("bearbeiten")
    if not profile:
        return
    reminders_file = PROFILES_DIR / profile / "reminders.json"
    reminders = _load_json(reminders_file)

    while True:
        print(f"\n⏰ Reminder von '{profile}':")
        if not reminders:
            print("  (leer)")
        for i, r in enumerate(reminders, 1):
            status = "✅" if r.get("done") else "🔔"
            print(f"  [{i}] {status} {r.get('time', '?')} – {r.get('text', '?')}")

        print("\n  [d] Reminder löschen")
        print("  [r] Reminder als unerledigt markieren")
        print("  [0] Zurück")
        action = input("Auswahl: ").strip().lower()

        if action == "0":
            break
        elif action == "d":
            try:
                idx = int(input("Nummer löschen: ")) - 1
                removed = reminders.pop(idx)
                _save_json(reminders_file, reminders)
                print(f"✅ Reminder '{removed.get('text')}' gelöscht.")
            except (ValueError, IndexError):
                print("❌ Ungültige Nummer.")
        elif action == "r":
            try:
                idx = int(input("Nummer zurücksetzen: ")) - 1
                reminders[idx]["done"] = False
                _save_json(reminders_file, reminders)
                print("✅ Reminder zurückgesetzt.")
            except (ValueError, IndexError):
                print("❌ Ungültige Nummer.")


# =====================
# USER PROFIL
# =====================

def _edit_user_profile():
    profile = _select_profile("bearbeiten")
    if not profile:
        return
    profile_file = PROFILES_DIR / profile / "user_profile.json"
    data = _load_json(profile_file)
    if not isinstance(data, dict):
        data = {}

    print(f"\n👤 Benutzerprofil von '{profile}':")
    if not data:
        print("  (leer)")
    for k, v in data.items():
        print(f"  {k}: {v}")

    print("\n  [a] Eintrag hinzufügen/ändern")
    print("  [d] Eintrag löschen")
    print("  [0] Zurück")
    action = input("Auswahl: ").strip().lower()

    if action == "a":
        key = input("Schlüssel (z.B. name, alter): ").strip()
        value = input("Wert: ").strip()
        if key:
            data[key] = value
            _save_json(profile_file, data)
            print(f"✅ '{key}' = '{value}' gespeichert.")
    elif action == "d":
        key = input("Schlüssel löschen: ").strip()
        if key in data:
            del data[key]
            _save_json(profile_file, data)
            print(f"✅ '{key}' gelöscht.")
        else:
            print(f"❌ '{key}' nicht gefunden.")


# =====================
# EINSTELLUNGEN
# =====================

def _edit_settings():
    profile = _select_profile("bearbeiten")
    if not profile:
        return
    settings_file = PROFILES_DIR / profile / "settings.json"
    data = _load_json(settings_file)
    if not isinstance(data, dict):
        data = {}

    print(f"\n⚙️  Einstellungen von '{profile}':")
    for k, v in data.items():
        print(f"  {k}: {v}")

    print("\n  [a] Einstellung ändern")
    print("  [0] Zurück")
    action = input("Auswahl: ").strip().lower()

    if action == "a":
        key = input("Schlüssel (z.B. agent_name): ").strip()
        value = input("Wert: ").strip()
        if key:
            # Boolean konvertieren
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            data[key] = value
            _save_json(settings_file, data)
            print(f"✅ '{key}' = '{value}' gespeichert.")