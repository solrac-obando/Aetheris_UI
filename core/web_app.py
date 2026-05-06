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
import math
import time
import json
import logging
import secrets
import threading
import http.server
import socketserver
import urllib.parse
from pathlib import Path
from typing import List, Optional, Any

logger = logging.getLogger("aetheris.webapp")

# ── Security Constants ────────────────────────────────────────────────────
_MAX_COORDINATE = float(os.environ.get("AETHERIS_MAX_COORD", "100000"))
_MAX_INPUT_STR_LEN = 256


def _validate_coord(val, default: float = 0.0) -> float:
    """Validate and clamp a coordinate from untrusted WebSocket input.

    Rejects NaN, Inf, and values beyond _MAX_COORDINATE.
    """
    try:
        f = float(val)
        if not math.isfinite(f):
            return default
        return max(-_MAX_COORDINATE, min(_MAX_COORDINATE, f))
    except (ValueError, TypeError):
        return default

from core.engine_selector import EngineSelector
from core.web_bridge import WebBridge
from core.web_server import WebServer
from core.web_elements import WebElement
from core.input_manager import InputManager


# ── HTTP Server for serving the hybrid client ───────────────────────
class _HybridHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Serves the hybrid client HTML/JS files with token-based authentication. (H-01 Fix)"""
    _web_hybrid_dir: str = ""
    _auth_token: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self._web_hybrid_dir, **kwargs)

    def do_GET(self):
        """Intercept GET requests to validate session token."""
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        token = query_params.get('token', [None])[0]

        if token != self._auth_token:
            self.send_error(403, "Forbidden: Missing or invalid session token.")
            return

        super().do_GET()

    def translate_path(self, path):
        """Path normalization to prevent Traversal (H-01)."""
        # Resolve path within directory
        path = super().translate_path(path)
        rel_path = os.path.relpath(path, self._web_hybrid_dir)
        if rel_path.startswith("..") or os.path.isabs(rel_path):
            return os.path.join(self._web_hybrid_dir, "index.html")
        return path

    def log_message(self, fmt, *args):
        pass  # Suppress HTTP logs


def _start_http_server(port: int, web_dir: str, auth_token: str) -> socketserver.TCPServer:
    """Start HTTP server for the hybrid client in a background thread.

    Security: Bound to 127.0.0.1 by default and protected by auth_token.
    """
    _HybridHTTPHandler._web_hybrid_dir = web_dir
    _HybridHTTPHandler._auth_token = auth_token
    http_host = os.environ.get("AETHERIS_HTTP_HOST", "127.0.0.1")
    server = socketserver.TCPServer((http_host, port + 1), _HybridHTTPHandler)
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

        # H-01: Session token for static file access
        self._auth_token = secrets.token_urlsafe(16)

        # Core components
        self.engine = EngineSelector()
        self.bridge = WebBridge(container_width=width, container_height=height)
        self.server = WebServer(port=ws_port)
        self._elements: List[WebElement] = []
        self._running = False
        self._http_server: Optional[socketserver.TCPServer] = None
        self._loop_thread: Optional[threading.Thread] = None

        # Set up WebSocket handlers
        self.server.set_message_handler(self._handle_ws_message)
        # H-FIX: Send initial_dom only once per new connection (C-01)
        self.server.set_connect_handler(self._handle_new_client)

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

    def _handle_new_client(self, client_id: str) -> None:
        """Send initial DOM state only once to a newly connected client. (C-01 fix)"""
        try:
            initial_dom = self.bridge.get_initial_dom_state()
            self.server.broadcast(json.dumps({
                "type": "initial_dom",
                "elements": initial_dom
            }))
            logger.debug("[Aether-Web] initial_dom sent to new client %s", client_id)
        except Exception as e:
            logger.warning("[Aether-Web] Failed to send initial_dom to %s: %s", client_id, e)

    def _handle_ws_message(self, client_id: str, message: str) -> None:
        """Handle incoming WebSocket messages from the browser.

        Security (H-03): All coordinate values are validated against NaN/Inf
        and clamped to [-MAX_COORDINATE, MAX_COORDINATE] before use.
        """
        # Guard: reject oversized messages before parsing
        if len(message) > 4096:
            logger.warning("[Aether-Web] Oversized message from %s (%d bytes), dropping",
                           client_id, len(message))
            return
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "pointerdown":
                x = _validate_coord(data.get("x", 0))
                y = _validate_coord(data.get("y", 0))
                self.engine.handle_pointer_down(x, y)
            elif msg_type == "pointermove":
                x = _validate_coord(data.get("x", 0))
                y = _validate_coord(data.get("y", 0))
                self.engine.handle_pointer_move(x, y)
            elif msg_type == "pointerup":
                self.engine.handle_pointer_up()
            elif msg_type == "input_value":
                # Validate element_id and value before assignment
                element_id = str(data.get("element_id", ""))[:_MAX_INPUT_STR_LEN]
                value = str(data.get("value", ""))[:_MAX_INPUT_STR_LEN]
                for elem in self._elements:
                    if elem._html_id == element_id and hasattr(elem, '_value'):
                        elem._value = value
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.debug("[Aether-Web] Invalid message from %s: %s", client_id, e)

    def _run_loop(self) -> None:
        """Main physics + sync loop — runs at 60 FPS.

        Security (C-01): initial_dom is NO LONGER broadcast here.
        It is sent once per client connection via _handle_new_client().
        The loop only broadcasts incremental physics updates.
        """
        target_dt = 1.0 / 60.0
        while self._running:
            t0 = time.perf_counter()

            # Physics tick
            self.engine.tick(self.width, self.height)

            # Sync incremental updates to web clients (delta only)
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
                self._http_server = _start_http_server(self.http_port, web_hybrid_dir, self._auth_token)
                host = os.environ.get("AETHERIS_HTTP_HOST", "localhost")
                print(f"[Aether-Web] HTTP server: http://{host}:{self.http_port + 1}?token={self._auth_token}")
            except OSError:
                print(f"[Aether-Web] HTTP port {self.http_port + 1} in use, skipping")

        # Start WebSocket server
        self.server.start()
        print(f"[Aether-Web] WebSocket server: ws://localhost:{self.ws_port}")
        print(f"[Aether-Web] {len(self._elements)} elements registered")
        print(f"[Aether-Web] Open http://{os.environ.get('AETHERIS_HTTP_HOST', 'localhost')}:{self.http_port + 1}?token={self._auth_token} in your browser")

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
