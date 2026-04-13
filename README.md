# Aetheris UI

> **Physics-as-UI** — The first hybrid Python/Rust physics-driven UI engine.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Rust](https://img.shields.io/badge/rust-1.70+-orange.svg)](https://www.rust-lang.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.6.1-gold.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-500%2B-brightgreen.svg)](tests/)
[![Security](https://img.shields.io/badge/security-NaN%2FInf%20protected-green.svg)](core/json_utils.py)

Aetheris UI treats user interface layout as a **dynamic physical system** governed by classical mechanics. Every UI element is a particle with position, velocity, and acceleration — evolving through **Symplectic Euler integration** with **Hooke's Law** restoring forces, **critical damping**, and **L2 norm clamping** for numerical stability.

Now features a **dual-engine architecture**: a pure Python engine and a **17.2x faster Rust engine** (5,000 elements benchmark), selectable at runtime via `EngineSelector`.

---

## Table of Contents

- [Features](#features)
- [Dual-Engine Architecture](#dual-engine-architecture)
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

- **🚀 Dual-Engine: Python + Rust** — Choose between pure Python or 17.2x faster Rust at runtime via `EngineSelector`. Automatic fallback if Rust is unavailable.
- **M1: WASM Ligero** (~200KB) — Lightweight WebAssembly adapter replacing Pyodide (40MB). Canvas 2D + WebGL support.
- **M2: Batch Asymptotes** — 50,000 elements at 60 FPS with Numba JIT kernels + 35% safety margin.
- **Physics-Driven Audio Integration** — Non-blocking, platform-agnostic audio bridge (`AetherAudioBridge`). Supports `impact`, `settle`, and `collision` triggers derived from physical state changes.
- **HPC-Optimized Core** — Numba-accelerated vectorized Python kernels + Rayon-parallelized Rust batch processing for 10 to 5,000+ elements.
- **Aether-Guard Safety** — Industrial-grade numerical stability. L2 norm clamping, epsilon-protected division, and NaN/Inf sanitization prevent engine collapses.
- **Dual-Telemetry Logging** — Native logging system with plugin architecture. Separate framework and project logs for developers and end users.
- **Web Security** — Automatic NaN/Inf to null conversion for JavaScript compatibility. Validates all data before JSON serialization.
- **Dynamic Resource Limits** — Auto-detect hardware capabilities with 35% safety margin for stable 60 FPS.
- **Zero External Math Dependencies** — Custom `Vec4` type in Rust, pure NumPy in Python. No linear algebra supply chain risk.
- **HTML/CSS Hydration** — Declarative UI definition via `AetherHTMLParser`. Maps HTML tags and CSS-like attributes to physics properties.

---

## Dual-Engine Architecture

Aetheris UI now ships with **two physics engines** and a unified selector:

| Engine | Language | Speed (5K elements) | Use Case |
|--------|----------|---------------------|----------|
| **Python** | Python + Numba | 27.6 FPS | Development, debugging, no Rust toolchain |
| **Rust** | Rust + Rayon | **473.6 FPS (17.2x)** | Production, high element counts, mobile battery |

### EngineSelector

```python
from core.engine_selector import EngineSelector

# Auto-detect: tries Rust, falls back to Python
engine = EngineSelector()

# Force a specific engine
engine = EngineSelector(engine_type="python")  # Always Python
engine = EngineSelector(engine_type="rust")    # Always Rust (error if unavailable)

---

## M2: Fully Vectorized Asymptotes

Aetheris UI v1.1+ includes **M2: Batch Asymptotes** for extreme performance:

| Métrica | Valor |
|---------|-------|
| Elementos | **50,000** @ 60 FPS |
| Safety Margin | **35%** |
| Batch Processing | Numba JIT |
| Async Optimization | Static/Dynamic classification |

### M2 Performance

```python
from core.solver_batch_asymptotes import BatchAsymptoteCalculator

calc = BatchAsymptoteCalculator()
result = calc.calculate(states, targets, (1280, 720))
# 50,000 elementos: <16ms (60 FPS target)
```

### Dynamic Limits

M2 includes automatic hardware detection:

```python
from core.dynamic_limits import get_system_profile

profile = get_system_profile()
print(profile["engine_limit"])  # e.g., 2080 for 4-core
print(profile["safety_margin"])   # 0.35 (35%)
```

---

## M1: WASM Ligero

Replace Pyodide (40MB) with lightweight adapter (~200KB):

```python
from wasm.light_wasm_adapter import LightWASMAdapter

adapter = LightWASMAdapter()
adapter.sync(elements)  # Same API as WebBridge
```

# Environment variable override
# AETHER_ENGINE=python python main.py
# AETHER_ENGINE=rust python main.py
```

The selector provides a **unified API** — your rendering code never changes regardless of which engine is active.

### Building the Rust Engine

```bash
cd aetheris-rust
pip install maturin
maturin develop -m crates/aether-pyo3/Cargo.toml
```

See [BENCHMARK.md](BENCHMARK.md) for full performance results.

---

## Installation

### Prerequisites

- Python 3.12+ 
- NumPy 1.26.4+
- For Rust engine: Rust 1.70+ and `maturin`
- For WASM: Modern browser with SharedArrayBuffer support (COOP/COEP headers)

### pip install (recommended)

```bash
pip install aetheris-ui
```

### From source

```bash
git clone https://github.com/carlosobando/aetheris-ui.git
cd aetheris-ui
pip install -e .

# Optional: Build Rust engine for 17x performance
cd aetheris-rust && pip install maturin && maturin develop -m crates/aether-pyo3/Cargo.toml && cd ..

# Run with GPU renderer (headless validation)
xvfb-run -a python3 main.py --gl --frames 50

# Run with Tkinter debug renderer
python3 main.py --tkinter

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
from core.engine_selector import EngineSelector
from core.elements import SmartPanel
from core.renderer_base import MockRenderer

# 1. Create the engine (auto-selects Rust if available)
engine = EngineSelector()

# 2. Register a responsive panel (5% padding from all edges)
panel = SmartPanel(color=(0.9, 0.2, 0.6, 0.8), z=0)
engine.register_element(panel)

# 3. Create a renderer
renderer = MockRenderer()
renderer.init_window(800, 600, "Hello Physics")

# 4. Run the physics loop
for frame in range(60):
    data = engine.tick(800, 600)
    renderer.clear_screen((0.1, 0.1, 0.1, 1.0))
    renderer.render_frame(data)
    renderer.swap_buffers()

    if frame % 10 == 0:
        print(f"Frame {frame}: rect={data[0]['rect']}")
```

### Server-Driven Layout

```python
from core.engine_selector import EngineSelector
from core.ui_builder import UIBuilder

engine = EngineSelector()

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
```

### Database-Driven Layout (Aether-Data Bridge)

```python
from core.engine import AetherEngine
from core.ui_builder import UIBuilder
from core.data_bridge import SQLiteProvider, min_max_scale

engine = AetherEngine()
builder = UIBuilder()

db = SQLiteProvider("./my_app.db")
db.connect()

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

count = builder.build_from_datasource(engine, db, "SELECT * FROM movies", template)
print(f"Created {count} elements from database")
db.disconnect()
```

### AI Embedding Visualization

```python
from core.data_bridge import vector_to_tensor

embedding = [0.5, -0.3, 0.8, -0.1]  # AI embedding from pgvector
force = vector_to_tensor(embedding, scale=100.0)
# force = [50.0, -30.0, 80.0, -10.0] — ready for StateTensor.apply_force()
```

---

## Dual-Telemetry Logging

Aetheris v1.6+ includes a native logging system with plugin architecture:

```python
from core.logging import framework_logger, project_logger
from core.logging.plugins import StandardFilePlugin

# Framework log (for developers)
framework_logger.add_plugin(StandardFilePlugin("logs/aetheris.log"))
framework_logger.info("Engine initialized")

# Project log (for end users)
project_logger.add_plugin(StandardFilePlugin("logs/mi_proyecto.log"))
project_logger.info("Application started")
```

### Decorators

```python
from core.logging.decorators import log_operation, with_log, track_duration

@log_operation(project_logger, "process_data")
def process_data(data):
    return transform(data)

@track_duration(framework_logger, "heavy_operation")
def heavy_operation():
    # Function execution is automatically timed
    return compute()
```

See [core/logging/](core/logging/) for full documentation.

---

## Web Security: NaN/Inf Protection

Aetheris automatically converts NaN/Inf to `null` for JavaScript compatibility:

```python
from core.json_utils import to_json

# Before: {"x": NaN} would break JavaScript
# After: {"x": null} is valid JSON
data = {"x": float('nan'), "y": 42, "arr": np.array([1, float('nan'), 3])}
json_str = to_json(data)
# Result: '{"y": 42, "arr": [1, null, 3], "x": null}'
```

This prevents web rendering crashes and ensures all data is valid for browser consumption.

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

All renderers consume the **identical** NumPy array from the **identical** `engine.tick()` call. Switching renderers requires changing one line of code.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AETHERIS UI ENGINE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐        ┌───────────────────────────────┐  │
│  │   EngineSelector    │        │        Rendering Pipeline     │  │
│  │  (Unified Facade)   │        │                               │  │
│  │                     │        │  ┌──────────┐ ┌──────────┐   │  │
│  │  ┌───────────────┐  │        │  │GLRenderer│ │KivyRender│   │  │
│  │  │ Python Engine │  │        │  │(ModernGL)│ │ (Kivy)   │   │  │
│  │  │ (Numba+NumPy) │  │        │  └────┬─────┘ └────┬─────┘   │  │
│  │  └───────────────┘  │        │       │             │         │  │
│  │         OR          │        │       └──────┬──────┘         │  │
│  │  ┌───────────────┐  │        │  ┌──────────▼──────────────┐ │  │
│  │  │  Rust Engine  │  │        │  │  Structured NumPy Array │ │  │
│  │  │  (PyO3+Rayon) │  │        │  │  [('rect','f4',4),      │ │  │
│  │  │   17.2x fast  │  │        │  │   ('color','f4',4),     │ │  │
│  │  └───────────────┘  │        │  │   ('z','i4')]           │ │  │
│  └──────────┬──────────┘        │  └─────────────────────────┘ │  │
│             │                   │              │                │  │
│             │                   │  ┌───────────▼───────────────┐│  │
│             │                   │  │      JSON Metadata        ││  │
│             │                   │  │  (text, font, DOM data)   ││  │
│             │                   │  └───────────────────────────┘│  │
│             │                   └───────────────────────────────┘  │
│  ┌──────────▼──────────┐                                          │
│  │   Rust Core Crates  │                                          │
│  │  ┌───────────────┐  │                                          │
│  │  │  aether-math  │  │  Vec4, AetherGuard, StateTensor         │
│  │  │  (0 ext deps) │  │  L2 norm, safe_divide, clamp_magnitude  │
│  │  └───────────────┘  │                                          │
│  │  ┌───────────────┐  │                                          │
│  │  │  aether-core  │  │  Solver, Engine, InputMgr, StateMgr     │
│  │  │  (rayon)      │  │  Hooke's Law, boundaries, snap          │
│  │  └───────────────┘  │                                          │
│  └─────────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the complete mathematical deep-dive.

---

## Mathematical Foundations

### Symplectic Euler Integration

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

### Speed-to-Stiffness Mapping

```
k = 16 / T²  (where T is transition time in seconds)
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
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and mathematical foundations |
| [API_REFERENCE.md](docs/API_REFERENCE.md) | Complete API documentation |
| [USE_CASES.md](docs/USE_CASES.md) | 15 real-world use cases |
| [BENCHMARK.md](BENCHMARK.md) | Python vs Rust performance comparison (5,000 elements) |
| [MARKET_STUDY.md](docs/MARKET_STUDY.md) | Market analysis and competitive positioning |
| [WASM_PORTABILITY.md](docs/WASM_PORTABILITY.md) | WebAssembly deployment guide |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run the test suite: `pytest tests/ -v`
4. Run Rust tests: `cd aetheris-rust && cargo test`
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

---

## Strategic Vision

Aetheris UI is not a replacement for React or Flutter — it creates a **new category**: physics-driven data visualization where every data point is a physical object you can touch, throw, and explore.

**Target markets**: Netflix/Spotify catalog explorers, financial dashboards, AI embedding visualization, and interactive education tools.

**Unfair advantage**: Single Python code → 3 native platforms (Web, Desktop, Mobile) with **17.2x faster Rust engine option**, algebraic data normalization, and industrial-grade numerical stability via Aether-Guard.
