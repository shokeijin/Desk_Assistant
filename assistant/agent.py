import os
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage, AIMessage

from assistant.router import create_router
from assistant.tools.todo_tools import add_todo, list_todos, delete_todo
from assistant.tools.reminder_tools import add_reminder, list_reminders, delete_reminder
from assistant.tools.user_profile_tools import show_user_profile, update_user_profile
from assistant.tools.math_tools import calculator
from assistant.tools.web_tools import web_search
from assistant.tools.settings_tools import change_agent_name

# ✅ Melvin's Persönlichkeit
MELVIN_PERSONALITY = """
Du bist Melvin, ein persönlicher KI-Desktop-Assistent – inspiriert von J.A.R.V.I.S. aus Iron Man.

DEINE PERSÖNLICHKEIT:
- Du bist freundlich, warmherzig und leicht witzig – aber nie aufdringlich
- Du redest den Nutzer immer mit seinem Vornamen an wenn du ihn kennst
- Du antwortest immer in der Sprache des Nutzers (Deutsch wenn er Deutsch spricht)
- Du bist präzise und hilfreich – kein unnötiges Blabla
- Gelegentlich erlaubst du dir einen trockenen Witz oder eine freundliche Bemerkung
- Du verwendest keine steifen oder formellen Formulierungen wie "Wie kann ich Ihnen behilflich sein?"
- Stattdessen sagst du Dinge wie "Klar, mache ich!" oder "Gute Idee, {user_name}!"
- Bei Fehlern oder wenn du etwas nicht weißt, gibst du das locker zu: "Hmm, da bin ich überfragt."
- Du erinnerst dich an den Kontext des Gesprächs und beziehst dich darauf

DEINE ANTWORTEN:
- Kurz und prägnant – keine ellenlangen Erklärungen wenn nicht nötig
- Natürlich und menschlich – nicht wie ein Roboter
- Bei Listen oder Aufzählungen: strukturiert aber locker
- Emojis nur sehr sparsam und nur wenn es passt

AKTUELLE INFORMATIONEN:
- Aktuelle Zeit: {current_time}
- Nutzer: {user_name}
"""


def create_assistant():
    # ✅ temperature 0.5 für natürlichere Antworten
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

    tools = [
        add_todo, list_todos, delete_todo,
        add_reminder, list_reminders, delete_reminder,
        show_user_profile, update_user_profile,
        calculator,
        web_search,
        change_agent_name
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", MELVIN_PERSONALITY),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    router = create_router()

    chat_history = []

    def route_and_execute(inputs):
        user_input = inputs["input"]

        current_time = datetime.now().strftime('%d.%m.%Y %H:%M')
        user_name = os.getenv('USER_NAME', inputs.get("user_name", ""))

        # ✅ Persönlichkeit mit aktuellen Werten befüllen
        personality = MELVIN_PERSONALITY\
            .replace("{current_time}", current_time)\
            .replace("{user_name}", user_name)

        decision = router.invoke({"input": user_input})
        print(f"--- ROUTING: {decision.category.upper()} ---")

        if decision.category == "chat":
            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", personality),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ])
            chat_chain = chat_prompt | llm
            response = chat_chain.invoke({
                "input": user_input,
                "chat_history": chat_history,
            }).content
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=response))
            return {"output": response}
        else:
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