"""
Melvin WebSocket Bridge
-----------------------
Verbindet Python Backend mit der Electron UI.
Unterstützt jetzt auch Eingabe-Anfragen von Python an die UI.
"""

import asyncio
import json
import threading
import websockets

_clients = set()
_loop = None
_input_response = None
_input_event = threading.Event()


async def _handler(websocket):
    """Neue Verbindung von Electron."""
    global _input_response
    _clients.add(websocket)
    print("[BRIDGE] Electron UI verbunden ✅")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                # ✅ Eingabe von der UI empfangen
                if data.get("type") == "input_response":
                    _input_response = data.get("value", "")
                    _input_event.set()
            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        _clients.discard(websocket)
        print("[BRIDGE] Electron UI getrennt")


async def _broadcast(message: dict):
    """Sendet eine Nachricht an alle verbundenen Clients."""
    if _clients:
        data = json.dumps(message)
        await asyncio.gather(
            *[client.send(data) for client in _clients],
            return_exceptions=True
        )


def _send(message: dict):
    """Thread-sicher eine Nachricht senden."""
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(_broadcast(message), _loop)


def set_state(state: str, text: str = ""):
    """Sendet einen Zustand an die UI."""
    message = {"type": "state", "state": state}
    if text:
        message["text"] = text
    _send(message)


def request_input(prompt: str, input_type: str = "text", masked: bool = False) -> str:
    """
    ✅ NEU: Fragt die UI nach einer Texteingabe.
    Blockiert bis der Nutzer etwas eingegeben hat.

    prompt:     Text der in der UI angezeigt wird
    input_type: 'text' | 'pin' | 'confirm'
    masked:     True für PIN-Eingabe (Sternchen)
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

    # Warten bis UI antwortet (max 60 Sekunden)
    _input_event.wait(timeout=60)
    return _input_response or ""


def start_bridge(host="localhost", port=8765):
    """Startet den WebSocket-Server im Hintergrund-Thread."""
    global _loop

    def run():
        global _loop
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)

        async def serve():
            async with websockets.serve(_handler, host, port):
                print(f"[BRIDGE] WebSocket läuft auf ws://{host}:{port}")
                await asyncio.Future()

        _loop.run_until_complete(serve())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()