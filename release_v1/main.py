# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Main entry point for Aetheris UI demonstration.
Shows the decoupling between the mathematical engine and the renderer.
Can switch between MockRenderer (headless), TkinterRenderer (visual), GLRenderer (GPU), and KivyRenderer (mobile).
"""
import time
import sys
import numpy as np
import json
from core.engine import AetherEngine
from core.elements import StaticBox, SmartPanel, SmartButton, FlexibleTextNode
from core.renderer_base import MockRenderer
from core.tkinter_renderer import TkinterRenderer
from core.gl_renderer import GLRenderer
from core.ui_builder import UIBuilder


# Shared UI Intent definition (used by all renderers for parity)
UI_INTENT = {
    "layout": "column",
    "spacing": 20,
    "animation": "organic",
    "padding": 10,
    "transition_speed_ms": 300,
    "elements": [
        {
            "id": "header_panel",
            "type": "smart_panel",
            "padding": 0.03,
            "color": [0.15, 0.15, 0.25, 1.0],
            "z": 0,
        },
        {
            "id": "title_text",
            "type": "canvas_text",
            "x": 40,
            "y": 15,
            "w": 400,
            "h": 40,
            "color": [0, 0, 0, 0],
            "text_color": [1.0, 1.0, 1.0, 1.0],
            "font_size": 24,
            "font_family": "Arial",
            "text_content": "Aetheris Hybrid Canvas Text",
            "z": 5,
        },
        {
            "id": "content_panel",
            "type": "smart_panel",
            "padding": 0.05,
            "color": [0.2, 0.2, 0.3, 0.9],
            "z": 1,
        },
        {
            "id": "card_1",
            "type": "static_box",
            "x": 30,
            "y": 30,
            "w": 150,
            "h": 200,
            "color": [0.8, 0.2, 0.3, 0.9],
            "z": 2,
        },
        {
            "id": "card_2",
            "type": "static_box",
            "x": 200,
            "y": 30,
            "w": 150,
            "h": 200,
            "color": [0.2, 0.6, 0.9, 0.9],
            "z": 2,
        },
        {
            "id": "card_3",
            "type": "static_box",
            "x": 370,
            "y": 30,
            "w": 150,
            "h": 200,
            "color": [0.9, 0.7, 0.2, 0.9],
            "z": 2,
        },
        {
            "id": "action_button",
            "type": "smart_button",
            "parent": "content_panel",
            "offset_x": 20,
            "offset_y": 250,
            "offset_w": 120,
            "offset_h": 40,
            "color": [0.3, 0.8, 0.3, 1.0],
            "z": 3,
        },
        {
            "id": "description",
            "type": "dom_text",
            "x": 50,
            "y": 300,
            "w": 500,
            "h": 100,
            "color": [0, 0, 0, 0],
            "text_color": [0.8, 0.8, 0.8, 1.0],
            "font_size": 16,
            "font_family": "Arial",
            "text_content": "This is selectable HTML text driven by a physics engine.",
            "z": 10,
        },
    ]
}


def main(use_tkinter=False, use_gl=False, use_kivy=False):
    """Demonstrate the Aetheris UI architecture with a simple loop.
    
    Args:
        use_tkinter: If True, use TkinterRenderer
        use_gl: If True, use GLRenderer
        use_kivy: If True, use KivyRenderer (mobile)
    """
    print("=== Aetheris UI Demo ===")
    if use_kivy:
        print("Using KivyRenderer for native mobile rendering")
    elif use_gl:
        print("Using GLRenderer for GPU-accelerated rendering")
    elif use_tkinter:
        print("Using TkinterRenderer for visual prototyping")
    else:
        print("Using MockRenderer for headless validation")
    print("Decoupled Mathematical Engine + Renderer")
    print()
    
    # Initialize the mathematical engine (physics + AI)
    engine = AetherEngine()
    
    # Build elements from intent using UIBuilder
    builder = UIBuilder()
    builder.build_from_intent(engine, UI_INTENT)
    print(f"Built {engine.element_count} elements from UI intent")
    
    # Initialize the renderer based on choice
    if use_kivy:
        _run_kivy_app(engine)
    elif use_gl:
        print("Using GLRenderer for GPU acceleration")
        renderer = GLRenderer()
        renderer.init_window(800, 600, "Aetheris UI - GPU Rendering")
        
        frames_to_run = 50
        if len(sys.argv) > 2:
            try:
                frames_to_run = int(sys.argv[2])
            except ValueError:
                pass
                
        print(f"Starting render loop ({frames_to_run} frames for GPU validation)...")
        print()
        
        for frame in range(frames_to_run):
            if frame % 10 == 0:
                print(f"--- Frame {frame + 1} ---")
            
            win_w = 800 + (frame * 2)
            win_h = 600 + (frame * 1)
            
            data_buffer = engine.tick(win_w, win_h)
            engine_metadata = engine.get_ui_metadata()
            
            renderer.clear_screen((0.1, 0.1, 0.1, 1.0))
            renderer.render_frame(data_buffer, engine_metadata)
            renderer.swap_buffers()
            
            if frame % 10 == 0 and len(data_buffer) >= 2:
                for i, elem_data in enumerate(data_buffer):
                    rect = elem_data['rect']
                    z = elem_data['z']
                    print(f"  Element {i} (z={z}): [{rect[0]:.1f}, {rect[1]:.1f}, {rect[2]:.1f}, {rect[3]:.1f}]")
                print()
            
            time.sleep(0.01)
         
        print()
        print("GPU validation complete!")
        print("1. The renderer never touches DifferentialElement objects")
        print("2. Only the structured NumPy array flows from engine to renderer")
        print("3. Text metadata bridge enables Pillow-rasterized text on GPU")
        print("4. Elements converge toward their asymptotes over time")
        print("5. Rendering is hardware-accelerated using ModernGL and SDF shaders")
        
    elif use_tkinter:
        print("Using TkinterRenderer for visual prototyping")
        renderer = TkinterRenderer()
        renderer.init_window(800, 600, "Aetheris UI - Tkinter Prototyping")
        
        try:
            renderer.start(engine)
        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
        finally:
            renderer.stop()
    else:
        print("Using MockRenderer for headless validation")
        renderer = MockRenderer()
        renderer.init_window(800, 600, "Aetheris UI Demo")
        
        print("Starting render loop (100 frames for headless validation)...")
        print()
        
        for frame in range(100):
            if frame % 20 == 0:
                print(f"--- Frame {frame + 1} ---")
            
            win_w = 800 + (frame * 2)
            win_h = 600 + (frame * 1)
            
            data_buffer = engine.tick(win_w, win_h)
            
            renderer.clear_screen((0.1, 0.1, 0.1, 1.0))
            renderer.render_frame(data_buffer)
            renderer.swap_buffers()
            
            if frame % 20 == 0 and len(data_buffer) >= 4:
                for i, elem_data in enumerate(data_buffer):
                    rect = elem_data['rect']
                    z = elem_data['z']
                    print(f"  Element {i} (z={z}): [{rect[0]:.1f}, {rect[1]:.1f}, {rect[2]:.1f}, {rect[3]:.1f}]")
                print()
            
            time.sleep(0.01)
         
        print()
        print("Headless validation complete!")
        print("1. The renderer never touches DifferentialElement objects")
        print("2. Only the structured NumPy array flows from engine to renderer")
        print("3. Elements converge toward their asymptotes over time")


def _run_kivy_app(engine):
    """Run the Kivy application with physics-driven rendering."""
    from kivy.app import App
    from kivy.uix.widget import Widget
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.label import Label
    from kivy.clock import Clock
    from kivy.graphics import Color, Rectangle
    from core.kivy_renderer import KivyRenderer
    
    class AetherisKivyApp(App):
        """Kivy application that renders Aetheris UI elements."""
        
        def build(self):
            self.title = "Aetheris UI - Kivy Mobile Rendering"
            
            # Create the root layout
            self.root_layout = FloatLayout(size=(800, 600))
            self.root_layout.size_hint = (None, None)
            self.root_layout.size = (800, 600)
            self.root_layout.pos = (0, 0)
            
            # Container for DOM-like text labels
            self.dom_container = FloatLayout(size=(800, 600))
            self.root_layout.add_widget(self.dom_container)
            
            # Canvas widget for physics rendering
            self.canvas_widget = Widget(size=(800, 600))
            self.root_layout.add_widget(self.canvas_widget)
            
            # Initialize renderer
            self.renderer = KivyRenderer()
            self.renderer.init_window(800, 600, self.title)
            self.renderer.set_canvas(self.canvas_widget.canvas)
            self.renderer.set_dom_container(self.dom_container)
            
            # Frame counter for validation output
            self.frame_count = 0
            
            # Schedule the physics update at 60 FPS
            Clock.schedule_interval(self._update, 1.0 / 60.0)
            
            return self.root_layout
        
        def _update(self, dt):
            """Called every frame by Kivy's clock."""
            # Simulate slowly growing window to test responsiveness
            win_w = min(800 + (self.frame_count * 2), 1200)
            win_h = min(600 + (self.frame_count * 1), 900)
            
            # Update physics engine
            data_buffer = engine.tick(win_w, win_h)
            engine_metadata = engine.get_ui_metadata()
            
            # Render
            self.renderer.clear_screen((0.1, 0.1, 0.1, 1.0))
            self.renderer.render_frame(data_buffer, engine_metadata)
            self.renderer.swap_buffers()
            
            # Print validation output every 60 frames
            if self.frame_count % 60 == 0 and len(data_buffer) >= 2:
                print(f"--- Kivy Frame {self.frame_count + 1} ---")
                for i, elem_data in enumerate(data_buffer):
                    rect = elem_data['rect']
                    z = elem_data['z']
                    print(f"  Element {i} (z={z}): [{rect[0]:.1f}, {rect[1]:.1f}, {rect[2]:.1f}, {rect[3]:.1f}]")
                print()
            
            self.frame_count += 1
            
            # Stop after 300 frames (5 seconds) for validation
            if self.frame_count >= 300:
                print("Kivy validation complete!")
                self.stop()
                return False
            
            return True
        
        def on_stop(self):
            """Cleanup when app stops."""
            self.renderer.cleanup_dom_labels()
    
    print("Starting Kivy app (300 frames / 5 seconds for validation)...")
    print()
    AetherisKivyApp().run()


