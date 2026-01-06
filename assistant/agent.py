import os
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent  # Geändert!
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from assistant.tools.todo_tools import add_todo, list_todos, delete_todo
from assistant.tools.reminder_tools import add_reminder, list_reminders, delete_reminder
from assistant.tools.user_profile_tools import show_user_profile, update_user_profile

load_dotenv()


def create_assistant():
    user_name = os.getenv("USER_NAME", "User")
    assistant_tone = os.getenv("ASSISTANT_TONE", "neutral")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3
    )

    tools = [
        add_todo, list_todos, delete_todo,
        add_reminder, list_reminders, delete_reminder,
        show_user_profile, update_user_profile
    ]

    # Ein moderneres Prompt-Template für Tool Calling
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a helpful desktop assistant.
        Current Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        User name: {user_name}
        Tone: {assistant_tone}

        You have access to tools to manage todos, reminders and user profiles.
        Always use the tools if the user asks for these actions."""),
        ("human", "{input}"),
        # Das hier ist wichtig für Tool-Calling Agents:
        MessagesPlaceholder("agent_scratchpad"),
    ])

    # Erstelle den Tool Calling Agent (stabiler als ReAct)
    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True
        # handle_parsing_errors ist hier meist nicht mehr nötig
    )

    return executor