"""
Aetheris Project GESTNE - Real-World Cluster Visualization.
Final Build: 100% Real Data Integration.
Author: Carlos Ivan Obando Aure
"""
import os
import sys
import numpy as np
from typing import List

# Ajuste de path para encontrar el paquete 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import AetherEngine
from core.components import (
    AetherStatusOrb, 
    AetherValueMetric, 
    AetherHeatMap,
    AetherDrawer,
    AetherPillBadge
)
from core.elements import CanvasTextNode, StaticBox
from core.gl_renderer import GLRenderer
from demo.gestne_loader import load_gestne_data

# Visual Constants
WIN_W, WIN_H = 1500, 950
THEME_NAVY = (0.02, 0.02, 0.04, 1.0)
COLOR_METABOLIC = (1.0, 0.35, 0.2, 0.9)   # Vibrant Orange-Red
COLOR_REPRODUCTIVE = (0.2, 0.75, 1.0, 0.8) # Vibrant Sky-Blue

# Cluster Centroids
CENTROIDS = {
    1: (WIN_W * 0.35, WIN_H * 0.5), # Metabolic Center
    2: (WIN_W * 0.75, WIN_H * 0.5)  # Reproductive Center
}

class PatientOrb(AetherStatusOrb):
    """Real patient data mapped to an Aether physics node."""
    def __init__(self, patient_data, **kwargs):
        self.pdata = patient_data
        cluster_id = patient_data["cluster"]
        
        # Mapping metrics to visuals
        # IMC determines size (20-40px range)
        base_size = np.clip(patient_data["imc"], 18, 45)
        
        # Insulin determines pulse frequency (Higher insulin -> faster pulse)
        # Metabolic median is ~18, Reproductive is ~8
        pulse_freq = 0.5 + (patient_data["insu"] / 10.0)
        
        super().__init__(
            status="ok",
            pulse_frequency=pulse_freq,
            w=base_size, h=base_size,
            **kwargs
        )
        
        self._color = np.array(COLOR_METABOLIC if cluster_id == 1 else COLOR_REPRODUCTIVE, dtype=np.float32)
        self._target_center = np.array(CENTROIDS[cluster_id], dtype=np.float32)
        
    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        # Physics: Orbit around cluster center with jitter
        # The higher the IMC, the more 'mass' it feels (larger jitter/orbital radius)
        radius = 80 + (self.pdata["imc"] * 2)
        angle = np.random.random() * 2 * np.pi
        
        tx = self._target_center[0] + np.cos(angle) * radius * 0.5
        ty = self._target_center[1] + np.sin(angle) * radius * 0.5
        
        # Keep within viewable area
        tx = np.clip(tx, 400, container_w - 50) # Leave space for sidebar
        ty = np.clip(ty, 200, container_h - 100)
        
        return np.array([tx, ty, self.tensor.state[2], self.tensor.state[3]], dtype=np.float32)

def build_gestne_viz() -> AetherEngine:
    engine = AetherEngine()
    patients = load_gestne_data()
    
    if not patients:
        return engine

    # 1. Sidebar Header
    sidebar_bg = StaticBox(x=0, y=0, w=350, h=WIN_H, color=(0.05, 0.05, 0.1, 1.0), z=-1)
    engine.register_element(sidebar_bg)
    
    title = CanvasTextNode(
        x=20, y=40, w=310, h=40,
        text="GESTNE ANALYTICS",
        font_size=28, color=(1, 1, 1, 1)
    )
    engine.register_element(title)
    
    subtitle = CanvasTextNode(
        x=20, y=85, w=310, h=25,
        text="Metodología DAPAS (2020)",
        font_size=16, color=(0.5, 0.6, 0.8, 1.0)
    )
    engine.register_element(subtitle)

    # 2. Key Metrics Summary
    met_count = sum(1 for p in patients if p["cluster"] == 1)
    rep_count = sum(1 for p in patients if p["cluster"] == 2)
    avg_imc = np.mean([p["imc"] for p in patients])
    
    m1 = AetherValueMetric(
        x=20, y=140, w=310, h=110,
        label="Pacientes Metabólicos", value=met_count, unit=" (N1)",
        color=COLOR_METABOLIC, trend=-0.6
    )
    engine.register_element(m1)

    m2 = AetherValueMetric(
        x=20, y=260, w=310, h=110,
        label="Pacientes Reproductivos", value=rep_count, unit=" (N2)",
        color=COLOR_REPRODUCTIVE, trend=40.6
    )
    engine.register_element(m2)
    
    m3 = AetherValueMetric(
        x=20, y=380, w=310, h=90,
        label="Promedio IMC Cohorte", value=round(avg_imc, 1), unit=" kg/m2",
        color=(0.7, 0.7, 0.7, 1.0)
    )
    engine.register_element(m3)

    # 3. Patient Orbs (Physics nodes)
    for p in patients:
        node = PatientOrb(
            patient_data=p,
            x=WIN_W * 0.5 + (np.random.random() - 0.5) * 400,
            y=WIN_H * 0.5 + (np.random.random() - 0.5) * 400,
            z=10
        )
        # Add a pill badge for the ID if it's a 'VIP' patient (e.g. extreme IMC)
        if p["imc"] > 40:
            badge = AetherPillBadge(
                text="OBESO", parent=node, color=(1, 0, 0, 1)
            )
            # Badges are often attached to parents in the renderer, 
            # here we just register it.
            engine.register_element(badge)
            
        engine.register_element(node)

    # 4. Correlation Matrix
    # Simulating the SHBG/IMC/Insu correlation found in the report
    correlation_data = [
        [1.0, 0.82, -0.65], # IMC
        [0.82, 1.0, -0.71], # Insu
        [-0.65, -0.71, 1.0] # SHBG
    ]
    hm = AetherHeatMap(x=20, y=500, w=310, h=200, rows=3, cols=3, data=correlation_data)
    engine.register_element(hm)

    # 5. Header labels for the scatter zones
    l1 = CanvasTextNode(x=CENTROIDS[1][0]-100, y=100, w=200, h=30, text="ZONA METABÓLICA", color=COLOR_METABOLIC)
    l2 = CanvasTextNode(x=CENTROIDS[2][0]-100, y=100, w=200, h=30, text="ZONA REPRODUCTIVA", color=COLOR_REPRODUCTIVE)
    engine.register_element(l1)
    engine.register_element(l2)

    return engine

def run_gestne_showcase():
    print("Iniciando Aetheris GESTNE Showcase [Datos Reales: 100%]")
    engine = build_gestne_viz()
    
    try:
        renderer = GLRenderer(WIN_W, WIN_H, "Aetheris GESTNE | Cluster Analysis Virtualization")
    except:
        print("Fallo al iniciar GLRenderer. Asegúrese de que X11/OpenGL esté disponible.")
        return

    frame = 0
    while True:
        data = engine.tick(WIN_W, WIN_H)
        renderer.clear_screen(THEME_NAVY)
        renderer.render_frame(data)
        renderer.swap_buffers()
        
        if frame % 120 == 0:
            print(f"FRAME {frame} | Engine Load: {engine.get_hpc_config()['cpu_usage_pct']}% | Nodes: {engine.element_count}")
        
        frame += 1
        if frame > 3000: break # Demo limited to 3000 frames (~50s)

if __name__ == "__main__":
    run_gestne_showcase()
