from langchain_openai import ChatOpenAI
from langchain.agents import agent_executor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Lädt die Umgebungsvariablen aus der .env Datei (insb. den API-Schlüssel)
load_dotenv()

def create_assistant():
    """
    Erstellt und konfiguriert den LangChain Agenten.
    """

    # 1. Sprachmodell auswählen (hier gpt-4o-mini, wie in der Mindmap)
    llm = ChatOpenAI(model="gpt-4o-mini")

    # 2. Werkzeuge definieren (vorerst leer, wird später erweitert)
    # In Ihrer Mindmap sind dies "to do liste" und "Erinnerung"
    tools = []

    # 3. System-Prompt definieren
    # Dies gibt dem Agenten seine Persönlichkeit und Anweisungen.
    # Der Prompt wird so aufgebaut, dass der Agent eine Liste von Werkzeugen
    # und die Benutzereingabe erhält und darauf basierend entscheiden kann.
    prompt_template = """
    Du bist ein hilfreicher Desktop-Assistent. Antworte auf die folgende Anfrage so gut wie möglich.

    Du hast Zugriff auf die folgenden Werkzeuge:

    {tools}

    Verwende das folgende Format:

    Question: die Eingabefrage, auf die du antworten musst
    Thought: Du solltest immer überlegen, was zu tun ist
    Action: die auszuführende Aktion, sollte eines von [{tool_names}] sein
    Action Input: die Eingabe für die Aktion
    Observation: das Ergebnis der Aktion
    ... (dieses Thought/Action/Action Input/Observation kann sich wiederholen)
    Thought: Ich kenne jetzt die endgültige Antwort
    Final Answer: die endgültige Antwort auf die ursprüngliche Eingabefrage

    Beginne!

    Question: {input}
    Thought:{agent_scratchpad}
    """
    prompt = ChatPromptTemplate.from_template(prompt_template)


    # 4. Den Agenten erstellen
    # create_react_agent ist ein gängiger Agententyp, der auf Basis von Beobachtungen "reagiert"
    agent = create_react_agent(llm, tools, prompt)

    # 5. Den Agent Executor erstellen, der den Agenten ausführt
    # verbose=True sorgt dafür, dass wir die "Gedankengänge" des Agenten im Terminal sehen
    executor = agent_executor.AgentExecutor(agent=agent, tools=tools, verbose=True)

    return executor