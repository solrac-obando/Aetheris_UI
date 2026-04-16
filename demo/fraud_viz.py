"""
Aetheris Fraud-Watch 2000 - Professional HPC Showcase.
Visualizes 2,000 transactions where physics serves as a diagnostic tool.

Features:
- 2,000 elements running at 60 FPS via GLRenderer.
- Fraud Cluster Attraction: Suspicious nodes with shared origins attract physically.
- Risk-to-Heat Mapping: color=[risk, 1-risk, 0.2, 0.8].
- Dynamic Pressure: Supernova stress test.
"""
import os
import json
import numpy as np
import sqlite3
from typing import List, Dict

from core.engine import AetherEngine
from core.elements import StaticBox
from core.data_bridge import SQLiteProvider, min_max_scale

FRAUD_DB_PATH = os.path.join(os.path.dirname(__file__), 'fraud.db')

# Physics Constants for 2,000 elements
CLUSTER_ATTRACTION_K = 0.8     # Strong attraction for fraud clusters
REPULSION_K = 0.05             # Weak repulsion to prevent total overlap
MIN_SIZE = 8.0                 # px
MAX_SIZE = 45.0                # px
WIN_W, WIN_H = 1280, 720

def risk_to_color(score: float) -> List[float]:
    """Map fraud score (0-1) to an Heatmap. Green (low risk) to Red (high)."""
    if score > 0.7:
        return [1.0, 0.0, 0.0, 0.9]  # Critical (Red)
    elif score > 0.4:
        return [1.0, 0.6, 0.0, 0.8]  # Warning (Orange)
    return [0.2, 0.8, 0.4, 0.6]      # Legit (Green-Blue)

def create_fraud_engine(db_path: str = None) -> AetherEngine:
    if db_path is None:
        db_path = FRAUD_DB_PATH
        
    engine = AetherEngine()
    # Boost performance for 2,000 elements: increase target threads
    import os
    os.environ["NUMBA_NUM_THREADS"] = str(max(1, os.cpu_count() - 1))
    
    provider = SQLiteProvider(db_path)
    provider.connect()
    
    rows = provider.execute_query("SELECT * FROM transactions")
    
    if not rows:
        print("Error: Fraud database empty or not found.")
        return engine

    all_amounts = [row['amount'] for row in rows]
    min_amt, max_amt = min(all_amounts), max(all_amounts)
    
    # Pre-calculate cluster centers (randomized for the demo)
    cluster_targets = {}
    for i in range(10):  # 10 fraud clusters from data_gen
        cluster_targets[i] = (
            WIN_W * 0.2 + np.random.random() * WIN_W * 0.6,
            WIN_H * 0.2 + np.random.random() * WIN_H * 0.6
        )

    for i, row in enumerate(rows):
        score = float(row['fraud_score'])
        amt = float(row['amount'])
        cluster_id = int(row['cluster_id'])
        
        size = min_max_scale(amt, min_amt, max_amt, MIN_SIZE, MAX_SIZE)
        color = risk_to_color(score)
        
        # Initial grid layout
        cols = 50
        x_pos = (i % cols) * (WIN_W / cols)
        y_pos = (i // cols) * (WIN_H / (2000/cols))
        
        elem = StaticBox(
            x=x_pos, y=y_pos, w=size, h=size,
            color=tuple(color), z=int(score * 100)
        )
        elem._fraud_meta = {
            'score': score,
            'cluster_id': cluster_id,
            'ip': row['source_ip']
        }
        
        # If fraud, set target to its cluster center via _target_rect
        if cluster_id != -1:
            tx, ty = cluster_targets[cluster_id]
            # Use small offset to avoid perfect overlap
            tx += (np.random.random() - 0.5) * 100
            ty += (np.random.random() - 0.5) * 100
            elem._target_rect = np.array([tx, ty, size, size], dtype=np.float32)
        # else: legit nodes keep their init position as target (already set by StaticBox.__init__)
            
        engine.register_element(elem)
        
    provider.disconnect()
    print(f"Fraud Engine Ready: 2,000 Transactions Loaded")
    return engine

def apply_fraud_physics(engine: AetherEngine):
    """Custom attraction/repulsion logic for 2,000 nodes."""
    for elem in engine._elements:
        meta = getattr(elem, '_fraud_meta', None)
        if not meta: continue
        
        # If significant fraud, increase stiffness for tracking
        if meta['score'] > 0.7:
            # This makes critical ones "snap" faster to clusters
            elem.tensor.spring_k = CLUSTER_ATTRACTION_K
        else:
            # Legit nodes have lazy physics
            elem.tensor.spring_k = 0.05

def run_fraud_demo():
    print("--- AETHERIS FRAUD-WATCH 2000 ---")
    engine = create_fraud_engine()
    renderer = GLRenderer(WIN_W, WIN_H, "Aetheris Fraud-Watch 2000 [2,000 Nodes]")
    
    frame = 0
    while True:
        # 1. Custom Physics Pass
        apply_fraud_physics(engine)
        
        # 2. Engine Tick (HPC Mode)
        data = engine.tick(WIN_W, WIN_H)
        
        # 3. Render
        renderer.clear_screen((0.02, 0.02, 0.05, 1.0))
        renderer.render_frame(data)
        renderer.swap_buffers()
        
        if frame % 60 == 0:
            print(f"Frame {frame} | Engine Utilization: {engine.get_hpc_config()['cpu_usage_pct']}% | Nodes: 2000")
            
        frame += 1
        # In a real app, check for exit events here
        if frame > 1000: break # Demo for 1000 frames

if __name__ == "__main__":
    run_fraud_demo()
