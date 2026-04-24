from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class Route(BaseModel):
    """Klassifizierung der Benutzeranfrage."""
    # --- ÄNDERUNG HIER ---
    # Wir fügen 'math' und 'search' als mögliche Kategorien hinzu
    category: Literal["todo", "reminder", "profile", "math", "search", "chat"] = Field(
        description="Die Kategorie der Anfrage."
    )

def create_router():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(Route)

    # --- ÄNDERUNG HIER ---
    # Wir erklären dem Router, was die neuen Kategorien bedeuten
    system = """Du bist ein Routing-Experte für einen Desktop-Assistenten.
    Klassifiziere die Anfrage:
    - todo: Aufgaben listen, hinzufügen, löschen.
    - reminder: Erinnerungen/Termine (brauchen oft Zeitangaben).
    - profile: Name des Nutzers oder persönliche Daten.
    - math: Mathematische Berechnungen oder Zahlenoperationen.
    - search: Allgemeine Wissensfragen, Fragen zu Personen, Orten oder aktuellen Ereignissen.
    - chat: Begrüßung, Smalltalk, allgemeine Fragen ohne Tool-Bedarf."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{input}"),
    ])

    return prompt | structured_llm