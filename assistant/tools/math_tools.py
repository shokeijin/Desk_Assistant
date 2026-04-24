from langchain.tools import tool
import numexpr

@tool
def calculator(expression: str) -> str:
    """
    Berechnet einen mathematischen Ausdruck.
    Ist nützlich für Mathematik, wie z.B. 3*5 oder 2+2.
    """
    try:
        # numexpr ist sicherer und schneller als eval()
        result = numexpr.evaluate(expression)
        return f"Das Ergebnis von '{expression}' ist: {result}"
    except Exception as e:
        return f"Fehler bei der Berechnung: {e}. Bitte stelle sicher, dass es ein gültiger mathematischer Ausdruck ist."