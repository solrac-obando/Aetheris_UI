# Aetheris UI — Referencia de API

> Guía completa del desarrollador para todas las clases, métodos y funciones públicas.

---

## Tabla de Contenidos

- [Módulos del Núcleo](#módulos-del-núcleo)
- [Fundamento Matemático (`aether_math.py`)](#fundamento-matemático-aether_mathpy)
- [Elementos (`elements.py`)](#elementos-elementspy)
- [Motor (`engine.py`)](#motor-enginepy)
- [Solver (`solver.py` / `solver_wasm.py`)](#solver-solverpy--solver_wasmpy)
- [Gestor de Estado (`state_manager.py`)](#gestor-de-estado-state_managerpy)
- [Tensor Compiler (`tensor_compiler.py`)](#tensor-compiler-tensor_compilerpy)
- [UI Builder (`ui_builder.py`)](#ui-builder-ui_builderpy)
- [Renderizadores](#renderizadores)
- [Base del Renderizador (`renderer_base.py`)](#base-del-renderizador-renderer_basepy)
- [Renderizador GL (`gl_renderer.py`)](#renderizador-gl-gl_rendererpy)
- [Renderizador Kivy (`kivy_renderer.py`)](#renderizador-kivy-kivy_rendererpy)
- [Renderizador Tkinter (`tkinter_renderer.py`)](#renderizador-tkinter-tkinter_rendererpy)
- [Puente del Solver (`solver_bridge.py`)](#puente-del-solver-solver_bridgepy)

---

## Módulos del Núcleo

Todos los módulos del núcleo residen en `core/` y se importan como:

```python
from core.engine import AetherEngine
from core.elements import SmartPanel, StaticBox, CanvasTextNode, DOMTextNode
from core.tensor_compiler import TensorCompiler
from core.ui_builder import UIBuilder
```

---

## Fundamento Matemático (`aether_math.py`)

### Constantes del Módulo

| Constante | Tipo | Valor | Descripción |
|-----------|------|-------|-------------|
| `EPSILON` | `np.float32` | `1e-9` | Denominador mínimo para división segura |
| `MAX_VELOCITY` | `np.float32` | `5000.0` | Velocidad máxima en píxeles/segundo |
| `MAX_ACCELERATION` | `np.float32` | `10000.0` | Aceleración máxima en píxeles/segundo² |
| `SNAP_DISTANCE` | `np.float32` | `0.5` | Umbral de distancia para el Ajuste por Épsilon (píxeles) |
| `SNAP_VELOCITY` | `np.float32` | `5.0` | Umbral de velocidad para el Ajuste por Épsilon (px/s) |

### `safe_divide(numerator, denominator, epsilon=EPSILON)`

División segura con protección por épsilon para prevenir división entre cero.

**Parámetros:**
- `numerator`: Dividendo (escalar o arreglo NumPy)
- `denominator`: Divisor (escalar o arreglo NumPy)
- `epsilon`: Valor absoluto mínimo para el denominador (por defecto: `1e-9`)

**Retorna:**
- Resultado de división seguro, nunca `inf` o `NaN` por división entre cero.

**Lanza:**
- Ninguna — siempre devuelve un valor finito.

**Ejemplo:**
```python
from core.aether_math import safe_divide
resultado = safe_divide(10.0, 0.0)  # Devuelve ~1e10, no inf
```

### `clamp_magnitude(vector, max_val)`

Limita la norma L2 (magnitud) de un vector preservando su dirección.

**Parámetros:**
- `vector`: Arreglo NumPy que representa un vector
- `max_val`: Magnitud máxima permitida

**Retorna:**
- Vector limitado con `||v|| <= max_val`.

**Ejemplo:**
```python
from core.aether_math import clamp_magnitude
v = np.array([3000.0, 4000.0], dtype=np.float32)  # ||v|| = 5000
limitado = clamp_magnitude(v, 3000.0)  # ||limitado|| = 3000
```

### `check_and_fix_nan(array, name="tensor")`

Detecta valores NaN/Inf y devuelve un arreglo puesto a cero con una advertencia.

**Parámetros:**
- `array`: Arreglo NumPy a verificar
- `name`: Identificador para el mensaje de advertencia

**Retorna:**
- Arreglo original si está limpio, arreglo puesto a cero si se detecta NaN/Inf.

**Lanza:**
- `RuntimeWarning`: Si se detecta NaN o Inf.

### `class StateTensor`

Representa un elemento de la interfaz como una partícula física con vectores de estado, velocidad y aceleración.

#### `__init__(x=0.0, y=0.0, w=100.0, h=100.0)`

Inicializa un StateTensor con posición y dimensiones.

**Parámetros:**
- `x`: Posición X en píxeles
- `y`: Posición Y en píxeles (origen arriba-izquierda)
- `w`: Ancho en píxeles
- `h`: Alto en píxeles

**Atributos:**
- `state`: `np.ndarray` de forma `(4,)`, tipo `float32` — `[x, y, w, h]`
- `velocity`: `np.ndarray` de forma `(4,)`, tipo `float32` — vector de velocidad
- `acceleration`: `np.ndarray` de forma `(4,)`, tipo `float32` — vector de aceleración

#### `apply_force(force)`

Aplica un vector de fuerza al tensor de aceleración.

Asume masa `m=1`, por lo que `F = ma` se convierte en `F = a`. Las fuerzas se acumulan.

**Parámetros:**
- `force`: `np.ndarray` de forma `(4,)`, tipo `float32` — vector de fuerza `[fx, fy, fw, fh]`

**Lanza:**
- `RuntimeWarning`: Si Aether-Guard detecta NaN/Inf en la fuerza de entrada.

#### `euler_integrate(dt, viscosity=0.1, target_state=None)`

Actualiza el estado de física usando integración de Euler semi-implícita.

**Pasos:**
1. Valida `dt` con `safe_divide` (rango de 0 a 1 segundo)
2. Actualiza velocidad: `v = (v + a·dt) · (1 - viscosidad)`
3. Limita magnitud de velocidad a `MAX_VELOCITY`
4. Actualiza estado: `s = s + v·dt`
5. Limita ancho/alto a >= 0
6. Reinicia aceleración a cero
7. Verifica NaN/Inf en estado y velocidad
8. Aplica Ajuste por Épsilon si está cerca de `target_state`

**Parámetros:**
- `dt`: Delta de tiempo en segundos
- `viscosity`: Factor de amortiguamiento (0.0 = sin amortiguamiento, 1.0 = detención total)
- `target_state`: Objetivo opcional `[x, y, w, h]` para verificación de ajuste

---

## Elementos (`elements.py`)

### `class DifferentialElement(ABC)`

Clase base abstracta para todos los elementos de la interfaz. Cada elemento posee un `StateTensor` y define cómo calcular su estado objetivo (asíntota).

#### `__init__(x=0, y=0, w=100, h=100, color=(1,1,1,1), z=0)`

**Parámetros:**
- `x, y`: Coordenadas de posición
- `w, h`: Ancho y alto
- `color`: Tupla RGBA, valores float32 de 0 a 1
- `z`: Índice-Z para profundidad de renderizado

#### `calculate_asymptotes(container_w, container_h) -> np.ndarray` *(abstracto)*

Calcula el `[x, y, w, h]` objetivo para el solver basado en el tamaño del contenedor.

**Parámetros:**
- `container_w`: Ancho del contenedor/ventana en píxeles
- `container_h`: Alto del contenedor/ventana en píxeles

**Retorna:**
- `np.ndarray` de forma `(4,)`, tipo `float32` — estado objetivo

#### `rendering_data` *(propiedad)*

Devuelve un diccionario con `rect`, `color` y `z` para el renderizador.

### `class StaticBox(DifferentialElement)`

Un elemento estático con posición objetivo fija. Ignora el tamaño del contenedor.

#### `__init__(x, y, w, h, color=(1,1,1,1), z=0)`

**Parámetros:**
- `x, y`: Posición fija
- `w, h`: Dimensiones fijas
- `color`: Tupla RGBA
- `z`: Índice-Z

### `class SmartPanel(DifferentialElement)`

Un panel responsivo que mantiene un margen porcentual desde los bordes del contenedor.

#### `__init__(x=0, y=0, w=100, h=100, color=(1,1,1,1), z=0, padding=0.05)`

**Parámetros:**
- `x, y, w, h`: Valores iniciales (sobrescritos por la asíntota)
- `color`: Tupla RGBA
- `z`: Índice-Z
- `padding`: Fracción del contenedor para el margen (0.05 = 5%)

#### `calculate_asymptotes(container_w, container_h)`

Devuelve `[container_w·padding, container_h·padding, container_w·(1-2·padding), container_h·(1-2·padding)]`.

### `class FlexibleTextNode(DifferentialElement)`

Un elemento de texto con posicionamiento estático. Actualmente se comporta como `StaticBox` con metadatos de texto.

#### `__init__(x=0, y=0, w=200, h=50, color=(1,1,1,1), z=0, text="Text")`

**Parámetros:**
- `x, y, w, h`: Posición y dimensiones
- `color`: Tupla RGBA
- `z`: Índice-Z
- `text`: Contenido del texto

#### `text` *(propiedad)*

Obtiene/establece el contenido del texto.

### `class SmartButton(DifferentialElement)`

Un botón anclado a un elemento padre con desplazamientos configurables.

#### `__init__(parent, offset_x=0, offset_y=0, offset_w=100, offset_h=50, color=(0.8,0.8,0.2,1.0), z=0)`

**Parámetros:**
- `parent`: `DifferentialElement` padre al cual anclarse
- `offset_x`: Desplazamiento X desde el borde izquierdo del padre
- `offset_y`: Desplazamiento Y desde el borde superior del padre
- `offset_w`: Ancho del botón
- `offset_h`: Alto del botón
- `color`: Tupla RGBA
- `z`: Índice-Z

#### `calculate_asymptotes(container_w, container_h)`

Devuelve `[padre.x + offset_x, padre.y + offset_y, offset_w, offset_h]`.

### `class CanvasTextNode(DifferentialElement)`

Texto renderizado directamente en el Canvas vía `ctx.fillText`. Participa completamente en la simulación de física.

#### `__init__(x=0, y=0, w=200, h=50, color=(1,1,1,1), z=0, text="Text", font_size=24, font_family="Arial")`

**Parámetros:**
- `x, y, w, h`: Posición y dimensiones impulsadas por física
- `color`: Tupla RGBA para el color del texto (float32, 0-1)
- `z`: Índice-Z
- `text`: Contenido del texto
- `font_size`: Tamaño de fuente en píxeles
- `font_family`: Nombre de la familia de fuente

#### `text_metadata` *(propiedad)*

Devuelve `{"type": "canvas_text", "text": ..., "size": ..., "family": ..., "color": ...}`.

### `class DOMTextNode(DifferentialElement)`

Texto renderizado como un `<div>` de HTML superpuesto en el Canvas. Habilita selección de texto, accesibilidad y SEO.

#### `__init__(x=0, y=0, w=200, h=50, color=(0,0,0,0), z=0, text="Text", font_size=16, font_family="Arial", text_color=(1,1,1,1))`

**Parámetros:**
- `x, y, w, h`: Posición y dimensiones impulsadas por física
- `color`: RGBA para el fondo del rectángulo (típicamente transparente)
- `z`: Índice-Z
- `text`: Contenido del texto
- `font_size`: Tamaño de fuente en píxeles
- `font_family`: Nombre de la familia de fuente
- `text_color`: Tupla RGBA para el color del texto (float32, 0-1)

#### `text_metadata` *(propiedad)*

Devuelve `{"type": "dom_text", "text": ..., "size": ..., "family": ..., "color": ..., "bg_color": ...}`.

---

## Motor (`engine.py`)

### `class AetherEngine`

El orquestador central. Gestiona el registro de elementos, el bucle de simulación de física, y la extracción de datos.

#### `__init__()`

Inicializa el motor con registro vacío, seguimiento de tiempo, StateManager y TensorCompiler.

#### `register_element(element)`

Registra un `DifferentialElement` para simulación de física.

**Parámetros:**
- `element`: Una instancia de `DifferentialElement`

#### `tick(win_w, win_h) -> np.ndarray`

Ejecuta un frame de la simulación de física.

**Pasos:**
1. Calcular delta de tiempo
2. Verificar choque de diseño (hiper-amortiguamiento)
3. Para cada elemento: calcular asíntota, computar fuerzas, integrar
4. Extraer arreglo NumPy estructurado

**Parámetros:**
- `win_w`: Ancho de ventana en píxeles
- `win_h`: Alto de ventana en píxeles

**Retorna:**
- `np.ndarray` estructurado con tipo `[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')]`

#### `get_ui_metadata() -> str`

Devuelve una cadena JSON conteniendo metadatos de texto para elementos `CanvasTextNode` y `DOMTextNode`, indexados por índice-Z.

**Retorna:**
- Cadena JSON, por ejemplo: `{"5": {"type": "canvas_text", "text": "Título", "size": 24, ...}}`

#### `dt` *(propiedad)*

Delta de tiempo del último frame en segundos.

#### `element_count` *(propiedad)*

Número de elementos registrados.

---

## Solver (`solver.py` / `solver_wasm.py`)

### `calculate_restoring_force(current_state, target_state, spring_constant) -> np.ndarray`

Aplica la Ley de Hooke: `F = (objetivo - actual) · k`.

**Parámetros:**
- `current_state`: `[x, y, w, h]` actual como `float32`
- `target_state`: `[x, y, w, h]` objetivo como `float32`
- `spring_constant`: Rigidez `k`

**Retorna:**
- Vector de fuerza como `float32`, magnitud limitada a 10,000.

### `calculate_boundary_forces(state, container_w, container_h, boundary_stiffness) -> np.ndarray`

Calcula fuerzas de repulsión por violaciones de frontera.

**Parámetros:**
- `state`: `[x, y, w, h]` actual como `float32`
- `container_w`: Ancho del contenedor
- `container_h`: Alto del contenedor
- `boundary_stiffness`: Constante de resorte para repulsión de frontera

**Retorna:**
- Vector de fuerza de frontera como `float32`, magnitud limitada a 5,000.

### `clamp_vector_magnitude(vector, max_val) -> np.ndarray`

Limita la norma L2 del vector preservando la dirección.

**Parámetros:**
- `vector`: Vector de entrada
- `max_val`: Magnitud máxima

**Retorna:**
- Vector limitado.

---

## Gestor de Estado (`state_manager.py`)

### `class StateManager`

Gestiona la detección de choques de diseño y la interpolación lineal para transiciones de estado.

#### `__init__()`

Inicializa con dimensiones cero y sin amortiguamiento activo.

#### `check_teleportation_shock(current_w, current_h) -> float`

Detecta cambios drásticos en el tamaño de la ventana y devuelve un multiplicador de viscosidad.

**Parámetros:**
- `current_w`: Ancho actual de la ventana
- `current_h`: Alto actual de la ventana

**Retorna:**
- `5.0` si se detecta choque (15 cuadros de amortiguamiento 5x), `1.0` en caso contrario.

#### `lerp_arrays(state_a, state_b, t) -> np.ndarray`

Interpolación lineal: `(1-t)·a + t·b`.

**Parámetros:**
- `state_a`: Arreglo de estado inicial
- `state_b`: Arreglo de estado objetivo
- `t`: Factor de interpolación [0, 1]

**Retorna:**
- Arreglo interpolado como `float32`.

---

## Tensor Compiler (`tensor_compiler.py`)

### `class TensorCompiler`

Compila intenciones de diseño JSON en arreglos de coeficientes de física.

#### `STIFFNESS_MAP` *(atributo de clase)*

Valores de rigidez predefinidos: `{"snappy": 0.8, "organic": 0.1, "fluid": 0.05, "rigid": 2.0, "gentle": 0.02}`

#### `VISCOSITY_MAP` *(atributo de clase)*

Valores de viscosidad predefinidos: `{"snappy": 0.3, "organic": 0.5, "fluid": 0.7, "rigid": 0.1, "gentle": 0.85}`

#### `compile_intent(intent_json) -> np.ndarray`

Compila un JSON de intención de diseño en un arreglo de coeficientes de física.

**Parámetros:**
- `intent_json`: Diccionario con `layout`, `spacing`, `animation`, `padding`, `elements`, etc.

**Retorna:**
- Arreglo estructurado con tipo `[('element_id', 'U64'), ('stiffness', 'f4'), ('viscosity', 'f4'), ('boundary_padding', 'f4', 4), ('spacing', 'f4')]`

#### `apply_coefficients(engine, coefficients)`

Aplica coeficientes compilados a una instancia de `AetherEngine`.

**Parámetros:**
- `engine`: `AetherEngine` objetivo
- `coefficients`: Arreglo estructurado de `compile_intent()`

#### `get_default_coefficients(animation="organic", spacing=0.0, padding=0.0) -> np.ndarray`

Obtiene coeficientes predeterminados para un ajuste de animación dado.

### `speed_to_stiffness(transition_time_ms) -> float`

Deriva la constante de resorte desde la duración de transición: `k = 16 / T²`.

**Parámetros:**
- `transition_time_ms`: Tiempo de transición deseado en milisegundos

**Retorna:**
- Constante de resorte `k` como `float32`, limitada a 10,000.

### `speed_to_viscosity(transition_time_ms) -> float`

Deriva la viscosidad desde la velocidad de transición.

**Parámetros:**
- `transition_time_ms`: Tiempo de transición deseado en milisegundos

**Retorna:**
- Valor de viscosidad (0.05–0.95) como `float32`.

---

## UI Builder (`ui_builder.py`)

### `class UIBuilder`

Traduce Intención JSON en elementos `AetherEngine` registrados.

#### `ELEMENT_TYPES` *(atributo de clase)*

Mapeo: `{"static_box": StaticBox, "smart_panel": SmartPanel, "smart_button": SmartButton, "flexible_text": FlexibleTextNode, "canvas_text": CanvasTextNode, "dom_text": DOMTextNode}`

#### `build_from_intent(engine, intent)`

Analiza la intención JSON y registra todos los elementos con el motor.

**Parámetros:**
- `engine`: `AetherEngine` objetivo
- `intent`: Diccionario de intención JSON

#### `element_count` *(propiedad)*

Número de elementos construidos.

---

## Renderizadores

### `renderer_base.py`

#### `class BaseRenderer(ABC)`

Interfaz abstracta para todos los renderizadores.

**Métodos abstractos:**
- `init_window(width, height, title)` — Inicializa la superficie de renderizado
- `clear_screen(color)` — Limpia con color de fondo
- `render_frame(data_buffer)` — Renderiza el arreglo estructurado
- `swap_buffers()` — Presenta el frame

### `gl_renderer.py`

#### `class GLRenderer(BaseRenderer)`

Renderizador ModernGL con shaders SDF y texturas de texto Pillow.

**Métodos clave:**
- `init_window(width, height, title)` — Crea contexto OpenGL independiente
- `render_frame(data_buffer, engine_metadata=None)` — Renderiza con metadatos de texto opcionales
- `_get_or_create_text_texture(text, font_size, color_rgba, font_family)` — Almacena texturas de texto en caché

### `kivy_renderer.py`

#### `class KivyRenderer(BaseRenderer)`

Renderizador Kivy con inversión del eje Y y soporte de texto híbrido.

**Métodos clave:**
- `init_window(width, height, title)` — Inicializa el renderizador
- `set_canvas(canvas)` — Establece el widget canvas de Kivy
- `set_dom_container(container)` — Establece el contenedor para etiquetas tipo DOM
- `render_frame(data_buffer, engine_metadata=None)` — Renderiza con inversión del eje Y
- `cleanup_dom_labels()` — Elimina todas las etiquetas de texto DOM

### `tkinter_renderer.py`

#### `class TkinterRenderer(BaseRenderer)`

Renderizador de depuración Tkinter para prototipado rápido.

**Métodos clave:**
- `init_window(width, height, title)` — Crea ventana Tk y Canvas
- `start(engine_instance)` — Inicia el bucle principal de Tkinter con actualizaciones de física
- `stop()` — Detiene el renderizador y limpia

### `solver_bridge.py`

Detecta automáticamente la disponibilidad de Numba e importa la implementación de solver apropiada.

**Exporta:**
- `calculate_restoring_force` — De `solver.py` (Numba) o `solver_wasm.py` (NumPy)
- `calculate_boundary_forces` — Misma lógica de doble ruta
- `HAS_NUMBA` — Booleano indicando qué ruta está activa

---

*Para contexto arquitectónico, ver [ARCHITECTURE_ES.md](ARCHITECTURE_ES.md). Para el README principal, ver [../README_ES.md](../README_ES.md).*
