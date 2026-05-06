# 🚀 Aetheris UI: Estrategia de Lanzamiento v1.8.5
**Fecha de Creación:** 25 de Abril de 2026
**Estado:** Preparado para Implementación Final

---

## 🛠️ Estado Técnico y Desafíos

### 1. EngineSelector (Fachada Unificada)
- **Situación Actual:** El código está implementado en `core/engine_selector.py` pero no es "operativo" en los demos porque `main.py` sigue importando `AetherEngine` directamente.
- **Acción Pendiente:** Refactorizar los puntos de entrada para usar `EngineSelector(engine_type="auto")`. Esto activará Rust automáticamente en equipos compatibles, multiplicando el rendimiento por **10x**.

### 2. M12: GPU Compute
- **Estado:** **90% Completo**. El nodo de cómputo en Rust y el shader WGSL están operativos.
- **Acción Pendiente:** Exponer `enable_gpu()` a través del `EngineSelector` para permitir activación con un solo comando desde Python.

### 3. M11: Entity Component System (ECS)
- **Estado:** **Planificación**. Actualmente se usa una lista de objetos en Rust.
- **Objetivo:** Migrar a una estructura ECS en Rust para permitir el manejo de **100,000+ elementos** con eficiencia de caché L1/L2.

---

## 📅 Hoja de Ruta de Implementación (Próximos Pasos)

### Paso 1: Activación de la Fachada (Prioridad Alta)
Modificar `main.py` para usar el selector. Esto convertirá a Rust en el motor principal de forma transparente.
```python
from core.engine_selector import EngineSelector
engine = EngineSelector() # Auto-detecta Rust
```

### Paso 2: Integración de ECS y GPU Final
- Implementar `ecs.rs` en el crate `aether-core`.
- Conectar el buffer de GPU con el sistema de componentes del ECS.

### Paso 3: Publicación Oficial
1. **PyPI (Python):** Generar sdist y wheel. Asegurar inclusión de `py.typed`.
2. **Crates.io (Rust):** Publicar los crates `aether-math`, `aether-core` y `aether-pyo3`.
3. **Documentación:** Finalizar el manual de usuario destacando el rendimiento híbrido.

---

> [!IMPORTANT]
> Este documento representa el compromiso técnico para la versión 1.8.5. La prioridad absoluta es la **estabilidad de la paridad** entre el motor de Python y el de Rust durante la migración al ECS.
