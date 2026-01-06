import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "todos.json"


def load_todos() -> list[str]:
    # 1. Prüfen, ob die Datei überhaupt existiert
    if not DATA_FILE.exists():
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            # 2. Prüfen, ob die Datei leer ist
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        # 3. Bei Fehlern (z.B. kaputtes JSON) leere Liste zurückgeben
        return []


def save_todos(todos: list[str]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)