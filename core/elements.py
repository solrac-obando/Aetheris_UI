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


class SmartPanel(DifferentialElement):
    """A responsive panel that maintains percentage-based padding from container edges.
    
    By default, maintains 5% padding on all sides, adapting to container size changes.
    """
    
    def __init__(self, x=0, y=0, w=100, h=100, color=(1, 1, 1, 1), z=0, padding=0.05):
        """Initialize a smart panel.
        
        Args:
            x, y: Initial position (will be overridden by asymptote calculation)
            w, h: Initial dimensions (will be overridden by asymptote calculation)
            color: RGBA tuple (float32, values 0-1)
            z: Z-index for rendering depth
            padding: Fraction of container to maintain as padding (0.05 = 5%)
        """
        super().__init__(x, y, w, h, color, z)
        self._padding = padding

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Calculate target rectangle with percentage-based padding.
        
        Applies linear scaling (Escalamiento Lineal) from Álgebra de Baldor:
        - Position: container * padding
        - Dimensions: container * (1 - 2*padding)
        
        Args:
            container_w: Width of the container/window
            container_h: Height of the container/window
            
        Returns:
            numpy.array: Target state [x, y, w, h] as float32
        """
        # Linear scaling transformation: map [0, container] to [padding*container, (1-padding)*container]
        x = container_w * self._padding
        y = container_h * self._padding
        w = container_w * (1.0 - 2.0 * self._padding)
        h = container_h * (1.0 - 2.0 * self._padding)
        
        return np.array([x, y, w, h], dtype=np.float32)


class FlexibleTextNode(DifferentialElement):
    """A text element that can be positioned and sized relative to container.
    
    For simplicity in Phase 8, this behaves like a StaticBox but with text-specific defaults.
    In future phases, it would integrate with text rendering systems.
    """
    
    def __init__(self, x=0, y=0, w=200, h=50, color=(1, 1, 1, 1), z=0, text="Text"):
        """Initialize a flexible text node.
        
        Args:
            x, y: Position coordinates
            w, h: Width and height dimensions
            color: RGBA tuple (float32, values 0-1)
            z: Z-index for rendering depth
            text: The text content to display
        """
        super().__init__(x, y, w, h, color, z)
        self._text = text
        # For now, treat as static element - future versions will have text-specific layout logic

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Return fixed target rectangle (static behavior for now).
        
        In Phase 8, we use static positioning. Future phases will implement
        text wrapping, alignment, and responsive text sizing.
        """
        # Return current state as target (static behavior)
        return self.tensor.state.copy()
        
    @property
    def text(self):
        """Get the text content."""
        return self._text
        
    @text.setter
    def text(self, value):
        """Set the text content."""
        self._text = value


class SmartButton(DifferentialElement):
    """A button element that anchors to a parent element with offsets.
    
    The button maintains a fixed offset from its parent's position,
    allowing for relative positioning that stays consistent when the parent moves.
    """
    
    def __init__(self, parent, offset_x=0, offset_y=0, offset_w=100, offset_h=50, 
                 color=(0.8, 0.8, 0.2, 1.0), z=0):
        """Initialize a smart button anchored to a parent.
        
        Args:
            parent: The parent DifferentialElement to anchor to
            offset_x: X offset from parent's left edge
            offset_y: Y offset from parent's top edge
            offset_w: Width of the button
            offset_h: Height of the button
            color: RGBA tuple (float32, values 0-1)
            z: Z-index for rendering depth
        """
        # Initialize at parent's position + offset
        super().__init__(
            parent.tensor.state[0] + offset_x,
            parent.tensor.state[1] + offset_y,
            offset_w,
            offset_h,
            color,
            z
        )
        self._parent = parent
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._offset_w = offset_w
        self._offset_h = offset_h

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        """Calculate target position based on parent's current position plus offset.
        
        The button dynamically follows its parent by calculating asymptotes
        based on the parent's current state (which includes physics simulation).
        
        Args:
            container_w: Width of the container/window (unused, kept for interface consistency)
            container_h: Height of the container/window (unused, kept for interface consistency)
            
        Returns:
            numpy.array: Target state [x, y, w, h] as float32
        """
        # Get parent's current position
        parent_state = self._parent.tensor.state
        
        # Calculate target: parent position + offset
        target_x = parent_state[0] + self._offset_x
        target_y = parent_state[1] + self._offset_y
        target_w = self._offset_w
        target_h = self._offset_h
        
        return np.array([target_x, target_y, target_w, target_h], dtype=np.float32)