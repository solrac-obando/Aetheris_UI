# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Live demo: Instantiates all 32 Aetheris components, runs a headless
physics simulation, and prints metadata for each.

Usage:
    python3 demo/demo_all_components.py --frames 50
"""
import sys
import argparse
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine import AetherEngine
from core.components import (
    AetherGauge, AetherSparkline, AetherBarGroup, AetherStatusOrb,
    AetherHeatMap, AetherKineticToggle, AetherRadialProgress, AetherValueMetric,
    AetherWindow, AetherSideNav, AetherToolbar, AetherModal,
    AetherSplitter, AetherScrollPanel, AetherContextMenu, AetherTooltipBox,
    AetherHero, AetherPricingCard, AetherNavbar, AetherToastAlert,
    AetherAccordionItem, AetherDrawer, AetherTabs, AetherPillBadge,
    AetherSpringBox, AetherAttractor, AetherBoundary, AetherSurface,
    AetherBouncyLabel, AetherMagnetLink, AetherPhysicsDivider, AetherTeleport,
)

COMPONENTS = [
    ("Phase A: Dashboard", [
        ("AetherGauge", lambda: AetherGauge(x=10, y=10, w=120, h=120, value=72, min_val=0, max_val=100, label="CPU")),
        ("AetherSparkline", lambda: AetherSparkline(x=140, y=10, w=200, h=60, data=[10, 20, 15, 30, 25, 40], label="Revenue")),
        ("AetherBarGroup", lambda: AetherBarGroup(x=350, y=10, w=300, h=150, values=[30, 50, 70, 45], labels=["Q1", "Q2", "Q3", "Q4"])),
        ("AetherStatusOrb", lambda: AetherStatusOrb(x=10, y=140, w=40, h=40, status="ok", pulse_frequency=1.5, label="API")),
        ("AetherHeatMap", lambda: AetherHeatMap(x=60, y=140, w=300, h=200, rows=4, cols=6, data=np.random.rand(4, 6) * 100)),
        ("AetherKineticToggle", lambda: AetherKineticToggle(x=370, y=170, w=80, h=40, is_on=True, label="Dark Mode")),
        ("AetherRadialProgress", lambda: AetherRadialProgress(x=460, y=170, w=100, h=100, progress=0.65, label="Upload")),
        ("AetherValueMetric", lambda: AetherValueMetric(x=10, y=350, w=200, h=80, value=2_450_000, unit="USD", label="Revenue", trend=12.5)),
    ]),
    ("Phase B: Desktop", [
        ("AetherWindow", lambda: AetherWindow(x=10, y=10, w=600, h=400, title="Main Window")),
        ("AetherSideNav", lambda: AetherSideNav(x=0, y=0, w=250, h=600, is_open=True, position="left")),
        ("AetherToolbar", lambda: AetherToolbar(x=0, y=0, w=800, h=48, items=[{"label": "File"}, {"label": "Edit"}, {"label": "View"}])),
        ("AetherModal", lambda: AetherModal(w=500, h=350, title="Confirm Action", is_visible=True)),
        ("AetherSplitter", lambda: AetherSplitter(w=800, h=600, orientation="vertical", ratio=0.4)),
        ("AetherScrollPanel", lambda: AetherScrollPanel(w=400, h=300, content_h=800)),
        ("AetherContextMenu", lambda: AetherContextMenu(w=200, h=150, items=[{"label": "Copy"}, {"label": "Paste"}], is_visible=True)),
        ("AetherTooltipBox", lambda: AetherTooltipBox(w=150, h=40, text="Click to edit", target_x=300, target_y=200)),
    ]),
    ("Phase C: Web", [
        ("AetherHero", lambda: AetherHero(w=1280, h=500, title="Welcome", subtitle="Build beautiful UIs", parallax_factor=0.3)),
        ("AetherPricingCard", lambda: AetherPricingCard(w=300, h=400, plan="Pro", price=29.99, features=["Unlimited", "Priority"], is_featured=True)),
        ("AetherNavbar", lambda: AetherNavbar(w=1280, h=64, items=[{"label": "Home"}, {"label": "About"}], is_sticky=True)),
        ("AetherToastAlert", lambda: AetherToastAlert(w=350, h=60, message="Saved successfully!", toast_type="success", duration=5.0)),
        ("AetherAccordionItem", lambda: AetherAccordionItem(w=600, h=50, title="FAQ", content="Answer here", is_expanded=True, expanded_h=150)),
        ("AetherDrawer", lambda: AetherDrawer(w=300, h=600, is_open=True, position="left")),
        ("AetherTabs", lambda: AetherTabs(w=600, h=48, tabs=["Overview", "Details", "Settings"], active_index=0)),
        ("AetherPillBadge", lambda: AetherPillBadge(w=24, h=24, text="3", anchor="top-right")),
    ]),
    ("Phase D: Physics Utilities", [
        ("AetherSpringBox", lambda: AetherSpringBox(w=200, h=100, spring_k=15.0, damping_c=2.5)),
        ("AetherAttractor", lambda: AetherAttractor(x=400, y=300, strength=500, radius=300)),
        ("AetherBoundary", lambda: AetherBoundary(x=0, y=0, w=1280, h=720, clamp_inside=True)),
        ("AetherSurface", lambda: AetherSurface(w=400, h=300, friction=0.25, is_draggable=True)),
        ("AetherBouncyLabel", lambda: AetherBouncyLabel(w=200, h=40, text="Hello!", font_size=18)),
        ("AetherMagnetLink", lambda: AetherMagnetLink(w=100, h=100, snap_distance=25, linked_ids=["elem1", "elem2"])),
        ("AetherPhysicsDivider", lambda: AetherPhysicsDivider(w=20, h=600, min_size=10, preferred_size=40, stiffness=8.0)),
        ("AetherTeleport", lambda: AetherTeleport(w=200, h=200, state_a={"opacity": 1}, state_b={"opacity": 0}, blend=0.5)),
    ]),
]


def run_demo(frames: int = 50) -> bool:
    engine = AetherEngine()
    all_elements = []

    for phase_name, components in COMPONENTS:
        print(f"\n{'='*60}")
        print(f"  {phase_name}")
        print(f"{'='*60}")
        for comp_name, factory in components:
            elem = factory()
            engine.register_element(elem)
            all_elements.append((comp_name, elem))

    total = len(all_elements)
    print(f"\n[OK] Registered {total} components with engine")

    print(f"\n[ENGINE] Running {frames} frames of headless simulation...")
    for i in range(frames):
        data = engine.tick(1280, 720)
        if np.any(np.isnan(data['rect'])) or np.any(np.isnan(data['color'])):
            print(f"[FAIL] NaN detected at frame {i}")
            return False

    print(f"[OK] {frames} frames completed — numerical stability verified")

    print(f"\n{'='*60}")
    print(f"  Component Metadata Summary")
    print(f"{'='*60}")
    for comp_name, elem in all_elements:
        state = elem.tensor.state
        meta_type = getattr(elem, '_element_type', 'unknown')
        print(f"  {comp_name:25s} [{meta_type}] "
              f"pos=({state[0]:.0f}, {state[1]:.0f}) "
              f"size=({state[2]:.0f}, {state[3]:.0f})")

    print(f"\n[OK] All {total} components instantiated and simulated successfully")
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Aetheris 32-Component Demo')
    parser.add_argument('--frames', type=int, default=50, help='Simulation frames')
    args = parser.parse_args()
    success = run_demo(frames=args.frames)
    sys.exit(0 if success else 1)
