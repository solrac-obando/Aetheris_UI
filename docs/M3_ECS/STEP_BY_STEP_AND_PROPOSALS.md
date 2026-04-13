# 🚀 M3 (ECS): Proceso de Implementación y Propuestas

Este documento detalla la hoja de ruta para transformar el motor Aetheris en un sistema basado en datos (ECS) sin interrumpir la operatividad actual.

---

## 1. Proceso Paso a Paso (Roadmap)

### Fase 1: Infraestructura de Almacenamiento (Semana 1)
1.  **EntityManager:** Crear una clase que gestione una pila de IDs (reutilizando IDs de entidades destruidas).
2.  **ComponentPools:** Implementar una clase que pre-asigne arrays de NumPy de tamaño fijo (ej. 10,000 slots) para cada componente (`Transform`, `Motion`, `Style`).
3.  **Entity-to-Index Map:** Un array denso que mapee rápidamente `EntityID -> Index` en el pool de componentes.

### Fase 2: Refactorización de Kernels (Semana 2)
1.  **Pure Data Kernels:** Modificar `hpc_solver.py` para que sus funciones de Numba reciban solo los arrays del pool, eliminando la dependencia de objetos `StateTensor`.
2.  **System Dispatcher:** Crear un orquestador que llame a los kernels en orden: `TargetSystem -> ForceSystem -> IntegrationSystem -> ConstraintSystem`.

### Fase 3: Capa de Compatibilidad (The Proxy Layer) (Semana 3)
1.  **Legacy Wrapper:** Modificar `DifferentialElement` para que, en lugar de tener su propio `np.ndarray`, mantenga una referencia `self.entity_id`.
2.  **Getter/Setter Redirection:** Usar `@property` para que `element.x` mapee internamente a `global_pool.pos_x[entity_id]`.
3.  **Graceful Migration:** Permitir que los renderizadores actuales (Kivy, Web) sigan pidiendo datos a los objetos, mientras que los nuevos sistemas leen directamente de los arrays.

---

## 2. 5 Propuestas de Implementación para M3

| Propuesta | Descripción | Ventaja | Riesgo |
|---|---|---|---|
| **P1: Hybrid Proxy** | Los objetos `Element` coexisten con el ECS y actúan como handles. | 100% retrocompatible. | Sobrecarga mínima de objetos. |
| **P2: Pure Data-Driven** | Se eliminan las clases `Element`. La UI se define como un `DataFrame` de componentes. | Rendimiento máximo absoluto. | Curva de aprendizaje alta. |
| **P3: Rust-Side ECS** | El ECS se implementa íntegramente en Rust (usando `Bevy_ECS` o `Legion`). | Paralelismo real sin GIL. | Complejidad de bindings PyO3. |
| **P4: Archetype ECS** | Entidades agrupadas por "tipo" (ej. todos los Dashboard Gauges juntos). | Optimización de caché L1/L2. | Cambios de arquetipo son caros. |
| **P5: Reactive ECS** | Los sistemas solo operan sobre entidades marcadas como "sucias" (dirty-flag). | Ahorro masivo de energía/CPU. | Lógica de tracking de estado. |

---

## 3. Guía para No Romper el Proyecto (Safety Guidelines)

1.  **Double-Buffering:** Durante la transición, mantener los dos sistemas en paralelo. Validar mediante unit tests que `old_engine.tick()` y `ecs_engine.tick()` producen resultados idénticos con un margen de error del 1e-7.
2.  **Incremental Rollout:** Migrar primero los elementos simples (`StaticBox`) al ECS. Dejar los complejos (`AetherWindow`) en el sistema antiguo hasta que el ECS soporte jerarquías.
3.  **Circuit Breaker:** Si el sistema ECS detecta una condición de inestabilidad (NaNs masivos), poder revertir al sistema basado en objetos en caliente.
4.  **Metadata Shadowing:** Mantener el JSON bridge de metadatos fuera del ECS para evitar que los strings "ensucien" los arrays de floats del sistema de física.

---

## 4. Ejemplo de Configuración Pro (Bajo Nivel)

```python
# Habilitación de M3 con Hybrid Proxy (Propuesta 1)
engine = AetherEngine(mode="ECS_HYBRID")
engine.configure_pool(
    storage="flat_buffers",
    alignment=64, # Alignment para AVX-512
    parallel_systems=True
)
```
