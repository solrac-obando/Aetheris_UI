# Aetheris UI

> **Physics-as-UI** — The first high-performance UI engine driven by linear algebra for Python & WebAssembly.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-375%20passing-brightgreen.svg)](tests/)

Aetheris UI treats user interface layout as a **dynamic physical system** governed by the laws of classical mechanics. Instead of static positioning rules, every UI element is a particle with position, velocity, and acceleration — evolving through **Euler integration** with **Hooke's Law** restoring forces, **critical damping**, and **L2 norm clamping** for numerical stability.

The same Python physics logic drives **three native rendering pipelines**: HTML5 Canvas via Pyodide/WASM, desktop OpenGL via ModernGL, and mobile via Kivy — all consuming the same structured NumPy data bridge.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [The Multi-Renderer Trinity](#the-multi-renderer-trinity)
- [Architecture Overview](#architecture-overview)
- [Mathematical Foundations](#mathematical-foundations)
- [API Reference](#api-reference)
- [Use Cases](#use-cases)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Physics-Driven Audio Integration** — Non-blocking, platform-agnostic audio bridge (`AetherAudioBridge`). Supports `impact`, `settle`, and `collision` triggers directly derived from physical state changes.
- **HPC-Optimized Core** — Numba-accelerated vectorized physics kernels. Parallel batch processing for large-scale UI simulations (10 to 5,000+ elements).
- **32-Component Library** — A comprehensive library of physics-aware components across 4 categories: Dashboard (Gauges, Orbs), Interactive (Toggles, Sliders), Desktop (Windows, Modals), and Layout (Grids, Stacks).
- **Aether-Guard Safety** — Industrial-grade numerical stability. L2 norm clamping, epsilon-protected division, and NaN/Inf sanitization prevent engine collapses under extreme forces.
- **HTML/CSS Hydration** — Declarative UI definition via `AetherHTMLParser`. Maps standard HTML tags and CSS-like attributes to physics properties with kebab-to-snake normalization.

---

## Installation

### Prerequisites

- Python 3.12+
- NumPy 1.26.4+
- For WASM: A modern browser with SharedArrayBuffer support (requires COOP/COEP headers)

### Desktop (ModernGL Renderer)

```bash
git clone https://github.com/your-org/aetheris-ui.git
cd aetheris-ui
pip install -r requirements.txt

# Run with GPU renderer (headless validation)
xvfb-run -a python3 main.py --gl --frames 50

# Run with Tkinter debug renderer
python3 main.py --tkinter

# Run with MockRenderer (headless, no display)
python3 main.py
```

### Web (Pyodide/WASM Renderer)

```bash
# Start the Flask server with PWA support
python3 app_server.py

# Open in browser
# http://localhost:5000/
```

The Flask server serves the PWA manifest, Service Worker, and injects the UI Intent JSON. The browser loads Pyodide (~15MB), mounts the Python core files into the virtual filesystem, and runs the physics engine at 60 FPS.

### Mobile (Kivy Renderer)

```bash
# Run with Kivy renderer
python3 main.py --kivy
```

Kivy handles the event loop, canvas drawing, and Y-axis coordinate inversion automatically.

### Docker

```bash
docker build -t aetheris-ui .
docker run --rm aetheris-ui
```

---

## Quick Start

### Hello Physics

```python
from core.engine import AetherEngine
from core.elements import SmartPanel
from core.renderer_base import MockRenderer

# 1. Create the physics engine
engine = AetherEngine()

# 2. Register a responsive panel (5% padding from all edges)
panel = SmartPanel(color=(0.9, 0.2, 0.6, 0.8), z=0)
engine.register_element(panel)

# 3. Create a renderer
renderer = MockRenderer()
renderer.init_window(800, 600, "Hello Physics")

# 4. Run the physics loop
for frame in range(60):
    # The engine calculates forces, integrates physics, and returns
    # a structured NumPy array for the renderer
    data = engine.tick(800, 600)
    
    renderer.clear_screen((0.1, 0.1, 0.1, 1.0))
    renderer.render_frame(data)
    renderer.swap_buffers()
    
    # The panel smoothly converges to its asymptote:
    # x = 800 * 0.05 = 40, y = 600 * 0.05 = 30
    # w = 800 * 0.90 = 720, h = 600 * 0.90 = 540
    if frame % 10 == 0:
        print(f"Frame {frame}: rect={data[0]['rect']}")
```

### Server-Driven Layout

```python
from core.engine import AetherEngine
from core.ui_builder import UIBuilder

engine = AetherEngine()

intent = {
    "layout": "column",
    "spacing": 20,
    "animation": "organic",
    "padding": 10,
    "elements": [
        {"id": "header", "type": "smart_panel", "padding": 0.03, "z": 0},
        {"id": "title", "type": "canvas_text", "x": 40, "y": 15, "w": 400, "h": 40,
         "text_content": "Hello Aetheris", "font_size": 24, "z": 5},
        {"id": "content", "type": "smart_panel", "padding": 0.05, "z": 1},
    ]
}

builder = UIBuilder()
builder.build_from_intent(engine, intent)
# engine now has 3 elements with physics-driven positions
```

### Database-Driven Layout (Aether-Data Bridge)

```python
from core.engine import AetherEngine
from core.ui_builder import UIBuilder
from core.data_bridge import SQLiteProvider, min_max_scale

# Create engine and builder
engine = AetherEngine()
builder = UIBuilder()

# Connect to a local SQLite database
db = SQLiteProvider("./my_app.db")
db.connect()

# Define how DB columns map to physics properties with Min-Max normalization
template = {
    "type": "static_box",
    "columns": {
        "x": {"source": "pos_x", "scale": [0, 1000, 10, 790]},
        "y": {"source": "pos_y", "scale": [0, 1000, 10, 590]},
        "w": {"source": "width", "scale": [0, 10000, 50, 500]},
        "h": {"source": "height", "scale": [0, 10000, 50, 500]},
        "z": {"source": "layer"},
    },
    "metadata_fields": ["title", "rating"],
}

# Build elements directly from database query
count = builder.build_from_datasource(engine, db, "SELECT * FROM movies", template)
print(f"Created {count} elements from database")

db.disconnect()
```

### AI Embedding Visualization

```python
from core.data_bridge import vector_to_tensor

# Convert a PostgreSQL vector embedding into a physics force
embedding = [0.5, -0.3, 0.8, -0.1]  # AI embedding from pgvector
force = vector_to_tensor(embedding, scale=100.0)
# force = [50.0, -30.0, 80.0, -10.0] — ready for StateTensor.apply_force()
```

---

## Component Gallery (The 32-Component Suite)

Aetheris UI includes 32 pre-built components designed for high-performance dashboards and interactive tools:

### Dashboard & Metrics
- `AetherGauge`: Rotational spring needle with damping.
- `AetherSparkline`: Real-time minimal k-vector plot.
- `AetherStatusOrb`: Pulsing frequency-based light.
- `AetherValueMetric`: Unit-aware numeric node.
- `AetherRadialProgress`: Circular fill with elastic snap.

### Interactive Controls
- `AetherKineticToggle`: Binary switch with inertia.
- `AetherPhysicsSlider`: Spring-loaded range control.
- `AetherMagnetButton`: Button with cursor-attraction forces.
- `AetherElasticInput`: Text input with vibration feedbacks.

### Desktop & Containers
- `AetherWindow`: Gravity-anchored title bar container.
- `AetherModal`: Scaled overlay with spring entry.
- `AetherSideNav`: Sliding panel with elastic friction.
- `AetherToolbar`: staggered entry button array.

### Layout & Grids
- `AetherHeatMap`: Physics-normalized grid cells.
- `AetherGravityGrid`: Self-organizing masonry layout.
- `AetherElasticStack`: Layered cards with depth-sorting.

---

## The Multi-Renderer Trinity

Aetheris UI's core innovation is the **decoupled rendering architecture**. The physics engine produces a single structured NumPy array per frame:

```python
dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')]
```

This array — containing `[x, y, width, height]`, `[r, g, b, a]`, and `z_index` for each element — is the **only** data the renderer receives. The renderer has zero knowledge of `DifferentialElement` objects, spring constants, or asymptote calculations.

| Renderer | Technology | Text Support | Platform |
|----------|-----------|--------------|----------|
| **GLRenderer** | ModernGL + SDF shaders + Pillow textures | GPU-rasterized text textures | Desktop (Linux/Windows/macOS) |
| **Pyodide Canvas** | HTML5 Canvas 2D + DOM overlay | Hybrid: Canvas fillText + HTML `<div>` | Web (any browser) |
| **KivyRenderer** | Kivy Graphics + Label widgets | Hybrid: CoreLabel textures + Kivy Labels | Mobile (iOS/Android) |
| **TkinterRenderer** | Tkinter Canvas | Debug text via `create_text` | Desktop (debug only) |
| **MockRenderer** | stdout printing | N/A | Headless CI/CD |

All renderers consume the **identical** NumPy array from the **identical** `AetherEngine.tick()` call. Switching renderers requires changing one line of code.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AETHERIS UI ENGINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────────────────┐│
│  │  Mathematical   │    │         Rendering Pipeline       ││
│  │     Domain      │    │                                  ││
│  │                 │    │  ┌──────────┐ ┌──────────┐      ││
│  │ ┌─────────────┐ │    │  │GLRenderer│ │KivyRender│      ││
│  │ │StateTensor  │ │    │  │(ModernGL)│ │ (Kivy)   │      ││
│  │ │- state[4]   │ │    │  └────┬─────┘ └────┬─────┘      ││
│  │ │- velocity[4]│ │    │       │             │            ││
│  │ │- accel[4]   │ │    │       └──────┬──────┘            ││
│  │ └─────────────┘ │    │              │                   ││
│  │        │        │    │  ┌───────────▼───────────────┐  ││
│  │ ┌─────────────┐ │    │  │  Structured NumPy Array   │  ││
│  │ │   Solver    │ │    │  │  [('rect','f4',4),        │  ││
│  │ │- Hooke'sLaw │ │    │  │   ('color','f4',4),       │  ││
│  │ │- Boundaries │ │    │  │   ('z','i4')]             │  ││
│  │ └─────────────┘ │    │  └───────────────────────────┘  ││
│  │        │        │    │              │                   ││
│  │ ┌─────────────┐ │    │  ┌───────────▼───────────────┐  ││
│  │ │StateManager │ │    │  │      JSON Metadata        │  ││
│  │ │- Lerp       │ │    │  │  (text, font, DOM data)   │  ││
│  │ │- HyperDamp  │ │    │  └───────────────────────────┘  ││
│  │ └─────────────┘ │    │                                  ││
│  └────────┬────────┘    └──────────────────────────────────┘│
│           │                                                   │
│  ┌────────▼────────┐                                         │
│  │  AetherEngine   │                                         │
│  │  - tick()       │                                         │
│  │  - registry     │                                         │
│  │  - dt tracking  │                                         │
│  └─────────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the complete mathematical deep-dive.

---

## Mathematical Foundations

### Euler Integration

Each frame, element state evolves via:

```
v(t+dt) = (v(t) + a(t) · dt) · (1 - viscosity)
s(t+dt) = s(t) + v(t+dt) · dt
```

### Hooke's Law

Restoring force pulls elements toward their asymptote:

```
F = (target - current) · k
```

### Critical Damping

For a spring-mass system with m=1:

```
c_critical = 2 · √k
```

### L2 Norm Clamping (Aether-Guard)

```
if ||v|| > V_max:
    v = (v / ||v||) · V_max
```

### Epsilon Snapping (99% Rule)

```
if ||s - target|| < 0.5 AND ||v|| < 5.0:
    s = target
    v = 0
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full derivations.

---

## API Reference

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for complete class and method documentation.

---

## Use Cases

Aetheris UI excels in specific niches where physics-based transitions provide natural, organic user experiences:

| # | Use Case | Industry |
|---|----------|----------|
| 1 | IoT Dashboard - Real-Time Sensor Monitoring | Industrial |
| 2 | AI/ML Embedding Visualization | Data Science |
| 3 | Financial Trading Terminals | Fintech |
| 4 | Educational Physics Simulations | EdTech |
| 5 | Network/Graph Topology Visualization | Analytics |
| 6 | Game Development - 2D UI Elements | Gaming |
| 7 | Digital Twins - Real-Time State Visualization | Manufacturing |
| 8 | Data Exploration - Interactive Scatter Plots | Analytics |
| 9 | Audio Visualization - Frequency Spectrum | Media |
| 10 | Robotics - Telemetry Dashboard | Robotics |

See [docs/USE_CASES.md](docs/USE_CASES.md) for complete use case documentation.

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and design patterns |
| [API_REFERENCE.md](docs/API_REFERENCE.md) | Complete API documentation |
| [USE_CASES.md](docs/USE_CASES.md) | 15 real-world use cases |
| [MARKET_STUDY.md](docs/MARKET_STUDY.md) | Market analysis and competitive positioning |
| [WASM_PORTABILITY.md](docs/WASM_PORTABILITY.md) | WebAssembly deployment guide |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run the test suite: `pytest tests/ -v`
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

---

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

---

## Strategic Vision

Aetheris UI is not a replacement for React or Flutter — it creates a **new category**: physics-driven data visualization where every data point is a physical object you can touch, throw, and explore.

**Target markets**: Netflix/Spotify catalog explorers, financial dashboards, AI embedding visualization, and interactive education tools.

**Unfair advantage**: Single Python code → 3 native platforms (Web, Desktop, Mobile) with algebraic data normalization and industrial-grade numerical stability via Aether-Guard.
