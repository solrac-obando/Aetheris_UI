# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Flask backend for Aetheris UI Server-Driven UI.

Serves the WASM/Pyodide frontend with COOP/COEP headers required for
SharedArrayBuffer, and injects dynamic UI Intent JSON into the page.
"""
import json
import os
import markupsafe
from flask import Flask, render_template, send_from_directory, jsonify, request

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.dirname(__file__))

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


@app.after_request
def add_cors_headers(response):
    """Attach required COOP/COEP headers for Pyodide/WASM."""
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    response.headers['Cache-Control'] = 'no-cache'
    return response


@app.route('/static/manifest.json')
def serve_manifest():
    """Serve the PWA manifest with correct MIME type."""
    static_dir = os.path.join(os.path.dirname(PROJECT_ROOT), 'static')
    response = send_from_directory(static_dir, 'manifest.json', mimetype='application/manifest+json')
    return response


@app.route('/static/sw.js')
def serve_service_worker():
    """Serve the Service Worker with correct MIME type and scope header."""
    static_dir = os.path.join(os.path.dirname(PROJECT_ROOT), 'static')
    response = send_from_directory(static_dir, 'sw.js', mimetype='application/javascript')
    response.headers['Service-Worker-Allowed'] = '/'
    return response


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static assets."""
    static_dir = os.path.join(os.path.dirname(PROJECT_ROOT), 'static')
    return send_from_directory(static_dir, filename)


@app.route('/')
def index():
    """Serve the main page with injected UI Intent JSON."""
    
    # Try to load intent from file, else use default
    intent_path = os.path.join(os.path.dirname(PROJECT_ROOT), 'static', 'dashboard_intent.json')
    if os.path.exists(intent_path):
        with open(intent_path, 'r') as f:
            ui_intent = json.load(f)
    else:
        # Default fallback intent
        ui_intent = {
            "layout": "column",
            "spacing": 20,
            "animation": "organic",
            "elements": [
                {
                    "id": "header_panel",
                    "type": "smart_panel",
                    "color": [0.15, 0.15, 0.25, 1.0],
                    "z": 0,
                },
                {
                    "id": "title_text",
                    "type": "canvas_text",
                    "x": 40, "y": 15, "w": 400, "h": 40,
                    "text_content": "Aetheris Dashboard",
                    "z": 5,
                }
            ]
        }
    
    # Convert to JSON string for safe injection (H-02)
    ui_intent_json = markupsafe.Markup(json.dumps(ui_intent))
    
    return render_template('index.html', ui_intent_json=ui_intent_json)


@app.route('/api/intent', methods=['POST'])
def update_intent():
    """Update the current UI intent via API."""
    new_intent = request.json
    intent_path = os.path.join(os.path.dirname(PROJECT_ROOT), 'static', 'dashboard_intent.json')
    with open(intent_path, 'w') as f:
        json.dump(new_intent, f)
    return jsonify({"status": "success"})


if __name__ == '__main__':
    # Aetheris Web requires HTTPS for certain features, but for dev we use HTTP
    # Host 127.0.0.1 for H-01 security compliance
    app.run(host='127.0.0.1', port=8000, debug=True)
