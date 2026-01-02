from assistant.agent import create_assistant

if __name__ == "__main__":
    # Erstellen einer Instanz unseres KI-Assistenten
    ki_assistant = create_assistant()

    print("KI Desktop Assistant ist bereit. Stellen Sie Ihre Frage (beenden mit 'exit').")

    while True:
        # 1. Input: Benutzereingabe entgegennehmen
        user_input = input("Was kann ich für Sie tun: ")

        if user_input.lower() == 'exit':
            print("Auf Wiedersehen!")
            break

        # 2. KI Assistant: Die Eingabe an den Agenten zur Verarbeitung senden
        # Das Ergebnis des Agenten enthält den Output
        result = ki_assistant.invoke({"input": user_input})

        # 3. Output: Das Ergebnis ausgeben
        print("\nAntwort des Assistenten:")
        print(result['output'])
        print("-" * 20)