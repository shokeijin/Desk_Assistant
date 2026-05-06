"""
Todo-Tools
==========
LangChain-Tools für die Verwaltung der Todo-Liste.
Werden vom KI-Agenten aufgerufen wenn der Nutzer Aufgaben
hinzufügen, anzeigen oder löschen möchte.
"""

from langchain.tools import tool

from assistant.storage.todo_store import load_todos, save_todos


@tool
def add_todo(task: str) -> str:
    """Fügt eine neue Aufgabe zur Todo-Liste des aktiven Profils hinzu."""
    todos = load_todos()
    todos.append(task)
    save_todos(todos)
    return f"✅ Aufgabe hinzugefügt: {task}"


@tool
def list_todos(dummy: str = "") -> str:
    """Zeigt alle offenen Aufgaben der Todo-Liste an."""
    todos = load_todos()

    if not todos:
        return "📭 Deine To-Do-Liste ist leer."

    eintraege = "\n".join(f"{i + 1}. {task}" for i, task in enumerate(todos))
    return f"📝 Deine To-Dos:\n{eintraege}"


@tool
def delete_todo(input_text: str) -> str:
    """
    Löscht eine Aufgabe anhand ihrer Nummer in der Liste.
    Erwartet eine einzelne Zahl als Eingabe, z.B. "2".
    """
    todos = load_todos()

    try:
        index = int(input_text.strip()) - 1
        removed = todos.pop(index)
        save_todos(todos)
        return f"🗑️ Aufgabe gelöscht: {removed}"
    except ValueError:
        return "❌ Bitte gib eine gültige Nummer an (z.B. 1)."
    except IndexError:
        return "❌ Diese Aufgabe existiert nicht."