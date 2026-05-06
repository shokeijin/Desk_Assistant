"""
Admin-Panel
===========
Terminal-basierte Verwaltungsoberfläche für Melvin.
Bietet vollen Zugriff auf alle Profil-Daten: Todos, Reminder,
Benutzerprofile und Einstellungen.

Aktivierung: F12-Taste drücken → 6-stellige PIN eingeben.
"""

import json
import shutil
from pathlib import Path

# Basispfad zu allen Nutzerprofilen
PROFILES_DIR = Path(__file__).parent / "assistant" / "storage" / "profiles"


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _get_profiles() -> list[str]:
    """Gibt eine Liste aller vorhandenen Profilnamen zurück."""
    if not PROFILES_DIR.exists():
        return []
    return [p.name for p in PROFILES_DIR.iterdir() if p.is_dir()]


def _load_json(path: Path) -> list | dict:
    """Lädt eine JSON-Datei sicher. Gibt eine leere Liste bei Fehlern zurück."""
    if not path.exists():
        return []
    try:
        content = path.read_text(encoding="utf-8").strip()
        return json.loads(content) if content else []
    except (json.JSONDecodeError, IOError):
        return []


def _save_json(path: Path, data: list | dict) -> None:
    """Speichert Daten als formatierte JSON-Datei."""
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def _show_profiles() -> None:
    """Gibt alle Profile mit Anzahl der Todos und Reminder aus."""
    profiles = _get_profiles()
    if not profiles:
        print("\n📭 Keine Profile vorhanden.")
        return

    print(f"\n👤 Vorhandene Profile ({len(profiles)}):")
    for i, name in enumerate(profiles, 1):
        todos = _load_json(PROFILES_DIR / name / "todos.json")
        reminders = _load_json(PROFILES_DIR / name / "reminders.json")
        print(f"  [{i}] {name} – {len(todos)} Todos, {len(reminders)} Reminder")


def _select_profile(action: str = "auswählen") -> str | None:
    """
    Lässt den Admin ein Profil aus der Liste auswählen.
    Gibt den Profilnamen zurück oder None wenn kein gültiges Profil gewählt wurde.
    """
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


# ---------------------------------------------------------------------------
# Profil-Verwaltung
# ---------------------------------------------------------------------------

def _delete_profile() -> None:
    """Löscht ein Profil samt aller zugehörigen Daten nach Bestätigung."""
    profile = _select_profile("Löschen")
    if not profile:
        return

    confirm = input(
        f"⚠️  Profil '{profile}' wirklich löschen? "
        "Alle Daten gehen verloren! (ja/nein): "
    ).strip().lower()

    if confirm in ("ja", "j"):
        shutil.rmtree(PROFILES_DIR / profile)
        print(f"✅ Profil '{profile}' wurde gelöscht.")
    else:
        print("Abgebrochen.")


def _rename_profile() -> None:
    """Benennt ein vorhandenes Profil um."""
    profile = _select_profile("Umbenennen")
    if not profile:
        return

    new_name = input(f"Neuer Name für '{profile}': ").strip().capitalize()

    if not new_name:
        print("❌ Name darf nicht leer sein.")
        return

    if new_name in _get_profiles():
        print(f"❌ Profil '{new_name}' existiert bereits.")
        return

    (PROFILES_DIR / profile).rename(PROFILES_DIR / new_name)
    print(f"✅ Profil '{profile}' → '{new_name}' umbenannt.")


# ---------------------------------------------------------------------------
# Todo-Verwaltung
# ---------------------------------------------------------------------------

def _show_todos() -> None:
    """Zeigt alle Todos eines ausgewählten Profils an."""
    profile = _select_profile("anzeigen")
    if not profile:
        return

    todos = _load_json(PROFILES_DIR / profile / "todos.json")
    if not todos:
        print(f"\n📭 Keine Todos für '{profile}'.")
        return

    print(f"\n📝 Todos von '{profile}':")
    for i, task in enumerate(todos, 1):
        print(f"  [{i}] {task}")


