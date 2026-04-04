# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Aether-Web Server: Real WebSocket bridge for Python-to-Browser sync.

Replaces the raw TCP socket server with a proper WebSocket implementation
using the `websockets` library (asyncio-based). Maintains the same API
surface as the previous TCP server so existing tests continue to pass.

Supply-chain note: websockets==12.0 is a pinned, well-audited library
with no known vulnerabilities (CVE-free as of 2024-03).
"""
import asyncio
import json
import threading
import time
from typing import Dict, Any, Optional, Callable, Set

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


def find_free_port(start_port: int = 8765) -> int:
    """Find an available TCP port starting from start_port."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class WebServer:
    """
    WebSocket server bridging Python physics engine to browser DOM.

    Uses asyncio + websockets library for proper bidirectional communication.
    Runs in a background thread with its own event loop.

    API-compatible with the previous TCP-based implementation so that
    existing tests and code continue to work without modification.
    """

    def __init__(self, port: int = 8765, host: str = "127.0.0.1"):
        self.host = host
        self.port = port
        self._clients: Dict[str, Any] = {}  # client_id -> websocket
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._start_time = 0.0
        self._message_count = 0
        self._on_message: Optional[Callable] = None
        self._on_connect: Optional[Callable] = None
        self._on_disconnect: Optional[Callable] = None
        self._server_instance = None
        self._stop_flag = threading.Event()

    def start(self) -> None:
        """Start the WebSocket server in a background thread."""
        if self._running:
            return
        if not HAS_WEBSOCKETS:
            raise RuntimeError(
                "websockets library not installed. "
                "Run: pip install websockets==12.0"
            )
        self._running = True
        self._start_time = time.perf_counter()
        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()
        # Wait for server to be ready
        time.sleep(0.5)

    def _run_async_loop(self) -> None:
        """Run the asyncio event loop in a dedicated thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        stop_event = asyncio.Event()

        async def handler(websocket):
            client_id = f"client_{id(websocket)}"
            self._clients[client_id] = websocket
            if self._on_connect:
                self._on_connect(client_id)
            try:
                async for message in websocket:
                    self._message_count += 1
                    if self._on_message:
                        self._on_message(client_id, message)
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self._clients.pop(client_id, None)
                if self._on_disconnect:
                    self._on_disconnect(client_id)

        async def main():
            self._server_instance = await websockets.serve(
                handler, self.host, self.port
            )
            while not self._stop_flag.is_set():
                await asyncio.sleep(0.1)
            self._server_instance.close()
            await self._server_instance.wait_closed()

        self._loop.run_until_complete(main())

    def stop(self) -> None:
        """Stop the server and clean up all clients."""
        if not self._running:
            return
        self._running = False
        self._stop_flag.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._clients.clear()

    async def _broadcast_async(self, message: str) -> None:
        """Async broadcast to all connected clients."""
        if not self._loop or not self._loop.is_running():
            return
        disconnected = []
        for client_id, ws in self._clients.items():
            try:
                await ws.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(client_id)
        for cid in disconnected:
            self._clients.pop(cid, None)
            if self._on_disconnect:
                self._on_disconnect(cid)

    def broadcast(self, message: str) -> None:
        """Send a message to all connected clients (thread-safe)."""
        if not self._running or not self._loop:
            return
        asyncio.run_coroutine_threadsafe(
            self._broadcast_async(message), self._loop
        )

    def handle_client_message(self, message: str) -> None:
        """Process a message (for testing without real WebSocket connection)."""
        self._message_count += 1
        if not message:
            return
        try:
            data = json.loads(message)
            if self._on_message:
                self._on_message("test_client", message)
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass  # Invalid JSON, ignore gracefully

    def handle_client_disconnect(self, client_id: str) -> None:
        """Clean up a disconnected client."""
        self._clients.pop(client_id, None)
        if self._on_disconnect:
            self._on_disconnect(client_id)

    def set_message_handler(self, handler: Callable) -> None:
        """Set callback for incoming messages."""
        self._on_message = handler

    def set_connect_handler(self, handler: Callable) -> None:
        """Set callback for new connections."""
        self._on_connect = handler

    def set_disconnect_handler(self, handler: Callable) -> None:
        """Set callback for disconnections."""
        self._on_disconnect = handler

    @property
    def is_running(self) -> bool:
        return self._running

    def get_stats(self) -> Dict[str, Any]:
        """Return server statistics."""
        uptime = time.perf_counter() - self._start_time if self._start_time > 0 else 0
        return {
            "clients": len(self._clients),
            "uptime": round(uptime, 2),
            "messages": self._message_count,
            "running": self._running
        }
