from abc import ABC, abstractmethod
import numpy as np
from typing import Union


class BaseRenderer(ABC):
    """Abstract base class for all renderers in Aetheris UI.
    
    This class defines the visual contract - renderers must never access
    DifferentialElement objects directly. They only receive the structured
    NumPy array from AetherEngine.tick(), ensuring complete decoupling
    between the mathematical engine and the visual representation.
    """
    
    def __init__(self):
        """Initialize the renderer."""
        self._width = 0
        self._height = 0
        self._title = ""
    
    @abstractmethod
    def init_window(self, width: int, height: int, title: str = "Aetheris UI") -> None:
        """Initialize the rendering window.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
        """
        pass
    
    @abstractmethod
    def clear_screen(self, color: Union[tuple, list, np.ndarray]) -> None:
        """Clear the screen with a background color.
        
        Args:
            color: RGBA color values (float32, 0-1 range)
        """
        pass
    
    @abstractmethod
    def render_frame(self, data_buffer: np.ndarray) -> None:
        """Render a frame from the structured data buffer.
        
        This is the primary entry point. The renderer receives a flat
        structured NumPy array with dtype [('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')]
        and must iterate through it to draw each element.
        
        Args:
            data_buffer: Structured array from AetherEngine.tick()
        """
        pass
    
    @abstractmethod
    def draw_rect(self, rect: np.ndarray, color: np.ndarray, z: int) -> None:
        """Draw a rectangle.
        
        Args:
            rect: [x, y, width, height] in pixel coordinates
            color: RGBA color values (float32, 0-1 range)
            z: Z-index for rendering depth
        """
        pass
    
    @abstractmethod
    def draw_rounded_rect(self, rect: np.ndarray, color: np.ndarray, z: int, radius: float) -> None:
        """Draw a rectangle with rounded corners.
        
        Args:
            rect: [x, y, width, height] in pixel coordinates
            color: RGBA color values (float32, 0-1 range)
            z: Z-index for rendering depth
            radius: Corner radius in pixels
        """
        pass
    
    @abstractmethod
    def draw_text(self, text: str, pos: np.ndarray, size: int, color: np.ndarray) -> None:
        """Draw text.
        
        Args:
            text: String to render
            pos: [x, y] position in pixel coordinates (baseline)
            size: Font size in pixels
            color: RGBA color values (float32, 0-1 range)
        """
        pass
    
    @abstractmethod
    def swap_buffers(self) -> None:
        """Finalize the frame and present it to the screen."""
        pass
    
    @property
    def width(self) -> int:
        """Get the current window width."""
        return self._width
    
    @property
    def height(self) -> int:
        """Get the current window height."""
        return self._height
    
    @property
    def title(self) -> str:
        """Get the current window title."""
        return self._title


class MockRenderer(BaseRenderer):
    """A mock renderer for headless validation and testing.
    
    This renderer prints drawing commands to stdout instead of actually
    rendering graphics, making it perfect for testing and development
    without a display server.
    """
    
    def init_window(self, width: int, height: int, title: str = "Aetheris UI") -> None:
        """Initialize the mock window."""
        self._width = width
        self._height = height
        self._title = title
        print(f"[MockRenderer] Initialized window: {width}x{height}, title: '{title}'")
    
    def clear_screen(self, color) -> None:
        """Clear the screen (mock implementation)."""
        print(f"[MockRenderer] Clearing screen with color: {color}")
    
    def render_frame(self, data_buffer: np.ndarray) -> None:
        """Render a frame by iterating over the structured data.
        
        This demonstrates the data contract: we only access the structured
        array, never DifferentialElement objects directly.
        """
        if len(data_buffer) == 0:
            print("[MockRenderer] Rendering empty frame")
            return
            
        print(f"[MockRenderer] Rendering frame with {len(data_buffer)} elements:")
        for i, element in enumerate(data_buffer):
            rect = element['rect']
            color = element['color']
            z = element['z']
            print(f"  Element {i}: Rect[{rect[0]:.1f}, {rect[1]:.1f}, {rect[2]:.1f}, {rect[3]:.1f}] "
                  f"Color[{color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f}, {color[3]:.2f}] Z={z}")
    
    def draw_rect(self, rect: np.ndarray, color: np.ndarray, z: int) -> None:
        """Draw a rectangle (mock implementation)."""
        print(f"[MockRenderer] Drawing rect: [{rect[0]:.1f}, {rect[1]:.1f}, {rect[2]:.1f}, {rect[3]:.1f}] "
              f"color: [{color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f}, {color[3]:.2f}] z={z}")
    
    def draw_rounded_rect(self, rect: np.ndarray, color: np.ndarray, z: int, radius: float) -> None:
        """Draw a rounded rectangle (mock implementation)."""
        print(f"[MockRenderer] Drawing rounded rect: [{rect[0]:.1f}, {rect[1]:.1f}, {rect[2]:.1f}, {rect[3]:.1f}] "
              f"color: [{color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f}, {color[3]:.2f}] z={z} radius={radius}")
    
    def draw_text(self, text: str, pos: np.ndarray, size: int, color: np.ndarray) -> None:
        """Draw text (mock implementation)."""
        print(f"[MockRenderer] Drawing text: '{text}' at [{pos[0]:.1f}, {pos[1]:.1f}] "
              f"size: {size} color: [{color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f}, {color[3]:.2f}]")
    
    def swap_buffers(self) -> None:
        """Swap buffers (mock implementation)."""
        print("[MockRenderer] Swapping buffers")


def pixel_to_ndc(x: float, y: float, width: float, height: float) -> tuple:
    """Convert pixel coordinates to Normalized Device Coordinates (NDC).
    
    Uses coordinate transformation principles from Álgebra de Baldor 2 and
    Precálculo algebra 1 regarding coordinate systems and axis translation.
    
    The transformation maps:
    - Pixel X: [0, width] → NDC X: [-1, 1]
    - Pixel Y: [0, height] → NDC Y: [1, -1] (Y inverted for graphics systems)
    
    Formulas derived:
    NDC_x = (2 * x / width) - 1
    NDC_y = 1 - (2 * y / height)
    
    Args:
        x: X coordinate in pixels
        y: Y coordinate in pixels
        width: Window width in pixels
        height: Window height in pixels
        
    Returns:
        tuple: (ndc_x, ndc_y) in range [-1, 1]
    """
    ndc_x = (2.0 * x / width) - 1.0
    ndc_y = 1.0 - (2.0 * y / height)
    return ndc_x, ndc_y