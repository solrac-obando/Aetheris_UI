# Aetheris UI - API Reference

> Referencia de API para desarrolladores
> Versión: v1.1.0

---

## 📦 Módulos Principales

### core.engine

#### AetherEngine

```python
from core.engine import AetherEngine

engine = AetherEngine()
```

| Método | Descripción |
|--------|-------------|
| `register_element(element)` | Registrar un elemento |
| `tick(win_w, win_h)` | Actualizar física (retorna array) |
| `unregister_element(index)` | Eliminar elemento |

---

### core.elements

#### DifferentialElement (Abstract)

```python
from core.elements import DifferentialElement

class MyElement(DifferentialElement):
    def calculate_asymptotes(self, w, h):
        return np.array([target_x, target_y, w, h])
```

#### StaticBox

```python
from core.elements import StaticBox

box = StaticBox(x=100, y=200, w=150, h=50, color=(1, 0, 0, 1))
```

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| x | float | Posición X inicial |
| y | float | Posición Y inicial |
| w | float | Ancho |
| h | float | Alto |
| color | tuple | RGBA (0-1) |

---

### core.solver_batch_asymptotes (M2)

#### BatchAsymptoteCalculator

```python
from core.solver_batch_asymptotes import BatchAsymptoteCalculator

calc = BatchAsymptoteCalculator(
    lerp_factor=0.15,
    static_threshold=0.5,
    enable_async=True
)
```

| Parámetro | Tipo | Default | Descripción |
|-----------|------|----------|-------------|
| lerp_factor | float | 0.15 | Factor de interpolación por frame |
| static_threshold | float | 0.5 | Pixels para clasificar "estático" |
| enable_async | bool | True | Habilitar optimización async |

##### Métodos

| Método | Descripción |
|--------|-------------|
| `calculate(states, targets, dims)` | Calcular estados |
| `get_dynamic_ratio(states)` | Ratio de elementos dinámicos |

#### Funciones de Bajo Nivel

```python
from core.solver_batch_asymptotes import (
    batch_calculate_asymptotes,
    classify_dynamic_elements,
    batch_asymptote_delta,
)
```

| Función | Descripción |
|---------|-------------|
| `batch_calculate_asymptotes(states, targets, lerp, w, h, out)` | Cálculo vectorizado |
| `classify_dynamic_elements(current, previous, threshold)` | Clasificar estático/dinámico |
| `batch_asymptote_delta(current, previous)` | Calcular delta de movimiento |

---

### core.dynamic_limits (M2)

```python
from core.dynamic_limits import (
    get_system_profile,
    get_optimal_max_elements,
    get_theoretical_capacity,
    SAFETY_MARGIN,
)
```

| Función | Descripción |
|---------|-------------|
| `get_system_profile()` | Perfil de hardware |
| `get_theoretical_capacity()` | Capacidad sin safety margin |
| `get_optimal_max_elements()` | Capacidad operativa |

#### Perfil del Sistema

```python
profile = get_system_profile()
print(profile["cpu_count_logical"])   # Hilos CPU
print(profile["engine_limit"])       # Límite operativo
print(profile["safety_margin"])      # 0.35 (35%)
print(profile["performance_mode"])   # True/False
```

---

### wasm.light_wasm_adapter (M1)

```python
from wasm.light_wasm_adapter import LightWASMAdapter, create_adapter

# Usar factory (recomendado)
adapter = create_adapter(
    container_width=1280,
    container_height=720,
    force_adapter="js_renderer"  # "js_renderer", "pyodide", "webgl"
)
```

| Parámetro | Tipo | Default | Descripción |
|-----------|------|----------|-------------|
| container_width | float | 1280 | Ancho del contenedor |
| container_height | float | 720 | Alto del contenedor |
| force_adapter | str | None | Forzar adapter específico |

#### Métodos

| Método | Descripción |
|--------|-------------|
| `register_element(index, html_id, metadata)` | Registrar elemento |
| `unregister_element(index)` | Eliminar elemento |
| `sync(elements)` | Sincronizar estados (retorna JSON) |
| `get_initial_dom_state()` | Estado inicial del DOM |
| `stats` | Estadísticas del adapter |

---

## 🔧 Utilidades

### core.aether_math

```python
from core.aether_math import (
    safe_divide,
    clamp_magnitude,
    check_and_fix_nan,
)
```

### core.solver_bridge

```python
from core.solver_bridge import (
    get_hpc_config,
    batch_restoring_forces,
    batch_boundary_forces,
    batch_integrate,
)
```

---

## 📊 Constantes

### M2 Constants

| Constante | Valor | Descripción |
|-----------|-------|-------------|
| `SAFETY_MARGIN` | 0.35 | Safety margin del 35% |
| `DEFAULT_LERP_FACTOR` | 0.15 | Factor lerp por defecto |
| `THRESHOLD_STATIC` | 0.5 | Threshold pixels para estático |

---

## 🧪 Tests

### Ejecutar Tests

```bash
# Todos
pytest tests/ -v

# M1
pytest tests/test_m1_*.py -v

# M2
pytest tests/test_m2_*.py -v

# Vulnerabilidad
pytest tests/test_*_ataques.py -v
```

### Archivos de Test

| Archivo | Tests | Descripción |
|---------|-------|-------------|
| `test_engine.py` | 5 | Tests motor |
| `test_m1_unitarios.py` | 20 | Tests unitarios M1 |
| `test_m1_estres.py` | 19 | Tests estrés M1 |
| `test_m2_unitarios.py` | 35 | Tests unitarios M2 |
| `test_m2_batch_asymptotes.py` | 9 | Tests batch M2 |
| `test_m2_ataques.py` | 14 | Tests vulnerabilidad |

---

## 🚨 Errores Comunes

### "Numba not found"

```bash
pip install numba
```

### "Element limit exceeded"

```python
# Ver límites
from core.dynamic_limits import get_system_profile
print(get_system_profile())
```

### "Memory error with large arrays"

```python
# Reducir elementos o usar chunking
# El sistema automáticamente aplica safety margin
```

---

*API Reference generada: Abril 2026*
*Versión: v1.1.0*