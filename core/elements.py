from abc import ABC, abstractmethod
import numpy as np
from core.aether_math import StateTensor


class DifferentialElement(ABC):
    """Abstract base class for all UI elements in Aetheris.
    
    Each element owns a StateTensor that represents its current physical state
    [x, y, width, height] and evolves through forces and integration.
    """
    
    def __init__(self, x=0, y=0, w=100, h=100, color=(1, 1, 1, 1), z=0):
        """Initialize a differential element.
        
        Args:
            x, y: Position coordinates
            w, h: Width and height dimensions
            color: RGBA tuple (float32, values 0-1)
            z: Z-index for rendering depth
        """
        self.tensor = StateTensor(x, y, w, h)
        self._color = np.array(color, dtype=np.float32)
        self._z_index = z

    @abstractmethod
    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Calculates the target [x, y, w, h] for the solver.
        
        This is the core logic where each element type defines its desired
        target state based on environmental constraints.
        
        Args:
            container_w: Width of the container/window
            container_h: Height of the container/window
            
        Returns:
            numpy.array: Target state [x, y, w, h] as float32
        """
        pass

    @property
    def rendering_data(self):
        """Returns data needed for rendering the element.
        
        Returns:
            dict: Contains rect (StateTensor.state), color, and z_index
        """
        return {
            "rect": self.tensor.state,
            "color": self._color,
            "z": self._z_index
        }


class StaticBox(DifferentialElement):
    """A simple static box element that maintains a fixed target position.
    
    Unlike responsive elements, StaticBox always returns the same target
    regardless of container size.
    """
    
    def __init__(self, x, y, w, h, color=(1, 1, 1, 1), z=0):
        """Initialize a static box with fixed target rectangle.
        
        Args:
            x, y: Position of the target rectangle
            w, h: Width and height of the target rectangle
            color: RGBA tuple (float32, values 0-1)
            z: Z-index for rendering depth
        """
        super().__init__(x, y, w, h, color, z)
        self._target_rect = np.array([x, y, w, h], dtype=np.float32)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Return the fixed target rectangle as the asymptote.
        
        Ignores container size since this is a static element.
        """
        return self._target_rect.copy()