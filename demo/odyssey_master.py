"""
Aetheris Odyssey - The Master Showcase.
A high-density Media Universe explorer that pushes every module to its limit.

Features:
- 100 physics-driven elements from SQLite database
- Min-Max scaling: rating→color, votes→size, year→Y position
- AI-Gravity: Genre Orbit attraction toward screen center
- Drag-and-Throw for all 100 elements simultaneously
- Supernova chaos protocol with Aether-Guard recovery
"""
import json
import time
import os
import numpy as np
from typing import Dict, List, Optional

from core.engine import AetherEngine
from core.elements import StaticBox
from core.data_bridge import SQLiteProvider, min_max_scale, vector_to_tensor
from core.ui_builder import UIBuilder
from core.input_manager import InputManager

# Odyssey configuration
ODYSSEY_DB_PATH = os.path.join(os.path.dirname(__file__), 'odyssey.db')

# Physics mapping constants
ODYSSEY_MIN_SIZE = 20.0    # Minimum element size (px)
ODYSSEY_MAX_SIZE = 120.0   # Maximum element size (px)
ODYSSEY_MIN_YEAR = 1950    # Earliest year in dataset
ODYSSEY_MAX_YEAR = 2026    # Latest year in dataset
ODYSSEY_MIN_VOTES = 100    # Minimum votes
ODYSSEY_MAX_VOTES = 3_000_000  # Maximum votes

# Genre Orbit
GENRE_ORBIT_STIFFNESS = 0.05  # Gentle attraction to center for matching genre
GENRE_ORBIT_RADIUS = 300.0    # Radius of genre orbit zone

# Supernova
SUPERNOVA_FORCE = 100_000.0  # px/s² conflict force
SUPERNOVA_RECOVERY_TIME = 3.0  # seconds to return to orbit


def rating_to_color(rating: float) -> List[float]:
    """
    Map rating (0-10) to a color gradient from Red (0.0) to Emerald (10.0).
    
    Uses smooth interpolation through intermediate colors:
    Red (0) → Orange (3) → Yellow (5) → Green (7) → Emerald (10)
    """
    t = max(0.0, min(1.0, rating / 10.0))
    
    if t < 0.3:
        # Red to Orange
        s = t / 0.3
        r = 1.0
        g = 0.1 + s * 0.5
        b = 0.1
    elif t < 0.5:
        # Orange to Yellow
        s = (t - 0.3) / 0.2
        r = 1.0
        g = 0.6 + s * 0.4
        b = 0.1
    elif t < 0.7:
        # Yellow to Green
        s = (t - 0.5) / 0.2
        r = 1.0 - s * 0.5
        g = 1.0
        b = 0.1 + s * 0.3
    else:
        # Green to Emerald
        s = (t - 0.7) / 0.3
        r = 0.5 - s * 0.3
        g = 1.0
        b = 0.4 + s * 0.4
    
    return [round(r, 2), round(g, 2), round(b, 2), 0.85]


