from langchain.tools import tool
from assistant.storage.todo_store import load_todos, save_todos


@tool
def add_todo(task: str) -> str:
    """Fügt eine Aufgabe zur To-Do-Liste hinzu."""
    todos = load_todos()
    todos.append(task)
    save_todos(todos)
    return f"✅ Aufgabe hinzugefügt: {task}"


@tool
def list_todos(dummy: str = "") -> str:
    """Listet alle To-Dos auf."""
    todos = load_todos()
    if not todos:
        return "📭 Deine To-Do-Liste ist leer."

    return "📝 Deine To-Dos:\n" + "\n".join(
        f"{i+1}. {task}" for i, task in enumerate(todos)
    )


@tool
def delete_todo(input_text: str) -> str:
    """
    Löscht eine Aufgabe anhand ihrer Nummer.
    Erwartet eine Zahl, z.B. "1"
    """
    todos = load_todos()

    try:
        index = int(input_text.strip())
        removed = todos.pop(index - 1)
        save_todos(todos)
        return f"🗑️ Aufgabe gelöscht: {removed}"
    except ValueError:
        return "❌ Bitte gib eine gültige Nummer an (z.B. 1)."
    except IndexError:
        return "❌ Diese Aufgabe existiert nicht."

