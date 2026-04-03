"""
Main entry point for Aetheris UI demonstration.
Shows the decoupling between the mathematical engine and the renderer.
Can switch between MockRenderer (headless), TkinterRenderer (visual), and GLRenderer (GPU).
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


def main(use_tkinter=False, use_gl=False):
    """Demonstrate the Aetheris UI architecture with a simple loop.
    
    Args:
        use_tkinter: If True, use TkinterRenderer; otherwise use MockRenderer
        use_gl: If True, use GLRenderer (overrides use_tkinter if both are True)
    """
    print("=== Aetheris UI Demo ===")
    if use_gl:
        print("Using GLRenderer for GPU-accelerated rendering")
    elif use_tkinter:
        print("Using TkinterRenderer for visual prototyping")
    else:
        print("Using MockRenderer for headless validation")
    print("Decoupled Mathematical Engine + Renderer")
    print()
    
    # Initialize the mathematical engine (physics + AI)
    engine = AetherEngine()
    
    # Define the UI Intent - same as app_server.py for parity
    ui_intent = {
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
    
    # Build elements from intent using UIBuilder
    builder = UIBuilder()
    builder.build_from_intent(engine, ui_intent)
    print(f"Built {engine.element_count} elements from UI intent")
    
    # Initialize the renderer based on choice
    if use_gl:
        print("Using GLRenderer for GPU acceleration")
        renderer = GLRenderer()
        renderer.init_window(800, 600, "Aetheris UI - GPU Rendering")
        
        # Run for specified number of frames or until interrupted
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
            
            # Update the mathematical engine
            data_buffer = engine.tick(win_w, win_h)
            
            # Get text metadata for the renderer (Phase 14.3)
            engine_metadata = engine.get_ui_metadata()
            
            # Render using the decoupled renderer with metadata
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
        print("GPU validation complete! Notice how:")
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


if __name__ == "__main__":
    use_tkinter = "--tkinter" in sys.argv
    use_gl = "--gl" in sys.argv
    
    if use_gl:
        print("Starting with GL renderer (GPU-accelerated mode)")
    elif use_tkinter:
        print("Starting with Tkinter renderer (visual mode)")
    else:
        print("Starting with Mock renderer (headless validation mode)")
        print("Tip: Use '--tkinter' flag for visual prototyping or '--gl' for GPU acceleration")
    main(use_tkinter=use_tkinter, use_gl=use_gl)