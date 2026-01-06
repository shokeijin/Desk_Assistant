from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class Route(BaseModel):
    """Klassifizierung der Benutzeranfrage."""
    category: Literal["todo", "reminder", "profile", "chat"] = Field(
        description="Die Kategorie der Anfrage."
    )

def create_router():
    # Temperatur 0 ist wichtig für konsistente Entscheidungen
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(Route)

    system = """Du bist ein Routing-Experte für einen Desktop-Assistenten.
    Klassifiziere die Anfrage:
    - todo: Aufgaben listen, hinzufügen, löschen.
    - reminder: Erinnerungen/Termine (brauchen oft Zeitangaben).
    - profile: Name des Nutzers oder persönliche Daten.
    - chat: Begrüßung, Smalltalk, allgemeine Fragen ohne Tool-Bedarf."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{input}"),
    ])

    return prompt | structured_llm