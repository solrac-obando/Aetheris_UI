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


# ============================================================================
# Aether-Data Bridge: Server-Side PostgreSQL Simulation
# ============================================================================

# Simulated movie database (in production, this would be a real PostgreSQL connection)
SIMULATED_MOVIES = [
    {"id": 1, "title": "The Matrix", "rating": 8.7, "year": 1999, "rating_count": 1800000, "genre": "Sci-Fi"},
    {"id": 2, "title": "Inception", "rating": 8.8, "year": 2010, "rating_count": 2300000, "genre": "Sci-Fi"},
    {"id": 3, "title": "Interstellar", "rating": 8.6, "year": 2014, "rating_count": 1700000, "genre": "Sci-Fi"},
    {"id": 4, "title": "The Dark Knight", "rating": 9.0, "year": 2008, "rating_count": 2600000, "genre": "Action"},
    {"id": 5, "title": "Pulp Fiction", "rating": 8.9, "year": 1994, "rating_count": 2000000, "genre": "Crime"},
    {"id": 6, "title": "Fight Club", "rating": 8.8, "year": 1999, "rating_count": 2100000, "genre": "Drama"},
    {"id": 7, "title": "Forrest Gump", "rating": 8.8, "year": 1994, "rating_count": 2000000, "genre": "Drama"},
    {"id": 8, "title": "The Shawshank Redemption", "rating": 9.3, "year": 1994, "rating_count": 2700000, "genre": "Drama"},
]


@app.route('/api/v1/db-bridge', methods=['GET', 'POST'])
def db_bridge():
    """
    Aether-Data Bridge endpoint.
    
    This endpoint simulates a PostgreSQL database response for the
    RemoteAetherProvider. In production, this would connect to a real
    PostgreSQL database and execute queries server-side.
    
    Security: DB credentials are NEVER exposed to the client.
    All query validation and sanitization happens server-side.
    
    GET: Returns bridge status.
    POST: Executes a simulated database operation.
          Payload: {"action": "query|insert|get|delete", ...}
    """
    if request.method == 'GET':
        return jsonify({
            "status": "connected",
            "provider": "simulated_postgres",
            "tables": ["movies", "element_states"],
        })
    
    data = request.get_json(silent=True) or {}
    action = data.get('action', 'query')
    
    if action == 'query':
        query = data.get('query', 'SELECT * FROM movies')
        
        # Simulate SQL parsing for basic movie queries
        if 'movies' in query.lower():
            # Simulate WHERE clause
            genre_filter = None
            if 'genre' in query.lower():
                for movie in SIMULATED_MOVIES:
                    if movie['genre'].lower() in query.lower():
                        genre_filter = movie['genre']
                        break
            
            if genre_filter:
                results = [m for m in SIMULATED_MOVIES if m['genre'] == genre_filter]
            else:
                results = SIMULATED_MOVIES
            
            return jsonify({"success": True, "data": results, "count": len(results)})
        
        return jsonify({"success": True, "data": [], "count": 0})
    
    elif action == 'insert':
        element_id = data.get('element_id', '')
        state = data.get('state', {})
        return jsonify({"success": True, "element_id": element_id, "message": "State saved"})
    
    elif action == 'get':
        element_id = data.get('element_id', '')
        # Return a simulated element state
        return jsonify({
            "success": True,
            "data": [{"element_id": element_id, "x": 100.0, "y": 100.0, "w": 200.0, "h": 150.0, "z": 0}],
        })
    
    elif action == 'delete':
        element_id = data.get('element_id', '')
        return jsonify({"success": True, "element_id": element_id, "message": "State deleted"})
    
    return jsonify({"success": False, "error": f"Unknown action: {action}"}), 400


@app.route('/odyssey')
def odyssey():
    """Serve the Odyssey demo page."""
    return render_template('odyssey.html')


@app.route('/api/odyssey/elements')
def odyssey_elements():
    """API endpoint returning Odyssey media elements for the web frontend."""
    from demo.odyssey_db import create_database
    from core.data_bridge import SQLiteProvider
    
    db_path = os.path.join(PROJECT_ROOT, 'demo', 'odyssey.db')
    if not os.path.exists(db_path):
        create_database(db_path)
    
    provider = SQLiteProvider(db_path)
    provider.connect()
    rows = provider.execute_query("SELECT * FROM media ORDER BY year ASC")
    provider.disconnect()
    
    return jsonify({"elements": rows, "count": len(rows)})


if __name__ == '__main__':
    print("=" * 50)
    print("Aetheris UI - Flask Server-Driven UI")
    print("=" * 50)
    print("Open: http://localhost:5000/")
    print("API:  http://localhost:5000/api/intent")
    print("Odyssey: http://localhost:5000/odyssey")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
