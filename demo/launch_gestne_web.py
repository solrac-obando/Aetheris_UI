import http.server
import socketserver
import webbrowser
import threading
import os
import sys

PORT = 8081
DIRECTORY = os.path.join(os.path.dirname(__file__), 'gestne_web')

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Servidor GESTNE activo en http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    print("--- Lanzador de Dashboard Web Aetheris | GESTNE ---")
    
    # Start server in a thread so it doesn't block the script execution (optional, but clean)
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Give it a second to start
    import time
    time.sleep(1)
    
    url = f"http://localhost:{PORT}/index.html"
    print(f"Abriendo visualización en el navegador: {url}")
    webbrowser.open(url)
    
    print("\nPresione CTRL+C para cerrar el servidor.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nServidor cerrado.")
        sys.exit(0)
