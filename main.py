"""
Main entry point for Aetheris UI demonstration.
Shows the decoupling between the mathematical engine and the renderer.
"""
import time
from core.engine import AetherEngine
from core.elements import StaticBox, SmartPanel, SmartButton
from core.renderer_base import MockRenderer


def main():
    """Demonstrate the Aetheris UI architecture with a simple loop."""
    print("=== Aetheris UI Demo ===")
    print("Decoupled Mathematical Engine + Renderer")
    print()
    
    # Initialize the mathematical engine (physics + AI)
    engine = AetherEngine()
    
    # Create some UI elements
    static_box = StaticBox(50, 50, 100, 80, color=(0.2, 0.6, 0.9, 1.0), z=0)
    smart_panel = SmartPanel(color=(0.9, 0.2, 0.6, 0.8), z=1)
    
    # Create a button that anchors to the panel
    button = SmartButton(smart_panel, offset_x=10, offset_y=10, 
                        offset_w=80, offset_h=30, color=(0.8, 0.8, 0.2, 1.0), z=2)
    
    # Register elements with the engine
    engine.register_element(static_box)
    engine.register_element(smart_panel)
    engine.register_element(button)
    
    # Initialize the renderer (decoupled from engine)
    renderer = MockRenderer()
    renderer.init_window(800, 600, "Aetheris UI Demo")
    
    # Main loop - run for 5 frames
    print("Starting render loop (5 frames)...")
    print()
    
    for frame in range(5):
        print(f"--- Frame {frame + 1} ---")
        
        # Window size could change each frame (responsive design)
        win_w = 800 + (frame * 50)  # Gradually increase width
        win_h = 600 + (frame * 25)  # Gradually increase height
        
        # Update the mathematical engine (physics + asymptote calculation)
        data_buffer = engine.tick(win_w, win_h)
        
        # Render using the decoupled renderer
        renderer.clear_screen((0.1, 0.1, 0.1, 1.0))  # Dark gray background
        renderer.render_frame(data_buffer)
        renderer.swap_buffers()
        
        # Small delay to see the output
        time.sleep(0.1)
    
    print()
    print("Demo complete! Notice how:")
    print("1. The renderer never touches DifferentialElement objects")
    print("2. Only the structured NumPy array flows from engine to renderer")
    print("3. Mathematical engine handles physics, AI asymptotes, and temporal variation")
    print("4. Renderer handles only visual presentation")


if __name__ == "__main__":
    main()