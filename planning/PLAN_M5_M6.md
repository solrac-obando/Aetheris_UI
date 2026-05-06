# 📋 PLAN M5: Layout Declarativo DSL

> **Objetivo**: Crear un DSL para definir UIs físicas sin cálculos manuales
> **Dificultad**: 🟠 Media
> **Impacto**: 🎯🎯 (Alta adopción por no-físicos)
> **Independencia**: ✅ No afecta M3/M4

---

## 🎯 Definición del Problema

Actualmente, los desarrolladores deben calcular manualmente:
- Posiciones (x, y)
- Dimensiones (w, h)
- Velocidades iniciales
- Constantes de resorte (stiffness)

**Ejemplo actual (complejo):**
```python
button = SmartButton(x=100, y=200, w=150, h=50)
button.set_stiffness(0.15)
button.set_damping(0.8)
```

**Ejemplo con DSL (simple):**
```python
layout = AetherLayout("""
    row:
        button#submit "Submit"
        button#cancel "Cancel"
    column#sidebar:
        nav "Home"
        nav "About"
""")
```

---

## 📐 Arquitectura M5

```
┌─────────────────────────────────────────────────────────┐
│                  M5 DSL Pipeline                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   ┌─────────────────────────────────────────────┐   │
│   │  AetherLayout DSL Parser                     │   │
│   │  - YAML-like syntax                         │   │
│   │  - Hierarchical structure                    │   │
│   │  - CSS-like properties                      │   │
│   └─────────────────────────────────────────────┘   │
│                        │                              │
│                        ▼                              │
│   ┌─────────────────────────────────────────────┐   │
│   │  Layout Compiler                            │   │
│   │  - tree → element hierarchy                │   │
│   │  - flexbox → physics rules                │   │
│   │  - css → stiffness/damping               │   │
│   └─────────────────────────────────────────────┘   │
│                        │                              │
│                        ▼                              │
│   ┌─────────────────────────────────────────────┐   │
│   │  Element Factory                           │   │
│   │  - StaticBox, SmartPanel, SmartButton      │   │
│   │  - Auto-position calculation              │   │
│   └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 Especificación DSL

### Sintaxis Propuesta

```yaml
# Ejemplo: Dashboard Layout
dashboard:
  header:
    height: 60
    background: "#1a1a2e"
    
  main:
    grid: 3x2
    gap: 16
    padding: 24
    
    card#revenue:
      physics: spring(k=0.1, damping=0.8)
      position: row-1, col-1
      
    card#users:
      physics: spring(k=0.15)
      position: row-1, col-2
      
    chart#analytics:
      physics: spring(k=0.05)
      position: row-2, span-2
      
  sidebar:
    width: 250
    position: right
    physics: fixed
```

### Propiedades Soportadas

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `position` | string | Posición (row, col, grid) |
| `size` | string | Dimensiones (width, height) |
| `physics` | object | Parámetros físicos |
| `grid` | string | Grid layout (cols x rows) |
| `gap` | int | Espaciado entre elementos |
| `padding` | int | Relleno |

---

## 📅 Cronograma M5

### Semana 1: Parser DSL

| Día | Tarea | Entregable |
|-----|-------|-------------|
| 1 | Diseñar gramática DSL | `docs/M5_GRAMMAR.md` |
| 2 | Implementar lexer | `lexer.py` |
| 3 | Implementar parser | `parser.py` |
| 4 | Tests parser | 10 tests |

### Semana 2: Layout Compiler

| Día | Tarea | Entregable |
|-----|-------|-------------|
| 5 | Tree builder | `layout_builder.py` |
| 6 | Flexbox mapper | `flexbox_mapper.py` |
| 7 | Physics compiler | `physics_compiler.py` |
| 8 | Tests compiler | 10 tests |

### Semana 3: Element Factory

| Día | Tarea | Entregable |
|-----|-------|-------------|
| 9 | Factory base | `element_factory.py` |
| 10 | Auto-sizing logic | Factory extensions |
| 11 | Integration | `AetherLayout` class |
| 12 | Tests factory | 10 tests |

### Semana 4: Validación

| Día | Tarea | Entregable |
|-----|-------|-------------|
| 13 | End-to-end test | Layout completo |
| 14 | Performance | Benchmarks |
| 15 | Docs | `docs/M5_USAGE.md` |
| 16 | Buffer | Testing adicional |

---

## 📦 Entregables M5

| Archivo | Descripción |
|---------|-------------|
| `core/layout_parser.py` | Parser DSL |
| `core/layout_compiler.py` | Layout compiler |
| `core/layout_element_factory.py` | Element factory |
| `core/layout.py` | Main API |
| `tests/test_m5_layout.py` | Tests unitarios |
| `docs/M5_USAGE.md` | Documentación |

---

## 🔗 Dependencias

```
M5 Dependencies:
- None required (standalone)
- Uses existing: core.elements, core.engine
- Independent of: M3 (ECS), M4 (GPU)
```

---

## ⚠️ Precauciones

1. **No modificar engine.py** - M5 debe ser 100% externo
2. **Backwards compatibility** - Mantener API actual
3. **Performance** - No agregar overhead >5%

---

## ✅ Criterios de Éxito

- [ ] DSL soporta grid, flex, stack layouts
- [ ] Conversión automática a elementos físicos
- [ ] Tests covering >80%
- [ ] Performance <10ms para layout típico
- [ ] Documentación completa

---

# 📋 PLAN M6: Sistema de Lifecycle (dispose())

> **Objetivo**: Gestión explícita de recursos para prevenir memory leaks
> **Dificultad**: 🟠 Media  
> **Impacto**: ⚡ (Estabilidad producción)
> **Independencia**: ✅ No afecta M3/M4

---

## 🎯 Definición del Problema

Actualmente:
- Elementos no se limpian correctamente
- Referencias circulares
- Memory leaks en aplicaciones de larga duración
- Sin forma de cleanup explícito

---

## 📐 Arquitectura M6

```
┌─────────────────────────────────────────────────────────┐
│                M6 Lifecycle System                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   ┌─────────────────────────────────────────────┐    │
│   │  BaseElement (ABC)                           │    │
│   │  - __init__()                               │    │
│   │  - dispose()  ← NEW                          │    │
│   │  - __enter__/__exit__                        │    │
│   └─────────────────────────────────────────────┘    │
│                        │                               │
│         ┌──────────────┼──────────────┐              │
│         ▼              ▼              ▼              │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐        │
│   │StaticBox│   │SmartPanel│   │SmartBtn │        │
│   │dispose()│   │dispose()│   │dispose()│        │
│   └─────────┘   └─────────┘   └─────────┘        │
│                                                          │
│   ┌─────────────────────────────────────────────┐    │
│   │  LifecycleManager (Singleton)                 │    │
│   │  - track(element)                           │    │
│   │  - dispose_all()                           │    │
│   │  - gc_roots()                              │    │
│   └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 API Propuesta

