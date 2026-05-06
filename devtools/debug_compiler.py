# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Debug script for Phase 11: Tensor Compiler validation.
Tests the compilation of design intent JSON into physics coefficients
and verifies convergence with the AetherEngine, including teleportation shock.
"""
import sys
import time
import numpy as np
from core.engine import AetherEngine
from core.elements import StaticBox, SmartPanel, SmartButton
from core.tensor_compiler import TensorCompiler, speed_to_stiffness, speed_to_viscosity
from core.renderer_base import MockRenderer
from core.gl_renderer import GLRenderer


def test_compiler_basic():
    """Test basic tensor compiler functionality."""
    compiler = TensorCompiler()
    
    # Test basic compilation
    intent = {
        "layout": "column",
        "spacing": 20,
        "animation": "snappy",
        "padding": 10,
    }
    
    coefficients = compiler.compile_intent(intent)
    
    print("=== Tensor Compiler - Basic Test ===")
    print(f"Layout: column, Spacing: 20px, Animation: snappy, Padding: 10px")
    print(f"Compiled coefficients shape: {coefficients.shape}")
    print(f"Default stiffness: {coefficients[0]['stiffness']:.4f}")
    print(f"Default viscosity: {coefficients[0]['viscosity']:.4f}")
    print(f"Boundary padding: {coefficients[0]['boundary_padding']}")
    print(f"Spacing: {coefficients[0]['spacing']:.1f}")
    print()
    
    # Test all animation presets
    for anim in ["snappy", "organic", "fluid", "rigid", "gentle"]:
        coeffs = compiler.compile_intent({"animation": anim})
        print(f"  {anim:10s} -> k={coeffs[0]['stiffness']:.4f}, v={coeffs[0]['viscosity']:.4f}")
    print()
    
    return coefficients


def test_compiler_with_elements():
    """Test compilation with individual element definitions."""
    compiler = TensorCompiler()
    
    intent = {
        "layout": "grid",
        "spacing": 15,
        "animation": "organic",
        "padding": [20, 10, 20, 10],  # [top, right, bottom, left]
        "elements": [
            {"id": "header", "animation": "snappy", "stiffness": 0.5},
            {"id": "content", "animation": "fluid", "viscosity": 0.6},
            {"id": "footer", "animation": "gentle"},
        ]
    }
    
    coefficients = compiler.compile_intent(intent)
    
    print("=== Tensor Compiler - Multi-Element Test ===")
    for coeff in coefficients:
        elem_id = str(coeff['element_id'])
        stiffness = coeff['stiffness']
        viscosity = coeff['viscosity']
        print(f"  {elem_id:10s} -> k={stiffness:.4f}, v={viscosity:.4f}")
    print()
    
    return coefficients


def test_mathematical_derivation():
    """Test the mathematical derivation of k from transition time T."""
    print("=== Mathematical Derivation: k = f(T) ===")
    print()
    print("Formula: k = 16 / T^2 (where T is in seconds)")
    print("Derivation:")
    print("  1. Critical damping: c = 2*sqrt(m*k)")
    print("  2. With m=1: c = 2*sqrt(k)")
    print("  3. Time constant: tau = 2m/c = 1/sqrt(k)")
    print("  4. Settling time (99%): T = 4*tau = 4/sqrt(k)")
    print("  5. Solving: k = 16/T^2")
    print()
    
    test_cases = [
        (100, "100ms (fast)"),
        (200, "200ms (snappy)"),
        (300, "300ms (medium)"),
        (500, "500ms (slow)"),
        (1000, "1000ms (very slow)"),
    ]
    
    for T_ms, label in test_cases:
        k = speed_to_stiffness(T_ms)
        T_sec = T_ms / 1000.0
        expected_k = 16.0 / (T_sec * T_sec)
        v = speed_to_viscosity(T_ms)
        print(f"  {label:25s} -> k={k:10.2f} (expected: {expected_k:10.2f}), v={v:.3f}")
    print()


def test_teleportation_shock_with_compiler(use_gl=False):
    """Test teleportation shock (1920->375px) with compiled coefficients."""
    print("=== Teleportation Shock Test (1920px -> 375px) ===")
    
    engine = AetherEngine()
    compiler = TensorCompiler()
    
    # Create elements
    panel = SmartPanel(color=(0.9, 0.2, 0.6, 0.8), z=1)
    button = SmartButton(panel, offset_x=10, offset_y=10, 
                        offset_w=80, offset_h=30, color=(0.8, 0.8, 0.2, 1.0), z=2)
    static_box = StaticBox(50, 50, 100, 80, color=(0.2, 0.6, 0.9, 1.0), z=0)
    
    engine.register_element(static_box)
    engine.register_element(panel)
    engine.register_element(button)
    
    # Compile snappy intent
    intent = {
        "layout": "column",
        "spacing": 20,
        "animation": "snappy",
        "padding": 10,
        "transition_speed_ms": 300,
    }
    
    coefficients = compiler.compile_intent(intent)
    compiler.apply_coefficients(engine, coefficients)
    
    # Initialize renderer
    if use_gl:
        renderer = GLRenderer()
        renderer.init_window(1920, 1080, "Aetheris UI - Teleportation Shock Test")
    else:
        renderer = MockRenderer()
        renderer.init_window(1920, 1080, "Aetheris UI - Teleportation Shock Test")
    
    # Run 10 frames at 1920x1080
    print("Running 10 frames at 1920x1080...")
    for frame in range(10):
        data = engine.tick(1920, 1080)
        renderer.clear_screen((0.1, 0.1, 0.1, 1.0))
        renderer.render_frame(data)
        renderer.swap_buffers()
        time.sleep(0.01)
    
    # Record positions before shock
    data_before = engine.tick(1920, 1080)
    panel_before = data_before[1]['rect'].copy()
    print(f"  Panel before shock: [{panel_before[0]:.1f}, {panel_before[1]:.1f}, {panel_before[2]:.1f}, {panel_before[3]:.1f}]")
    
    # TELEPORTATION SHOCK: Resize to 375px width (mobile)
    print(">> TELEPORTATION SHOCK: 1920px -> 375px <<")
    
    # Run 20 frames at 375x667 (mobile)
    for frame in range(20):
        data = engine.tick(375, 667)
        renderer.clear_screen((0.1, 0.1, 0.1, 1.0))
        renderer.render_frame(data)
        renderer.swap_buffers()
        
        if frame in [0, 5, 10, 15]:
            panel_rect = data[1]['rect']
            print(f"  Frame {frame+1}: Panel [{panel_rect[0]:.1f}, {panel_rect[1]:.1f}, {panel_rect[2]:.1f}, {panel_rect[3]:.1f}]")
        
        time.sleep(0.01)
    
    # Verify no NaN or infinity
    data_after = engine.tick(375, 667)
    for i, elem_data in enumerate(data_after):
        rect = elem_data['rect']
        assert not np.any(np.isnan(rect)), f"Element {i} has NaN values!"
        assert not np.any(np.isinf(rect)), f"Element {i} has infinity values!"
    
    panel_after = data_after[1]['rect']
    print(f"  Panel after shock:  [{panel_after[0]:.1f}, {panel_after[1]:.1f}, {panel_after[2]:.1f}, {panel_after[3]:.1f}]")
    print(f"  Expected mobile:    [{375*0.05:.1f}, {667*0.05:.1f}, {375*0.9:.1f}, {667*0.9:.1f}]")
    print()
    print("Teleportation shock test PASSED - No numerical explosions detected!")
    print()


def main(use_gl=False):
    """Run all Phase 11 validation tests."""
    print("=" * 60)
    print("AETHERIS UI - PHASE 11: TENSOR COMPILER VALIDATION")
    print("=" * 60)
    print()
    
    # Test 1: Basic compiler functionality
    test_compiler_basic()
    
    # Test 2: Multi-element compilation
    test_compiler_with_elements()
    
    # Test 3: Mathematical derivation
    test_mathematical_derivation()
    
    # Test 4: Teleportation shock with compiled coefficients
    test_teleportation_shock_with_compiler(use_gl=use_gl)
    
    print("=" * 60)
    print("PHASE 11 VALIDATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    use_gl = "--gl" in sys.argv
    main(use_gl=use_gl)
