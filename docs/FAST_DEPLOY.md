# Aetheris UI — Fast Deployment Guide / Guía de Despliegue Rápido

> **Aetheris UI v1.0.0** — Physics-as-UI: The first high-performance UI engine driven by linear algebra for Python & WebAssembly.

---

## English Version

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/carlosobando/aetheris-ui.git
cd aetheris-ui

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Generate the Odyssey database
python3 demo/odyssey_db.py
```

### 2. The 3-Line Data-to-UI Implementation

```python
from core.engine import AetherEngine
from core.data_bridge import SQLiteProvider
from core.ui_builder import UIBuilder

# 1. Create engine + connect to database
engine = AetherEngine()
provider = SQLiteProvider("./demo/odyssey.db")
provider.connect()

# 2. Build UI from database with Min-Max scaling
builder = UIBuilder()
builder.build_from_datasource(engine, provider, "SELECT * FROM media", {
    'type': 'static_box',
    'columns': {
        'x': {'source': 'id'},
        'w': {'source': 'votes', 'scale': [0, 3000000, 20, 120]},
        'h': {'source': 'rating', 'scale': [0, 10, 20, 120]},
        'z': {'source': 'rating'},
    },
    'metadata_fields': ['title', 'rating', 'genre'],
})

# 3. Run physics loop
from core.renderer_base import MockRenderer
renderer = MockRenderer()
renderer.init_window(1200, 900, "My Dashboard")
for _ in range(300):
    data = engine.tick(1200, 900)
    renderer.render_frame(data)
```

### 3. Running the Master Odyssey Demo

```bash
# Desktop - Kivy (full interactive with keyboard)
python3 main.py --odyssey --kivy
# Space = Supernova | 1-6 = Genre | Esc = Exit

# Desktop - ModernGL (GPU-accelerated)
python3 main.py --odyssey --gl

# Web (Flask server with PWA)
python3 app_server.py
# Visit: http://localhost:5000/odyssey
# Space bar = Supernova | Genre buttons at bottom

# Headless validation
python3 main.py --odyssey
```

### 4. Running All Tests

```bash
pytest tests/ -v          # Full suite (143 tests)
pytest tests/ -v -k iron  # Iron Mountain stress tests only
pytest tests/ -v -k titan # Titan stress tests only
```

---

## Versión en Español

### 1. Configuración del Entorno

```bash
# Clonar el repositorio
git clone https://github.com/carlosobando/aetheris-ui.git
cd aetheris-ui

# Crear entorno virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate

# Instalar todas las dependencias
pip install -r requirements.txt

# Generar la base de datos de Odyssey
python3 demo/odyssey_db.py
```

### 2. Implementación Data-to-UI en 3 Líneas

```python
from core.engine import AetherEngine
from core.data_bridge import SQLiteProvider
from core.ui_builder import UIBuilder

# 1. Crear motor + conectar a base de datos
engine = AetherEngine()
provider = SQLiteProvider("./demo/odyssey.db")
provider.connect()

# 2. Construir UI desde base de datos con escalado Min-Max
builder = UIBuilder()
builder.build_from_datasource(engine, provider, "SELECT * FROM media", {
    'type': 'static_box',
    'columns': {
        'x': {'source': 'id'},
        'w': {'source': 'votes', 'scale': [0, 3000000, 20, 120]},
        'h': {'source': 'rating', 'scale': [0, 10, 20, 120]},
        'z': {'source': 'rating'},
    },
    'metadata_fields': ['title', 'rating', 'genre'],
})
```

### 3. Ejecutar la Demo Master Odyssey

```bash
# Escritorio - Kivy (interactivo completo con teclado)
python3 main.py --odyssey --kivy
# Espacio = Supernova | 1-6 = Género | Esc = Salir

# Escritorio - ModernGL (acelerado por GPU)
python3 main.py --odyssey --gl

# Web (servidor Flask con PWA)
python3 app_server.py
# Visitar: http://localhost:5000/odyssey
# Barra espaciadora = Supernova | Botones de género abajo

# Validación sin cabeza
python3 main.py --odyssey
```

### 4. Ejecutar Todas las Pruebas

```bash
pytest tests/ -v          # Suite completa (143 pruebas)
pytest tests/ -v -k iron  # Solo pruebas Iron Mountain
pytest tests/ -v -k titan # Solo pruebas Titan
```

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────┐
│              AETHERIS UI v1.0.0                     │
├─────────────────────────────────────────────────────┤
│  Physics Core    │  Aether-Guard   │  Data Bridge  │
│  - Euler Int.    │  - L2 Clamp     │  - SQLite     │
│  - Hooke's Law   │  - NaN Guard    │  - PostgreSQL │
│  - Solver Dual   │  - Epsilon Snap │  - Min-Max    │
├─────────────────────────────────────────────────────┤
│  Renderers: ModernGL (Desktop) │ Canvas (Web) │ Kivy│
├─────────────────────────────────────────────────────┤
│  Input: Drag & Throw │ Genre Orbit │ Supernova     │
└─────────────────────────────────────────────────────┘
```

---

*© 2026 Carlos Ivan Obando Aure — MIT License*
