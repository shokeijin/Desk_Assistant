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


def create_assistant():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    tools = [
        add_todo, list_todos, delete_todo,
        add_reminder, list_reminders, delete_reminder,
        show_user_profile, update_user_profile,
        calculator,
        web_search,
        change_agent_name
    ]

    # ✅ FIX 1: Zeit wird jetzt dynamisch bei jeder Anfrage neu gesetzt
    # durch einen RunnableLambda im System-Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are Melvin, a helpful personal desktop assistant inspired by J.A.R.V.I.S. "
            "Be polite, efficient and slightly witty. Respond in the same language the user uses. "
            "Current time: {current_time}\n"
            "User: {user_name}"
        )),
        MessagesPlaceholder("chat_history"),  # ✅ FIX 2: Gesprächsgedächtnis
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    router = create_router()

    # ✅ FIX 2: Gesprächshistorie wird hier gespeichert
    chat_history = []

    def route_and_execute(inputs):
        user_input = inputs["input"]

        # ✅ FIX 1: Zeit wird bei JEDER Anfrage neu berechnet
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        user_name = os.getenv('USER_NAME', 'User')

        decision = router.invoke({"input": user_input})
        print(f"--- ROUTING: {decision.category.upper()} ---")

        if decision.category == "chat":
            # ✅ FIX: Chat-Prompt mit Historie und System-Kontext aufbauen
            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are Melvin, a helpful personal desktop assistant inspired by J.A.R.V.I.S. "
                    "Be polite, efficient and slightly witty. Respond in the same language the user uses. "
                    f"Current time: {current_time}\n"
                    f"User: {user_name}"
                )),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ])
            chat_chain = chat_prompt | llm
            response = chat_chain.invoke({
                "input": user_input,
                "chat_history": chat_history,
            }).content
            # Chat-Antworten zur Historie hinzufügen
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
            # Historie aktualisieren
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=result["output"]))
            return result

    return RunnableLambda(route_and_execute)