from langchain.tools import tool

TODOS = []

@tool
def add_todo(task: str) -> str:
    """Fügt eine Aufgabe zur To-Do-Liste hinzu."""
    TODOS.append(task)
    return f"✅ Aufgabe hinzugefügt: {task}"

@tool
def list_todos(dummy: str = "") -> str:
    """Listet alle To-Dos auf."""
    if not TODOS:
        return "📭 Deine To-Do-Liste ist leer."
    return "📝 Deine To-Dos:\n" + "\n".join(
        f"{i+1}. {task}" for i, task in enumerate(TODOS)
    )

@tool
def delete_todo(index: int) -> str:
    """Löscht eine Aufgabe anhand ihrer Nummer."""
    try:
        removed = TODOS.pop(index - 1)
        return f"🗑️ Aufgabe gelöscht: {removed}"
    except IndexError:
        return "❌ Ungültige Nummer."
