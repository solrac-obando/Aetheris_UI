Core Elements Module
==================

This module provides the 32-component UI suite for Aetheris.

SmartPanel
---------

.. autoclass:: core.elements.SmartPanel
   :members:

StaticBox
--------

.. autoclass:: core.elements.StaticBox
   :members:

CanvasTextNode
-----------

.. autoclass:: core.elements.CanvasTextNode
   :members:

Component Gallery
--------------

Aetheris includes 32 pre-built components:

Dashboard Components
~~~~~~~~~~~~~~~~~~~~

- ``AetherGauge`` - Rotational spring needle with damping
- ``AetherSparkline`` - Real-time minimal k-vector plot
- ``AetherStatusOrb`` - Pulsing frequency-based light
- ``AetherValueMetric`` - Unit-aware numeric node
- ``AetherRadialProgress`` - Circular fill with elastic snap

Interactive Controls
~~~~~~~~~~~~~~~~~~

- ``AetherKineticToggle`` - Binary switch with inertia
- ``AetherPhysicsSlider`` - Spring-loaded range control
- ``AetherMagnetButton`` - Button with cursor-attraction
- ``AetherElasticInput`` - Text input with vibration feedback

Containers
~~~~~~~~~~~

- ``AetherWindow`` - Gravity-anchored title bar
- ``AetherModal`` - Scaled overlay with spring entry
- ``AetherSideNav`` - Sliding panel with elastic friction
- ``AetherToolbar`` - Staggered entry button array

Usage Example
----------

.. code-block:: python

   from core.elements import SmartPanel, StaticBox
   
   # Responsive panel
   panel = SmartPanel(
       color=(0.9, 0.2, 0.6, 0.8),
       padding=0.05,
       z_index=0
   )
   
   # Static container
   box = StaticBox(
       position=(100, 100),
       size=(200, 200),
       z_index=1
   )