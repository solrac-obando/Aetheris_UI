"""
Flask backend for Aetheris UI Server-Driven UI.

Serves the WASM/Pyodide frontend with COOP/COEP headers required for
SharedArrayBuffer, and injects dynamic UI Intent JSON into the page.
"""
import json
import os
from flask import Flask, render_template, send_from_directory, jsonify

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
    static_dir = os.path.join(PROJECT_ROOT, 'static')
    response = send_from_directory(static_dir, 'manifest.json', mimetype='application/manifest+json')
    return response


@app.route('/static/sw.js')
def serve_service_worker():
    """Serve the Service Worker with correct MIME type and scope header.
    
    The Service-Worker-Allowed header tells the browser this SW can control
    the entire origin (/), not just its own directory (/static/).
    """
    static_dir = os.path.join(PROJECT_ROOT, 'static')
    response = send_from_directory(static_dir, 'sw.js', mimetype='application/javascript')
    response.headers['Service-Worker-Allowed'] = '/'
    return response


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static assets (icons, etc.)."""
    static_dir = os.path.join(PROJECT_ROOT, 'static')
    return send_from_directory(static_dir, filename)


@app.route('/')
def index():
    """Serve the main page with injected UI Intent JSON."""
    
    # Define the UI Intent - this is the server-driven configuration
    # In production, this would come from a database or CMS
    ui_intent = {
        "layout": "column",
        "spacing": 20,
        "animation": "organic",
        "padding": 10,
        "transition_speed_ms": 300,
        "elements": [
            {
                "id": "header_panel",
                "type": "smart_panel",
                "padding": 0.03,
                "color": [0.15, 0.15, 0.25, 1.0],
                "z": 0,
            },
            {
                "id": "title_text",
                "type": "canvas_text",
                "x": 40,
                "y": 15,
                "w": 400,
                "h": 40,
                "color": [0, 0, 0, 0],
                "text_color": [1.0, 1.0, 1.0, 1.0],
                "font_size": 24,
                "font_family": "Arial",
                "text_content": "Aetheris Hybrid Canvas Text",
                "z": 5,
            },
            {
                "id": "content_panel",
                "type": "smart_panel",
                "padding": 0.05,
                "color": [0.2, 0.2, 0.3, 0.9],
                "z": 1,
            },
            {
                "id": "card_1",
                "type": "static_box",
                "x": 30,
                "y": 30,
                "w": 150,
                "h": 200,
                "color": [0.8, 0.2, 0.3, 0.9],
                "z": 2,
            },
            {
                "id": "card_2",
                "type": "static_box",
                "x": 200,
                "y": 30,
                "w": 150,
                "h": 200,
                "color": [0.2, 0.6, 0.9, 0.9],
                "z": 2,
            },
            {
                "id": "card_3",
                "type": "static_box",
                "x": 370,
                "y": 30,
                "w": 150,
                "h": 200,
                "color": [0.9, 0.7, 0.2, 0.9],
                "z": 2,
            },
            {
                "id": "action_button",
                "type": "smart_button",
                "parent": "content_panel",
                "offset_x": 20,
                "offset_y": 250,
                "offset_w": 120,
                "offset_h": 40,
                "color": [0.3, 0.8, 0.3, 1.0],
                "z": 3,
            },
            {
                "id": "description",
                "type": "dom_text",
                "x": 50,
                "y": 300,
                "w": 500,
                "h": 100,
                "color": [0, 0, 0, 0],
                "text_color": [0.8, 0.8, 0.8, 1.0],
                "font_size": 16,
                "font_family": "Arial",
                "text_content": "This is selectable HTML text driven by a physics engine.",
                "z": 10,
            },
        ]
    }
    
    # Convert to JSON string for safe injection
    ui_intent_json = json.dumps(ui_intent)
    
    return render_template('index.html', ui_intent_json=ui_intent_json)


@app.route('/wasm/<path:filename>')
def serve_wasm(filename):
    """Serve WASM/JS files from the wasm directory."""
    wasm_dir = os.path.join(PROJECT_ROOT, 'wasm')
    return send_from_directory(wasm_dir, filename)


@app.route('/core/<path:filename>')
def serve_core(filename):
    """Serve core Python files for Pyodide mounting."""
    core_dir = os.path.join(PROJECT_ROOT, 'core')
    return send_from_directory(core_dir, filename)


@app.route('/api/intent', methods=['GET'])
def get_intent():
    """API endpoint to get the current UI Intent (for debugging)."""
    # Same intent as index page - in production this would be dynamic
    ui_intent = {
        "layout": "column",
        "spacing": 20,
        "animation": "organic",
        "padding": 10,
        "transition_speed_ms": 300,
        "elements": [
            {"id": "header_panel", "type": "smart_panel", "padding": 0.03, "color": [0.15, 0.15, 0.25, 1.0], "z": 0},
            {"id": "title_text", "type": "canvas_text", "x": 40, "y": 15, "w": 400, "h": 40, "color": [0, 0, 0, 0], "text_color": [1.0, 1.0, 1.0, 1.0], "font_size": 24, "text_content": "Aetheris Hybrid Canvas Text", "z": 5},
            {"id": "content_panel", "type": "smart_panel", "padding": 0.05, "color": [0.2, 0.2, 0.3, 0.9], "z": 1},
            {"id": "card_1", "type": "static_box", "x": 30, "y": 30, "w": 150, "h": 200, "color": [0.8, 0.2, 0.3, 0.9], "z": 2},
            {"id": "card_2", "type": "static_box", "x": 200, "y": 30, "w": 150, "h": 200, "color": [0.2, 0.6, 0.9, 0.9], "z": 2},
            {"id": "card_3", "type": "static_box", "x": 370, "y": 30, "w": 150, "h": 200, "color": [0.9, 0.7, 0.2, 0.9], "z": 2},
            {"id": "action_button", "type": "smart_button", "parent": "content_panel", "offset_x": 20, "offset_y": 250, "offset_w": 120, "offset_h": 40, "color": [0.3, 0.8, 0.3, 1.0], "z": 3},
            {"id": "description", "type": "dom_text", "x": 50, "y": 300, "w": 500, "h": 100, "color": [0, 0, 0, 0], "text_color": [0.8, 0.8, 0.8, 1.0], "font_size": 16, "text_content": "This is selectable HTML text driven by a physics engine.", "z": 10},
        ]
    }
    return jsonify(ui_intent)


if __name__ == '__main__':
    print("=" * 50)
    print("Aetheris UI - Flask Server-Driven UI")
    print("=" * 50)
    print("Open: http://localhost:5000/")
    print("API:  http://localhost:5000/api/intent")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
