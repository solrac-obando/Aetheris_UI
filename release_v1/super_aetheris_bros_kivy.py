#!/usr/bin/env python3
"""
Super Aetheris Bros — 2026 NEXT-GEN EDITION. (KIVY + RUST)
Vitrina tecnológica de Aetheris UI.
Características: 3D Elements, Parallax 5-layer, Glow HDR, Camera Shake, Physics Weight.
"""

import os
import sys
import math
import time
import random

# ─── Entorno ───
venv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv')
if os.path.exists(venv_path):
    site_packages = os.path.join(venv_path, 'lib', 'python3.12', 'site-packages')
    if site_packages not in sys.path:
        sys.path.insert(0, site_packages)

try:
    import aether_pyo3
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Ellipse, InstructionGroup, Line, PushMatrix, PopMatrix, Translate, Rotate, Scale
from kivy.properties import NumericProperty
from kivy.utils import get_color_from_hex

# ─── Configuración ───
SW, SH = 900, 640
TILE = 32
GROUND_Y_TL = SH - 2 * TILE

# Físicas de "Peso" 2026
GRAVITY = 0.52
JUMP_VEL = -13.2
MOVE_SPD = 5.2
MAX_FALL = 12.0
FRICTION = 0.85
ACCEL = 0.9
DECEL = 0.35

