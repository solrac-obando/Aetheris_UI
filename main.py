"""
Main entry point for Aetheris UI demonstration.
Shows the decoupling between the mathematical engine and the renderer.
Can switch between MockRenderer (headless), TkinterRenderer (visual), and GLRenderer (GPU).
"""
import time
import sys
import numpy as np
from core.engine import AetherEngine
from core.elements import StaticBox, SmartPanel, SmartButton, FlexibleTextNode
from core.renderer_base import MockRenderer
from core.tkinter_renderer import TkinterRenderer
from core.gl_renderer import GLRenderer


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
    
    # Create UI elements as specified in Phase 8 requirements
    
    # 1. SmartPanel with 5% padding (will adapt to container size)
    smart_panel = SmartPanel(
        color=(0.9, 0.2, 0.6, 0.8),  # Purpleish color
        z=1
    )
    
    # 2. FlexibleTextNode centered at the top
    # We'll position it at y=10, with width 80% of container, height 40
    # X position will be calculated to center it
    flexible_text = FlexibleTextNode(
        x=0, y=10, w=200, h=40,  # Initial values, will be overridden by asymptotes
        color=(0.2, 0.6, 0.9, 1.0),  # Blue color
        z=2,
        text="Aetheris UI Physics Engine"
    )
    
    # 3. SmartButton anchored to the panel with offset
    button = SmartButton(
        parent=smart_panel,
        offset_x=10, offset_y=10,
        offset_w=80, offset_h=30,
        color=(0.8, 0.8, 0.2, 1.0),  # Yellow color
        z=3
    )
    
    # Also keep the original static box for comparison
    static_box = StaticBox(
        50, 50, 100, 80,
        color=(0.2, 0.6, 0.9, 1.0),
        z=0
    )
    
    # Register elements with the engine
    engine.register_element(static_box)
    engine.register_element(smart_panel)
    engine.register_element(flexible_text)
    engine.register_element(button)
    
    # Register UI states for demonstration (Phase 10 feature)
    # Desktop state: normal layout
    desktop_state = {
        smart_panel: np.array([40.0, 30.0, 720.0, 540.0], dtype=np.float32),  # 5% padding in 800x600
        flexible_text: np.array([200.0, 10.0, 400.0, 40.0], dtype=np.float32),  # Centered
        button: np.array([150.0, 140.0, 80.0, 30.0], dtype=np.float32)  # Example position
    }
    engine.register_state('desktop', desktop_state)
    
    # Mobile state: different layout (simulating rotation or mobile view)
    mobile_state = {
        smart_panel: np.array([20.0, 20.0, 760.0, 360.0], dtype=np.float32),  # Different padding
        flexible_text: np.array([100.0, 10.0, 600.0, 40.0], dtype=np.float32),  # Full width
        button: np.array([50.0, 50.0, 100.0, 30.0], dtype=np.float32)  # Different position
    }
    engine.register_state('mobile', mobile_state)
    
    # Initialize the renderer based on choice
    if use_gl:
        print("Using GLRenderer for GPU acceleration")
        renderer = GLRenderer()
        renderer.init_window(800, 600, "Aetheris UI - GPU Rendering")
        
        # Run for specified number of frames or until interrupted
        frames_to_run = 100  # Increased to show state transition
        if len(sys.argv) > 2:
            try:
                frames_to_run = int(sys.argv[2])
            except ValueError:
                pass
                
        print(f"Starting render loop ({frames_to_run} frames for GPU validation)...")
        print("State transition from 'desktop' to 'mobile' will occur at frame 50")
        print()
        
        for frame in range(frames_to_run):
            if frame % 10 == 0:  # Print every 10 frames to reduce output
                print(f"--- Frame {frame + 1} ---")
            
            # Window size could change each frame (responsive design)
            # Gradually increase size to test responsiveness
            win_w = 800 + (frame * 2)  # Slow width increase
            win_h = 600 + (frame * 1)  # Slow height increase
            
            # State transition demonstration: switch to mobile state at frame 50
            if frame == 50:
                print(">> TRANSITIONING TO MOBILE STATE <<")
                engine.transition_to('mobile')
            
            # Update the mathematical engine (physics + asymptote calculation)
            data_buffer = engine.tick(win_w, win_h)
            
            # Render using the decoupled renderer
            renderer.clear_screen((0.1, 0.1, 0.1, 1.0))  # Dark gray background
            renderer.render_frame(data_buffer)
            renderer.swap_buffers()
            
            # Print element positions every 10 frames for validation
            if frame % 10 == 0 and len(data_buffer) >= 4:
                static_rect = data_buffer[0]['rect']
                panel_rect = data_buffer[1]['rect'] 
                text_rect = data_buffer[2]['rect']
                button_rect = data_buffer[3]['rect']
                
                print(f"  StaticBox:    [{static_rect[0]:.1f}, {static_rect[1]:.1f}, {static_rect[2]:.1f}, {static_rect[3]:.1f}]")
                print(f"  SmartPanel:   [{panel_rect[0]:.1f}, {panel_rect[1]:.1f}, {panel_rect[2]:.1f}, {panel_rect[3]:.1f}]")
                print(f"  FlexibleText: [{text_rect[0]:.1f}, {text_rect[1]:.1f}, {text_rect[2]:.1f}, {text_rect[3]:.1f}]")
                print(f"  SmartButton:  [{button_rect[0]:.1f}, {button_rect[1]:.1f}, {button_rect[2]:.1f}, {button_rect[3]:.1f}]")
                
                # Calculate expected asymptotes for validation
                expected_panel_x = win_w * 0.05  # 5% padding
                expected_panel_y = win_h * 0.05
                expected_panel_w = win_w * 0.9   # 90% width (100% - 2*5%)
                expected_panel_h = win_h * 0.9
                print(f"  Expected Panel: [{expected_panel_x:.1f}, {expected_panel_y:.1f}, {expected_panel_w:.1f}, {expected_panel_h:.1f}]")
                print()
            
            # Small delay to see the output (only for mock renderer)
            time.sleep(0.01)
         
        print()
        print("GPU validation complete! Notice how:")
        print("1. The renderer never touches DifferentialElement objects")
        print("2. Only the structured NumPy array flows from engine to renderer")
        print("3. Mathematical engine handles physics, AI asymptotes, and temporal variation")
        print("4. Renderer handles only visual presentation via GPU shaders")
        print("5. Elements converge toward their asymptotes over time")
        print("6. Rendering is hardware-accelerated using ModernGL and SDF shaders")
        print("7. State management enables efficient UI transitions (desktop <-> mobile)")
        print("8. UI Snap Threshold (99% Rule) prevents unnecessary computation at rest")
        
    elif use_tkinter:
        print("Using TkinterRenderer for visual prototyping")
        renderer = TkinterRenderer()
        renderer.init_window(800, 600, "Aetheris UI - Tkinter Prototyping")
        
        # Start the Tkinter main loop (this will block)
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
        
        # Main loop - run for 100 frames for validation
        print("Starting render loop (100 frames for headless validation)...")
        print("State transition from 'desktop' to 'mobile' will occur at frame 50")
        print()
        
        for frame in range(100):
            if frame % 20 == 0:  # Print every 20 frames to reduce output
                print(f"--- Frame {frame + 1} ---")
            
            # Window size could change each frame (responsive design)
            # Gradually increase size to test responsiveness
            win_w = 800 + (frame * 2)  # Slow width increase
            win_h = 600 + (frame * 1)  # Slow height increase
            
            # State transition demonstration: switch to mobile state at frame 50
            if frame == 50:
                print(">> TRANSITIONING TO MOBILE STATE <<")
                engine.transition_to('mobile')
            
            # Update the mathematical engine (physics + asymptote calculation)
            data_buffer = engine.tick(win_w, win_h)
            
            # Render using the decoupled renderer
            renderer.clear_screen((0.1, 0.1, 0.1, 1.0))  # Dark gray background
            renderer.render_frame(data_buffer)
            renderer.swap_buffers()
            
            # Print element positions every 20 frames for validation
            if frame % 20 == 0 and len(data_buffer) >= 4:
                static_rect = data_buffer[0]['rect']
                panel_rect = data_buffer[1]['rect'] 
                text_rect = data_buffer[2]['rect']
                button_rect = data_buffer[3]['rect']
                
                print(f"  StaticBox:    [{static_rect[0]:.1f}, {static_rect[1]:.1f}, {static_rect[2]:.1f}, {static_rect[3]:.1f}]")
                print(f"  SmartPanel:   [{panel_rect[0]:.1f}, {panel_rect[1]:.1f}, {panel_rect[2]:.1f}, {panel_rect[3]:.1f}]")
                print(f"  FlexibleText: [{text_rect[0]:.1f}, {text_rect[1]:.1f}, {text_rect[2]:.1f}, {text_rect[3]:.1f}]")
                print(f"  SmartButton:  [{button_rect[0]:.1f}, {button_rect[1]:.1f}, {button_rect[2]:.1f}, {button_rect[3]:.1f}]")
                
                # Calculate expected asymptotes for validation
                expected_panel_x = win_w * 0.05  # 5% padding
                expected_panel_y = win_h * 0.05
                expected_panel_w = win_w * 0.9   # 90% width (100% - 2*5%)
                expected_panel_h = win_h * 0.9
                print(f"  Expected Panel: [{expected_panel_x:.1f}, {expected_panel_y:.1f}, {expected_panel_w:.1f}, {expected_panel_h:.1f}]")
                print()
            
            # Small delay to see the output (only for mock renderer)
            time.sleep(0.01)
         
        print()
        print("Headless validation complete! Notice how:")
        print("1. The renderer never touches DifferentialElement objects")
        print("2. Only the structured NumPy array flows from engine to renderer")
        print("3. Mathematical engine handles physics, AI asymptotes, and temporal variation")
        print("4. Renderer handles only visual presentation")
        print("5. Elements converge toward their asymptotes over time")
        print("6. State management enables efficient UI transitions (desktop <-> mobile)")
        print("7. UI Snap Threshold (99% Rule) prevents unnecessary computation at rest")


if __name__ == "__main__":
    # Check command line arguments for renderer selection
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