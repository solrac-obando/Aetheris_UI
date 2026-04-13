# Installation Guide
# =================

## Requirements

- Python 3.12 or higher
- NumPy 1.26.4 or higher

## Platform-Specific Requirements

### Linux (Desktop)

.. code-block:: bash

   sudo apt-get install python3-dev libgl1-mesa-glx

### macOS

.. code-block:: bash

   brew install glfw

### Windows

No additional requirements.

## Installation Methods

### Method 1: From PyPI (Recommended)

.. code-block:: bash

   pip install aetheris

### Method 2: From Source

.. code-block:: bash

   git clone https://github.com/carlosobando/aetheris-ui.git
   cd aetheris-ui
   pip install -e .

### Method 3: With Rust Engine (17x Faster)

.. code-block:: bash

   # Install Rust first
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

   # Build Rust extension
   cd aetheris-rust
   pip install maturin
   maturin develop -m crates/aether-pyo3/Cargo.toml
   cd ..

## Verification

Verify your installation:

.. code-block:: bash

   python -c "
   from core.engine import AetherEngine
   from core.elements import SmartPanel
   
   engine = AetherEngine()
   panel = SmartPanel()
   engine.register_element(panel)
   data = engine.tick(800, 600)
   print(f'✓ Aetheris installed: {len(data)} elements')
   "

Expected output:

.. code-block:: text

   ✓ Aetheris installed: 1 elements

## Optional Dependencies

For web deployment:

.. code-block:: bash

   pip install aetheris[web]

For development:

.. code-block:: bash

   pip install aetheris[dev]

## Troubleshooting

### Issue: Missing OpenGL

**Error**: ``ImportError: libGL.so not found``

**Solution**:

.. code-block:: bash

   # Linux
   sudo apt-get install libgl1-mesa-glx

### Issue: NumPy not found

**Solution**:

.. code-block:: bash

   pip install numpy>=1.26.4