def create_odyssey_engine(db_path: str = None) -> AetherEngine:
    """
    Create and populate an AetherEngine with 100 media elements from the database.
    
    Data-to-Physics Mapping:
    - Rating → Color (Red=0.0, Emerald=10.0)
    - Votes → Size (ODYSSEY_MIN_SIZE to ODYSSEY_MAX_SIZE)
    - Year → Y-Axis Position (creating a physical timeline)
    - Genre Vector → Stored as metadata for AI-Gravity interaction
    
    Args:
        db_path: Path to the Odyssey SQLite database
        
    Returns:
        Populated AetherEngine with 100 physics-driven elements
    """
    if db_path is None:
        db_path = ODYSSEY_DB_PATH
    
    engine = AetherEngine()
    provider = SQLiteProvider(db_path)
    provider.connect()
    
    # Fetch all media entries
    rows = provider.execute_query("SELECT * FROM media ORDER BY year ASC")
    
    if not rows:
        # Generate database if it doesn't exist
        from demo.odyssey_db import create_database
        create_database(db_path)
        provider.disconnect()
        provider = SQLiteProvider(db_path)
        provider.connect()
        rows = provider.execute_query("SELECT * FROM media ORDER BY year ASC")
    
    # Window dimensions for layout
    win_w = 1200
    win_h = 900
    
    # Calculate global ranges for Min-Max scaling
    all_votes = [row['votes'] for row in rows]
    min_votes = min(all_votes)
    max_votes = max(all_votes)
    
    all_years = [row['year'] for row in rows]
    min_year = min(all_years)
    max_year = max(all_years)
    
    # Create elements with physics mapping
    elements_data = []
    for row in rows:
        rating = float(row['rating'])
        year = int(row['year'])
        votes = int(row['votes'])
        genre_vector = json.loads(row['genre_vector'])
        
        # Map votes to element size
        size = min_max_scale(float(votes), float(min_votes), float(max_votes),
                            ODYSSEY_MIN_SIZE, ODYSSEY_MAX_SIZE)
        
        # Map year to Y position (newer = higher on screen)
        year_t = (float(year) - float(min_year)) / max(1.0, float(max_year) - float(min_year))
        y_pos = win_h * 0.1 + year_t * (win_h * 0.7)
        
        # Spread elements across X axis in a grid-like pattern
        idx = int(row['id']) - 1
        cols = 10
        col = idx % cols
        x_pos = 80 + col * (win_w - 160) / cols
        
        # Map rating to color
        color = rating_to_color(rating)
        
        elements_data.append({
            'id': str(row['id']),
            'x': x_pos,
            'y': y_pos,
            'w': size,
            'h': size,
            'color': color,
            'z': int(rating * 10),  # Higher rating = higher z-index
            'metadata': {
                'title': row['title'],
                'type': row['type'],
                'genre': row['genre'],
                'rating': rating,
                'year': year,
                'votes': votes,
                'genre_vector': genre_vector,
            }
        })
    
    # Build elements using UIBuilder
    builder = UIBuilder()
    
    for elem_data in elements_data:
        elem = StaticBox(
            x=elem_data['x'],
            y=elem_data['y'],
            w=elem_data['w'],
            h=elem_data['h'],
            color=tuple(elem_data['color']),
            z=elem_data['z']
        )
        elem._id = elem_data['id']
        elem._odyssey_metadata = elem_data['metadata']
        elem._original_x = elem_data['x']
        elem._original_y = elem_data['y']
        engine.register_element(elem)
    
    provider.disconnect()
    print(f"Odyssey Engine created with {engine.element_count} elements")
    return engine


def apply_genre_orbit(engine: AetherEngine, focused_genre: str, 
                      center_x: float, center_y: float) -> None:
    """
    Apply Hooke's Law attraction toward screen center for elements matching the focused genre.
    
    Elements with matching genre_vector components are gently pulled toward the center,
    creating an "orbit" effect. Non-matching elements are unaffected.
    
    Args:
        engine: The AetherEngine instance
        focused_genre: Genre to focus on (e.g., 'action', 'scifi')
        center_x: X coordinate of the orbit center
        center_y: Y coordinate of the orbit center
    """
    genre_vectors = {
        'action': 0, 'scifi': 1, 'drama': 2, 'comedy': 3,
        'thriller': 0, 'horror': 0, 'romance': 2, 'animation': 3,
        'fantasy': 1, 'documentary': 2,
    }
    
    genre_idx = genre_vectors.get(focused_genre, 0)
    
    for element in engine._elements:
        if not hasattr(element, '_odyssey_metadata'):
            continue
        
        meta = element._odyssey_metadata
        gv = meta.get('genre_vector', [0.25, 0.25, 0.25, 0.25])
        
        # Calculate match strength (how much this element belongs to the focused genre)
        match_strength = gv[genre_idx]
        
        if match_strength > 0.3:
            # Apply gentle attraction toward center, scaled by genre match
            rect = element.tensor.state
            cx = float(rect[0]) + float(rect[2]) / 2.0
            cy = float(rect[1]) + float(rect[3]) / 2.0
            
            # Hooke's Law: F = -k * displacement
            dx = center_x - cx
            dy = center_y - cy
            
            force_x = dx * GENRE_ORBIT_STIFFNESS * match_strength
            force_y = dy * GENRE_ORBIT_STIFFNESS * match_strength
            
            element.tensor.apply_force(
                np.array([force_x, force_y, 0.0, 0.0], dtype=np.float32)
            )


