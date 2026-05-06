# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");

import os
import sys
import json

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

def generate_premium_dashboard():
    """Generates a high-end dashboard intent for Aetheris UI."""
    
    intent = {
        "layout": "dashboard",
        "theme": "nebula_dark",
        "elements": [
            # Background Attractor (Dynamic Background)
            {
                "id": "bg_gravity",
                "type": "aether_attractor",
                "x": 600, "y": 400,
                "strength": 0.5,
                "radius": 1000
            },
            # Header
            {
                "id": "header_panel",
                "type": "smart_panel",
                "x": 20, "y": 20, "w": 1160, "h": 80,
                "color": [0.1, 0.1, 0.15, 0.8],
                "z": 1,
                "padding": 0.01
            },
            {
                "id": "app_title",
                "type": "canvas_text",
                "x": 40, "y": 45, "w": 300, "h": 40,
                "text_content": "AETHERIS COMMAND CENTER",
                "font_size": 28,
                "color": [0.0, 0.8, 1.0, 1.0]
            },
            # Main Stats Row
            {
                "id": "cpu_gauge",
                "type": "aether_gauge",
                "x": 20, "y": 120, "w": 280, "h": 200,
                "label": "CPU UTILIZATION",
                "value": 42.5,
                "color": [0.0, 0.9, 0.4, 0.9]
            },
            {
                "id": "memory_sparkline",
                "type": "aether_sparkline",
                "x": 310, "y": 120, "w": 570, "h": 200,
                "label": "MEMORY LOAD (VIRTUAL)",
                "data": [30, 45, 32, 67, 89, 45, 56, 78, 90, 85],
                "color": [0.8, 0.2, 0.9, 0.9]
            },
            {
                "id": "engine_status",
                "type": "aether_status_orb",
                "x": 890, "y": 120, "w": 290, "h": 200,
                "label": "ENGINE CLUSTER",
                "status": "ok",
                "pulse_frequency": 2.0
            },
            # Main Content Area
            {
                "id": "main_content",
                "type": "aether_window",
                "x": 20, "y": 340, "w": 860, "h": 440,
                "title": "SYSTEM TELEMETRY DATA",
                "color": [0.05, 0.05, 0.1, 0.6]
            },
            {
                "id": "physics_heatmap",
                "type": "aether_heatmap",
                "x": 40, "y": 400, "w": 820, "h": 360,
                "rows": 8, "cols": 12,
                "data": [0.1, 0.5, 0.9, 0.2, 0.4, 0.8] * 16
            },
            # Side Control Panel
            {
                "id": "control_panel",
                "type": "smart_panel",
                "x": 890, "y": 340, "w": 290, "h": 440,
                "color": [0.12, 0.12, 0.18, 0.85],
                "title": "ENGINE CONTROLS"
            },
            {
                "id": "toggle_rust",
                "type": "aether_kinetic_toggle",
                "x": 910, "y": 400, "w": 250, "h": 60,
                "label": "RUST ACCELERATION",
                "is_on": True
            },
            {
                "id": "optimize_btn",
                "type": "smart_button",
                "parent": "control_panel",
                "offset_x": 20, "offset_y": 300, "offset_w": 250, "offset_h": 60,
                "color": [0.0, 0.5, 1.0, 1.0],
                "text_content": "OPTIMIZE CLUSTER"
            }
        ],
        "animation": "quantum_elastic",
        "transition_speed_ms": 800
    }
    
    with open(os.path.join(PROJECT_ROOT, "static", "dashboard_intent.json"), "w") as f:
        json.dump(intent, f, indent=2)
    
    print("✨ Premium Dashboard Intent generated in static/dashboard_intent.json")

if __name__ == "__main__":
    generate_premium_dashboard()
