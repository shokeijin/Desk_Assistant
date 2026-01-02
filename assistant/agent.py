from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from assistant.tools.todo_tools import add_todo, list_todos, delete_todo
from assistant.tools.reminder_tools import add_reminder, list_reminders, delete_reminder

from dotenv import load_dotenv

load_dotenv()

def create_assistant():
    llm = ChatOpenAI(model="gpt-4o-mini")

    tools = [
        add_todo,
        list_todos,
        delete_todo,
        add_todo,
        list_todos,
        delete_todo,
        add_reminder,
        list_reminders,
        delete_reminder
    ]


    react_prompt = """
    Du bist ein hilfreicher Desktop-Assistent.

    Du hast Zugriff auf die folgenden Werkzeuge:
    {tools}

    Verwende dieses Format:

    Question: die Benutzereingabe
    Thought: überlege, was zu tun ist
    Action: eine der Aktionen [{tool_names}]
    Action Input: Eingabe für die Aktion
    Observation: Ergebnis der Aktion
    Thought: Ich kenne jetzt die endgültige Antwort
    Final Answer: die Antwort an den Nutzer

    Beginne!

    Question: {input}
    Thought: {agent_scratchpad}
    """

    prompt = ChatPromptTemplate.from_template(react_prompt)

    agent = create_react_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
