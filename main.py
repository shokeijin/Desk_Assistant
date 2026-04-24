# --- MODIFIZIERTE DATEI: main.py ---

# GANZ AM ANFANG LADEN!
from dotenv import load_dotenv
load_dotenv()

# Jetzt erst den Rest importieren
from assistant.agent import create_assistant

if __name__ == "__main__":
    ki_assistant = create_assistant()
    print("KI Desktop Assistant ist bereit. Stellen Sie Ihre Frage (beenden mit 'exit').")

    while True:
        user_input = input("Ihre Frage: ")
        if user_input.lower() == 'exit':
            print("Auf Wiedersehen!")
            break

        result = ki_assistant.invoke({"input": user_input})
        print("\nAntwort des Assistenten:")
        print(result['output'])
        print("-" * 20)