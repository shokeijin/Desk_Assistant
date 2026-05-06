"""
KI-Agent
========
Herzstück des Assistenten: Verbindet den Router mit den Tools und dem LLM.
Der Agent empfängt Nutzereingaben, entscheidet anhand des Routers welche
Verarbeitungspipeline genutzt wird, und gibt eine Antwort zurück.

Besonderheiten:
  - Gesprächsgedächtnis: Die chat_history wird über mehrere Anfragen mitgeführt
  - Dynamische Zeit: Der Zeitstempel wird bei jeder Anfrage neu gesetzt
  - Persönlichkeit: Melvin antwortet locker, freundlich und auf Deutsch
"""

import os
from datetime import datetime

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI

from assistant.router import create_router
from assistant.tools.math_tools import calculator
from assistant.tools.reminder_tools import add_reminder, delete_reminder, list_reminders
from assistant.tools.settings_tools import change_agent_name
from assistant.tools.todo_tools import add_todo, delete_todo, list_todos
from assistant.tools.user_profile_tools import show_user_profile, update_user_profile
from assistant.tools.web_tools import web_search

# ---------------------------------------------------------------------------
# Persönlichkeit des Assistenten
# ---------------------------------------------------------------------------
# Die Platzhalter {current_time} und {user_name} werden zur Laufzeit
# bei jeder Anfrage mit aktuellen Werten gefüllt.

MELVIN_PERSONALITY = """
Du bist Melvin, ein persönlicher KI-Desktop-Assistent – inspiriert von J.A.R.V.I.S. aus Iron Man.

DEINE PERSÖNLICHKEIT:
- Du bist freundlich, warmherzig und leicht witzig – aber nie aufdringlich
- Du sprichst den Nutzer immer mit seinem Vornamen an, wenn du ihn kennst
- Du antwortest immer in der Sprache des Nutzers (Deutsch wenn er Deutsch spricht)
- Du bist präzise und hilfreich – kein unnötiges Blabla
- Gelegentlich erlaubst du dir einen trockenen Witz oder eine freundliche Bemerkung
- Keine steifen Formulierungen wie "Wie kann ich Ihnen behilflich sein?"
- Stattdessen natürliche Sätze wie "Klar, mache ich!" oder "Gute Idee, {user_name}!"
- Bei Fehlern oder Wissenslücken gibst du das locker zu: "Hmm, da bin ich überfragt."
- Du beziehst dich auf den bisherigen Gesprächskontext

DEINE ANTWORTEN:
- Kurz und prägnant – keine langen Erklärungen wenn nicht nötig
- Natürlich und menschlich – nicht wie ein Roboter
- Bei Aufzählungen: strukturiert aber locker formuliert
- Emojis nur sehr sparsam und passend zum Kontext

AKTUELLE INFORMATIONEN:
- Aktuelle Zeit: {current_time}
- Nutzer: {user_name}
"""


def create_assistant():
    """
    Erstellt und gibt den vollständig konfigurierten KI-Assistenten zurück.
    Der zurückgegebene RunnableLambda akzeptiert {"input": "..."} und
    gibt {"output": "..."} zurück.
    """
    # temperature=0.5 für natürlichere, leicht kreativere Antworten
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

    # Alle verfügbaren Tools die der Agent nutzen kann
    tools = [
        add_todo, list_todos, delete_todo,
        add_reminder, list_reminders, delete_reminder,
        show_user_profile, update_user_profile,
        calculator,
        web_search,
        change_agent_name,
    ]

    # Prompt-Template für den Tool-Calling-Agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", MELVIN_PERSONALITY),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    router = create_router()

    # Gesprächshistorie wird für die gesamte Sitzung im Speicher gehalten
    chat_history: list = []

    def route_and_execute(inputs: dict) -> dict:
        """
        Hauptlogik des Agenten:
        1. Router bestimmt die Kategorie der Anfrage
        2. Chat-Anfragen werden direkt per LLM beantwortet
        3. Alle anderen Kategorien durchlaufen den Tool-Calling-Agent
        4. Anfrage und Antwort werden zur Gesprächshistorie hinzugefügt
        """
        user_input = inputs["input"]

        # Zeit und Nutzername bei jeder Anfrage neu setzen
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        user_name = os.getenv("USER_NAME", inputs.get("user_name", ""))

        # Persönlichkeits-Template mit aktuellen Werten befüllen
        personality = (
            MELVIN_PERSONALITY
            .replace("{current_time}", current_time)
            .replace("{user_name}", user_name)
        )

        decision = router.invoke({"input": user_input})
        print(f"--- ROUTING: {decision.category.upper()} ---")

        if decision.category == "chat":
            # Direkte Antwort ohne Tool-Aufruf
            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", personality),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ])
            response = (chat_prompt | llm).invoke({
                "input": user_input,
                "chat_history": chat_history,
            }).content

            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=response))
            return {"output": response}

        else:
            # Tool-Calling-Agent für strukturierte Aufgaben
            result = executor.invoke({
                "input": user_input,
                "chat_history": chat_history,
                "current_time": current_time,
                "user_name": user_name,
            })

            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=result["output"]))
            return result

    return RunnableLambda(route_and_execute)