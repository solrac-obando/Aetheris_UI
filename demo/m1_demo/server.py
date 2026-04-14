#!/usr/bin/env python3
"""
Aetheris M1 Demo Server
LightWASM Adapter integration demo
"""
import json
import time
import os
from flask import Flask, render_template, request, jsonify

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import M1 LightWASM Adapter
from wasm.light_wasm_adapter import LightWASMAdapter

app = Flask(__name__, template_folder='.')

# Initialize M1 Adapter
ADAPTER = None
ELEMENT_MAP = {}

def get_adapter():
    global ADAPTER
    if ADAPTER is None:
        ADAPTER = LightWASMAdapter(
            container_width=800.0,
            container_height=400.0
        )
    return ADAPTER


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/init', methods=['GET'])
def init():
    adapter = get_adapter()
    return jsonify({
        'adapter_type': str(adapter.adapter_type),
        'bundle_size': adapter.bundle_size,
        'max_elements': 20000
    })


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    adapter = get_adapter()
    
    adapter.register_element(
        index=data.get('index', 0),
        html_id=data.get('id', 'elem-0'),
        metadata=data.get('metadata', {})
    )
    
    return jsonify({'status': 'ok', 'count': adapter.element_count})


@app.route('/unregister', methods=['POST'])
def unregister():
    data = request.json
    adapter = get_adapter()
    
    adapter.unregister_element(data.get('index', 0))
    
    return jsonify({'status': 'ok', 'count': adapter.element_count})


@app.route('/sync', methods=['POST'])
def sync():
    data = request.json
    elements = data.get('elements', [])
    
    adapter = get_adapter()
    
    # Convert frontend element format to AetherEngine-like objects
    class MockElement:
        def __init__(self, x, y, w, h, idx):
            self._z_index = idx
            self.tensor = type('obj', (object,), {
                'state': [x, y, w, h]
            })()
    
    mock_elements = [
        MockElement(e['x'], e['y'], e['w'], e['h'], i)
        for i, e in enumerate(elements)
    ]
    
    # Get sync from M1 adapter
    start = time.perf_counter()
    result = adapter.sync(mock_elements)
    elapsed = (time.perf_counter() - start) * 1000
    
    # Parse result
    result_data = json.loads(result)
    
    return jsonify({
        'elements': result_data.get('elements', []),
        'frame': result_data.get('frame', 0),
        'adapter_type': str(adapter.adapter_type),
        'sync_time': elapsed
    })


@app.route('/reset', methods=['POST'])
def reset():
    global ADAPTER
    ADAPTER = None
    return jsonify({'status': 'reset'})


@app.route('/stats', methods=['GET'])
def stats():
    adapter = get_adapter()
    return jsonify(adapter.stats)


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Aetheris M1 Demo Server")
    print("=" * 50)
    print("LightWASM Adapter - Starting...")
    print()
    print("Open your browser at: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)