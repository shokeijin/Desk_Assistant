"""
Router
======
Klassifiziert eingehende Nutzeranfragen in Kategorien,
damit der Agent das passende Tool oder die direkte Chat-Antwort wählt.

Kategorien:
  - todo:     Aufgabenverwaltung (hinzufügen, anzeigen, löschen)
  - reminder: Erinnerungen mit Zeitangabe
  - profile:  Persönliche Nutzerdaten
  - math:     Mathematische Berechnungen
  - web:      Aktuelle Informationen aus dem Internet
  - chat:     Smalltalk und allgemeine Fragen ohne Tool-Bedarf
"""

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class Route(BaseModel):
    """Datenmodell für die Routing-Entscheidung des LLM."""

    category: Literal["todo", "reminder", "profile", "math", "web", "chat"] = Field(
        description="Die Kategorie der Nutzeranfrage."
    )


# Systemprompt für den Router – temperature=0 für deterministische Entscheidungen
_ROUTER_SYSTEM_PROMPT = """Du bist ein Routing-Experte für einen KI-Desktop-Assistenten.
Klassifiziere die Nutzeranfrage in genau eine der folgenden Kategorien:

- todo:     Aufgaben auflisten, hinzufügen oder löschen
- reminder: Erinnerungen oder Termine setzen (enthalten meist Zeitangaben)
- profile:  Name, Alter oder andere persönliche Daten des Nutzers
- math:     Mathematische Berechnungen, Formeln oder Gleichungen
- web:      Aktuelle Informationen, Nachrichten, Wetter oder unbekannte Fakten
- chat:     Begrüßungen, Smalltalk und allgemeine Fragen ohne Tool-Bedarf"""


def create_router():
    """
    Erstellt und gibt den konfigurierten Router zurück.
    Der Router nutzt structured output, um immer eine valide Kategorie zu liefern.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(Route)

    prompt = ChatPromptTemplate.from_messages([
        ("system", _ROUTER_SYSTEM_PROMPT),
        ("human", "{input}"),
    ])

    return prompt | structured_llm