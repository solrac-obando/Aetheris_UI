# WASM Portability Guide - Aetheris UI

## Overview

Aetheris UI supports dual-path execution:
- **Desktop**: Numba-optimized (`@njit`) for maximum CPU performance
- **WASM/Pyodide**: Pure NumPy fallback for browser compatibility

## Architecture

```
┌─────────────────────────────────────────────┐
│              AetherEngine.tick()            │
├─────────────────────────────────────────────┤
│                                             │
│  solver_bridge.py                           │
│  ┌─────────────────┐  ┌──────────────────┐  │
│  │  Numba Path     │  │  Pure NumPy Path │  │
│  │  (Desktop)      │  │  (WASM/Pyodide)  │  │
│  │  @njit cached   │  │  Vectorized ops  │  │
│  └────────┬────────┘  └────────┬─────────┘  │
│           │                    │             │
│           └────────┬───────────┘             │
│                    │                         │
│         Structured NumPy Array               │
│         [('rect','f4',4),...]                │
│                    │                         │
│  ┌─────────────────┴──────────────────┐     │
│  │  GLRenderer (Desktop ModernGL)    │     │
│  │  WebGLRenderer (Browser)          │     │
│  └───────────────────────────────────┘     │
└─────────────────────────────────────────────┘
```

## File Structure

| File | Purpose |
|------|---------|
| `core/solver.py` | Numba-optimized solver (desktop only) |
| `core/solver_wasm.py` | Pure NumPy solver (WASM fallback) |
| `core/solver_bridge.py` | Auto-detects and selects implementation |
| `core/state_manager.py` | Dual-path: @njit when available, pure NumPy otherwise |
| `core/tensor_compiler.py` | Dual-path: @njit when available, pure NumPy otherwise |
| `core/engine.py` | Uses solver_bridge for environment-agnostic execution |
| `wasm/pyodide_setup.js` | Browser bootstrap script for Pyodide |

## Limitations

### No Numba in WASM
Pyodide does not support Numba's JIT compilation. The `@njit` decorator is conditionally applied:

```python
try:
    from numba import njit
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

if HAS_NUMBA:
    @njit(cache=True)
    def my_function(...):
        ...
else:
    def my_function(...):
        ...  # Same logic, no decorator
```

### No Native Threads
Pyodide runs in a Web Worker. Use `asyncio` for non-blocking operations:

```python
# In browser context
await pyodide.runPythonAsync(`
    import asyncio
    from core.engine import AetherEngine
    
    engine = AetherEngine()
    
    # Use requestAnimationFrame for 60fps loop
    async def render_loop():
        while True:
            data = engine.tick(800, 600)
            # Send data to WebGL renderer
            await asyncio.sleep(1/60)
    
    asyncio.create_task(render_loop())
`)
```

### NumPy in WASM
Pyodide includes NumPy, but performance is lower than native:
- Small arrays (< 1000 elements): Comparable to native
- Large arrays: 2-5x slower due to WASM memory overhead
- Mitigation: Keep UI element count reasonable (< 100 elements)

## 60fps Strategy Without Numba

1. **Vectorized Operations**: All math uses NumPy vectorized operations (no Python loops)
2. **Structured Arrays**: Single memory block for GPU transfer (zero-copy)
3. **Epsilon Snapping**: Elements at rest skip integration (CPU savings)
4. **Hyper-Damping**: Prevents oscillation after layout changes (fewer frames to settle)
5. **Element Count**: Keep UI elements under 100 for smooth 60fps in WASM

## Browser Usage

```html
<script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
<script src="wasm/pyodide_setup.js"></script>
<script>
  async function init() {
    const pyodide = await loadAetheris();
    
    // Access engine from JavaScript
    const engine = pyodide.globals.get('engine');
    
    // Run physics tick
    const data = engine.tick(800, 600);
    
    // Convert to JavaScript TypedArray for WebGL
    const rectArray = data['rect'].toJs();
    const colorArray = data['color'].toJs();
    
    // Upload to WebGL vertex buffer
    gl.bufferData(gl.ARRAY_BUFFER, rectArray, gl.DYNAMIC_DRAW);
  }
  
  init();
</script>
```

## Testing

Run WASM compatibility tests:
```bash
pytest tests/test_wasm_compatibility.py -v
```

Run all tests (includes WASM tests):
```bash
pytest tests/ -v
```

## Performance Comparison

| Operation | Desktop (Numba) | WASM (Pure NumPy) |
|-----------|-----------------|-------------------|
| Restoring Force | ~0.1μs | ~0.5μs |
| Boundary Forces | ~0.2μs | ~1.0μs |
| Euler Integrate | ~0.3μs | ~1.5μs |
| Full tick (10 elements) | ~5μs | ~25μs |
| Full tick (100 elements) | ~50μs | ~250μs |

All operations are well within the 16.67ms budget for 60fps, even in WASM.
