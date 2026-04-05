# Aetheris UI — API Reference

> Complete developer guide for all public classes, methods, and functions.

---

## Table of Contents

- [Core Modules](#core-modules)
- [Math Foundation (`aether_math.py`)](#math-foundation-aether_mathpy)
- [Elements (`elements.py`)](#elements-elementspy)
- [Engine (`engine.py`)](#engine-enginepy)
- [Solver (`solver.py` / `solver_wasm.py`)](#solver-solverpy--solver_wasmpy)
- [State Manager (`state_manager.py`)](#state-manager-state_managerpy)
- [Tensor Compiler (`tensor_compiler.py`)](#tensor-compiler-tensor_compilerpy)
- [UI Builder (`ui_builder.py`)](#ui-builder-ui_builderpy)
- [Renderers](#renderers)
- [Renderer Base (`renderer_base.py`)](#renderer-base-renderer_basepy)
- [GL Renderer (`gl_renderer.py`)](#gl-renderer-gl_rendererpy)
- [Kivy Renderer (`kivy_renderer.py`)](#kivy-renderer-kivy_rendererpy)
- [Tkinter Renderer (`tkinter_renderer.py`)](#tkinter-renderer-tkinter_rendererpy)
- [Solver Bridge (`solver_bridge.py`)](#solver-bridge-solver_bridgepy)
- [Audio Bridge (`audio_bridge.py`)](#audio-bridge-audio_bridgepy)

---

## Core Modules

All core modules live in `core/` and are imported as:

```python
from core.engine import AetherEngine
from core.elements import SmartPanel, StaticBox, CanvasTextNode, DOMTextNode
from core.tensor_compiler import TensorCompiler
from core.ui_builder import UIBuilder
```

---

## Math Foundation (`aether_math.py`)

### Module-Level Constants

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `EPSILON` | `np.float32` | `1e-9` | Minimum denominator for safe division |
| `MAX_VELOCITY` | `np.float32` | `5000.0` | Maximum velocity in pixels/second |
| `MAX_ACCELERATION` | `np.float32` | `10000.0` | Maximum acceleration in pixels/second² |
| `SNAP_DISTANCE` | `np.float32` | `0.5` | Distance threshold for Epsilon Snapping (pixels) |
| `SNAP_VELOCITY` | `np.float32` | `5.0` | Velocity threshold for Epsilon Snapping (px/s) |

### `safe_divide(numerator, denominator, epsilon=EPSILON)`

Safe division with epsilon protection to prevent division-by-zero.

**Args:**
- `numerator`: Dividend (scalar or NumPy array)
- `denominator`: Divisor (scalar or NumPy array)
- `epsilon`: Minimum absolute value for denominator (default: `1e-9`)

**Returns:**
- Safe division result, never `inf` or `NaN` from zero division.

**Raises:**
- None — always returns a finite value.

**Example:**
```python
from core.aether_math import safe_divide
result = safe_divide(10.0, 0.0)  # Returns ~1e10, not inf
```

### `clamp_magnitude(vector, max_val)`

Clamp the L2 norm (magnitude) of a vector while preserving its direction.

**Args:**
- `vector`: NumPy array representing a vector
- `max_val`: Maximum allowed magnitude

**Returns:**
- Clamped vector with `||v|| <= max_val`.

**Example:**
```python
from core.aether_math import clamp_magnitude
v = np.array([3000.0, 4000.0], dtype=np.float32)  # ||v|| = 5000
clamped = clamp_magnitude(v, 3000.0)  # ||clamped|| = 3000
```

### `check_and_fix_nan(array, name="tensor")`

Detect NaN/Inf values and return a zeroed array with a warning.

**Args:**
- `array`: NumPy array to check
- `name`: Identifier for the warning message

**Returns:**
- Original array if clean, zeroed array if NaN/Inf detected.

**Raises:**
- `RuntimeWarning`: If NaN or Inf is detected.

### `class StateTensor`

Represents a UI element as a physical particle with state, velocity, and acceleration vectors.

#### `__init__(x=0.0, y=0.0, w=100.0, h=100.0)`

Initialize a StateTensor with position and dimensions.

**Args:**
- `x`: X position in pixels
- `y`: Y position in pixels (top-left origin)
- `w`: Width in pixels
- `h`: Height in pixels

**Attributes:**
- `state`: `np.ndarray` of shape `(4,)`, dtype `float32` — `[x, y, w, h]`
- `velocity`: `np.ndarray` of shape `(4,)`, dtype `float32` — velocity vector
- `acceleration`: `np.ndarray` of shape `(4,)`, dtype `float32` — acceleration vector

#### `apply_force(force)`

Apply a force vector to the acceleration tensor.

Assumes mass `m=1`, so `F = ma` becomes `F = a`. Forces accumulate.

**Args:**
- `force`: `np.ndarray` of shape `(4,)`, dtype `float32` — force vector `[fx, fy, fw, fh]`

**Raises:**
- `RuntimeWarning`: If Aether-Guard detects NaN/Inf in the input force.

#### `euler_integrate(dt, viscosity=0.1, target_state=None)`

Update physics state using semi-implicit Euler integration.

**Steps:**
1. Validate `dt` with `safe_divide` (0 to 1 second range)
2. Update velocity: `v = (v + a·dt) · (1 - viscosity)`
3. Clamp velocity magnitude to `MAX_VELOCITY`
4. Update state: `s = s + v·dt`
5. Clamp width/height to >= 0
6. Reset acceleration to zero
7. Check for NaN/Inf in state and velocity
8. Apply Epsilon Snapping if near `target_state`

**Args:**
- `dt`: Delta time in seconds
- `viscosity`: Damping factor (0.0 = no damping, 1.0 = full stop)
- `target_state`: Optional target `[x, y, w, h]` for snapping check

---

## Elements (`elements.py`)

### `class DifferentialElement(ABC)`

Abstract base class for all UI elements. Each element owns a `StateTensor` and defines how to calculate its target state (asymptote).

#### `__init__(x=0, y=0, w=100, h=100, color=(1,1,1,1), z=0, sound_trigger=None)`

**Args:**
- `x, y`: Position coordinates
- `w, h`: Width and height
- `color`: RGBA tuple, float32 values 0-1
- `z`: Z-index for rendering depth
- `sound_trigger`: Optional dictionary for sound triggers (e.g., `{"impact": "撞击.ogg", "settle": "asentamiento.wav"}`)

#### `calculate_asymptotes(container_w, container_h) -> np.ndarray` *(abstract)*

Calculate the target `[x, y, w, h]` for the solver based on container size.

**Args:**
- `container_w`: Container/window width in pixels
- `container_h`: Container/window height in pixels

**Returns:**
- `np.ndarray` of shape `(4,)`, dtype `float32` — target state

#### `rendering_data` *(property)*

Returns a dict with `rect`, `color`, and `z` for the renderer.

### `class StaticBox(DifferentialElement)`

A static element with a fixed target position. Ignores container size.

#### `__init__(x, y, w, h, color=(1,1,1,1), z=0)`

**Args:**
- `x, y`: Fixed position
- `w, h`: Fixed dimensions
- `color`: RGBA tuple
- `z`: Z-index

### `class SmartPanel(DifferentialElement)`

A responsive panel that maintains percentage-based padding from container edges.

#### `__init__(x=0, y=0, w=100, h=100, color=(1,1,1,1), z=0, padding=0.05)`

**Args:**
- `x, y, w, h`: Initial values (overridden by asymptote)
- `color`: RGBA tuple
- `z`: Z-index
- `padding`: Fraction of container for padding (0.05 = 5%)

#### `calculate_asymptotes(container_w, container_h)`

Returns `[container_w·padding, container_h·padding, container_w·(1-2·padding), container_h·(1-2·padding)]`.

### `class FlexibleTextNode(DifferentialElement)`

A text element with static positioning. Currently behaves like `StaticBox` with text metadata.

#### `__init__(x=0, y=0, w=200, h=50, color=(1,1,1,1), z=0, text="Text")`

**Args:**
- `x, y, w, h`: Position and dimensions
- `color`: RGBA tuple
- `z`: Z-index
- `text`: Text content string

#### `text` *(property)*

Get/set the text content.

### `class SmartButton(DifferentialElement)`

A button anchored to a parent element with configurable offsets.

#### `__init__(parent, offset_x=0, offset_y=0, offset_w=100, offset_h=50, color=(0.8,0.8,0.2,1.0), z=0)`

**Args:**
- `parent`: Parent `DifferentialElement` to anchor to
- `offset_x`: X offset from parent's left edge
- `offset_y`: Y offset from parent's top edge
- `offset_w`: Button width
- `offset_h`: Button height
- `color`: RGBA tuple
- `z`: Z-index

#### `calculate_asymptotes(container_w, container_h)`

Returns `[parent.x + offset_x, parent.y + offset_y, offset_w, offset_h]`.

### `class CanvasTextNode(DifferentialElement)`

Text rendered directly on the Canvas via `ctx.fillText`. Participates fully in physics simulation.

#### `__init__(x=0, y=0, w=200, h=50, color=(1,1,1,1), z=0, text="Text", font_size=24, font_family="Arial")`

**Args:**
- `x, y, w, h`: Physics-driven position and dimensions
- `color`: RGBA tuple for text color (float32, 0-1)
- `z`: Z-index
- `text`: Text content
- `font_size`: Font size in pixels
- `font_family`: Font family name

#### `text_metadata` *(property)*

Returns `{"type": "canvas_text", "text": ..., "size": ..., "family": ..., "color": ...}`.

### `class DOMTextNode(DifferentialElement)`

Text rendered as an HTML `<div>` overlaid on the Canvas. Enables text selection, accessibility, and SEO.

#### `__init__(x=0, y=0, w=200, h=50, color=(0,0,0,0), z=0, text="Text", font_size=16, font_family="Arial", text_color=(1,1,1,1))`

**Args:**
- `x, y, w, h`: Physics-driven position and dimensions
- `color`: RGBA for rect background (typically transparent)
- `z`: Z-index
- `text`: Text content
- `font_size`: Font size in pixels
- `font_family`: Font family name
- `text_color`: RGBA tuple for text color (float32, 0-1)

#### `text_metadata` *(property)*

Returns `{"type": "dom_text", "text": ..., "size": ..., "family": ..., "color": ..., "bg_color": ...}`.

---

## Engine (`engine.py`)

### `class AetherEngine`

The central orchestrator. Manages element registry, physics simulation loop, and data extraction.

#### `__init__()`

Initialize the engine with empty registry, time tracking, StateManager, and TensorCompiler.

#### `register_element(element)`

Register a `DifferentialElement` for physics simulation.

**Args:**
- `element`: A `DifferentialElement` instance

#### `tick(win_w, win_h) -> np.ndarray`

Execute one frame of the physics simulation.

**Steps:**
1. Calculate delta time
2. Check for layout shock (hyper-damping)
3. For each element: calculate asymptote, compute forces, integrate
4. Extract structured NumPy array

**Args:**
- `win_w`: Window width in pixels
- `win_h`: Window height in pixels

**Returns:**
- Structured `np.ndarray` with dtype `[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')]`

#### `get_ui_metadata() -> str`

Return JSON string containing text metadata for `CanvasTextNode` and `DOMTextNode` elements, keyed by z-index.

**Returns:**
- JSON string, e.g.: `{"5": {"type": "canvas_text", "text": "Title", "size": 24, ...}}`

#### `dt` *(property)*

Delta time of the last frame in seconds.

#### `element_count` *(property)*

Number of registered elements.

---

## Solver (`solver.py` / `solver_wasm.py`)

### `calculate_restoring_force(current_state, target_state, spring_constant) -> np.ndarray`

Apply Hooke's Law: `F = (target - current) · k`.

**Args:**
- `current_state`: Current `[x, y, w, h]` as `float32`
- `target_state`: Target `[x, y, w, h]` as `float32`
- `spring_constant`: Stiffness `k`

**Returns:**
- Force vector as `float32`, magnitude-clamped to 10,000.

### `calculate_boundary_forces(state, container_w, container_h, boundary_stiffness) -> np.ndarray`

Calculate repulsion forces for boundary violations.

**Args:**
- `state`: Current `[x, y, w, h]` as `float32`
- `container_w`: Container width
- `container_h`: Container height
- `boundary_stiffness`: Spring constant for boundary repulsion

**Returns:**
- Boundary force vector as `float32`, magnitude-clamped to 5,000.

### `clamp_vector_magnitude(vector, max_val) -> np.ndarray`

Clamp vector L2 norm while preserving direction.

**Args:**
- `vector`: Input vector
- `max_val`: Maximum magnitude

**Returns:**
- Clamped vector.

---

## State Manager (`state_manager.py`)

### `class StateManager`

Manages layout shock detection and linear interpolation for state transitions.

#### `__init__()`

Initialize with zero dimensions and no active damping.

#### `check_teleportation_shock(current_w, current_h) -> float`

Detect drastic window size changes and return a viscosity multiplier.

**Args:**
- `current_w`: Current window width
- `current_h`: Current window height

**Returns:**
- `5.0` if shock detected (15 frames of 5x damping), `1.0` otherwise.

#### `lerp_arrays(state_a, state_b, t) -> np.ndarray`

Linear interpolation: `(1-t)·a + t·b`.

**Args:**
- `state_a`: Starting state array
- `state_b`: Target state array
- `t`: Interpolation factor [0, 1]

**Returns:**
- Interpolated array as `float32`.

---

## Tensor Compiler (`tensor_compiler.py`)

### `class TensorCompiler`

Compiles JSON design intents into physics coefficient arrays.

#### `STIFFNESS_MAP` *(class attribute)*

Preset stiffness values: `{"snappy": 0.8, "organic": 0.1, "fluid": 0.05, "rigid": 2.0, "gentle": 0.02}`

#### `VISCOSITY_MAP` *(class attribute)*

Preset viscosity values: `{"snappy": 0.3, "organic": 0.5, "fluid": 0.7, "rigid": 0.1, "gentle": 0.85}`

#### `compile_intent(intent_json) -> np.ndarray`

Compile a design intent JSON into a physics coefficient array.

**Args:**
- `intent_json`: Dict with `layout`, `spacing`, `animation`, `padding`, `elements`, etc.

**Returns:**
- Structured array with dtype `[('element_id', 'U64'), ('stiffness', 'f4'), ('viscosity', 'f4'), ('boundary_padding', 'f4', 4), ('spacing', 'f4')]`

#### `apply_coefficients(engine, coefficients)`

Apply compiled coefficients to an `AetherEngine` instance.

**Args:**
- `engine`: Target `AetherEngine`
- `coefficients`: Structured array from `compile_intent()`

#### `get_default_coefficients(animation="organic", spacing=0.0, padding=0.0) -> np.ndarray`

Get default coefficients for a given animation preset.

### `speed_to_stiffness(transition_time_ms) -> float`

Derive spring constant from transition duration: `k = 16 / T²`.

**Args:**
- `transition_time_ms`: Desired transition time in milliseconds

**Returns:**
- Spring constant `k` as `float32`, capped at 10,000.

### `speed_to_viscosity(transition_time_ms) -> float`

Derive viscosity from transition speed.

**Args:**
- `transition_time_ms`: Desired transition time in milliseconds

**Returns:**
- Viscosity value (0.05–0.95) as `float32`.

---

## UI Builder (`ui_builder.py`)

### `class UIBuilder`

Translates JSON Intent into registered `AetherEngine` elements.

#### `ELEMENT_TYPES` *(class attribute)*

Mapping: `{"static_box": StaticBox, "smart_panel": SmartPanel, "smart_button": SmartButton, "flexible_text": FlexibleTextNode, "canvas_text": CanvasTextNode, "dom_text": DOMTextNode}`

#### `build_from_intent(engine, intent)`

Parse JSON intent and register all elements with the engine.

**Args:**
- `engine`: Target `AetherEngine`
- `intent`: JSON intent dictionary

#### `element_count` *(property)*

Number of built elements.

---

## Renderers

### `renderer_base.py`

#### `class BaseRenderer(ABC)`

Abstract interface for all renderers.

**Abstract methods:**
- `init_window(width, height, title)` — Initialize the rendering surface
- `clear_screen(color)` — Clear with background color
- `render_frame(data_buffer)` — Render the structured array
- `swap_buffers()` — Present the frame

### `gl_renderer.py`

#### `class GLRenderer(BaseRenderer)`

ModernGL renderer with SDF shaders and Pillow text textures.

**Key methods:**
- `init_window(width, height, title)` — Create standalone OpenGL context
- `render_frame(data_buffer, engine_metadata=None)` — Render with optional text metadata
- `_get_or_create_text_texture(text, font_size, color_rgba, font_family)` — Cache text textures

### `kivy_renderer.py`

#### `class KivyRenderer(BaseRenderer)`

Kivy renderer with Y-axis inversion and hybrid text support.

**Key methods:**
- `init_window(width, height, title)` — Initialize renderer
- `set_canvas(canvas)` — Set the Kivy canvas widget
- `set_dom_container(container)` — Set container for DOM-like labels
- `render_frame(data_buffer, engine_metadata=None)` — Render with Y-axis inversion
- `cleanup_dom_labels()` — Remove all DOM text labels

### `tkinter_renderer.py`

#### `class TkinterRenderer(BaseRenderer)`

Tkinter debug renderer for rapid prototyping.

**Key methods:**
- `init_window(width, height, title)` — Create Tk window and Canvas
- `start(engine_instance)` — Start the Tkinter main loop with physics updates
- `stop()` — Stop the renderer and cleanup

### `solver_bridge.py`

Auto-detects Numba availability and imports the appropriate solver implementation.

**Exports:**
- `calculate_restoring_force` — From `solver.py` (Numba) or `solver_wasm.py` (NumPy)
- `calculate_boundary_forces` — Same dual-path logic
- `HAS_NUMBA` — Boolean indicating which path is active

---

*For architectural context, see [ARCHITECTURE.md](ARCHITECTURE.md). For the main README, see [../README.md](../README.md).*

---

## Data Bridge (`data_bridge.py`)

### Module Constants

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `DATA_NORMALIZE_MIN` | `float` | `10.0` | Default minimum for Min-Max scaling (pixels) |
| `DATA_NORMALIZE_MAX` | `float` | `500.0` | Default maximum for Min-Max scaling (pixels) |
| `VECTOR_TENSOR_SCALE` | `float` | `100.0` | Default scale factor for vector-to-tensor conversion |
| `REMOTE_CONNECT_TIMEOUT` | `int` | `5` | Timeout for remote provider connectivity check (seconds) |
| `REMOTE_REQUEST_TIMEOUT` | `int` | `10` | Timeout for remote provider requests (seconds) |
| `NORMALIZATION_EPSILON` | `float` | `1e-9` | Epsilon for safe division in normalization |

### `min_max_scale(value, data_min, data_max, target_min=DATA_NORMALIZE_MIN, target_max=DATA_NORMALIZE_MAX)`

Min-Max Scaling with Aether-Guard protection.

**Parameters:**
- `value`: The value to scale
- `data_min`: Minimum value in the source data
- `data_max`: Maximum value in the source data
- `target_min`: Minimum of target range (default: 10.0)
- `target_max`: Maximum of target range (default: 500.0)

**Returns:**
- Scaled value clamped to `[target_min, target_max]`.

### `normalize_column(values, target_min=DATA_NORMALIZE_MIN, target_max=DATA_NORMALIZE_MAX)`

Normalize an entire column of values using Min-Max scaling.

**Parameters:**
- `values`: List of source values
- `target_min`: Minimum of target range
- `target_max`: Maximum of target range

**Returns:**
- List of normalized values.

### `vector_to_tensor(vector, scale=VECTOR_TENSOR_SCALE)`

Convert a PostgreSQL vector embedding into a StateTensor force.

**Parameters:**
- `vector`: List of floats (AI embedding)
- `scale`: Scaling factor (default: 100.0)

**Returns:**
- `np.ndarray` of shape `(4,)`, dtype `float32` — force vector `[fx, fy, fw, fh]`.

### `class BaseAetherProvider(ABC)`

Abstract base class for data providers.

**Abstract methods:**
- `connect()` — Establish connection
- `disconnect()` — Close connection
- `execute_query(query, params)` — Execute query, return list of dicts
- `insert_element_state(element_id, state)` — Save element state
- `get_element_state(element_id)` — Retrieve element state
- `delete_element_state(element_id)` — Delete element state

### `class SQLiteProvider(BaseAetherProvider)`

SQLite-based provider for local persistence.

#### `__init__(db_path=None)`

**Parameters:**
- `db_path`: Path to SQLite database. Auto-detects WASM vs Desktop.

#### `connect()`

Establishes connection and creates `element_states` table if needed.

#### `disconnect()`

Closes connection. Safe to call multiple times.

#### `execute_query(query, params=())`

Executes SQL query and returns list of dictionaries.

#### `insert_element_state(element_id, state)`

Saves element state using INSERT OR REPLACE.

**Parameters:**
- `element_id`: Unique identifier
- `state`: Dict with x, y, w, h, r, g, b, a, z, metadata

**Returns:**
- `True` on success, `False` on failure.

#### `get_element_state(element_id)`

Retrieves element state by ID.

**Returns:**
- Dict with element state, or `None` if not found.

#### `delete_element_state(element_id)`

Deletes element state by ID.

**Returns:**
- `True` if row was deleted, `False` otherwise.

#### `get_all_states()`

Retrieves all element states ordered by z-index.

### `class RemoteAetherProvider(BaseAetherProvider)`

REST proxy provider for PostgreSQL via server endpoint.

#### `__init__(base_url="http://localhost:5000")`

**Parameters:**
- `base_url`: Base URL of the Aetheris server.

#### `connect()`

Verifies connectivity to `/api/v1/db-bridge`.

#### `disconnect()`

Marks connection as closed.

#### `execute_query(query, params=())`

Sends query to server proxy endpoint.

#### `insert_element_state(element_id, state)`

Saves element state via server proxy.

#### `get_element_state(element_id)`

Retrieves element state via server proxy.

#### `delete_element_state(element_id)`

Deletes element state via server proxy.

---

## Audio Bridge (`audio_bridge.py`)

### `class AetherAudioBridge(ABC)`

Abstract base class for platform-agnostic audio playback.

#### `play(sound_path, volume=1.0)` *(abstract)*

Play a sound file.

#### `stop_all()` *(abstract)*

Stop all currently playing sounds.

### `class DesktopAudioProvider(AetherAudioBridge)`

High-fidelity audio provider for Linux/Windows/macOS using `PyOgg` and `PyAudio`. Uses a dedicated thread pool to avoid blocking the physics engine.

### `class MobileAudioProvider(AetherAudioBridge)`

Low-latency audio provider for Android/iOS using `pygame.mixer`.

### `class WebAudioProvider(AetherAudioBridge)`

WebAssembly audio provider. Emits JSON messages via the PWA bridge to the browser's Web Audio API.

### `class MockAudioProvider(AetherAudioBridge)`

Headless audio provider for CI/CD. Logs sound events to a buffer without emitting audio.

### `create_audio_bridge(platform='desktop') -> AetherAudioBridge`

Factory function to create the appropriate audio bridge for the current runtime.
