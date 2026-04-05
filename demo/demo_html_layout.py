# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Live demo: Loads external .html and .css files, parses them into Aetheris elements,
and runs a headless physics simulation.

Usage:
    python3 demo/demo_html_layout.py --frames 100
    python3 demo/demo_html_layout.py --html demo/sample.html --css demo/sample.css
"""
import sys
import argparse
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SAMPLE_HTML = '''
<!DOCTYPE html>
<html>
<head><title>Aetheris HTML Demo</title></head>
<body>
    <div class="main-panel" id="main">
        <h1 id="title">Aetheris UI</h1>
        <p id="subtitle">HTML/CSS Driven Physics Layout</p>
        <div class="card" id="card1">
            <h3 id="card1-title">Spring Card</h3>
            <p id="card1-desc">Hover to see spring physics</p>
            <button id="card1-btn">Activate</button>
        </div>
        <div class="card" id="card2">
            <h3 id="card2-title">Data Card</h3>
            <p id="card2-desc">Real-time data visualization</p>
            <button id="card2-btn">Refresh</button>
        </div>
        <div id="footer">
            <label id="copyright">Aetheris v1.0</label>
        </div>
    </div>
</body>
</html>
'''

SAMPLE_CSS = '''
.main-panel {
    background-color: #1a1a2e;
    width: 90%;
    height: 90%;
    padding: 5%;
}

#title {
    color: #e63399cc;
    font-size: 32px;
}

#subtitle {
    color: #a0a0b0;
    font-size: 16px;
}

.card {
    background-color: #16213e;
    width: 300px;
    height: 150px;
    padding: 10px;
}

.card:hover {
    transform: scale(1.1);
    transition: transform 0.3s aether-spring(k=20, c=1.5);
}

button {
    background-color: #e94560;
    width: 120px;
    height: 40px;
}

#footer {
    background-color: #0f3460;
    width: 100%;
    height: 50px;
}

#copyright {
    color: #a0a0b0;
    font-size: 12px;
}
'''


def load_file(path: str, fallback: str) -> str:
    """Load content from file or return fallback string."""
    if path and Path(path).exists():
        return Path(path).read_text()
    return fallback


def run_demo(html_path: str = '', css_path: str = '', frames: int = 100) -> bool:
    """
    Load HTML/CSS, build UI, run headless simulation.

    Args:
        html_path: Path to HTML file (uses sample if not found)
        css_path: Path to CSS file (uses sample if not found)
        frames: Number of simulation frames to run

    Returns:
        True if simulation completed without errors
    """
    from core.engine import AetherEngine
    from core.ui_builder import UIBuilder

    html_str = load_file(html_path, SAMPLE_HTML)
    css_str = load_file(css_path, SAMPLE_CSS)

    print(f"[HTML] Parsing {'file: ' + html_path if html_path else 'sample HTML'}...")
    print(f"[CSS]  Parsing {'file: ' + css_path if css_path else 'sample CSS'}...")

    engine = AetherEngine()
    builder = UIBuilder()

    count = builder.build_from_html(engine, html_str, css_str)
    print(f"[OK] Created {count} elements from HTML/CSS")

    print(f"\n[ENGINE] Running {frames} frames of headless simulation...")
    for i in range(frames):
        data = engine.tick(1280, 720)
        if np.any(np.isnan(data['rect'])) or np.any(np.isnan(data['color'])):
            print(f"[FAIL] NaN detected at frame {i}")
            return False

    print(f"[OK] {frames} frames completed — numerical stability verified")

    print("\n[ELEMENTS] Summary:")
    for elem_id, elem in builder._element_refs.items():
        state = elem.tensor.state
        print(f"  {elem_id:20s} type={elem.__class__.__name__:20s} "
              f"pos=({state[0]:.1f}, {state[1]:.1f}) size=({state[2]:.1f}, {state[3]:.1f})")

    if builder._element_refs:
        print(f"\n[OK] All {len(builder._element_refs)} elements rendered successfully")

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Aetheris HTML/CSS Layout Demo')
    parser.add_argument('--html', type=str, default='', help='Path to HTML file')
    parser.add_argument('--css', type=str, default='', help='Path to CSS file')
    parser.add_argument('--frames', type=int, default=100, help='Number of simulation frames')
    args = parser.parse_args()

    success = run_demo(html_path=args.html, css_path=args.css, frames=args.frames)
    sys.exit(0 if success else 1)
