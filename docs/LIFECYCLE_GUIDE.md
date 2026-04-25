# Aetheris Lifecycle Management Guide

Aetheris uses a robust lifecycle management system to prevent memory leaks in long-running applications (especially in WASM/Web environments) and to provide hooks for global events like theme changes.

## Core Components

### 1. `Disposable` (`core/lifecycle/base.py`)
The base class for any object that manages resources (NumPy arrays, file handles, event listeners).
- **`dispose()`**: Explicitly cleans up resources.
- **`_register_cleanup(callback)`**: Internal method to add cleanup tasks.
- **Context Manager**: Supports `with` blocks for automatic cleanup.

### 2. `LifecycleManager` (`core/lifecycle/manager.py`)
A singleton that tracks all active UI elements using `weakref.WeakSet`.
- **Automatic Tracking**: Elements are added to the manager upon initialization.
- **`dispose_all()`**: Utility to clean up the entire engine state.
- **`on_theme_change()`**: Broadcasts theme updates to all tracked elements.

### 3. `MemoryProfiler` (`core/lifecycle/profiler.py`)
Tools for monitoring memory usage and detecting leaks.
- **`take_snapshot()`**: Records memory state for comparison.
- **`@profile_memory`**: Decorator for measuring function-level memory impact.

## Best Practices

### Registering Cleanup
Always register cleanup for any internal resources in your custom elements:

```python
class CustomElement(DifferentialElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._buffer = np.zeros(1000)
        self._register_cleanup(lambda: print("Cleaning up buffer"))
```

### Handling Theme Changes
If your element depends on global theme colors, implement `update_theme()`:

```python
class ThemedElement(DifferentialElement):
    def update_theme(self):
        self._color = ThemeManager.get_color("primary")
```

### Context Managers
Use the RAII pattern for temporary elements:

```python
with StaticBox(0, 0, 100, 100) as box:
    engine.register(box)
    engine.tick(800, 600)
# box.dispose() is called automatically here
```

## Troubleshooting Leaks
Use the `LifecycleManager` to find objects that were never disposed:

```python
manager = get_lifecycle_manager()
leaks = manager.get_leaked_references()
print(f"Leaked elements: {leaks}")
```
