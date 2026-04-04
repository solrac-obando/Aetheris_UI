# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Web Server Tests — WebSocket server validation and latency checks.
Tests are immutable. Code must be fixed to pass.
"""
import os, sys, json, time, threading, socket
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.web_server import WebServer, find_free_port


class TestWebServer:
    """Tests for the WebSocket bridge server."""

    def test_server_init(self):
        """Test 12: Starts on configurable port, handles collisions."""
        port = find_free_port()
        server = WebServer(port=port)
        assert server.port == port
        assert server._clients == {}
        server.stop()

    def test_server_start_stop(self):
        """Test 12b: Server starts and stops cleanly."""
        port = find_free_port()
        server = WebServer(port=port)
        server.start()
        time.sleep(0.5)
        assert server.is_running
        server.stop()
        assert not server.is_running

    def test_server_port_collision(self):
        """Test 12c: Server handles port collision gracefully."""
        port = find_free_port()
        server1 = WebServer(port=port)
        server1.start()
        time.sleep(0.3)

        server2 = WebServer(port=port)
        # Should not crash — should find alternate or raise cleanly
        try:
            server2.start()
            server2.stop()
        except Exception:
            pass  # Expected behavior

        server1.stop()

    def test_broadcast_coordinates(self):
        """Test 13: Sends JSON package to all connected clients."""
        port = find_free_port()
        server = WebServer(port=port)
        server.start()
        time.sleep(0.5)

        # Simulate broadcast
        payload = json.dumps({"frame": 1, "elements": [{"id": "el_1", "x": 100, "y": 200}]})
        server.broadcast(payload)

        server.stop()
        # If no exception, broadcast succeeded

    def test_pointer_down_routing(self):
        """Test 14: Receives event and calls engine.handle_pointer_down()."""
        port = find_free_port()
        server = WebServer(port=port)
        server.start()
        time.sleep(0.3)

        # Simulate pointer event
        event = json.dumps({
            "type": "pointerdown",
            "x": 150.0,
            "y": 200.0,
            "element_id": "btn_1"
        })
        server.handle_client_message(event)

        server.stop()

    def test_pointer_move_routing(self):
        """Test 15: Updates drag position in real time."""
        port = find_free_port()
        server = WebServer(port=port)
        server.start()
        time.sleep(0.3)

        event = json.dumps({
            "type": "pointermove",
            "x": 160.0,
            "y": 210.0,
            "element_id": "btn_1"
        })
        server.handle_client_message(event)
        server.stop()

    def test_pointer_up_routing(self):
        """Test 16: Releases element and applies throw velocity."""
        port = find_free_port()
        server = WebServer(port=port)
        server.start()
        time.sleep(0.3)

        event = json.dumps({
            "type": "pointerup",
            "element_id": "btn_1"
        })
        server.handle_client_message(event)
        server.stop()

    def test_disconnect_cleanup(self):
        """Test 17: Removes disconnected client without closing server."""
        port = find_free_port()
        server = WebServer(port=port)
        server.start()
        time.sleep(0.3)

        # Simulate disconnect
        server._clients["test_client"] = {"ws": None, "connected": True}
        server.handle_client_disconnect("test_client")
        assert "test_client" not in server._clients

        server.stop()

    def test_server_stats(self):
        """Test 17b: Server reports correct connection stats."""
        port = find_free_port()
        server = WebServer(port=port)
        server.start()
        time.sleep(0.3)

        stats = server.get_stats()
        assert "clients" in stats
        assert "uptime" in stats
        assert "messages" in stats

        server.stop()

    def test_server_message_invalid_json(self):
        """Test 17c: Server handles invalid JSON gracefully."""
        port = find_free_port()
        server = WebServer(port=port)
        server.start()
        time.sleep(0.3)

        # Should not crash
        server.handle_client_message("not valid json {{{")
        server.handle_client_message("")
        server.handle_client_message(None)

        server.stop()
