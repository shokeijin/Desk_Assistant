# --- MODIFIZIERTE DATEI: assistant/agent.py ---

import os
from datetime import datetime

# Die 'dotenv' Imports hier werden nicht mehr benötigt
# from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda

from assistant.router import create_router
from assistant.tools.todo_tools import add_todo, list_todos, delete_todo
from assistant.tools.reminder_tools import add_reminder, list_reminders, delete_reminder
from assistant.tools.user_profile_tools import show_user_profile, update_user_profile
from assistant.tools.math_tools import calculator
from assistant.tools.web_tools import web_search

# load_dotenv() wird hier entfernt, da es jetzt in main.py ist
# load_dotenv()

def create_assistant():
    # ... der Rest Ihrer agent.py Datei bleibt unverändert ...
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    tools = [
        add_todo, list_todos, delete_todo,
        add_reminder, list_reminders, delete_reminder,
        show_user_profile, update_user_profile,
        calculator,
        web_search
    ]
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a helpful assistant.
        Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        User: {os.getenv('USER_NAME', 'User')}"""),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    router = create_router()
    def route_and_execute(inputs):
        user_input = inputs["input"]
        decision = router.invoke({"input": user_input})
        print(f"--- ROUTING: {decision.category.upper()} ---")
        if decision.category == "chat":
            return {"output": llm.invoke(user_input).content}
        else:
            return executor.invoke({"input": user_input})
    return RunnableLambda(route_and_execute)