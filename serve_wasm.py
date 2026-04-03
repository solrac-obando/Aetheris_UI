"""
Local development server for Aetheris UI WASM/Pyodide.

Modern browsers require specific CORS/COOP headers for Pyodide to work:
- Cross-Origin-Opener-Policy: same-origin
- Cross-Origin-Embedder-Policy: require-corp

Usage:
    python3 serve_wasm.py

Then open: http://localhost:8080/wasm/index.html
"""
import http.server
import socketserver
import os

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class WASMHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with required headers for Pyodide/WASM."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Required headers for SharedArrayBuffer (Pyodide needs these)
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def log_message(self, format, *args):
        """Custom log format with colored output."""
        print(f"[Aetheris Server] {args[0]}")


def main():
    with socketserver.TCPServer(("", PORT), WASMHandler) as httpd:
        print(f"=" * 50)
        print(f"Aetheris UI - WASM Development Server")
        print(f"=" * 50)
        print(f"Serving from: {DIRECTORY}")
        print(f"Open: http://localhost:{PORT}/wasm/index.html")
        print(f"Press Ctrl+C to stop")
        print(f"=" * 50)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
