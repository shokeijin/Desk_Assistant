"""
Web-Tools
=========
LangChain-Tool für die Internetsuche via Tavily.
Tavily ist eine KI-optimierte Suchmaschine die strukturierte
Ergebnisse liefert und sich gut in LangChain-Agenten integriert.

Voraussetzung: TAVILY_API_KEY muss in der .env-Datei gesetzt sein.
"""

from langchain_community.tools.tavily_search import TavilySearchResults

# Maximale Anzahl der zurückgegebenen Suchergebnisse pro Anfrage.
# 3 Ergebnisse sind ein guter Kompromiss zwischen Vollständigkeit und Geschwindigkeit.
web_search = TavilySearchResults(
    max_results=3,
    description=(
        "Nützlich für die Suche nach aktuellen Informationen, Nachrichten, "
        "Wetter, Personen, Orten oder allgemeinen Wissensfragen."
    ),
)