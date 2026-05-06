# 🔧 devtools/

Herramientas de desarrollo interno, scripts de utilidad y archivos temporales.
Estos archivos NO forman parte del núcleo del framework ni del build de PyPI.

## Archivos

| Archivo | Descripción |
|---|---|
| `app_server.py` | Servidor Flask para demos interactivos y modo headless web |
| `serve_wasm.py` | Servidor HTTP mínimo para servir los archivos WASM en desarrollo |
| `debug_compiler.py` | Herramienta de debug del compilador de tensores |

## Subcarpetas

| Carpeta | Descripción |
|---|---|
| `scratch/` | Archivos temporales, notas y logs de análisis (no versionar) |

## Uso típico

```bash
# Levantar el servidor de demos
python devtools/app_server.py

# Servir WASM en localhost
python devtools/serve_wasm.py
```
