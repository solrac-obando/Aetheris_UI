# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Aether-Web Server: Lightweight WebSocket bridge for real-time sync.

Provides bidirectional communication between the Python physics engine
and the browser's DOM. Handles coordinate broadcasting and pointer
event routing.
"""
import json
import time
import socket
import threading
from typing import Dict, Any, Optional, Callable


def find_free_port(start_port: int = 8765) -> int:
    """Find an available TCP port starting from start_port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class WebServer:
    """
    Lightweight WebSocket-like server for bridging Python physics to web DOM.

    Uses standard library socketserver for zero-dependency operation.
    In production, replace with `websockets` or `FastAPI` for full WS support.
    """

    def __init__(self, port: int = 8765, host: str = "127.0.0.1"):
        self.host = host
        self.port = port
        self._clients: Dict[str, Any] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._start_time = 0.0
        self._message_count = 0
        self._on_message: Optional[Callable] = None
        self._on_connect: Optional[Callable] = None
        self._on_disconnect: Optional[Callable] = None

    def start(self) -> None:
        """Start the server in a background thread."""
        if self._running:
            return
        self._running = True
        self._start_time = time.perf_counter()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the server and clean up clients."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._clients.clear()

    def _run_loop(self) -> None:
        """Main server loop — listens for connections."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
                server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_sock.bind((self.host, self.port))
                server_sock.listen(5)
                server_sock.settimeout(1.0)

                while self._running:
                    try:
                        client_sock, addr = server_sock.accept()
                        client_id = f"client_{addr[0]}_{addr[1]}"
                        self._clients[client_id] = {
                            "sock": client_sock,
                            "connected": True,
                            "connected_at": time.perf_counter()
                        }
                        if self._on_connect:
                            self._on_connect(client_id)
                        # Handle client in separate thread
                        t = threading.Thread(
                            target=self._handle_client,
                            args=(client_id, client_sock),
                            daemon=True
                        )
                        t.start()
                    except socket.timeout:
                        continue
                    except OSError:
                        break
        except OSError:
            pass  # Server stopped

    def _handle_client(self, client_id: str, client_sock: socket.socket) -> None:
        """Handle a single client connection."""
        try:
            client_sock.settimeout(5.0)
            while self._running and client_id in self._clients:
                try:
                    data = client_sock.recv(4096)
                    if not data:
                        break
                    message = data.decode('utf-8', errors='replace')
                    self._message_count += 1
                    if self._on_message:
                        self._on_message(client_id, message)
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break
        except Exception:
            pass
        finally:
            self.handle_client_disconnect(client_id)
            try:
                client_sock.close()
            except Exception:
                pass

    def broadcast(self, message: str) -> None:
        """Send a message to all connected clients."""
        if not self._running:
            return
        data = message.encode('utf-8') if isinstance(message, str) else message
        disconnected = []
        for client_id, info in self._clients.items():
            try:
                info["sock"].sendall(data)
            except (OSError, BrokenPipeError):
                disconnected.append(client_id)
        for cid in disconnected:
            self.handle_client_disconnect(cid)

    def handle_client_message(self, message: str) -> None:
        """Process a message from a client (for testing without real socket)."""
        self._message_count += 1
        if not message:
            return
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")
            if self._on_message:
                self._on_message("test_client", message)
        except (json.JSONDecodeError, AttributeError):
            pass  # Invalid JSON, ignore

    def handle_client_disconnect(self, client_id: str) -> None:
        """Clean up a disconnected client."""
        client = self._clients.pop(client_id, None)
        if client and self._on_disconnect:
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
