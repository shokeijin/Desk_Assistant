"""
WebSocket-Bridge
================
Verbindet das Python-Backend bidirektional mit der Electron-UI.

Funktionsweise:
  - Python startet einen lokalen WebSocket-Server (Standard: ws://localhost:8765)
  - Die Electron-UI verbindet sich als Client
  - Python sendet Zustandsänderungen und Texte an die UI
  - Die UI kann Texteingaben des Nutzers zurück an Python senden

Nachrichtentypen (Python → UI):
  {"type": "state", "state": "idle|listening|thinking|speaking", "text": "..."}
  {"type": "input_request", "prompt": "...", "input_type": "text|pin|confirm", "masked": bool}
  {"type": "quit"}

Nachrichtentypen (UI → Python):
  {"type": "input_response", "value": "..."}
"""

import asyncio
import json
import threading

import websockets

# Alle aktiven WebSocket-Verbindungen (in der Regel nur eine: die Electron-UI)
_clients: set = set()

# Event-Loop des WebSocket-Server-Threads
_loop: asyncio.AbstractEventLoop | None = None

# Synchronisierungsmechanismus für blockierende Eingabe-Anfragen
_input_response: str | None = None
_input_event = threading.Event()


async def _handler(websocket) -> None:
    """
    Verarbeitet eine neue WebSocket-Verbindung.
    Lauscht auf eingehende Nachrichten und leitet Nutzereingaben weiter.
    """
    global _input_response

    _clients.add(websocket)
    print("[BRIDGE] Electron UI verbunden ✅")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "input_response":
                    # Nutzereingabe aus der UI empfangen und an den wartenden Thread übergeben
                    _input_response = data.get("value", "")
                    _input_event.set()
            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        _clients.discard(websocket)
        print("[BRIDGE] Electron UI getrennt")


async def _broadcast(message: dict) -> None:
    """Sendet eine Nachricht als JSON an alle verbundenen Clients."""
    if _clients:
        data = json.dumps(message)
        await asyncio.gather(
            *[client.send(data) for client in _clients],
            return_exceptions=True,
        )


def _send(message: dict) -> None:
    """
    Sendet eine Nachricht thread-sicher an die UI.
    Kann aus jedem Thread aufgerufen werden.
    """
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(_broadcast(message), _loop)


def set_state(state: str, text: str = "") -> None:
    """
    Teilt der UI den aktuellen Zustand des Assistenten mit.

    state: "idle" | "listening" | "thinking" | "speaking"
    text:  Optionaler Anzeigetext in der Antwort-Box der UI
    """
    message: dict = {"type": "state", "state": state}
    if text:
        message["text"] = text
    _send(message)


def request_input(
    prompt: str,
    input_type: str = "text",
    masked: bool = False,
) -> str:
    """
    Fordert eine Texteingabe vom Nutzer über die UI an.
    Blockiert den aufrufenden Thread bis der Nutzer bestätigt hat.

    prompt:     Anzeigetext im Eingabe-Overlay der UI
    input_type: "text" für freie Eingabe, "pin" für Zahleneingabe, "confirm" für Ja/Nein
    masked:     True blendet die Eingabe mit Sternchen ab (für PIN-Eingaben)

    Gibt die Nutzereingabe als String zurück, oder "" bei Timeout (60 Sekunden).
    """
    global _input_response

    _input_response = None
    _input_event.clear()

    _send({
        "type": "input_request",
        "prompt": prompt,
        "input_type": input_type,
        "masked": masked,
    })

    _input_event.wait(timeout=60)
    return _input_response or ""


def start_bridge(host: str = "localhost", port: int = 8765) -> None:
    """
    Startet den WebSocket-Server in einem Hintergrund-Thread.
    Kehrt sofort zurück – der Server läuft parallel zum Hauptprogramm.
    """
    global _loop

    def run() -> None:
        global _loop
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)

        async def serve() -> None:
            async with websockets.serve(_handler, host, port):
                print(f"[BRIDGE] WebSocket-Server läuft auf ws://{host}:{port}")
                await asyncio.Future()  # Läuft bis das Programm beendet wird

        _loop.run_until_complete(serve())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()