def _edit_todos() -> None:
    """Öffnet das Todo-Bearbeitungsmenü für ein ausgewähltes Profil."""
    profile = _select_profile("bearbeiten")
    if not profile:
        return

    todos_file = PROFILES_DIR / profile / "todos.json"
    todos = _load_json(todos_file)

    while True:
        print(f"\n📝 Todos von '{profile}':")
        print("  (leer)" if not todos else "")
        for i, task in enumerate(todos, 1):
            print(f"  [{i}] {task}")

        print("\n  [a] Todo hinzufügen  |  [d] Todo löschen  |  [0] Zurück")
        action = input("Auswahl: ").strip().lower()

        if action == "0":
            break
        elif action == "a":
            text = input("Neues Todo: ").strip()
            if text:
                todos.append(text)
                _save_json(todos_file, todos)
                print("✅ Todo hinzugefügt.")
        elif action == "d":
            try:
                idx = int(input("Nummer löschen: ")) - 1
                removed = todos.pop(idx)
                _save_json(todos_file, todos)
                print(f"✅ '{removed}' gelöscht.")
            except (ValueError, IndexError):
                print("❌ Ungültige Nummer.")


# ---------------------------------------------------------------------------
# Reminder-Verwaltung
# ---------------------------------------------------------------------------

def _show_reminders() -> None:
    """Zeigt alle Reminder eines ausgewählten Profils an."""
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


def _edit_reminders() -> None:
    """Öffnet das Reminder-Bearbeitungsmenü für ein ausgewähltes Profil."""
    profile = _select_profile("bearbeiten")
    if not profile:
        return

    reminders_file = PROFILES_DIR / profile / "reminders.json"
    reminders = _load_json(reminders_file)

    while True:
        print(f"\n⏰ Reminder von '{profile}':")
        print("  (leer)" if not reminders else "")
        for i, r in enumerate(reminders, 1):
            status = "✅" if r.get("done") else "🔔"
            print(f"  [{i}] {status} {r.get('time', '?')} – {r.get('text', '?')}")

        print("\n  [d] Löschen  |  [r] Als unerledigt markieren  |  [0] Zurück")
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


# ---------------------------------------------------------------------------
# Benutzerprofil-Verwaltung
# ---------------------------------------------------------------------------

def _edit_user_profile() -> None:
    """Zeigt und bearbeitet die persönlichen Daten eines Profils."""
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

    print("\n  [a] Eintrag hinzufügen/ändern  |  [d] Eintrag löschen  |  [0] Zurück")
    action = input("Auswahl: ").strip().lower()

    if action == "a":
        key = input("Schlüssel (z.B. name, alter, beruf): ").strip()
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


# ---------------------------------------------------------------------------
# Einstellungs-Verwaltung
# ---------------------------------------------------------------------------

def _edit_settings() -> None:
    """Zeigt und bearbeitet die Einstellungen eines Profils."""
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

    print("\n  [a] Einstellung ändern  |  [0] Zurück")
    action = input("Auswahl: ").strip().lower()

    if action == "a":
        key = input("Schlüssel (z.B. agent_name): ").strip()
        value = input("Wert: ").strip()
        if key:
            # "true"/"false" als Strings in Python-Booleans umwandeln
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            data[key] = value
            _save_json(settings_file, data)
            print(f"✅ '{key}' = '{value}' gespeichert.")


# ---------------------------------------------------------------------------
# Hauptmenü
# ---------------------------------------------------------------------------

def run_admin_panel() -> None:
    """Startet das interaktive Admin-Panel im Terminal."""
    print("\n" + "=" * 50)
    print("  🔐 MELVIN ADMIN PANEL")
    print("=" * 50)

    menu_actions = {
        "1": ("Profile anzeigen", _show_profiles),
        "2": ("Profil löschen", _delete_profile),
        "3": ("Profil umbenennen", _rename_profile),
        "4": ("Todos anzeigen", _show_todos),
        "5": ("Todos bearbeiten", _edit_todos),
        "6": ("Reminder anzeigen", _show_reminders),
        "7": ("Reminder bearbeiten", _edit_reminders),
        "8": ("Benutzerprofil bearbeiten", _edit_user_profile),
        "9": ("Einstellungen bearbeiten", _edit_settings),
        "0": ("Admin Panel beenden", None),
    }

    while True:
        print("\n📋 HAUPTMENÜ:")
        for key, (label, _) in menu_actions.items():
            print(f"  [{key}] {label}")

        choice = input("\nAuswahl: ").strip()

        if choice == "0":
            print("\n✅ Admin Panel beendet.\n")
            break

        if choice in menu_actions:
            _, action_fn = menu_actions[choice]
            if action_fn:
                action_fn()
        else:
            print("❌ Ungültige Auswahl.")