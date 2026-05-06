# Benchmark: Python vs Rust Engine — 5,000 Elementos

## Configuración
- **Elementos**: 5000 (2500 StaticBox + 2500 SmartPanel)
- **Frames**: 1000
- **Resolución**: 1920x1080
- **Fecha**: 2026-04-06

## Resultados

| Métrica | Python | Rust | Ratio |
|---------|--------|------|-------|
| **Tiempo total** | 36278.2ms | 2111.5ms | **17.2x** |
| **Avg/frame** | 36.28ms | 2.11ms | **17.2x** |
| **FPS** | 27.6 | 473.6 | **17.2x** |

## Prueba de Resiliencia (NaN Injection)
- **Inyección**: Frame 500, `pointer_down(nan, inf)`
- **Resultado**: PASS — Motor sanitizó valores sin crash

## Conclusión
El motor de Rust es **17.2x más rápido** que el motor de Python para 5000 elementos.
