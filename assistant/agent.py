from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

def create_assistant():
    """
    Erstellt den Agenten, ohne den problematischen 'hub' zu importieren.
    """
    llm = ChatOpenAI(model="gpt-4o-mini")
    tools = []

    # Wir definieren den Prompt manuell, anstatt ihn aus dem Hub zu laden.
    # Dies ist der exakte Text, den 'hub.pull' herunterladen würde.
    prompt_template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

    prompt = ChatPromptTemplate.from_template(prompt_template)

    # Der Rest des Codes ist identisch
    agent = create_react_agent(llm, tools, prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    return executor