P = {
    'sky_top': get_color_from_hex('#0a1128'),
    'sky_mid': get_color_from_hex('#1c315e'),
    'sky_bot': get_color_from_hex('#5c94fc'),
    'gnd': get_color_from_hex('#d27d2c'),
    'brick': get_color_from_hex('#c46420'),
    'qb_glow': get_color_from_hex('#ffcc33'),
    'coin_gold': get_color_from_hex('#fccc3c'),
    'mario_red': get_color_from_hex('#e02020'),
    'mario_blue': get_color_from_hex('#1520a6'),
    'mario_skin': get_color_from_hex('#fcbcb0'),
    'neon_green': get_color_from_hex('#39ff14'),
    'glass': (1, 1, 1, 0.15),
}
def aabb(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

class ParticleSystem:
    def __init__(self):
        self.particles = [] # [x, y, vx, vy, life, color, size]
    
    def spawn(self, x, y, color, count=5, speed=2.0):
        for _ in range(count):
            self.particles.append([
                x, y, 
                random.uniform(-speed, speed), 
                random.uniform(-speed, speed) - 2,
                random.randint(10, 30), color, random.randint(2, 5)
            ])
            
    def update(self):
        for p in self.particles[:]:
            p[0] += p[2]; p[1] += p[3]; p[3] += 0.2
            p[4] -= 1
            if p[4] <= 0: self.particles.remove(p)

class GameWidget(Widget):
    coin_rot = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self.keyboard.bind(on_key_down=self._on_key_down)
        self.keyboard.bind(on_key_up=self._on_key_up)
        self.pressed_keys = set()
        
        self.frame = 0
        self.shake = 0
        self.ps = ParticleSystem()
        self.engine = aether_pyo3.AetherEngine() if RUST_AVAILABLE else None
        
        self.reset()
        Clock.schedule_interval(self.update, 1.0/60.0)

    def _keyboard_closed(self):
        self.keyboard = None

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        self.pressed_keys.add(keycode[1])
        if keycode[1] == 'escape': App.get_running_app().stop()
        if keycode[1] == 'r': self.reset()
        return True

    def _on_key_up(self, keyboard, keycode):
        if keycode[1] in self.pressed_keys: self.pressed_keys.remove(keycode[1])
        return True

    def reset(self):
        self.cam_x = 0.0
        self.mx, self.my = 120.0, float(GROUND_Y_TL - 40)
        self.mvx, self.mvy = 0.0, 0.0
        self.on_gnd = False
        self.face = 1
        self.squash_y = 1.0
        self.score = 0
        self.dead = False
        self.won = False
        
        self._build_level()

    def _build_level(self):
        T = TILE
        self.blocks = []
        for xt, yt, bt in [(20,13,'Q'), (24,13,'B'), (25,13,'Q'), (26,13,'B'), (40,9,'Q'), (60,13,'Q')]:
            self.blocks.append([xt*T, yt*T, bt, 1, 0]) # x, y, type, state, bump_t
            if self.engine: self.engine.register_static_box(xt*T, yt*T, T, T, aether_pyo3.Vec4(*P['qb_glow']), len(self.blocks))
            
        self.coins = [[300, GROUND_Y_TL-120], [600, GROUND_Y_TL-150], [1200, GROUND_Y_TL-120]]
        self.goombas = [[800, GROUND_Y_TL-32, -2.0, True], [1500, GROUND_Y_TL-32, -2.0, True]]
        
        # Parallax Data: layer_speed, list_of_objects (x, y, w, h, color)
        self.stars = [[random.randint(0, 5000), random.randint(400, 600)] for _ in range(100)]
        self.clouds = [[i*600 + random.randint(0, 200), 450, 120, 40] for i in range(10)]
        self.hills = [[i*400, GROUND_Y_TL-80, 200, 80] for i in range(15)]

    def update(self, dt):
        if self.dead: return
        self.coin_rot = (self.frame * 8) % 360
        self.frame += 1
        if self.shake > 0: self.shake -= 1
        
        # Physics Input
        target_vx = 0
        i = self.pressed_keys
        if 'left' in i or 'a' in i: target_vx = -MOVE_SPD; self.face = -1
        if 'right' in i or 'd' in i: target_vx = MOVE_SPD; self.face = 1
        
        self.mvx += (target_vx - self.mvx) * ACCEL
        if target_vx == 0: self.mvx *= FRICTION
        
        if ('up' in i or 'w' in i or 'space' in i) and self.on_gnd:
            self.mvy = JUMP_VEL
            self.on_gnd = False
            self.ps.spawn(self.mx+12, self.my+38, (1,1,1,0.5), 8)
            self.squash_y = 1.3
            
        # Variable Jump & Gravity
        if not ('up' in i or 'w' in i or 'space' in i) and self.mvy < -4: self.mvy = -4
        self.mvy = min(self.mvy + GRAVITY, MAX_FALL)
        
        # Movement
        self.mx += self.mvx
        self.my += self.mvy
        
        # Pseudo-Collision
        self.on_gnd = False
        if self.my >= GROUND_Y_TL - 40:
            if self.mvy > 5: self.ps.spawn(self.mx+12, GROUND_Y_TL, (1,1,1,0.3), 10); self.squash_y = 0.7
            self.my = GROUND_Y_TL - 40; self.mvy = 0; self.on_gnd = True
            
        for b in self.blocks:
            if aabb(self.mx+4, self.my, 16, 40, b[0], b[1], 32, 32):
                if self.mvy < 0 and self.my > b[1]+15: # Bump from below
                    self.my = b[1]+32; self.mvy = 1; b[4] = 8; self.shake = 5
                    self.ps.spawn(b[0]+16, b[1]+16, P['qb_glow'], 15)
                    self.score += 50
                elif self.mvy > 0 and self.my < b[1]: # Land on top
                    self.my = b[1]-40; self.mvy = 0; self.on_gnd = True
                elif self.mvx > 0: self.mx = b[0]-20
                else: self.mx = b[0]+32
        
        # Camera (Modern Smooth Follow)
        target_cam = self.mx - SW * 0.4
        self.cam_x += (target_cam - self.cam_x) * 0.12 # Agresivo but smooth
        self.cam_x = max(0, self.cam_x)
        
        self.ps.update()
        self.squash_y += (1.0 - self.squash_y) * 0.2
        if self.engine: self.engine.tick(SW*5, SH)
        self.draw()

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            # ─── PROFUNDIDAD: PARALLAX ───
            # Fondo (Cielo Dinámico)
            Color(*P['sky_mid'])
            Rectangle(pos=(0, 0), size=(SW, SH))
            
            # Capa 1: Estrellas (0.05x)
            Color(1,1,1,0.8)
            for s in self.stars:
                Ellipse(pos=( (s[0] - self.cam_x*0.05) %SW, s[1] ), size=(2,2))
                
            # Capa 2: Nubes (0.2x)
            for c in self.clouds:
                Color(1,1,1,0.3)
                Ellipse(pos=(c[0]-self.cam_x*0.2, c[1]), size=(c[2], c[3]))
                
            # Capa 3: Montañas (0.4x)
            for h in self.hills:
                Color(0.2, 0.4, 0.3, 0.6)
                Rectangle(pos=(h[0]-self.cam_x*0.4, SH-h[1]-h[3]), size=(h[2], h[3]))

            # ─── PLANO DE JUEGO ───
            PushMatrix()
            # Camera Shake
            if self.shake > 0: Translate(random.uniform(-4,4), random.uniform(-4,4), 0)
            Translate(-self.cam_x, 0, 0)
            
            # Suelo (Glossy Ground)
            Color(*P['gnd'])
            Rectangle(pos=(0, 0), size=(5000, 64))
            Color(0,0,0,0.3)
            Rectangle(pos=(0, 60), size=(5000, 4)) # Linea de borde
            
            # Bloques interactivos con f-3D
            for b in self.blocks:
                ky = SH - b[1] - TILE
                bump = -b[4] if b[4] > 0 else 0
                if b[4] > 0: b[4] -= 1
                
                # Resplandor HDR (Glow)
                pulse = 0.5 + math.sin(self.frame*0.15)*0.5
                Color(*P['qb_glow'][:3], 0.2 * pulse)
                Ellipse(pos=(b[0]-16, ky-16+bump), size=(64, 64))
                
                # Cubo
                Color(*P['brick'])
                Rectangle(pos=(b[0], ky+bump), size=(TILE, TILE))
                Color(1,1,1,0.2); Line(rectangle=(b[0], ky+bump, TILE, TILE), width=2)
                
            # Monedas 3D (Rotación Real)
            for c in self.coins:
                ky = SH - c[1]
                PushMatrix()
                Translate(c[0]+16, ky+16, 0)
                Rotate(angle=self.coin_rot, axis=(0,1,0)) # ROTACIÓN 3D
                Color(*P['coin_gold'])
                Ellipse(pos=(-8, -12), size=(16, 24))
                Color(1,1,1,0.6); Line(ellipse=(-8, -12, 16, 24), width=1)
                PopMatrix()

            # Partículas
            for p in self.ps.particles:
                Color(*p[5][:3], p[4]/30.0)
                Rectangle(pos=(p[0], SH-p[1]), size=(p[6], p[6]))

            # MODERN MARIO NEXT-GEN
            self.draw_2026_mario(self.mx, SH - self.my - 40)
            
            PopMatrix()
            
            # ─── UI: NEO-GLASSMORPHISM ───
            # ─── UI: NEO-GLASSMORPHISM (2026 HUD) ───
            Color(0,0,0,0.5)
            Rectangle(pos=(0, SH-80), size=(SW, 80))
            
            # Glass Panel
            Color(1,1,1,0.1)
            Rectangle(pos=(20, SH-70), size=(240, 60))
            Color(1,1,1,0.3)
            Line(rectangle=(20, SH-70, 240, 60), width=1)
            
            # Metrics Indicator
            Color(0.2, 0.8, 1, 1) # Dev Speed Color
            Rectangle(pos=(SW-200, SH-50), size=(180, 4))
            Color(*P['neon_green'])
            Ellipse(pos=(SW-215, SH-53), size=(10, 10))
            
            # Milestone Badge
            Color(*P['neon_green'], 0.6)
            Line(rectangle=(SW//2-100, SH-50, 200, 25), width=2)

            
    def draw_2026_mario(self, x, y):
        f = self.face
        s_y = self.squash_y
        
        PushMatrix()
        Translate(x+12, y, 0)
        Scale(1.0, s_y, 1.0) # SQUASH & STRETCH
        
        # Cuerpo
        Color(*P['mario_blue'])
        Rectangle(pos=(-8, 6), size=(16, 18))
        
        # Cabeza (High-detail Ellipses)
        Color(*P['mario_skin'])
        Ellipse(pos=(-10, 24), size=(20, 18))
        
        # Gorra HDR
        Color(*P['mario_red'])
        Ellipse(pos=(-10, 36), size=(20, 10))
        Rectangle(pos=( (8 if f==1 else -16), 37), size=(12, 4))
        
        # Ojos Modernos
        Color(1,1,1,1)
        Ellipse(pos=( (6 if f==1 else -10), 32), size=(5, 7))
        Color(0,0,0,1)
        Ellipse(pos=( (8 if f==1 else -8), 33), size=(2, 4))
        
        # Detalle de Zapatos
        Color(0.2, 0.1, 0, 1)
        Rectangle(pos=(-11, 0), size=(10, 8))
        Rectangle(pos=(1, 0), size=(10, 8))
        
        PopMatrix()

class MarioNextGen(App):
    def build(self):
        return GameWidget()

if __name__ == '__main__':
    MarioNextGen().run()
