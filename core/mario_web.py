# Copyright 2026 Carlos Ivan Obando Aure
# Super Aetheris Bros - Classic Edition Engine
# Optimized for Sprite-based rendering and tighter platformer physics.

import numpy as np
import json
from core.engine import AetherEngine
from core.elements import StaticBox

class MarioWebEngine(AetherEngine):
    def __init__(self):
        super().__init__()
        self.mario_x = 100
        self.mario_y = 500
        self.mario_vx = 0
        self.mario_vy = 0
        
        # Physics Constants (Classic Feel)
        self.GRAVITY = 0.8
        self.WALK_SPEED = 5.0
        self.JUMP_FORCE = -15.0
        self.FRICTION = 0.85
        self.FALL_CLAMP = 14.0
        
        self.on_ground = False
        self.facing_right = True
        self.state = "idle" # idle, walking, jumping
        
        # Level Data: (x, y, type) 
        # Types: 0: Ground, 1: Brick, 2: Question, 3: Pipe
        self.tiles = []
        self.coins = []
        self.camera_x = 0
        
        self.setup_level()
        
    def setup_level(self):
        # Ground (Type 0)
        for i in range(0, 150):
            # We don't register every ground tile in AetherEngine to save performance,
            # just the collision boundaries or key elements.
            # But for the demo, let's keep it simple.
            if i % 3 == 0: # Sparse registration for engine demo
                self.register_element(StaticBox(i * 64, 576, 64, 64, color=[1,1,1,1], z=1))
            self.tiles.append((i * 64, 576, 0))
            
        # Bricks and Questions
        level_map = [
            (300, 400, 1), (364, 400, 2), (428, 400, 1), # Block trio
            (600, 350, 1), (664, 350, 1), (728, 350, 1),
            (1000, 450, 3), # Pipe
        ]
        for x, y, t in level_map:
            self.tiles.append((x, y, t))
            # Question blocks are interactive, bricks are static for now
            self.register_element(StaticBox(x, y, 64, 64, color=[1,1,1,1], z=2))

    def handle_input(self, keys_json):
        keys = json.loads(keys_json)
        
        # Horizontal Movement
        if keys.get('left'):
            self.mario_vx = -self.WALK_SPEED
            self.facing_right = False
            self.state = "walking"
        elif keys.get('right'):
            self.mario_vx = self.WALK_SPEED
            self.facing_right = True
            self.state = "walking"
        else:
            self.mario_vx *= self.FRICTION
            if abs(self.mario_vx) < 0.1: 
                self.mario_vx = 0
                self.state = "idle"
            
        # Gravity
        self.mario_vy += self.GRAVITY
        if self.mario_vy > self.FALL_CLAMP: self.mario_vy = self.FALL_CLAMP
        
        # Jumping
        if keys.get('up') and self.on_ground:
            self.mario_vy = self.JUMP_FORCE
            self.on_ground = False
            self.state = "jumping"
            
        if not self.on_ground:
            self.state = "jumping"
            
        # Collision Detection
        new_x = self.mario_x + self.mario_vx
        new_y = self.mario_y + self.mario_vy
        
        self.on_ground = False
        m_w, m_h = 48, 64 # Mario collision box
        
        for tx, ty, tt in self.tiles:
            # Simple AABB
            if self.aabb(new_x, new_y, m_w, m_h, tx, ty, 64, 64):
                # Vertical collision
                if self.mario_vy > 0 and self.mario_y + m_h <= ty + 10:
                    new_y = ty - m_h
                    self.mario_vy = 0
                    self.on_ground = True
                elif self.mario_vy < 0 and self.mario_y >= ty + 54:
                    new_y = ty + 64
                    self.mario_vy = 0
                # Horizontal collision
                else:
                    new_x = self.mario_x
                    self.mario_vx = 0
                    
        self.mario_x = new_x
        self.mario_y = new_y
        
        # Camera Follow (Smooth)
        target_cam = self.mario_x - 400
        self.camera_x += (target_cam - self.camera_x) * 0.1
        if self.camera_x < 0: self.camera_x = 0

    def aabb(self, ax, ay, aw, ah, bx, by, bw, bh):
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def get_render_state(self):
        return json.dumps({
            "mario": {
                "x": self.mario_x,
                "y": self.mario_y,
                "state": self.state,
                "facing": "right" if self.facing_right else "left"
            },
            "camera": self.camera_x,
            "tiles": self.tiles # Send tiles to JS for sprite rendering
        })
