"""
High-performance GPU renderer for Aetheris UI using ModernGL and SDF shaders.
Implements hardware-accelerated rendering with Signed Distance Functions for
anti-aliased rounded rectangles.
"""
import numpy as np
import moderngl
from typing import Union
from core.renderer_base import BaseRenderer


class GLRenderer(BaseRenderer):
    """OpenGL renderer using ModernGL for hardware-accelerated UI rendering.
    
    This renderer implements the BaseRenderer contract using ModernGL with
    Signed Distance Function (SDF) shaders to render anti-aliased rounded
    rectangles with orthographic projection matching pixel coordinates.
    """
    
    def __init__(self):
        """Initialize the OpenGL renderer."""
        super().__init__()
        self._ctx = None
        self._prog = None
        self._vbo = None
        self._vao = None

    def init_window(self, width: int, height: int, title: str = "Aetheris UI") -> None:
        """Initialize the ModernGL context and OpenGL resources.
        
        Creates a standalone OpenGL context suitable for headless operation
        (e.g., inside Docker containers) and sets up shaders, buffers, and
        vertex array objects for rendering.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
            title: Window title (not used in headless context but kept for interface)
        """
        self._width = width
        self._height = height
        self._title = title
        
        # Create standalone OpenGL context for headless operation
        self._ctx = moderngl.create_standalone_context(require=330)
        
        # Enable blending for transparency
        self._ctx.enable(moderngl.BLEND)
        self._ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # Compile shaders
        self._prog = self._ctx.program(
            vertex_shader='''
                #version 330
                in vec4 in_rect;   // [x, y, w, h]
                in vec4 in_color;  // [r, g, b, a]
                uniform mat4 projection;
                out vec4 v_color;
                out vec2 v_texcoord;
                out vec2 size;
                out float radius;
                
                void main() {
                    v_color = in_color;
                    size = in_rect.zw;
                    radius = 10.0; // Fixed radius for now
                    
                    // Generate quad vertices based on gl_VertexID (0 to 3)
                    vec2 pos = vec2(0.0);
                    if(gl_VertexID == 0) { 
                        pos = vec2(in_rect.x, in_rect.y); 
                        v_texcoord = vec2(0.0, 0.0); 
                    }
                    if(gl_VertexID == 1) { 
                        pos = vec2(in_rect.x + in_rect.z, in_rect.y); 
                        v_texcoord = vec2(1.0, 0.0); 
                    }
                    if(gl_VertexID == 2) { 
                        pos = vec2(in_rect.x, in_rect.y + in_rect.w); 
                        v_texcoord = vec2(0.0, 1.0); 
                    }
                    if(gl_VertexID == 3) { 
                        pos = vec2(in_rect.x + in_rect.z, in_rect.y + in_rect.w); 
                        v_texcoord = vec2(1.0, 1.0); 
                    }
                    
                    gl_Position = projection * vec4(pos, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330
                in vec2 v_texcoord;
                in vec4 v_color;
                uniform vec2 size;
                uniform float radius;
                out vec4 f_color;
                
                float roundedRectSDF(vec2 p, vec2 b, float r) {
                    vec2 q = abs(p) - b + r;
                    return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r;
                }
                
                void main() {
                    // Traslación de Ejes: Center the coordinate system
                    vec2 p = (v_texcoord - 0.5) * size;
                    
                    float d = roundedRectSDF(p, size * 0.5, radius);
                    
                    // Smoothstep for Anti-Aliasing
                    float alpha = smoothstep(0.5, -0.5, d); 
                    
                    f_color = vec4(v_color.rgb, v_color.a * alpha);
                }
            '''
        )
        
        # We'll create VBO and VAO in render_frame since we don't know the size yet
        self._vbo = None
        self._vao = None

    def clear_screen(self, color: Union[tuple, list, np.ndarray]) -> None:
        """Clear the screen with a background color.
        
        Args:
            color: RGBA color values (float32, 0-1 range)
        """
        if self._ctx is None:
            return
            
        # Convert to tuple if needed
        if isinstance(color, np.ndarray):
            color_tuple = tuple(color)
        else:
            color_tuple = color
            
        # Clear with the specified color
        self._ctx.clear(color_tuple[0], color_tuple[1], color_tuple[2], color_tuple[3])

    def render_frame(self, data_buffer: np.ndarray) -> None:
        """Render a frame from the structured data buffer using GPU acceleration.
        
        Flattens the structured NumPy array to float32 bytes and uploads to GPU
        VBO for efficient rendering with SDF shaders.
        
        Args:
            data_buffer: Structured array from AetherEngine.tick()
                        with dtype [('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')]
        """
        if self._ctx is None or self._prog is None or len(data_buffer) == 0:
            return
            
        rects = data_buffer['rect']  # Shape: (n_elements, 4) [x, y, w, h]
        colors = data_buffer['color']  # Shape: (n_elements, 4) [r, g, b, a]
        
        # We need 4 vertices per element for the quad.
        # We just duplicate the [x,y,w,h, r,g,b,a] data 4 times per element.
        n_elements = len(data_buffer)
        vertex_data = np.zeros((n_elements * 4, 8), dtype=np.float32)
        
        for i in range(n_elements):
            base_idx = i * 4
            # Duplicate the data for the 4 corners of the quad
            for j in range(4):
                vertex_data[base_idx + j, 0:4] = rects[i]
                vertex_data[base_idx + j, 4:8] = colors[i]
                
        vertex_bytes = vertex_data.tobytes()
        
        if self._vbo is None or self._vbo.size < len(vertex_bytes):
            if self._vbo is not None: 
                self._vbo.release()
            self._vbo = self._ctx.buffer(reserve=max(len(vertex_bytes), 1024 * 1024))  # At least 1MB
            
        self._vbo.write(vertex_bytes)
        
        if self._vao is not None: 
            self._vao.release()
            
        self._vao = self._ctx.vertex_array(
            self._prog,
            [(self._vbo, '4f 4f', 'in_rect', 'in_color')]
        )
        
        # Calculate projection matrix dynamically based on current width/height
        # Matrix from Part 1: P = [[2/W, 0, 0, -1], [0, -2/H, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]]
        proj_matrix = np.array([
            [2.0 / self._width, 0.0, 0.0, -1.0],
            [0.0, -2.0 / self._height, 0.0, 1.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)
        
        self._prog['projection'].write(proj_matrix.tobytes())
        
        # Render using triangle strip (0,1,2,3 for each quad gives us two triangles)
        self._vao.render(moderngl.TRIANGLE_STRIP, vertices=n_elements * 4)

    def swap_buffers(self) -> None:
        """Finalize the frame and present it to the screen.
        
        In standalone ModernGL context, this ensures all commands are executed.
        """
        if self._ctx is not None:
            self._ctx.finish()

    # Abstract method implementations from BaseRenderer
    # These are not used in our optimized render_frame path but required by the interface
    
    def draw_rect(self, rect: np.ndarray, color: np.ndarray, z: int) -> None:
        """Draw a rectangle.
        
        This implementation is provided for completeness but not used in our optimized path.
        The actual rendering happens in render_frame() via the structured array approach.
        
        Args:
            rect: [x, y, width, height] in pixel coordinates
            color: RGBA color values (float32, 0-1 range)
            z: Z-index for rendering depth
        """
        # For completeness, we could implement immediate mode rendering here
        # but it would be inefficient. The proper way is to batch all draw calls
        # into the structured array approach used in render_frame.
        pass

    def draw_rounded_rect(self, rect: np.ndarray, color: np.ndarray, z: int, radius: float) -> None:
        """Draw a rectangle with rounded corners.
        
        This implementation is provided for completeness but not used in our optimized path.
        The actual rendering happens in render_frame() via the structured array approach.
        
        Args:
            rect: [x, y, width, height] in pixel coordinates
            color: RGBA color values (float32, 0-1 range)
            z: Z-index for rendering depth
            radius: Corner radius in pixels
        """
        # For completeness, we could implement immediate mode rendering here
        # but it would be inefficient. The proper way is to batch all draw calls
        # into the structured array approach used in render_frame.
        pass

    def draw_text(self, text: str, pos: np.ndarray, size: int, color: np.ndarray) -> None:
        """Draw text.
        
        This implementation is provided for completeness but not used in our optimized path.
        Text rendering would require a separate approach (bitmap fonts, distance field fonts, etc.)
        and is not implemented in this GPU renderer phase.
        
        Args:
            text: String to render
            pos: [x, y] position in pixel coordinates (baseline)
            size: Font size in pixels
            color: RGBA color values (float32, 0-1 range)
        """
        # Text rendering is not implemented in this phase
        # In a full implementation, we would use either:
        # 1. Bitmap font textures
        # 2. Signed Distance Field (SDF) fonts
        # 3. Vector text rendering
        pass

    def __del__(self):
        """Cleanup OpenGL resources."""
        try:
            if self._vao is not None:
                self._vao.release()
            if self._vbo is not None:
                self._vbo.release()
            if self._prog is not None:
                self._prog.release()
            if self._ctx is not None:
                self._ctx.release()
        except:
            pass  # Ignore errors during cleanup