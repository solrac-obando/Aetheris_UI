Aether Math Module
==================

This module provides the mathematical foundation for Aetheris physics.

StateTensor
-----------

.. autoclass:: core.aether_math.StateTensor
   :members:

Functions
---------

.. autofunction:: core.aether_math.check_and_fix_nan

.. autofunction:: core.aether_math.safe_divide

.. autofunction:: core.aether_math.clamp_magnitude

Mathematical Foundation
--------------------

The physics engine uses these core concepts:

Symplectic Euler Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. math::

   v(t+dt) = v(t) + a(t) \cdot dt
   s(t+dt) = s(t) + v(t+dt) \cdot dt

Hooke's Law
~~~~~~~~~

.. math::

   F = k \cdot (target - current)

Critical Damping
~~~~~~~~~~~~~~

.. math::

   c_{critical} = 2 \cdot \sqrt(k)

Aether-Guard Safety
~~~~~~~~~~~~~~~~~~

The Aether-Guard system prevents numerical instability:

.. code-block:: python

   if ||velocity|| > V_{max}:
       velocity = velocity / ||velocity|| * V_{max}

   if isnan(velocity) or isinf(velocity):
       velocity = 0

Usage
----

.. code-block:: python

   import numpy as np
   from core.aether_math import check_and_fix_nan, StateTensor
   
   # Create tensor
   tensor = StateTensor(shape=(100, 4))
   
   # Apply physics
   tensor.apply_force(force_vector)
   
   # Check for NaN/Inf
   tensor.state = check_and_fix_nan(tensor.state, "state")