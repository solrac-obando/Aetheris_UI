# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""Simple HTTP server for Aether-Web WASM Sandbox."""
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

WEB_DIR = Path(__file__).parent


class WASMHandler(SimpleHTTPRequestHandler):
    """Serve web files with correct MIME types for WASM/Pyodide."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self):
        # CORS headers for Pyodide
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def log_message(self, fmt, *args):
        print(f"[Aether-Web] {fmt % args}")


def main(port=8080):
    os.chdir(str(WEB_DIR))
    server = HTTPServer(('0.0.0.0', port), WASMHandler)
    print(f"=" * 50)
    print(f"  AETHER-WEB Sandbox Server")
    print(f"  http://localhost:{port}")
    print(f"  Serving: {WEB_DIR}")
    print(f"=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Aether-Web] Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
