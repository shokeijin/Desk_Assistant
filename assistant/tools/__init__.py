from .todo_tools import add_todo, list_todos, delete_todo
from .reminder_tools import add_reminder, list_reminders, delete_reminder
from .user_profile_tools import show_user_profile, update_user_profile
# ✅ FIX: Fehlende Tools hinzugefügt
from .math_tools import calculator
from .web_tools import web_search
from .settings_tools import change_agent_name

__all__ = [
    "add_todo",
    "list_todos",
    "delete_todo",
    "add_reminder",
    "list_reminders",
    "delete_reminder",
    "show_user_profile",
    "update_user_profile",
    "calculator",
    "web_search",
    "change_agent_name",
]