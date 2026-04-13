# 🏔️ Aetheris UI v1.2.0 - Official Documentation
**Production Version:** "Audio-Physics Milestone"

---

## 🛠️ Supported Technology Stack

To avoid technical surprises and ensure industry compatibility, the framework validates and uses the following cutting-edge technologies:

### Core Language
- **Python 3.11+** (Optimized for Linux/Docker environments)

### High-Performance Computing (HPC)
- **NumPy 1.26.4:** Processing of vectorized state tensors
- **Numba 0.59.1:** Just-in-Time (JIT) compilation with multi-core parallelism for physics kernels (`@njit(parallel=True, fastmath=True)` with `prange`)

### Real-Time Communication
- **WebSockets (websockets v12.0):** Low-latency, bidirectional, asynchronous tunnel
- **JSON API:** Protocol for exchanging coordinates and UI metadata between Python server and browser client

### Multi-Target Rendering
| Target | Technology | Status |
|---|---|---|
| **Desktop** | OpenGL (ModernGL for SDF shaders) + Kivy (touch UI) | ✅ Production |
| **Web** | Native HTML5 + CSS3 (Hardware Accelerated `translate3d`) | ✅ Production |
| **Mobile** | Native support via Kivy/Buildozer | ✅ Production |
| **Audio** | AetherAudioBridge (PyOgg/PyAudio/Pygame) | ✅ Production |
| **Headless CI** | MockRenderer + Xvfb | ✅ Production |

### Data Persistence
- **SQLite:** Local database with automatic mapping to physical states
- **PostgreSQL:** Remote data via REST proxy (RemoteAetherProvider)

### Infrastructure
- **Docker:** Isolated and reproducible environments (multi-stage builds, headless/interactive modes)
- **GitHub Actions:** Automated CI/CD with headless testing via `xvfb-run`

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     AetherEngine (Core)                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ StateTensor │  │ Aether-Guard │  │ HPC Solver (Numba)  │ │
│  │  [x,y,w,h]  │  │ NaN/Inf Guard│  │ parallel=True       │ │
│  │  velocity   │  │ L2 Clamp     │  │ prange              │ │
│  │ acceleration│  │ Epsilon Snap │  │ fastmath            │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │   Kivy      │  │  ModernGL   │  │  Web Hybrid │
   │  Renderer   │  │  Renderer   │  │  Bridge     │
   │  (Mobile)   │  │  (Desktop)  │  │  (Browser)  │
   └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 🚀 Quick Start

### Desktop (Kivy)
```python
from core.engine import AetherEngine
from core.elements import StaticBox

engine = AetherEngine()
engine.register_element(StaticBox(100, 100, 80, 40, z=0))
data = engine.tick(1280, 720)
```

### Web Hybrid
```python
from core.web_app import WebApp
from core.web_elements import WebButton, WebText

app = WebApp(title="My App", width=1280, height=720)
app.add(WebButton(text="Click Me", x=100, y=100, mass=2.0))
app.add(WebText(text="Hello World", x=100, y=150))
app.run(port=8765)
```

### Docker
```bash
docker-compose up aetheris-headless   # CI/server mode
docker-compose up aetheris-interactive # Local dev with GUI
```

---

## 📊 Performance Benchmarks

| Scenario | Nodes | Avg Frame Time | FPS |
|---|---|---|---|
| Gatekeeper Test | 100 | 11.9ms | 84 |
| Parallel Scaling | 2,000 | 12ms | 83 |
| High-Density Grid | 5,000 | 25ms | 40 |
| Stress Test | 10,000 | ~110ms | 9 |
| Web Sync (Bridge) | 50 | <1ms | 1000+ |

---

## 🧪 Testing

- **361 functional tests** passing (baseline + integration + audio)
- **43 private stress tests** (shielded, not committed)
- **CI/CD:** GitHub Actions with `xvfb-run` headless execution

```bash
# Run all public tests
pytest tests/ -v --ignore=tests/local_torture_test.py

# Run performance gatekeeper
pytest tests/test_performance_gatekeeper.py -v

# Run web integration tests
pytest tests/test_web_integration.py -v
```

---

## 📄 License

Licensed under the **Apache License, Version 2.0**.  
Copyright 2026 Carlos Ivan Obando Aure.
