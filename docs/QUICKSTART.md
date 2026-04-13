# Aetheris UI - Quick Start Guide

> Guía de inicio rápido para desarrolladores
> Versión: v1.1.0 (Abril 2026)

---

## 🚀 Instalación Rápida

```bash
# Clonar el proyecto
git clone https://github.com/your-repo/aetheris_UI
cd aetheris_UI

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python -c "from core.engine import AetherEngine; print('OK')"
```

---

## 📦 Estructura del Proyecto

```
aetheris_UI/
├── core/                    # Motor de física
│   ├── engine.py           # AetherEngine principal
│   ├── elements.py        # DifferentialElements
│   ├── solver_batch_asymptotes.py  # M2 batch processor
│   └── dynamic_limits.py  # M2 resource limits
│
├── wasm/                   # M1 WASM adapter
│   ├── adapters/          # Render adapters
│   └── light_wasm_adapter.py
│
├── tests/                  # Test suite
│   ├── test_m1_*.py      # M1 tests
│   ├── test_m2_*.py      # M2 tests
│   └── test_*_ataques.py # Vulnerability tests
│
└── docs/                  # Documentación
    ├── PROJECT_STATUS.md  # Estado del proyecto
    └── M1_WASM_LIGHTWEIGHT.md
```

---

## 🎯 Uso Básico

### 1. Crear un Elemento

```python
from core.elements import StaticBox

# Elemento que mantiene su posición
element = StaticBox(x=100, y=200, w=150, h=50)
```

### 2. Inicializar el Motor

```python
from core.engine import AetherEngine

engine = AetherEngine()
engine.register_element(element)
```

### 3. Ciclo de Renderizado

```python
import numpy as np

# En tu loop de render
while running:
    # Actualizar física
    rects = engine.tick(1280, 720)  # window size
    
    # Obtener datos para render
    # rects es un array estructurado con posiciones
```

---

## 🔧 Configuración M2

### Límites Dinámicos

M2 detecta automáticamente tu hardware:

```python
from core.dynamic_limits import get_system_profile

profile = get_system_profile()
print(f"CPU: {profile['cpu_count_logical']} threads")
print(f"Límite: {profile['engine_limit']} elementos")
print(f"Safety margin: {profile['safety_margin']*100}%")
```

### Batch Asymptotes

```python
from core.solver_batch_asymptotes import BatchAsymptoteCalculator

# Inicializar calculadora
calc = BatchAsymptoteCalculator(
    lerp_factor=0.15,      # 15% por frame
    static_threshold=0.5,  # pixels para "estático"
    enable_async=True      # Optimización async
)

# Calcular estados
result = calc.calculate(states, targets, (1280, 720))
```

---

## 🌐 Uso Web (M1)

### LightWASM Adapter

```python
from wasm.light_wasm_adapter import LightWASMAdapter

# Crear adapter (misma API que WebBridge)
adapter = LightWASMAdapter(
    container_width=1280,
    container_height=720,
    use_webgl=True  # Usar WebGL si disponible
)

# Sincronizar estados
adapter.register_element(0, "element-1")
json_payload = adapter.sync(elements)
```

---

## 🧪 Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Solo M2
pytest tests/test_m2_*.py -v

# Tests de vulnerabilidad
pytest tests/test_*_ataques.py -v
```

### Cobertura de Tests

| Suite | Tests |
|-------|-------|
| Core Engine | 12 |
| M1 (WASM) | 65 |
| M2 (Batch) | 58 |
| Vulnerability | 14 |
| **Total** | **511+** |

---

## ⚡ Benchmarks

### M2 Performance

| Elementos | Tiempo | FPS |
|-----------|--------|-----|
| 1,000 | <0.1ms | 60+ |
| 10,000 | <1ms | 60+ |
| 50,000 | <16ms | **60** |

### M2 Async Savings

- Dashboard típico: 75% elementos son estáticos
- Solo se calculan elementos dinámicos
- **~60% ahorro** en computation

---

## 🎓 Aprendizaje

### Para Principiantes

1. Lee `docs/PROJECT_STATUS.md` - Estado del proyecto
2. Estudia `tests/test_m2_unitarios.py` - 35 ejemplos de tests
3. Revisa `core/elements.py` - Entender DifferentialElement

### Para Intermedios

1. Lee `core/solver_batch_asymptotes.py` - M2 kernels
2. Estudia `core/dynamic_limits.py` - Resource management
3. Revisa tests de vulnerabilidad

### Para Avanzados

1. Lee `core/engine.py` - Motor completo
2. Estudia NUMBA JIT compilation
3. Implementa M3 (ECS Architecture)

---

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| `docs/PROJECT_STATUS.md` | Estado actual del proyecto |
| `docs/M1_WASM_LIGHTWEIGHT.md` | Documentación M1 |
| `docs/ARCHITECTURE.md` | Arquitectura completa |
| `docs/API_REFERENCE.md` | Referencia API |

---

## 🚨 Solución de Problemas

### Error: "Numba not found"

```bash
pip install numba
```

### Error: "WebSocket conflict"

```bash
# Cambiar puerto en tests/test_web_server.py
```

### Performance bajo

```python
# Verificar límites dinámicos
from core.dynamic_limits import get_system_profile
print(get_system_profile())
```

---

## ✅ Checklist de Producción

- [ ] Tests passing: `pytest tests/ -q`
- [ ] Performance: 60 FPS @ target elements
- [ ] Memory: <500MB RAM
- [ ] Bundle: ~200KB (M1)

---

*Guía generada: Abril 2026*
*Para más info: docs/PROJECT_STATUS.md*