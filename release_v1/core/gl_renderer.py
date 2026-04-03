"""
High-performance GPU renderer for Aetheris UI using ModernGL and SDF shaders.
Implements hardware-accelerated rendering with Signed Distance Functions for
anti-aliased rounded rectangles, plus Pillow-based text texture generation
for native desktop text rendering.
"""
import json
import numpy as np
import moderngl
from typing import Union
from PIL import Image, ImageDraw, ImageFont
from core.renderer_base import BaseRenderer


class GLRenderer(BaseRenderer):
    """OpenGL renderer using ModernGL for hardware-accelerated UI rendering.
    
    This renderer implements the BaseRenderer contract using ModernGL with
    Signed Distance Function (SDF) shaders to render anti-aliased rounded
    rectangles with orthographic projection matching pixel coordinates.
    
    Text rendering is achieved by rasterizing text with Pillow into RGBA
    textures, then rendering them as textured quads on the GPU.
    """
    
    def __init__(self):
        """Initialize the OpenGL renderer."""
        super().__init__()
        self._ctx = None
        self._prog = None
        self._vbo = None
        self._vao = None
        self._text_textures = {}
        self._text_prog = None
        self._text_vbo = None
        self._text_vao = None

    def init_window(self, width: int, height: int, title: str = "Aetheris UI") -> None:
        """Initialize the ModernGL context and OpenGL resources."""
        self._width = width
        self._height = height
        self._title = title
        
        self._ctx = moderngl.create_standalone_context(require=330)
        self._ctx.enable(moderngl.BLEND)
        self._ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # SDF shader for rounded rectangles
        self._prog = self._ctx.program(
            vertex_shader='''
                #version 330
                in vec4 in_rect;
                in vec4 in_color;
                uniform mat4 projection;
                out vec4 v_color;
                out vec2 v_texcoord;
                out vec2 size;
                out float radius;
                
                void main() {
                    v_color = in_color;
                    size = in_rect.zw;
                    radius = 10.0;
                    
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
                    vec2 p = (v_texcoord - 0.5) * size;
                    float d = roundedRectSDF(p, size * 0.5, radius);
                    float alpha = smoothstep(0.5, -0.5, d);
                    f_color = vec4(v_color.rgb, v_color.a * alpha);
                }
            '''
        )
        
        # Text shader - samples a texture quad
        self._text_prog = self._ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_pos;
                in vec2 in_uv;
                uniform mat4 projection;
                out vec2 v_uv;
                
                void main() {
                    v_uv = in_uv;
                    gl_Position = projection * vec4(in_pos, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330
                in vec2 v_uv;
                uniform sampler2D text_texture;
                out vec4 f_color;
                
                void main() {
                    f_color = texture(text_texture, v_uv);
                }
            '''
        )
        
        self._vbo = None
        self._vao = None
        self._text_vbo = None
        self._text_vao = None

    def _get_or_create_text_texture(self, text: str, font_size: int, 
                                     color_rgba: tuple, font_family: str = "Arial") -> moderngl.Texture:
        """Get or create a text texture from the cache.
        
        Uses Pillow to rasterize text into an RGBA texture that can be
        sampled by the GPU text shader.
        
        Args:
            text: Text string to render
            font_size: Font size in pixels
            color_rgba: RGBA tuple (0-255) for text color
            font_family: Font family name
            
        Returns:
            ModernGL texture object
        """
        cache_key = (text, font_size, color_rgba, font_family)
        if cache_key in self._text_textures:
            return self._text_textures[cache_key]
        
        # Try to load a TrueType font, fall back to default
        font = None
        for font_path in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except (IOError, OSError):
                continue
        
        if font is None:
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except (IOError, OSError):
                font = ImageFont.load_default()
        
        # Measure text size and create appropriately sized image
        bbox = font.getbbox(text)
        text_w = int(bbox[2] - bbox[0] + 4)  # Add padding
        text_h = int(bbox[3] - bbox[1] + 4)
        text_w = max(text_w, 1)
        text_h = max(text_h, 1)
        
        # Create transparent image
        img = Image.new('RGBA', (text_w, text_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw text centered in the image
        offset_x = -bbox[0] + 2
        offset_y = -bbox[1] + 2
        draw.text((offset_x, offset_y), text, font=font, fill=color_rgba)
        
        # Convert to bytes and create texture
        img_data = img.tobytes()
        texture = self._ctx.texture(
            size=(text_w, text_h),
            components=4,
            data=img_data,
        )
        texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        
        self._text_textures[cache_key] = texture
        return texture

    def clear_screen(self, color: Union[tuple, list, np.ndarray]) -> None:
        """Clear the screen with a background color."""
        if self._ctx is None:
            return
        if isinstance(color, np.ndarray):
            color_tuple = tuple(color)
        else:
            color_tuple = color
        self._ctx.clear(color_tuple[0], color_tuple[1], color_tuple[2], color_tuple[3])

    def render_frame(self, data_buffer: np.ndarray, engine_metadata: str = None) -> None:
        """Render a frame from the structured data buffer using GPU acceleration.
        
        Args:
            data_buffer: Structured array from AetherEngine.tick()
            engine_metadata: JSON string from engine.get_ui_metadata() containing
                           text element metadata (canvas_text, dom_text types)
        """
        if self._ctx is None or self._prog is None or len(data_buffer) == 0:
            return
        
        rects = data_buffer['rect']
        colors = data_buffer['color']
        z_indices = data_buffer['z']
        n_elements = len(data_buffer)
        
        # Parse metadata if provided
        text_metadata = {}
        if engine_metadata:
            try:
                text_metadata = json.loads(engine_metadata)
            except (json.JSONDecodeError, TypeError):
                text_metadata = {}
        
        # Separate regular elements from text elements
        regular_indices = []
        text_elements = []
        
        for i in range(n_elements):
            z = int(z_indices[i])
            z_key = str(z)
            if z_key in text_metadata:
                meta = text_metadata[z_key]
                elem_type = meta.get('type', '')
                if elem_type in ('canvas_text', 'dom_text'):
                    text_elements.append((i, meta))
                    continue
            regular_indices.append(i)
        
        # Render regular elements (SDF quads)
        if regular_indices:
            n_regular = len(regular_indices)
            vertex_data = np.zeros((n_regular * 4, 8), dtype=np.float32)
            
            for vi, i in enumerate(regular_indices):
                base_idx = vi * 4
                for j in range(4):
                    vertex_data[base_idx + j, 0:4] = rects[i]
                    vertex_data[base_idx + j, 4:8] = colors[i]
            
            vertex_bytes = vertex_data.tobytes()
            if self._vbo is None or self._vbo.size < len(vertex_bytes):
                if self._vbo is not None:
                    self._vbo.release()
                self._vbo = self._ctx.buffer(reserve=max(len(vertex_bytes), 1024 * 1024))
            self._vbo.write(vertex_bytes)
            
            if self._vao is not None:
                self._vao.release()
            self._vao = self._ctx.vertex_array(
                self._prog,
                [(self._vbo, '4f 4f', 'in_rect', 'in_color')]
            )
            
            proj_matrix = np.array([
                [2.0 / self._width, 0.0, 0.0, -1.0],
                [0.0, -2.0 / self._height, 0.0, 1.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]
            ], dtype=np.float32)
            
            self._prog['projection'].write(proj_matrix.tobytes())
            self._vao.render(moderngl.TRIANGLE_STRIP, vertices=n_regular * 4)
        
        # Render text elements (textured quads)
        if text_elements and self._text_prog is not None:
            proj_matrix = np.array([
                [2.0 / self._width, 0.0, 0.0, -1.0],
                [0.0, -2.0 / self._height, 0.0, 1.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]
            ], dtype=np.float32)
            self._text_prog['projection'].write(proj_matrix.tobytes())
            
            for i, meta in text_elements:
                rect = rects[i]
                x, y, w, h = float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
                
                text = meta.get('text', '')
                font_size = meta.get('size', 16)
                font_family = meta.get('family', 'Arial')
                text_color = meta.get('color', [1.0, 1.0, 1.0, 1.0])
                
                # Convert float 0-1 to int 0-255
                r = int(text_color[0] * 255)
                g = int(text_color[1] * 255)
                b = int(text_color[2] * 255)
                a = int(text_color[3] * 255)
                
                texture = self._get_or_create_text_texture(text, font_size, (r, g, b, a), font_family)
                
                # Create quad vertices for text: [x, y] + [u, v]
                # Flip Y for OpenGL (screen coords: Y down, OpenGL: Y up)
                text_vertex_data = np.array([
                    x,       y,        0.0, 1.0,  # bottom-left
                    x + w,   y,        1.0, 1.0,  # bottom-right
                    x,       y + h,    0.0, 0.0,  # top-left
                    x + w,   y + h,    1.0, 0.0,  # top-right
                ], dtype=np.float32)
                
                text_bytes = text_vertex_data.tobytes()
                if self._text_vbo is None or self._text_vbo.size < len(text_bytes):
                    if self._text_vbo is not None:
                        self._text_vbo.release()
                    self._text_vbo = self._ctx.buffer(reserve=max(len(text_bytes), 4096))
                self._text_vbo.write(text_bytes)
                
                if self._text_vao is not None:
                    self._text_vao.release()
                self._text_vao = self._ctx.vertex_array(
                    self._text_prog,
                    [(self._text_vbo, '2f 2f', 'in_pos', 'in_uv')]
                )
                
                # Bind texture and render
                texture.use(location=0)
                self._text_prog['text_texture'].value = 0
                self._text_vao.render(moderngl.TRIANGLE_STRIP, vertices=4)

    def swap_buffers(self) -> None:
        """Finalize the frame and present it to the screen."""
        if self._ctx is not None:
            self._ctx.finish()

    def draw_rect(self, rect: np.ndarray, color: np.ndarray, z: int) -> None:
        pass

    def draw_rounded_rect(self, rect: np.ndarray, color: np.ndarray, z: int, radius: float) -> None:
        pass

    def draw_text(self, text: str, pos: np.ndarray, size: int, color: np.ndarray) -> None:
        pass

    def __del__(self):
        """Cleanup OpenGL resources."""
        try:
            if self._vao is not None:
                self._vao.release()
            if self._vbo is not None:
                self._vbo.release()
            if self._text_vao is not None:
                self._text_vao.release()
            if self._text_vbo is not None:
                self._text_vbo.release()
            if self._prog is not None:
                self._prog.release()
            if self._text_prog is not None:
                self._text_prog.release()
            for tex in self._text_textures.values():
                tex.release()
            self._text_textures.clear()
            if self._ctx is not None:
                self._ctx.release()
        except:
            pass
