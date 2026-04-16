# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Aether-Web App: High-level API for building hybrid web apps in pure Python.

The developer writes only Python. The framework handles:
- Physics simulation (AetherEngine)
- WebSocket sync (WebServer)
- HTML element creation (WebBridge)
- Serving the client (HTTP server)

Usage:
    from aetheris.web import WebApp, WebButton, WebText, WebCard

    app = WebApp(title="My App", width=1280, height=720)
    app.add(WebButton("Click Me", x=100, y=100, mass=2.0))
    app.add(WebText("Hello World", x=100, y=150))
    app.run(port=8765)
"""
import os
import time
import json
import threading
import http.server
import socketserver
from pathlib import Path
from typing import List, Optional, Any

from core.engine import AetherEngine
from core.web_bridge import WebBridge
from core.web_server import WebServer
from core.web_elements import WebElement
from core.input_manager import InputManager


# ── HTTP Server for serving the hybrid client ───────────────────────
class _HybridHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Serves the hybrid client HTML/JS files."""
    _web_hybrid_dir: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self._web_hybrid_dir, **kwargs)

    def log_message(self, fmt, *args):
        pass  # Suppress HTTP logs


def _start_http_server(port: int, web_dir: str) -> socketserver.TCPServer:
    """Start HTTP server for the hybrid client in a background thread."""
    _HybridHTTPHandler._web_hybrid_dir = web_dir
    server = socketserver.TCPServer(("0.0.0.0", port + 1), _HybridHTTPHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# ── WebApp ──────────────────────────────────────────────────────────
class WebApp:
    """
    High-level application class for hybrid web physics apps.

    Manages the full lifecycle:
    1. Creates AetherEngine for physics
    2. Creates WebBridge for DOM sync
    3. Creates WebServer for WebSocket communication
    4. Serves the HTML/JS client via HTTP
    5. Runs the physics loop at 60 FPS
    """

    def __init__(
        self,
        title: str = "Aether-Web App",
        width: float = 1280.0,
        height: float = 720.0,
        http_port: int = 8080,
        ws_port: int = 8765,
    ):
        self.title = title
        self.width = width
        self.height = height
        self.http_port = http_port
        self.ws_port = ws_port

        # Core components
        self.engine = AetherEngine()
        self.bridge = WebBridge(container_width=width, container_height=height)
        self.server = WebServer(port=ws_port)
        self._elements: List[WebElement] = []
        self._running = False
        self._http_server: Optional[socketserver.TCPServer] = None
        self._loop_thread: Optional[threading.Thread] = None

        # Set up WebSocket message handler
        self.server.set_message_handler(self._handle_ws_message)

    def add(self, element: WebElement) -> None:
        """Add a web element to the app."""
        self._elements.append(element)
        idx = len(self._elements) - 1
        self.engine.register_element(element)
        self.bridge.register_element(idx, element._html_id, element.html_metadata)

    def remove(self, element: WebElement) -> None:
        """Remove a web element from the app."""
        if element in self._elements:
            idx = self._elements.index(element)
            self._elements.remove(element)
            self.bridge.unregister_element(idx)

    def _handle_ws_message(self, client_id: str, message: str) -> None:
        """Handle incoming WebSocket messages from the browser."""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "pointerdown":
                x = float(data.get("x", 0))
                y = float(data.get("y", 0))
                self.engine.handle_pointer_down(x, y)
            elif msg_type == "pointermove":
                x = float(data.get("x", 0))
                y = float(data.get("y", 0))
                self.engine.handle_pointer_move(x, y)
            elif msg_type == "pointerup":
                self.engine.handle_pointer_up()
            elif msg_type == "input_value":
                # Handle input value changes
                element_id = data.get("element_id", "")
                value = data.get("value", "")
                for elem in self._elements:
                    if elem._html_id == element_id and hasattr(elem, '_value'):
                        elem._value = value
        except (json.JSONDecodeError, ValueError, KeyError):
            pass

    def _run_loop(self) -> None:
        """Main physics + sync loop — runs at 60 FPS."""
        # Send initial DOM state to clients
        initial_dom = self.bridge.get_initial_dom_state()
        self.server.broadcast(json.dumps({
            "type": "initial_dom",
            "elements": initial_dom
        }))

        target_dt = 1.0 / 60.0
        while self._running:
            t0 = time.perf_counter()

            # Physics tick
            self.engine.tick(self.width, self.height)

            # Sync to web clients
            payload = self.bridge.sync(self._elements)
            self.server.broadcast(json.dumps({
                "type": "update",
                "elements": json.loads(payload)["elements"]
            }))

            # Frame pacing
            elapsed = time.perf_counter() - t0
            sleep_time = target_dt - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def run(self, blocking: bool = True) -> None:
        """
        Start the web app.

        Args:
            blocking: If True (default), blocks the calling thread.
                      If False, runs in a background thread.
        """
        if self._running:
            return

        self._running = True

        # Start HTTP server for the hybrid client
        web_hybrid_dir = str(Path(__file__).parent.parent / "demo" / "web_hybrid")
        if os.path.isdir(web_hybrid_dir):
            try:
                self._http_server = _start_http_server(self.http_port, web_hybrid_dir)
                print(f"[Aether-Web] HTTP server: http://localhost:{self.http_port + 1}")
            except OSError:
                print(f"[Aether-Web] HTTP port {self.http_port + 1} in use, skipping")

        # Start WebSocket server
        self.server.start()
        print(f"[Aether-Web] WebSocket server: ws://localhost:{self.ws_port}")
        print(f"[Aether-Web] {len(self._elements)} elements registered")
        print(f"[Aether-Web] Open http://localhost:{self.http_port + 1} in your browser")

        if blocking:
            try:
                self._run_loop()
            except KeyboardInterrupt:
                print("\n[Aether-Web] Shutting down…")
                self.stop()
        else:
            self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._loop_thread.start()

    def stop(self) -> None:
        """Stop the web app and clean up resources."""
        self._running = False
        self.server.stop()
        if self._http_server:
            self._http_server.shutdown()
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=2.0)
        print("[Aether-Web] Stopped.")