### Basic Lifecycle

```python
from core.lifecycle import Disposable

class MyElement(Disposable):
    def dispose(self):
        # Cleanup audio
        self.audio = None
        # Cleanup timers
        for timer in self.timers:
            timer.cancel()
        # Call parent
        super().dispose()

# Usage
with MyElement() as elem:
    elem.do_something()
# Automatic dispose when exiting context
```

### Lifecycle Manager

```python
from core.lifecycle import LifecycleManager

manager = LifecycleManager()

# Track all elements
manager.track(element)
manager.track(another_element)

# Force cleanup
manager.dispose_all()

# Check for leaks
leaked = manager.get_leaked_references()
```

---

## 📅 Cronograma M6

### Semana 1: Base Classes

| Día | Tarea | Entregable |
|-----|-------|-------------|
| 1 | Crear `Disposable` base class | `lifecycle/base.py` |
| 2 | Implement `__enter__/__exit__` | Context manager |
| 3 | Tests base class | 10 tests |
| 4 | Integration with elements | Modificar elements.py |

### Semana 2: Manager

| Día | Tarea | Entregable |
|-----|-------|-------------|
| 5 | LifecycleManager singleton | `lifecycle/manager.py` |
| 6 | Reference tracking | Weak refs |
| 7 | GC integration | `gc_roots()` |
| 8 | Tests manager | 10 tests |

### Semana 3: Integration

| Día | Tarea | Entregable |
|-----|-------|-------------|
| 9 | Integrate with engine | Engine.track() |
| 10 | Memory profiler hook | Profiler integration |
| 11 | Audio cleanup | AudioBridge cleanup |
| 12 | Tests integration | 10 tests |

### Semana 4: Validation

| Día | Tarea | Entregable |
|-----|-------|-------------|
| 13 | Leak detection test | Test suite |
| 14 | Long-running test | Stress test |
| 15 | Docs | `docs/M6_LIFECYCLE.md` |
| 16 | Buffer | Testing |

---

## 📦 Entregables M6

| Archivo | Descripción |
|---------|-------------|
| `core/lifecycle/__init__.py` | Package |
| `core/lifecycle/base.py` | Disposable ABC |
| `core/lifecycle/manager.py` | LifecycleManager |
| `core/lifecycle/profiler.py` | Memory profiler |
| `tests/test_m6_lifecycle.py` | Tests |
| `docs/M6_LIFECYCLE.md` | Documentación |

---

## 🔗 Dependencias

```
M6 Dependencies:
- gc (stdlib)
- weakref (stdlib)
- Uses existing: core.elements, core.engine
- Independent of: M3 (ECS), M4 (GPU)
```

---

## ⚠️ Precauciones

1. **No romper referencias fuertes** - Usar WeakRef
2. **Thread safety** - Lock en manager
3. **Performance** - No overhead en tick()

---

## ✅ Criterios de Éxito

- [ ] dispose() llamado automáticamente
- [ ] LifecycleManager reporta leaks
- [ ] Tests no memory leaks
- [ ] Compatible con existentes elementos
- [ ] Documentación completa

---

# 📊 RESUMEN M5 + M6

| Aspecto | M5 | M6 |
|---------|-----|-----|
| **Objetivo** | DSL para layouts | Cleanup recursos |
| **Dificultad** | Media | Media |
| **Impacto** | Adopción devs | Estabilidad |
| **Weeks** | 4 | 4 |
| **Tests** | 30+ | 30+ |
| **Indep M3/M4** | ✅ | ✅ |
| **Files new** | 5 | 5 |

---

## 🎯 Roadmap Q2 2026

```
Semana 1-4:   M5 - Layout DSL
Semana 5-8:   M6 - Lifecycle
Semana 9-12:  M8 - Static Typing (opcional)
```

---

*Plan creado: Abril 2026*
*Para implementación, confirmar con el equipo*