# Aetheris Rust Engine

Motor de física de alto rendimiento para Aetheris UI, escrito en Rust con bindings PyO3 para Python.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    EngineSelector (Python)                   │
│              Auto-detect: Rust → Fallback Python             │
├──────────────────────────┬──────────────────────────────────┤
│                          │                                  │
│    ┌─────────────┐      │      ┌────────────────────┐      │
│    │ PythonEngine│      │      │   RustEngine(PyO3) │      │
│    │  (existing) │      │      │   (aether-pyo3)    │      │
│    └─────────────┘      │      └────────────────────┘      │
│                          │                                  │
└──────────────────────────┴──────────────────────────────────┘
```

## Estructura del Workspace Rust

```
aetheris-rust/
├── Cargo.toml                 # Workspace root
├── crates/
│   ├── aether-math/           # Matemáticas puras (0 deps externas)
│   │   └── src/
│   │       ├── vec4.rs        # Tipo Vec4 personalizado (x,y,w,h)
│   │       ├── aether_guard.rs # Constantes de seguridad, sanitize
│   │       └── state_tensor.rs # Integración Euler simbólica
│   ├── aether-core/           # Motor de física
│   │   └── src/
│   │       ├── engine.rs      # Motor principal (batch + single)
│   │       ├── solver.rs      # Ley de Hooke, fronteras, drag
│   │       ├── input_manager.rs # Drag & throw
│   │       ├── state_manager.rs # Shock detection
│   │       └── elements.rs    # StaticBox, SmartPanel, etc.
│   ├── aether-pyo3/           # Bindings Python (PyO3)
│   │   └── src/lib.rs         # Clases expuestas a Python
│   └── aether-bin/            # CLI standalone
```

## Dependencias

| Dependencia | Versión | Confianza |
|---|---|---|
| **pyo3** | 0.23.5 | PyO3 Project (oficial) |
| **rayon** | 1.11.0 | rust-lang |
| **serde_json** | 1.0.149 | serde-rs |
| **libc** | 0.2.184 | rust-lang |

**0 dependencias de álgebra lineal externas** — Vec4 es implementación propia.

## Build

### Requisitos
- Rust 1.75+ (`rustup install stable`)
- Python 3.12+
- `maturin` (`pip install maturin`)

### Compilar bindings PyO3
```bash
cd aetheris-rust
maturin develop -m crates/aether-pyo3/Cargo.toml
```

### Build de producción
```bash
cd aetheris-rust
maturin build --release -m crates/aether-pyo3/Cargo.toml
```

### Tests Rust
```bash
cd aetheris-rust
cargo test                    # Todos los crates
cargo test -p aether-math     # Solo matemáticas (184 tests)
cargo test -p aether-core     # Solo motor (99 tests)
```

### Tests Python
```bash
cd ..
.venv/bin/python3 -m pytest tests/test_engine_parity.py -v
```

## Uso desde Python

### Selección automática (recomendado)
```python
from core.engine_selector import EngineSelector

# Intenta Rust, fallback a Python automáticamente
engine = EngineSelector()
print(f"Motor activo: {engine.engine_type}")  # "rust" o "python"
```

### Forzar motor específico
```python
# Forzar Rust (error si no disponible)
engine = EngineSelector(engine_type="rust")

# Forzar Python
engine = EngineSelector(engine_type="python")
```

### Variable de entorno
```bash
AETHER_ENGINE=rust python main.py
AETHER_ENGINE=python python main.py
AETHER_ENGINE=auto python main.py
```

### API unificada
```python
from core.elements import StaticBox, SmartPanel

engine.register_element(StaticBox(0, 0, 100, 100, (1, 0, 0, 1), 0))
engine.register_element(SmartPanel(padding=0.05, color=(0.2, 0.2, 0.3, 0.9), z=0))

data = engine.tick(1920, 1080)  # numpy structured array
metadata = engine.get_ui_metadata()
```

## Benchmark

### 5,000 Elementos (2,500 StaticBox + 2,500 SmartPanel)

| Métrica | Python | Rust | Ratio |
|---------|--------|------|-------|
| **Tiempo total** | 36,278ms | 2,112ms | **17.2x** |
| **Avg/frame** | 36.28ms | 2.11ms | **17.2x** |
| **FPS** | 27.6 | 473.6 | **17.2x** |

### Prueba de Resiliencia
- **NaN Injection**: ✅ Sanitizado sin crash
- **5,000 elementos**: Todos los valores finitos post-inyección

Ver `BENCHMARK.md` para detalles completos.

## Correcciones Aplicadas

### Fase 1: Mejoras de Código
- `Default` implementado para `InputManager` y `StateManager`
- `.max().min()` → `.clamp()` (3 lugares)
- Rango `||` → `.contains()` (1 lugar)
- Variable no usada `_t_prev2` prefijada con underscore

### Fase 2: Bindings PyO3
- `#[pyclass(unsendable)]` para evitar problemas de `Send` con `dyn DifferentialElement`
- `Vec4` campos corregidos: `x, y, w, h` (no `z`)
- `tick()` retorna `List[PyDict]` compatible con numpy

### Fase 3: EngineSelector
- Fallback automático: Rust → Python si no disponible
- API unificada: mismo contrato para ambos motores
- Variables de entorno: `AETHER_ENGINE=python|rust|auto`

## Auditoría de Seguridad

- ✅ 0 dependencias desconocidas
- ✅ 0 dependencias no mantenidas
- ✅ Todas de mantenedores reconocidos (rust-lang, dtolnay, etc.)
- ✅ PyO3 es binding oficial de Rust para Python
- ✅ Sin dependencias de álgebra lineal externas

## Licencia

Apache License 2.0 — Copyright 2026 Carlos Ivan Obando Aure
