from langchain_community.tools.tavily_search import TavilySearchResults

# Dies ist ein vorgefertigtes Tool von LangChain.
# Es sucht automatisch nach dem TAVILY_API_KEY in Ihrer .env-Datei.
# max_results=3 gibt die Anzahl der Suchergebnisse an, die der Agent erhält.
web_search = TavilySearchResults(
    max_results=3,
    description="Nützlich für die Suche nach aktuellen Informationen, Personen, Orten oder allgemeinen Wissensfragen."
)