import json
import os
import numpy as np

# 50,000 elements
elements = []
for i in range(50000):
    elements.append({
        "id": f"e_{i}",
        "type": "static_box",
        "x": np.random.uniform(0, 1280),
        "y": np.random.uniform(0, 720),
        "w": 2,
        "h": 2,
        "color": [
            np.random.uniform(0.1, 0.3),
            np.random.uniform(0.6, 0.9),
            np.random.uniform(0.8, 1.0),
            0.6
        ],
        "z": 0
    })

intent = {
    "layout": "absolute",
    "theme": "nebula_dark",
    "elements": elements,
    "animation": "fluid",
    "transition_speed_ms": 300
}

# Write to static/dashboard_intent.json (which is loaded by app_server.py)
output_path = "/home/carlosobando/proyectos_kivy/aetheris_UI/static/dashboard_intent.json"
with open(output_path, "w") as f:
    json.dump(intent, f)

print(f"✅ Generated 50,000 objects intent at {output_path}")
