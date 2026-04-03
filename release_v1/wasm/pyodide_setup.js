// wasm/pyodide_setup.js
// Bootstrap script for loading Aetheris UI in a browser using Pyodide/WASM

async function loadAetheris() {
  // Load Pyodide
  let pyodide = await loadPyodide({
    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/"
  });

  // Load numpy package (required for physics calculations)
  await pyodide.loadPackage("numpy");

  // Mount the core/ files into the virtual filesystem
  // In production, these would be fetched from your server
  const coreFiles = [
    'core/__init__.py',
    'core/aether_math.py',
    'core/solver_wasm.py',
    'core/solver_bridge.py',
    'core/state_manager.py',
    'core/tensor_compiler.py',
    'core/elements.py',
    'core/engine.py',
    'core/renderer_base.py',
  ];

  // Create core directory in Pyodide's virtual filesystem
  pyodide.FS.mkdir('/core');

  // Load each Python file into the virtual filesystem
  for (const file of coreFiles) {
    const response = await fetch(file);
    const content = await response.text();
    pyodide.FS.writeFile(`/${file}`, content);
  }

  // Initialize AetherEngine
  await pyodide.runPythonAsync(`
    import sys
    sys.path.insert(0, '/')
    
    import numpy as np
    from core.engine import AetherEngine
    from core.elements import StaticBox, SmartPanel, SmartButton
    from core.tensor_compiler import TensorCompiler
    
    # Create engine instance
    engine = AetherEngine()
    
    # Register a test element
    panel = SmartPanel(color=(0.9, 0.2, 0.6, 0.8), z=1)
    engine.register_element(panel)
    
    # Run a single tick to verify physics
    data = engine.tick(800, 600)
    print(f"Aetheris Engine Physics loaded in WASM")
    print(f"Elements: {engine.element_count}")
    print(f"Data shape: {data.shape}")
    print(f"Data dtype: {data.dtype}")
  `);

  return pyodide;
}

// Export for use in Web Workers or main thread
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { loadAetheris };
}