def trigger_supernova(engine: AetherEngine, center_x: float, center_y: float) -> None:
    """
    Apply a massive conflict force (100,000 px/s²) for 1 frame to all elements.
    
    This demonstrates Aether-Guard's clamping behavior and the engine's
    ability to recover from extreme forces within 3 seconds.
    
    Args:
        engine: The AetherEngine instance
        center_x: X coordinate of the supernova center
        center_y: Y coordinate of the supernova center
    """
    print(f"⚡ SUPERNOVA TRIGGERED at ({center_x}, {center_y})!")
    
    for element in engine._elements:
        rect = element.tensor.state
        cx = float(rect[0]) + float(rect[2]) / 2.0
        cy = float(rect[1]) + float(rect[3]) / 2.0
        
        # Calculate direction away from supernova center
        dx = cx - center_x
        dy = cy - center_y
        dist = max(1.0, np.sqrt(dx * dx + dy * dy))
        
        # Normalize and apply supernova force
        force_x = (dx / dist) * SUPERNOVA_FORCE
        force_y = (dy / dist) * SUPERNOVA_FORCE
        
        element.tensor.apply_force(
            np.array([force_x, force_y, 0.0, 0.0], dtype=np.float32)
        )


def run_odyssey(engine: AetherEngine, renderer, focused_genre: str = None,
                num_frames: int = 300, trigger_supernova_at: int = None) -> None:
    """
    Run the Odyssey simulation loop.
    
    Args:
        engine: The AetherEngine instance
        renderer: Any renderer implementing BaseRenderer interface
        focused_genre: Optional genre to apply orbit attraction
        num_frames: Number of frames to run
        trigger_supernova_at: Frame number to trigger supernova (None = never)
    """
    win_w = 1200
    win_h = 900
    center_x = win_w / 2.0
    center_y = win_h / 2.0
    
    print(f"Starting Odyssey simulation ({num_frames} frames)")
    print(f"Elements: {engine.element_count}")
    if focused_genre:
        print(f"Genre Focus: {focused_genre}")
    print()
    
    for frame in range(num_frames):
        # Apply genre orbit if focused
        if focused_genre:
            apply_genre_orbit(engine, focused_genre, center_x, center_y)
        
        # Trigger supernova at specified frame
        if trigger_supernova_at is not None and frame == trigger_supernova_at:
            trigger_supernova(engine, center_x, center_y)
        
        # Run physics tick
        data = engine.tick(win_w, win_h)
        
        # Render
        renderer.clear_screen((0.05, 0.05, 0.1, 1.0))
        
        # Pass metadata if renderer supports it
        try:
            renderer.render_frame(data, engine.get_ui_metadata())
        except TypeError:
            renderer.render_frame(data)
        
        renderer.swap_buffers()
        
        # Print status every 50 frames
        if frame % 50 == 0 or (trigger_supernova_at and abs(frame - trigger_supernova_at) <= 5):
            # Calculate average displacement from original positions
            total_disp = 0.0
            for elem in engine._elements:
                if hasattr(elem, '_original_x'):
                    dx = float(elem.tensor.state[0]) - elem._original_x
                    dy = float(elem.tensor.state[1]) - elem._original_y
                    total_disp += np.sqrt(dx * dx + dy * dy)
            avg_disp = total_disp / max(1, len(engine._elements))
            
            label = "SUPERNOVA!" if (trigger_supernova_at and abs(frame - trigger_supernova_at) <= 5) else "Stable"
            print(f"  Frame {frame:4d} | {label:12s} | Avg displacement: {avg_disp:.1f}px")
    
    print(f"\nOdyssey simulation complete ({num_frames} frames)")
