import os
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda

from assistant.router import create_router
from assistant.tools.todo_tools import add_todo, list_todos, delete_todo
from assistant.tools.reminder_tools import add_reminder, list_reminders, delete_reminder
from assistant.tools.user_profile_tools import show_user_profile, update_user_profile

load_dotenv()


def create_assistant():
    # 1. Setup LLM & Tools
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    tools = [
        add_todo, list_todos, delete_todo,
        add_reminder, list_reminders, delete_reminder,
        show_user_profile, update_user_profile
    ]

    # 2. Setup Agent Executor (Der "Spezialist" für Tools)
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a helpful assistant. 
        Current time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        User: {os.getenv('USER_NAME', 'User')}"""),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # 3. Setup Router
    router = create_router()

    # 4. Die Logik, die beides verbindet
    def route_and_execute(inputs):
        user_input = inputs["input"]

        # Erst fragen wir den Router
        decision = router.invoke({"input": user_input})
        print(f"--- ROUTING: {decision.category.upper()} ---")

        if decision.category == "chat":
            # Direkt antworten ohne Tools
            return {"output": llm.invoke(user_input).content}
        else:
            # Den Agent-Executor nutzen
            return executor.invoke({"input": user_input})

    # Wir geben ein Objekt zurück, das .invoke() versteht (wie dein altes main.py es erwartet)
    return RunnableLambda(route_and_execute)