if __name__ == "__main__":
    # Extract our flags BEFORE Kivy potentially parses sys.argv
    use_tkinter = "--tkinter" in sys.argv
    use_gl = "--gl" in sys.argv
    use_kivy = "--kivy" in sys.argv
    use_odyssey = "--odyssey" in sys.argv
    
    # Remove our flags from sys.argv so Kivy doesn't complain
    sys.argv = [a for a in sys.argv if a not in ('--tkinter', '--gl', '--kivy', '--odyssey')]
    
    # Disable Kivy's argument parser to avoid conflicts
    import os
    os.environ['KIVY_NO_ARGS'] = '1'
    
    if use_odyssey:
        print("Starting Aetheris Odyssey - The Master Showcase")
    elif use_kivy:
        print("Starting with Kivy renderer (native mobile mode)")
    elif use_gl:
        print("Starting with GL renderer (GPU-accelerated mode)")
    elif use_tkinter:
        print("Starting with Tkinter renderer (visual mode)")
    else:
        print("Starting with Mock renderer (headless validation mode)")
        print("Tip: Use '--odyssey' for the Master Showcase, '--tkinter', '--gl', or '--kivy'")
    
    if use_odyssey:
        from demo.odyssey_master import create_odyssey_engine, run_odyssey, trigger_supernova, apply_genre_orbit
        
        # Generate database if needed
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'demo', 'odyssey.db')):
            from demo.odyssey_db import create_database
            create_database()
        
        if use_gl:
            renderer = GLRenderer()
            renderer.init_window(1200, 900, "Aetheris Odyssey - GL")
            engine = create_odyssey_engine()
            
            print("Odyssey GL - Running 10000 frames (Ctrl+C to exit)")
            print("Space = Supernova | 1-6 = Genre focus")
            print()
            
            # Run with generous frame count (user can Ctrl+C)
            run_odyssey(engine, renderer, focused_genre='action',
                       num_frames=10000, interactive=True)
            
        elif use_kivy:
            from kivy.app import App
            from kivy.uix.widget import Widget
            from kivy.uix.floatlayout import FloatLayout
            from kivy.clock import Clock
            from kivy.core.window import Window as KivyWindow
            from core.kivy_renderer import KivyRenderer
            from demo.odyssey_master import apply_genre_orbit, trigger_supernova
            
            odyssey_engine = create_odyssey_engine()
            
            class OdysseyKivyApp(App):
                def build(self):
                    self.title = "Aetheris Odyssey - Kivy"
                    self.root_layout = FloatLayout(size=(1200, 900))
                    self.root_layout.size_hint = (None, None)
                    self.root_layout.size = (1200, 900)
                    self.root_layout.pos = (0, 0)
                    
                    self.dom_container = FloatLayout(size=(1200, 900))
                    self.root_layout.add_widget(self.dom_container)
                    
                    self.canvas_widget = Widget(size=(1200, 900))
                    self.root_layout.add_widget(self.canvas_widget)
                    
                    self.renderer = KivyRenderer()
                    self.renderer.init_window(1200, 900, self.title)
                    self.renderer.set_canvas(self.canvas_widget.canvas)
                    self.renderer.set_dom_container(self.dom_container)
                    
                    self.frame_count = 0
                    self.focused_genre = 'action'
                    
                    # Bind keyboard for supernova and genre switching
                    KivyWindow.bind(on_key_down=self._on_key_down)
                    
                    Clock.schedule_interval(self._update, 1.0 / 60.0)
                    return self.root_layout
                
                def _on_key_down(self, window, key, scancode, codepoint, modifiers):
                    center_x, center_y = 600, 450
                    
                    if codepoint == ' ':
                        trigger_supernova(odyssey_engine, center_x, center_y)
                    elif codepoint == '1':
                        self.focused_genre = 'action'
                    elif codepoint == '2':
                        self.focused_genre = 'scifi'
                    elif codepoint == '3':
                        self.focused_genre = 'drama'
                    elif codepoint == '4':
                        self.focused_genre = 'comedy'
                    elif codepoint == '5':
                        self.focused_genre = 'thriller'
                    elif codepoint == '6':
                        self.focused_genre = 'fantasy'
                    elif codepoint == '0':
                        self.focused_genre = 'none'
                    elif codepoint == 'escape':
                        self.stop()
                
                def _update(self, dt):
                    win_w, win_h = 1200, 900
                    center_x, center_y = 600, 450
                    
                    # Apply genre orbit
                    if self.focused_genre != 'none':
                        apply_genre_orbit(odyssey_engine, self.focused_genre, center_x, center_y)
                    
                    data = odyssey_engine.tick(win_w, win_h)
                    self.renderer.clear_screen((0.05, 0.05, 0.1, 1.0))
                    self.renderer.render_frame(data, odyssey_engine.get_ui_metadata())
                    
                    if self.frame_count % 120 == 0:
                        print(f"  Odyssey Kivy Frame {self.frame_count} | Genre: {self.focused_genre}")
                    
                    self.frame_count += 1
                    return True
                
                def on_stop(self):
                    self.renderer.cleanup_dom_labels()
                    print(f"Odyssey Kivy complete ({self.frame_count} frames)")
            
            print("Starting Odyssey Kivy app (interactive - press Space for Supernova, Esc to exit)")
            print("Keys: 1=Action 2=SciFi 3=Drama 4=Comedy 5=Thriller 6=Fantasy 0=None")
            print()
            OdysseyKivyApp().run()
        else:
            renderer = MockRenderer()
            renderer.init_window(1200, 900, "Aetheris Odyssey - Mock")
            engine = create_odyssey_engine()
            run_odyssey(engine, renderer, focused_genre='action', num_frames=300, trigger_supernova_at=150)
    else:
        main(use_tkinter=use_tkinter, use_gl=use_gl, use_kivy=use_kivy)