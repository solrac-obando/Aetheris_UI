# Quick Start Guide
# =================
#
# This guide will get you running Aetheris in under 5 minutes.

## Installation

Install from PyPI:

.. code-block:: bash

   pip install aetheris

Or install from source:

.. code-block:: bash

   git clone https://github.com/carlosobando/aetheris-ui.git
   cd aetheris-ui
   pip install -e .

## Your First Aetheris Application

Create a file called ``hello_physics.py``:

.. code-block:: python

   from core.engine import AetherEngine
   from core.elements import SmartPanel

   # 1. Create the physics engine
   engine = AetherEngine()

   # 2. Register a responsive panel
   panel = SmartPanel(
       color=(0.9, 0.2, 0.6, 0.8),
       padding=0.05,
       z_index=0
   )
   engine.register_element(panel)

   # 3. Run the physics loop
   for frame in range(60):
       data = engine.tick(800, 600)
       
       if frame % 10 == 0:
           print(f"Frame {frame}: {len(data)} elements rendered")

What's happening?

1. ``AetherEngine`` - The physics simulation engine
2. ``SmartPanel`` - A responsive component that follows physics
3. ``tick(width, height)`` - Advance physics by one frame

## Understanding the Physics

Each element simulates a physical object:

.. math::

   v(t+dt) = v(t) + acceleration * dt
   position(t+dt) = position(t) + velocity

The engine automatically applies:

- **Hooke's Law**: Force pulling toward target position
- **Critical Damping**: Prevents infinite oscillation
- **Aether-Guard**: Safety bounds checking

## Next Steps

- Read :doc:`tutorials/installation` for detailed setup
- Explore :doc:`tutorials/first-app` for more examples
- Check :doc:`api/core.engine` for API reference