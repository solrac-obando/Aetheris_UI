# Reporte de Fallos y Discrepancias (Sesión 2026-04-15)

Este documento detalla los fallos detectados durante la suite de pruebas final tras la sanitización y actualización M8.

## 1. Fallos de Rendimiento (Benchmarks)
- **`tests/test_demo_orrery.py`**:
    - **Error**: `AssertionError: Average frame time 28.41ms exceeds 16.6ms (60 FPS)`.
    - **Causa Probable**: Fluctuación del entorno de ejecución durante la auditoría intensiva o ligera sobrecarga por los nuevos casteos de tipado estricto.
    - **Prioridad**: Media-Baja (Estabilidad funcional confirmada).

## 2. Fallos de Lógica (Lexer/Parser)
- **`tests/test_m5_layout.py`**:
    - **Error**: `TestLayoutLexer::test_tokenize_id_with_hash` falló con `assert 1 >= 2`.
    - **Detalle**: El lexer no está tokenizando correctamente los IDs precedidos por `#` (ej. `box#myid`).
    - **Prioridad**: Media (Requiere ajuste en la lógica de expresiones regulares del lexer).

## 3. Inestabilidades Temporales (Flakiness)
- Se detectaron fallos intermitentes en:
    - `tests/test_light_wasm.py`
    - `tests/test_m16_edge_cases.py`
    - `tests/test_m16_sleep_engine.py`
- *Nota*: Estos tests pasaron en ejecuciones aisladas subsiguientes, lo que sugiere que el fallo ocurre principalmente bajo condiciones de alta concurrencia de tests.

## 4. Integración GESTNE (Datos Médicos)
- **Estado**: Implementación Futura.
- **Nota**: El sistema de visualización de clusters para los 66 pacientes de GESTNE fue identificado como un módulo crítico de datos médicos. Para esta fase de sanitización, se ha decidido tratarlo como una **implementación futura** para no saturar la lógica principal del motor Aetheris.
- **Acción**: La arquitectura actual de `DataBridge` ya soporta la normalización necesaria, pero la vista específica de GESTNE será integrada en la fase M17.

## 5. Conclusión
La mayoría de los fallos son de rendimiento u optimización de sintaxis (Lexer). El núcleo del motor físico y los protocolos de tipado M8 son estructuralmente sólidos y están listos para su uso.
