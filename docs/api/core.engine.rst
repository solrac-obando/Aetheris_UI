Core Engine Module
=================

.. automodule:: core.engine
   :members:
   :undoc-members:
   :show-inheritance:

Examples
---------

Basic engine usage:

.. code-block:: python

   from core.engine import AetherEngine
   
   engine = AetherEngine()
   
   # Register elements
   for i in range(10):
       engine.register_element(SmartPanel())
   
   # Run physics
   data = engine.tick(800, 600)

Tick Method
---------

.. method:: AetherEngine.tick(width, height)

   Advance the physics simulation by one frame.

   :param width: Viewport width in pixels
   :param height: Viewport height in pixels
   :return: NumPy array with element data

Return Format
----------

The tick method returns a NumPy array with this structure:

.. code-block:: python

   dtype = [
       ('x', 'f4'),      # X position
       ('y', 'f4'),      # Y position  
       ('w', 'f4'),      # Width
       ('h', 'f4'),      # Height
       ('r', 'f4'),      # Red (0-1)
       ('g', 'f4'),      # Green (0-1)
       ('b', 'f4'),      # Blue (0-1)
       ('a', 'f4'),      # Alpha (0-1)
       ('z', 'i4'),      # Z-index
   ]

Example data access:

.. code-block:: python

   data = engine.tick(800, 600)
   
   # All positions
   positions = data[['x', 'y']]
   
   # All colors
   colors = data[['r', 'g', 'b', 'a']]