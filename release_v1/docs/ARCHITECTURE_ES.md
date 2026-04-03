# Aetheris UI — Inmersión Profunda en Arquitectura

> El Alma Matemática de un Motor de Interfaz Impulsado por Física

---

## Tabla de Contenidos

- [1. La Filosofía Central: Física-como-UI](#1-la-filosofía-central-física-como-ui)
- [2. Integración de Euler: El Pulso Temporal](#2-integración-de-euler-el-pulso-temporal)
- [3. Ley de Hooke y el Solver de Restricciones](#3-ley-de-hooke-y-el-solver-de-restricciones)
- [4. Aether-Guard: Capa de Seguridad Matemática](#4-aether-guard-capa-de-seguridad-matemática)
- [5. Gestión de Estado y Estabilidad](#5-gestión-de-estado-y-estabilidad)
- [6. El Puente de Desacoplamiento](#6-el-puente-de-desacoplamiento)
- [7. Arquitectura del Pipeline de Renderizado](#7-arquitectura-del-pipeline-de-renderizado)
- [8. Interfaz Impulsada por Servidor y el Tensor Compiler](#8-interfaz-impulsada-por-servidor-y-el-tensor-compiler)
- [9. Características de Rendimiento](#9-características-de-rendimiento)

---

## 1. La Filosofía Central: Física-como-UI

Los motores de interfaz de usuario tradicionales utilizan **algoritmos de diseño estáticos**: flexbox, grid, posicionamiento absoluto. Estos son deterministas pero rígidos — saltan instantáneamente del estado A al estado B sin física intermedia.

Aetheris UI trata cada elemento de la interfaz como una **partícula física** con cuatro grados de libertad: posición (x, y) y dimensiones (ancho, alto). Cada partícula posee:

- Un **vector de estado** `s = [x, y, w, h]` en `np.float32`
- Un **vector de velocidad** `v = [vx, vy, vw, vh]`
- Un **vector de aceleración** `a = [ax, ay, aw, ah]`

El diseño de la interfaz emerge de la **integración de fuerzas** a lo largo del tiempo, no de un pase de diseño. Esto produce transiciones naturales y suaves con momento, sobrepaso y amortiguamiento — el mismo comportamiento físico que esperarías de un objeto real moviéndose por el espacio.

### Fundamento Matemático

El sistema se fundamenta en dos tradiciones matemáticas:

1. **Álgebra de Baldor** — Proporcionalidad y escalado lineal para diseños responsivos (por ejemplo, el margen de SmartPanel como fracción del tamaño del contenedor). La influencia de Baldor es explícita en la aplicación de proporciones directas e inversas para calcular posiciones y dimensiones relativas al contenedor.

2. **Precálculo** — Sistemas lineales, análisis de estabilidad, y la relación entre constantes de resorte, razones de amortiguamiento y tiempo de asentamiento. Los conceptos de límites y derivadas del Precálculo fundamentan la integración de Euler y el cálculo de velocidades mediante diferencias finitas.

---

## 2. Integración de Euler: El Pulso Temporal

### El Bucle de Integración

Cada frame, `AetherEngine.tick()` ejecuta la siguiente secuencia:

```
1. Calcular delta de tiempo: dt = t_actual - t_anterior
2. Para cada elemento:
   a. Calcular asíntota objetivo (estado deseado)
   b. Computar fuerza restauradora (Ley de Hooke)
   c. Computar fuerzas de frontera (restricciones del contenedor)
   d. Aplicar fuerzas al tensor de aceleración
   e. Integrar: actualizar velocidad y estado
   f. Aplicar verificaciones de seguridad Aether-Guard
   g. Verificar condición de Ajuste por Épsilon
3. Extraer arreglo NumPy estructurado para el renderizador
```

### Fórmula de Integración de Euler

La integración utiliza **Euler semi-implícito (simpléctico)**:

```python
# Actualización de velocidad con viscosidad (fricción)
v(t+dt) = (v(t) + a(t) · dt) · (1 - viscosidad)

# Actualización de estado
s(t+dt) = s(t) + v(t+dt) · dt
```

El término de viscosidad `(1 - viscosidad)` actúa como un factor de amortiguamiento. Con `viscosidad = 0.1`, la velocidad decae un 10% cada frame en ausencia de fuerzas — simulando la resistencia del aire.

### Validación del Delta de Tiempo

El valor `dt` se valida a través de la **división protegida por épsilon de Aether-Guard**:

```python
dt_seguro = safe_divide(dt, 1.0)  # Protegido por épsilon
dt_seguro = max(dt_seguro, 0.0)    # Sin tiempo negativo
dt_seguro = min(dt_seguro, 1.0)    # Limitado a 1 segundo máximo
```

Esto previene la "espiral de la muerte" donde un `dt` grande (por ejemplo, de una pausa del recolector de basura) causa que la física explote.

---

## 3. Ley de Hooke y el Solver de Restricciones

### Fuerza Restauradora

La fuerza principal que atrae elementos hacia su objetivo es la **Ley de Hooke**:

```
F_restauradora = (objetivo - actual) · k
```

Donde:
- `objetivo` es la asíntota calculada por el método `calculate_asymptotes()` del elemento
- `actual` es el estado actual del elemento
- `k` es la constante de resorte (rigidez)

**Mayor k** = resorte más rígido, convergencia más rápida, mayor potencial de sobrepaso.
**Menor k** = resorte más suave, convergencia más lenta, movimiento más fluido.

### Fuerzas de Frontera

Los elementos que cruzan los límites del contenedor experimentan una **fuerza de repulsión**:

```python
si x < 0:
    F_x += (0 - x) · rigidez_frontera
sino si x + w > ancho_contenedor:
    F_x -= ((x + w) - ancho_contenedor) · rigidez_frontera
```

Esto previene que los elementos escapen del área visible, actuando como paredes invisibles.

### Optimización con Numba

Las funciones del solver están decoradas con `@njit(cache=True)` para ejecución en escritorio, compilándose a código máquina en tiempo de ejecución. Para WASM/Pyodide (que carece de Numba), un respaldo puro de NumPy en `solver_wasm.py` proporciona comportamiento idéntico.

---

## 4. Aether-Guard: Capa de Seguridad Matemática

Los motores de física son inherentemente inestables. Rigidez alta, amortiguamiento bajo, o pasos de tiempo grandes pueden producir **velocidades explosivas** que crashean la aplicación. Aetheris UI implementa cuatro mecanismos de seguridad:

### 4.1 División Protegida por Épsilon

```python
def safe_divide(numerador, denominador, epsilon=1e-9):
    denom = max(|denominador|, epsilon)
    return numerador / (denom · sign(denominador))
```

Basada en la **definición de límite** del Cálculo: cuando x → 0, f(x)/x es indefinida. Reemplazamos el denominador con `max(|x|, ε)` para garantizar que nunca llegue a cero. Esta protección es fundamental para prevenir resultados infinitos o NaN que corromperían toda la simulación.

### 4.2 Limitación de Velocidad por Norma L2

```python
def clamp_magnitude(vector, max_val):
    mag = ||vector||  # Norma L2
    si mag > max_val:
        return (vector / mag) · max_val
    return vector
```

Basada en la **normalización de vectores** del Álgebra Lineal: si la magnitud de un vector excede el umbral, lo escalamos hacia abajo preservando su dirección. Esto previene que los elementos se muevan más rápido que `VELOCIDAD_MAX = 5000 px/s`.

La norma L2 (también llamada norma euclidiana) se calcula como:

```
||v|| = √(v₁² + v₂² + v₃² + v₄²)
```

### 4.3 Limitación de Aceleración

De manera similar, la aceleración se limita a `ACELERACION_MAX = 10,000 px/s²`. Esto previene que una sola fuerza grande (por ejemplo, de un error de desplazamiento masivo) cree aceleración inmanejable.

### 4.4 Detección y Recuperación de NaN/Inf

```python
def check_and_fix_nan(array, nombre="tensor"):
    si any(isnan(array)) o any(isinf(array)):
        advertir(f"Aether-Guard: NaN/Inf detectado en {nombre}")
        return array_ceros
    return array
```

Si cualquier cálculo produce `NaN` o `Infinito` (por ejemplo, de división por cero o desbordamiento), el tensor afectado se reinicia a cero con una advertencia. Esto previene que la corrupción se propague por la simulación.

---

## 5. Gestión de Estado y Estabilidad

### 5.1 La Regla del 99% (Ajuste por Épsilon)

Cuando los elementos se acercan a su objetivo, la fuerza restauradora se aproxima a cero pero nunca lo alcanza. En teoría, esto crea la **Paradoja de Zenón** — pasos infinitos para alcanzar el objetivo. En la práctica, ajustamos:

```python
si ||estado - objetivo|| < 0.5 Y ||velocidad|| < 5.0:
    estado = objetivo
    velocidad = 0
    aceleración = 0
```

Los umbrales (0.5 píxeles, 5.0 px/s) se eligen para estar **por debajo de la percepción visual humana** en DPI típico de pantalla. Una vez ajustado, el elemento deja de consumir ciclos de CPU hasta que se aplique una nueva fuerza.

### 5.2 Hiper-Amortiguamiento (Absorción de Choques de Diseño)

Cuando el tamaño de la ventana cambia drásticamente (por ejemplo, 1920px → 375px para móvil), las asíntotas saltan instantáneamente. La Ley de Hooke genera una fuerza masiva del gran error de desplazamiento, potencialmente causando que los elementos se desborden salvajemente.

**Solución**: Detectar el choque y aumentar temporalmente la viscosidad:

```python
si |delta_ancho| > 200px:
    cuadros_hiper_amortiguamiento = 15

si cuadros_hiper_amortiguamiento > 0:
    return viscosidad × 5.0  # 5x amortiguamiento
return viscosidad × 1.0      # Amortiguamiento normal
```

Esto es análogo al **amortiguador de un automóvil** golpeando un bache — el fluido de amortiguamiento se espesa momentáneamente para absorber el impacto, luego vuelve a la normalidad. El sistema mantiene un contador de cuadros que decae gradualmente, proporcionando una transición suave entre el estado de choque y el estado normal.

### 5.3 Interpolación Lineal (Lerp) para Transiciones de Estado

Al transicionar entre estados nombrados (por ejemplo, escritorio → móvil), el motor utiliza **interpolación lineal**:

```
P_nuevo = (1 - t) · P_base + t · P_objetivo
```

Con `t = 0.1`, cada frame mueve el 10% de la distancia restante — produciendo una transición suave y eased en lugar de un salto instantáneo. Esta fórmula proviene directamente del **Álgebra de Baldor**, capítulo de proporciones y mezclas, aplicada al dominio de vectores de estado.

---

## 6. El Puente de Desacoplamiento

### Arreglo NumPy Estructurado

El canal de comunicación entre el motor de física y el renderizador es un **arreglo estructurado plano y eficiente en memoria**:

```python
tipo_dato = [
    ('rect', 'f4', 4),    # [x, y, ancho, alto] como float32
    ('color', 'f4', 4),   # [r, g, b, a] como float32
    ('z', 'i4'),          # índice-z como int32
]
```

**¿Por qué este formato?**

1. **Compatible con GPU**: `float32` se mapea directamente a atributos de vértice OpenGL/WebGL.
2. **Eficiente en memoria**: Diseño de memoria contigua permite transferencias sin copia.
3. **Seguro en tipos**: El tipo estructurado previene desacuerdos accidentales de tipo.
4. **Agnóstico del renderizador**: Cualquier renderizador que entienda este formato puede consumir los datos.

### Puente de Metadatos JSON

Dado que el arreglo estructurado solo puede contener tipos numéricos, los **metadatos de texto** (cadenas, tamaños de fuente, familias de fuente) se exponen a través de un puente JSON separado:

```python
engine.get_ui_metadata()
# Devuelve: {"5": {"tipo": "canvas_text", "texto": "Título", "tamaño": 24, ...}}
```

El renderizador lee tanto el arreglo NumPy (para posiciones) como los metadatos JSON (para propiedades de texto) cada frame.

---

## 7. Arquitectura del Pipeline de Renderizado

### Escritorio: ModernGL + Shaders SDF

```
AetherEngine.tick()
    → Arreglo NumPy Estructurado
    → GLRenderer.render_frame()
        → Carga VBO (np.hstack → bytes)
        → Matriz de proyección ortográfica
        → Shader de vértices (generación de quad por gl_VertexID)
        → Shader de fragmentos (rectángulos redondeados SDF)
        → Texturas de texto (rasterización Pillow → textura GPU)
    → ctx.finish()
```

El shader de fragmentos SDF (Signed Distance Function / Función de Distancia con Signo) produce **rectángulos redondeados anti-aliased** a cualquier resolución:

```glsl
float roundedRectSDF(vec2 p, vec2 b, float r) {
    vec2 q = abs(p) - b + r;
    return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r;
}
```

La **traslación de ejes** en el shader (`vec2 p = (v_texcoord - 0.5) * size`) centra el sistema de coordenadas en el centro del rectángulo, simplificando enormemente el cálculo de la SDF. Sin esta traslación, tendríamos que calcular distancias desde cada esquina individualmente.

### Web: Pyodide + HTML5 Canvas

```
AetherEngine.tick()
    → Arreglo NumPy Estructurado (PyProxy)
    → aether_bridge.js renderLoop()
        → Extraer rects/colores vía .getBuffer().data
        → Canvas 2D: fillRect / roundRect
        → Canvas 2D: fillText (para canvas_text)
        → DOM: createElement('div') + translate3d (para dom_text)
        → Destruir todos los objetos PyProxy (sin fugas)
    → requestAnimationFrame(renderLoop)
```

### Móvil: Kivy

```
AetherEngine.tick()
    → Arreglo NumPy Estructurado
    → KivyRenderer.render_frame()
        → Inversión del eje Y: kivy_y = altura - y - h
        → kivy.graphics: Color + Rectangle/RoundedRectangle
        → kivy.core.text: textura CoreLabel (para canvas_text)
        → kivy.uix.label: widget Label (para dom_text)
    → Clock.schedule_interval(1/60)
```

---

## 8. Interfaz Impulsada por Servidor y el Tensor Compiler

### Intención JSON

Los diseños se definen como JSON, no como Python codificado:

```json
{
  "layout": "column",
  "spacing": 20,
  "animation": "organic",
  "padding": 10,
  "elements": [
    {"id": "header", "type": "smart_panel", "padding": 0.03, "z": 0},
    {"id": "title", "type": "canvas_text", "x": 40, "y": 15, "w": 400, "h": 40,
     "text_content": "Hola", "font_size": 24, "z": 5}
  ]
}
```

### TensorCompiler

El `TensorCompiler` traduce este JSON en **coeficientes de física**:

```python
compiler = TensorCompiler()
coeficientes = compiler.compile_intent(intent)
# Devuelve: arreglo estructurado con [rigidez, viscosidad, margen_frontera, espaciado]
```

### Derivación de Rigidez desde Tiempo de Transición

El compiler puede derivar la constante de resorte `k` desde una duración de transición deseada `T`:

```
Para amortiguamiento crítico (m=1):
  c = 2√k
  τ = 1/√k  (constante de tiempo)
  T_asentamiento = 4τ = 4/√k

Resolviendo para k:
  k = 16 / T²
```

Una transición de 300ms requiere `k = 16 / 0.3² ≈ 177.8`. Esta derivación proviene directamente del análisis de sistemas lineales del **Precálculo**, aplicando las propiedades de las ecuaciones diferenciales de segundo orden para sistemas masa-resorte amortiguados.

---

## 9. Características de Rendimiento

### Escritorio (optimizado con Numba)

| Operación | Tiempo (μs) |
|-----------|-------------|
| Fuerza restauradora (por elemento) | ~0.1 |
| Fuerzas de frontera (por elemento) | ~0.2 |
| Integración de Euler (por elemento) | ~0.3 |
| Tick completo (10 elementos) | ~5 |
| Tick completo (100 elementos) | ~50 |

### Web (NumPy puro vía Pyodide)

| Operación | Tiempo (μs) |
|-----------|-------------|
| Fuerza restauradora (por elemento) | ~0.5 |
| Fuerzas de frontera (por elemento) | ~1.0 |
| Integración de Euler (por elemento) | ~1.5 |
| Tick completo (10 elementos) | ~25 |
| Tick completo (100 elementos) | ~250 |

Todas las operaciones están bien dentro del **presupuesto de 16.67ms** para 60 FPS, incluso en WASM.

### Memoria

- Arreglo estructurado: 36 bytes por elemento (16 + 16 + 4)
- Sobrecarga PyProxy: ~100 bytes por proxy (destruido cada frame)
- Caché de texturas de texto: ~1KB por cadena de texto única

---

*Para documentación completa de la API, ver [API_REFERENCE_ES.md](API_REFERENCE_ES.md).*
*Para el README principal en español, ver [../README_ES.md](../README_ES.md).*

---

## 10. Aether-Data: El Puente de Base de Datos

### Resumen

Aether-Data proporciona una interfaz unificada para poblar elementos de la UI desde bases de datos. Soporta:

- **SQLite** — Persistencia local, compatible con WASM usando el sistema de archivos virtual de Pyodide
- **PostgreSQL (vía proxy REST)** — Datos remotos de alto rendimiento, con protección de credenciales del lado del servidor

### Normalización de Datos (Escalado Min-Max)

Los valores de la base de datos a menudo tienen rangos que causarían comportamiento de física "explosivo" (por ejemplo, calificaciones de películas de 0 a 10,000). Aether-Data aplica **Escalado Min-Max de Álgebra Lineal** para normalizar estos valores a rangos de píxeles seguros:

```
escalado = objetivo_min + (valor - datos_min) * (objetivo_max - objetivo_min) / (datos_max - datos_min)
```

**Protección Aether-Guard:** La división usa protección por épsilon (`1e-9`) para prevenir división entre cero cuando `datos_min == datos_max`. La salida se limita a `[objetivo_min, objetivo_max]`.

Rango objetivo predeterminado: `[10.0, 500.0]` píxeles — lo suficientemente grande para ser visible, lo suficientemente pequeño para permanecer en pantalla.

### Arquitectura de Proveedores

```
┌─────────────────────────────────────────────────┐
│              Motor Aetheris UI                  │
│                                                  │
│  UIBuilder.build_from_datasource()              │
│         │                                        │
│         ▼                                        │
│  ┌──────────────────┐    ┌──────────────────┐   │
│  │  SQLiteProvider  │    │RemoteAetherProv. │   │
│  │  (Local/SQLite)  │    │ (Proxy REST)     │   │
│  │                  │    │                  │   │
│  │  - Connect       │    │  - /api/v1/      │   │
│  │  - CRUD ops      │    │    db-bridge     │   │
│  │  - Disconnect    │    │  - Sin creds BD  │   │
│  └────────┬─────────┘    │    expuestos     │   │
│           │              └────────┬─────────┘   │
│           │                       │             │
│           ▼                       ▼             │
│    BD SQLite               Servidor Flask       │
│    (archivo local)        ┌──────────────┐      │
│                           │  PostgreSQL  │      │
│                           │  (simulado)  │      │
│                           └──────────────┘      │
└─────────────────────────────────────────────────┘
```

### Vector-a-Tensor: Visualizando Embeddings de IA

La utilidad `vector_to_tensor()` convierte embeddings `pgvector` de PostgreSQL en fuerzas de física:

```python
embedding = [0.5, -0.3, 0.8, -0.1]  # Embedding de IA
fuerza = vector_to_tensor(embedding, scale=100.0)
# fuerza = [50.0, -30.0, 80.0, -10.0]
elemento.tensor.apply_force(fuerza)
```

Esto permite "Visualizar Embeddings de IA" — cada dimensión del embedding se convierte en un eje de fuerza (x, y, ancho, alto), permitiendo que la similitud semántica se manifieste como proximidad física.

### Seguridad de Conexión

- **SQLiteProvider**: Implementa `__del__`, `__enter__`, y `__exit__` para limpieza garantizada. Las conexiones se cierran automáticamente en la recolección de basura o al salir del context manager.
- **RemoteAetherProvider**: Peticiones HTTP sin estado con timeouts configurables (`REMOTE_CONNECT_TIMEOUT = 5s`, `REMOTE_REQUEST_TIMEOUT = 10s`).

---

## 11. Física Háptica: Arrastrar, Soltar y Lanzar

### Diferencia Regresiva de Segundo Orden para Lanzamientos Suaves

Cuando un usuario arrastra y suelta un elemento, la velocidad de lanzamiento debe sentirse natural — no entrecortada. El cálculo ingenuo de velocidad `(P_n - P_{n-1}) / dt` amplifica el ruido de alta frecuencia en los datos del puntero, causando que los elementos se sacudan al soltar.

Aetheris UI utiliza la fórmula de **Diferencia Regresiva de Segundo Orden** del análisis numérico:

```
v ≈ (3·P_n - 4·P_{n-1} + P_{n-2}) / (2·dt)
```

Esta fórmula tiene **error O(dt²)** comparado con el error O(dt) del método ingenuo. Cancela los términos de error de primer orden ajustando una parábola a través de las últimas tres posiciones del puntero, extrayendo la derivada verdadera. El resultado: lanzamientos suaves y naturales que se sienten como objetos físicos reales.

---

## 12. Aether-Guard: Limitación de Estabilidad Numérica

Aether-Guard es la capa de seguridad que previene explosiones de física. Cada fuerza, velocidad y aceleración pasa por múltiples limitadores:

| Protección | Umbral | Fórmula |
|---|---|---|
| **MAX_VELOCITY** | 5,000 px/s | `v_limitada = (v / \|\|v\|\|) × 5000` |
| **MAX_ACCELERATION** | 10,000 px/s² | `a_limitada = (a / \|\|a\|\|) × 10000` |
| **MAX_PHYSICS_K** | 10,000 | Constante de resorte limitada a [0, 10000] |
| **SAFE_DT** | [0.0001, 1.0] | Filtro paso-banda temporal |
| **EPSILON** | 1e-9 | Protección contra división por cero |
| **SNAP_DISTANCE** | 0.5 px | Umbral de Ajuste por Épsilon |
| **SNAP_VELOCITY** | 5.0 px/s | Velocidad mínima para ajuste |

El **Protocolo Supernova** (explosión radial de 100,000 px/s²) demuestra que incluso fuerzas 10× por encima del umbral de limitación se absorben de forma segura, con elementos retornando a órbita en 3 segundos.

---

## 13. Visión Estratégica

### Posicionamiento en el Mercado

Aetheris UI ocupa un nicho único: **visualización de datos impulsada por física para dashboards interactivos**. No es un reemplazo de React o Flutter — es una nueva categoría donde cada punto de datos es un objeto físico que puedes tocar, lanzar y explorar.

### Ventajas Injustas

1. **Un solo código Python → 3 plataformas nativas** (Web/WASM, Desktop/ModernGL, Mobile/Kivy)
2. **Física como layout** — sin CSS, sin media queries, sin posicionamiento manual
3. **Normalización algebraica de datos** — filas de BD → elementos físicos con escalado Min-Max
4. **Aether-Guard** — estabilidad numérica de grado industrial que ningún competidor ofrece

### Casos de Uso Objetivo

- Exploradores de catálogos estilo Netflix/Spotify
- Visualizaciones de mercados financieros (Bloomberg/TradingView)
- Visualización de embeddings de IA (pgvector → partículas físicas)
- Herramientas educativas interactivas (física, matemáticas, ciencia de datos)
