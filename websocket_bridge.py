"""
Melvin WebSocket Bridge
-----------------------
Startet einen kleinen WebSocket-Server damit main.py
den Zustand an die Electron-UI senden kann.

Verwendung in main.py:
    from websocket_bridge import set_state, set_response

    set_state("listening")
    set_state("thinking")
    set_state("speaking", text="Hier ist die Antwort")
    set_state("idle")
"""

import asyncio
import json
import threading
import websockets

# Globale Verbindung zur UI
_clients = set()
_loop = None


async def _handler(websocket):
    """Neue Verbindung von Electron."""
    _clients.add(websocket)
    print("[BRIDGE] Electron UI verbunden ✅")
    try:
        async for _ in websocket:
            pass  # Wir empfangen nichts, nur senden
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
    """
    Sendet einen Zustand an die UI.
    state: 'idle' | 'listening' | 'thinking' | 'speaking'
    text: optional – wird bei 'speaking' als Antworttext angezeigt
    """
    message = {"type": "state", "state": state}
    if text:
        message["text"] = text
    _send(message)


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
                await asyncio.Future()  # läuft für immer

        _loop.run_until_complete(serve())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()