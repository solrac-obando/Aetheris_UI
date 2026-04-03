# Aetheris UI

> **Física-como-UI** — El primer motor de interfaz de usuario de alto rendimiento impulsado por álgebra lineal para Python y WebAssembly.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-green.svg)](LICENSE)
[![Pruebas](https://img.shields.io/badge/pruebas-31%20aprobadas-brightgreen.svg)](tests/)

Aetheris UI trata el diseño de interfaces de usuario como un **sistema físico dinámico** gobernado por las leyes de la mecánica clásica. En lugar de reglas de posicionamiento estáticas, cada elemento de la interfaz es una partícula con posición, velocidad y aceleración — evolucionando a través de **integración de Euler** con fuerzas restauradoras de la **Ley de Hooke**, **amortiguamiento crítico** y **limitación por norma L2** para estabilidad numérica.

La misma lógica física en Python impulsa **tres pipelines de renderizado nativos**: HTML5 Canvas vía Pyodide/WASM, OpenGL de escritorio vía ModernGL, y móvil vía Kivy — todos consumiendo el mismo puente de datos NumPy estructurado.

---

## Tabla de Contenidos

- [Características](#características)
- [Instalación](#instalación)
- [Inicio Rápido](#inicio-rápido)
- [La Trinidad del Multi-Renderizado](#la-trinidad-del-multi-renderizado)
- [Resumen de Arquitectura](#resumen-de-arquitectura)
- [Fundamentos Matemáticos](#fundamentos-matemáticos)
- [Referencia de API](#referencia-de-api)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

---

## Características

- **Diseño Impulsado por Física** — Cada elemento es una partícula con estado, velocidad y aceleración. Las transiciones de la interfaz son sistemas masa-resorte, no animaciones CSS.
- **Tres Renderizadores Nativos** — Un motor de física, tres backends de renderizado:
  - **Web**: Pyodide/WASM → HTML5 Canvas 2D + superposición DOM (listo para PWA)
  - **Escritorio**: ModernGL con shaders SDF + texturas de texto Pillow
  - **Móvil**: Kivy con inversión de coordenadas del eje Y + etiquetas híbridas
- **Seguridad Aether-Guard** — Limitación por norma L2, división protegida por épsilon, detección de NaN/Inf, y la Regla del 99% (Ajuste por Épsilon) previenen explosiones numéricas.
- **Puente Aether-Data** — Población de elementos UI desde bases de datos SQLite o PostgreSQL con normalización Min-Max automática y visualización de embeddings de IA.
- **Interfaz Impulsada por Servidor** — Definiciones de Intención JSON compiladas en coeficientes de física en tiempo de ejecución vía TensorCompiler.
- **Hiper-Amortiguamiento** — Absorción automática de choques cuando las dimensiones de la ventana cambian drásticamente (>200px), previniendo el sobrepaso cinético de la Ley de Hooke.
- **Composición de Texto Híbrida** — Texto renderizado en Canvas (rápido, no seleccionable) y superposiciones de etiquetas DOM/Kivy (seleccionables, accesibles) coexisten en la misma escena.
- **Gestión de Memoria Sin Fugas** — Objetos PyProxy destruidos cada frame en WASM; cachés de texturas en ModernGL; reciclaje de nodos DOM en Kivy.
- **Física Háptica** — Arrastrar, soltar y lanzar con Diferencia Regresiva de Segundo Orden para interacción suave y natural.

---

## Instalación

### Requisitos Previos

- Python 3.12+
- NumPy 1.26.4+
- Para WASM: Un navegador moderno con soporte para SharedArrayBuffer (requiere encabezados COOP/COEP)

### Escritorio (Renderizador ModernGL)

```bash
git clone https://github.com/your-org/aetheris-ui.git
cd aetheris-ui
pip install -r requirements.txt

# Ejecutar con renderizador GPU (validación sin cabeza)
xvfb-run -a python3 main.py --gl --frames 50

# Ejecutar con renderizador de depuración Tkinter
python3 main.py --tkinter

# Ejecutar con MockRenderer (sin cabeza, sin pantalla)
python3 main.py
```

### Web (Renderizador Pyodide/WASM)

```bash
# Iniciar el servidor Flask con soporte PWA
python3 app_server.py

# Abrir en el navegador
# http://localhost:5000/
```

El servidor Flask sirve el manifiesto PWA, el Service Worker, e inyecta el JSON de Intención de UI. El navegador carga Pyodide (~15MB), monta los archivos Python del núcleo en el sistema de archivos virtual, y ejecuta el motor de física a 60 FPS.

### Móvil (Renderizador Kivy)

```bash
# Ejecutar con renderizador Kivy
python3 main.py --kivy
```

Kivy maneja el bucle de eventos, el dibujo del canvas, y la inversión de coordenadas del eje Y automáticamente.

### Docker

```bash
docker build -t aetheris-ui .
docker run --rm aetheris-ui
```

---

## Inicio Rápido

### Hola Física

```python
from core.engine import AetherEngine
from core.elements import SmartPanel
from core.renderer_base import MockRenderer

# 1. Crear el motor de física
engine = AetherEngine()

# 2. Registrar un panel responsivo (5% de margen desde todos los bordes)
panel = SmartPanel(color=(0.9, 0.2, 0.6, 0.8), z=0)
engine.register_element(panel)

# 3. Crear un renderizador
renderer = MockRenderer()
renderer.init_window(800, 600, "Hola Física")

# 4. Ejecutar el bucle de física
for frame in range(60):
    # El motor calcula fuerzas, integra física, y devuelve
    # un arreglo NumPy estructurado para el renderizador
    data = engine.tick(800, 600)
    
    renderer.clear_screen((0.1, 0.1, 0.1, 1.0))
    renderer.render_frame(data)
    renderer.swap_buffers()
    
    # El panel converge suavemente a su asíntota:
    # x = 800 * 0.05 = 40, y = 600 * 0.05 = 30
    # w = 800 * 0.90 = 720, h = 600 * 0.90 = 540
    if frame % 10 == 0:
        print(f"Frame {frame}: rect={data[0]['rect']}")
```

### Diseño Impulsado por Servidor

```python
from core.engine import AetherEngine
from core.ui_builder import UIBuilder

engine = AetherEngine()

intent = {
    "layout": "column",
    "spacing": 20,
    "animation": "organic",
    "padding": 10,
    "elements": [
        {"id": "header", "type": "smart_panel", "padding": 0.03, "z": 0},
        {"id": "title", "type": "canvas_text", "x": 40, "y": 15, "w": 400, "h": 40,
         "text_content": "Hola Aetheris", "font_size": 24, "z": 5},
        {"id": "content", "type": "smart_panel", "padding": 0.05, "z": 1},
    ]
}

builder = UIBuilder()
builder.build_from_intent(engine, intent)
# engine ahora tiene 3 elementos con posiciones impulsadas por física
```

### Diseño Impulsado por Base de Datos (Puente Aether-Data)

```python
from core.engine import AetherEngine
from core.ui_builder import UIBuilder
from core.data_bridge import SQLiteProvider

engine = AetherEngine()
builder = UIBuilder()

# Conectar a una base de datos SQLite local
db = SQLiteProvider("./mi_app.db")
db.connect()

# Definir cómo las columnas de la BD se mapean a propiedades de física
template = {
    "type": "static_box",
    "columns": {
        "x": {"source": "pos_x", "scale": [0, 1000, 10, 790]},
        "y": {"source": "pos_y", "scale": [0, 1000, 10, 590]},
        "w": {"source": "width", "scale": [0, 10000, 50, 500]},
        "h": {"source": "height", "scale": [0, 10000, 50, 500]},
        "z": {"source": "layer"},
    },
    "metadata_fields": ["title", "rating"],
}

# Construir elementos directamente desde la consulta de base de datos
count = builder.build_from_datasource(engine, db, "SELECT * FROM movies", template)
print(f"Creados {count} elementos desde la base de datos")

db.disconnect()
```

---

## La Trinidad del Multi-Renderizado

La innovación central de Aetheris UI es la **arquitectura de renderizado desacoplada**. El motor de física produce un único arreglo NumPy estructurado por frame:

```python
dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')]
```

Este arreglo — que contiene `[x, y, ancho, alto]`, `[r, g, b, a]`, e `índice_z` para cada elemento — es el **único** dato que recibe el renderizador. El renderizador no tiene conocimiento de objetos `DifferentialElement`, constantes de resorte, o cálculos de asíntotas.

| Renderizador | Tecnología | Soporte de Texto | Plataforma |
|-------------|-----------|-----------------|------------|
| **GLRenderer** | ModernGL + shaders SDF + texturas Pillow | Texturas de texto rasterizadas en GPU | Escritorio (Linux/Windows/macOS) |
| **Pyodide Canvas** | HTML5 Canvas 2D + superposición DOM | Híbrido: Canvas fillText + HTML `<div>` | Web (cualquier navegador) |
| **KivyRenderer** | Kivy Graphics + widgets Label | Híbrido: texturas CoreLabel + Etiquetas Kivy | Móvil (iOS/Android) |
| **TkinterRenderer** | Tkinter Canvas | Texto de depuración vía `create_text` | Escritorio (solo depuración) |
| **MockRenderer** | impresión stdout | N/A | CI/CD sin cabeza |

Todos los renderizadores consumen el **idéntico** arreglo NumPy de la **idéntica** llamada `AetherEngine.tick()`. Cambiar de renderizador requiere modificar una sola línea de código.

---

## Resumen de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    MOTOR AETHERIS UI                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────────────────┐│
│  │  Dominio        │    │     Pipeline de Renderizado      ││
│  │  Matemático     │    │                                  ││
│  │                 │    │  ┌──────────┐ ┌──────────┐      ││
│  │ ┌─────────────┐ │    │  │GLRenderer│ │KivyRender│      ││
│  │ │StateTensor  │ │    │  │(ModernGL)│ │ (Kivy)   │      ││
│  │ │- state[4]   │ │    │  └────┬─────┘ └────┬─────┘      ││
│  │ │- velocity[4]│ │    │       │             │            ││
│  │ │- accel[4]   │ │    │       └──────┬──────┘            ││
│  │ └─────────────┘ │    │              │                   ││
│  │        │        │    │  ┌───────────▼───────────────┐  ││
│  │ ┌─────────────┐ │    │  │  Arreglo NumPy Estructurado│  ││
│  │ │   Solver    │ │    │  │  [('rect','f4',4),        │  ││
│  │ │- Ley de     │ │    │  │   ('color','f4',4),       │  ││
│  │ │  Hooke      │ │    │  │   ('z','i4')]             │  ││
│  │ └─────────────┘ │    │  └───────────────────────────┘  ││
│  │        │        │    │              │                   ││
│  │ ┌─────────────┐ │    │  ┌───────────▼───────────────┐  ││
│  │ │StateManager │ │    │  │     Metadatos JSON        │  ││
│  │ │- Lerp       │ │    │  │  (texto, fuente, datos    │  ││
│  │ │- HyperDamp  │ │    │  │   DOM)                    │  ││
│  │ └─────────────┘ │    │  └───────────────────────────┘  ││
│  └────────┬────────┘    └──────────────────────────────────┘│
│           │                                                   │
│  ┌────────▼────────┐                                         │
│  │  AetherEngine   │                                         │
│  │  - tick()       │                                         │
│  │  - registro     │                                         │
│  │  - seguimiento  │                                         │
│  │    de dt        │                                         │
│  └─────────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
```

Ver [docs/ARCHITECTURE_ES.md](docs/ARCHITECTURE_ES.md) para la inmersión profunda matemática completa.

---

## Fundamentos Matemáticos

### Integración de Euler

Cada frame, el estado del elemento evoluciona vía:

```
v(t+dt) = (v(t) + a(t) · dt) · (1 - viscosidad)
s(t+dt) = s(t) + v(t+dt) · dt
```

### Ley de Hooke

La fuerza restauradora atrae elementos hacia su asíntota:

```
F = (objetivo - actual) · k
```

### Amortiguamiento Crítico

Para un sistema masa-resorte con m=1:

```
c_crítico = 2 · √k
```

### Limitación por Norma L2 (Aether-Guard)

```
si ||v|| > V_max:
    v = (v / ||v||) · V_max
```

### Ajuste por Épsilon (Regla del 99%)

```
si ||s - objetivo|| < 0.5 Y ||v|| < 5.0:
    s = objetivo
    v = 0
```

Ver [docs/ARCHITECTURE_ES.md](docs/ARCHITECTURE_ES.md) para derivaciones completas.

---

## Referencia de API

Ver [docs/API_REFERENCE_ES.md](docs/API_REFERENCE_ES.md) para documentación completa de clases y métodos.

---

## Contribuir

1. Haz un fork del repositorio
2. Crea una rama de funcionalidad (`git checkout -b feature/funcionalidad-increible`)
3. Ejecuta la suite de pruebas: `pytest tests/ -v`
4. Confirma tus cambios (`git commit -m 'Agregar funcionalidad increíble'`)
5. Envía a la rama (`git push origin feature/funcionalidad-increible`)
6. Abre un Pull Request

---

## Licencia

Licencia MIT. Ver [LICENSE](LICENSE) para detalles.

---

## Visión Estratégica

Aetheris UI no es un reemplazo de React o Flutter — crea una **nueva categoría**: visualización de datos impulsada por física donde cada punto de datos es un objeto físico que puedes tocar, lanzar y explorar.

**Mercados objetivo**: Exploradores de catálogos estilo Netflix/Spotify, dashboards financieros, visualización de embeddings de IA, y herramientas educativas interactivas.

**Ventaja injusta**: Un solo código Python → 3 plataformas nativas (Web, Escritorio, Móvil) con normalización algebraica de datos y estabilidad numérica de grado industrial vía Aether-Guard.
