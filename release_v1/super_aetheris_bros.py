#!/usr/bin/env python3
"""
Super Aetheris Bros — RUST ENGINE EDITION.
El juego usa el motor de físicas Rust (aether_pyo3) compilado con Rayon
para todos los elementos visuales del nivel, mientras la lógica
de control del jugador y colisiones corre en Python.

Arquitectura:
  ┌─────────────┐     ┌──────────────────────────┐
  │  Game Logic  │────▶│  Aetheris Rust Engine     │
  │  (Python)    │     │  (Rayon parallelized)     │
  │  - Input     │     │  - StateTensor per block  │
  │  - Collision │     │  - Hooke's Law restoring  │
  │  - Camera    │◀────│  - Euler integration      │
  └─────────────┘     │  - Aether-Guard safety    │
                      └──────────────────────────┘
                                │
                      ┌─────────▼─────────┐
                      │  Tkinter Canvas    │
                      │  (60 FPS render)   │
                      └───────────────────┘

Controles:
  ← →  o  A D   : Mover
  Espacio / ↑ / W : Saltar
  R               : Reiniciar nivel
  ESC             : Salir
"""
import sys
import os
import math
import time
import tkinter as tk

# ─── Cargar motor Rust ────────────────────────────────────
# Activar venv si estamos fuera de él
venv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv')
if os.path.exists(venv_path):
    site_packages = os.path.join(venv_path, 'lib', 'python3.12', 'site-packages')
    if site_packages not in sys.path:
        sys.path.insert(0, site_packages)

try:
    import aether_pyo3
    RUST_ENGINE = True
    print("✅ Motor Rust (aether_pyo3) cargado — Rayon parallelization activo")
except ImportError:
    RUST_ENGINE = False
    print("⚠️  Motor Rust no disponible. Usa: cd aetheris-rust && maturin develop --release")
    print("    Ejecutando en modo Python puro (más lento)")

# ─── Constantes ───────────────────────────────────────────
SW, SH = 900, 640
TILE = 32
GROUND_Y = SH - 2 * TILE

GRAVITY = 0.50
JUMP_VEL = -12.5
MOVE_SPD = 4.2
MAX_FALL = 12.0
ACCEL = 0.6
DECEL = 0.35

# ─── Paleta NES ──────────────────────────────────────────
P = {
    'sky':       '#5c94fc', 'sky_top':   '#3870d8',
    'gnd':       '#d27d2c', 'gnd_dark':  '#9e4b14', 'gnd_top': '#e8a040',
    'brick':     '#c46420', 'brick_ln':  '#8a3c10', 'brick_hi': '#dc8c48',
    'qb':        '#fca044', 'qb_brd':    '#e45c10', 'qb_dead': '#806040',
    'pipe':      '#20a820', 'pipe_d':    '#0c7c0c', 'pipe_lip':'#50d850',
    'pipe_hi':   '#78e878',
    'coin':      '#fccc3c', 'coin_brd':  '#d09020',
    'hat':       '#e02020', 'blue':      '#2038ec', 'skin': '#fcbcb0',
    'shoe':      '#6c3400',
    'gmb':       '#c06000', 'gmb_d':     '#804000', 'gmb_eye': '#ffffff',
    'cloud':     '#f8f8f8', 'cloud_sh':  '#d0d8f0',
    'hill':      '#88d818',
    'bush':      '#20a820',
    'pole':      '#a0a0a0', 'pole_hi':   '#c8c8c8', 'flag': '#20c820',
    'txt':       '#ffffff', 'txt_sh':    '#000000',
    'title_r':   '#e03020', 'title_y':   '#fca044',
    'star':      '#fcfc00',
}


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def aabb(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


# ═══════════════════════════════════════════════════════════
#  PARTÍCULAS (mini sistema para efectos visuales)
# ═══════════════════════════════════════════════════════════
class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'color', 'size']
    def __init__(self, x, y, vx, vy, life, color, size=3):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.color = color
        self.size = size


# ═══════════════════════════════════════════════════════════
#  MOTOR RUST: Registrar elementos del nivel
# ═══════════════════════════════════════════════════════════
class RustLevelEngine:
    """Wrapper que registra elementos del nivel en el motor Rust."""

    def __init__(self):
        if RUST_ENGINE:
            self.engine = aether_pyo3.AetherEngine()
        else:
            self.engine = None
        self.element_map = {}   # z_index -> tipo de elemento
        self._next_z = 0

    def add_static_box(self, x, y, w, h, r, g, b, a=1.0, tag='block'):
        """Registra un StaticBox en el motor Rust."""
        z = self._next_z
        self._next_z += 1
        if self.engine:
            color = aether_pyo3.Vec4(r, g, b, a)
            self.engine.register_static_box(x, y, w, h, color, z)
        self.element_map[z] = tag
        return z

    def tick(self, win_w, win_h):
        """Ejecuta un tick del motor Rust y retorna datos de renderizado."""
        if self.engine:
            return self.engine.tick(win_w, win_h)
        return []

    @property
    def count(self):
        if self.engine:
            return self.engine.element_count()
        return 0


# ═══════════════════════════════════════════════════════════
#  JUEGO PRINCIPAL
# ═══════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        self.root = tk.Tk()
        engine_label = "RUST ENGINE" if RUST_ENGINE else "Python Fallback"
        self.root.title(f"Super Aetheris Bros — [{engine_label}]")
        self.root.resizable(False, False)
        self.root.configure(bg='black')

        self.cv = tk.Canvas(self.root, width=SW, height=SH,
                            bg=P['sky'], highlightthickness=0)
        self.cv.pack()

        self.keys = set()
        self.root.bind('<KeyPress>',   lambda e: self.keys.add(e.keysym.lower()))
        self.root.bind('<KeyRelease>', lambda e: self.keys.discard(e.keysym.lower()))

        self.frame = 0
        self.particles = []
        self.score_popups = []
        self.show_title = True
        self.fps_samples = []
        self.last_time = time.perf_counter()
        self.running = True
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.reset()
        self._loop()
        self.root.mainloop()

    def _on_close(self):
        self.running = False
        self.root.destroy()

    # ─── Reset ───────────────────────────────────────────
    def reset(self):
        self.cam = 0.0
        self.score = 0
        self.coin_n = 0
        self.dead = False
        self.won = False
        self.death_t = 0

        self.mx, self.my = 96.0, float(GROUND_Y - 36)
        self.mw, self.mh = 24, 36
        self.mvx, self.mvy = 0.0, 0.0
        self.on_gnd = False
        self.face = 1
        self.walk_frame = 0
        self.walk_timer = 0
        self.was_on_ground = True

        self.particles.clear()
        self.score_popups.clear()

        self._build_level()

    # ─── Nivel ───────────────────────────────────────────
    def _build_level(self):
        T = TILE
        self.rust_engine = RustLevelEngine()

        self.grounds = [(0, 69*T), (72*T, 42*T)]

        # Bloques con física Rust
        self.blocks = []
        for xt, yt, bt in [
            (16,13,'Q'),
            (20,13,'B'),(21,13,'Q'),(22,13,'B'),(23,13,'Q'),(24,13,'B'),
            (22,9,'Q'),
            (77,13,'Q'),(78,13,'B'),(79,13,'B'),
            (80,9,'B'),(81,9,'B'),(82,9,'B'),(83,9,'B'),
            (84,9,'B'),(85,9,'B'),(86,9,'B'),(87,9,'B'),
            (91,13,'Q'),(92,13,'B'),(93,13,'B'),(94,9,'Q'),
        ]:
            cr, cg, cb = hex_to_rgb(P['qb'] if bt == 'Q' else P['brick'])
            rust_z = self.rust_engine.add_static_box(
                xt*T, yt*T, T, T, cr/255.0, cg/255.0, cb/255.0, tag=bt)
            self.blocks.append([xt*T, yt*T, bt, 1 if bt=='Q' else 0, 0, rust_z])

        # Tubos en Rust
        self.pipes = []
        for xt, ht in [(28,2),(38,3),(46,4),(57,4)]:
            cr, cg, cb = hex_to_rgb(P['pipe'])
            rust_z = self.rust_engine.add_static_box(
                xt*T, GROUND_Y-ht*T, 2*T, ht*T, cr/255.0, cg/255.0, cb/255.0, tag='pipe')
            self.pipes.append([xt*T, GROUND_Y-ht*T, 2*T, ht*T, rust_z])

        # Monedas flotantes en Rust
        self.coins = []
        for xt, yt in [(17,10),(22,6),(78,9),(79,9),(83,6),(84,6),(85,6)]:
            cr, cg, cb = hex_to_rgb(P['coin'])
            rust_z = self.rust_engine.add_static_box(
                xt*T+8, yt*T+4, 16, 24, cr/255.0, cg/255.0, cb/255.0, tag='coin')
            self.coins.append([xt*T+8, yt*T+4, True, rust_z])

        # Escaleras (Stairs) - Bloques sólidos al final
        self.stairs = []
        for stack_x in range(100, 104):
            height = stack_x - 99
            for iy in range(height):
                rx, ry = stack_x * T, GROUND_Y - (iy + 1) * T
                cr, cg, cb = hex_to_rgb(P['brick'])
                rust_z = self.rust_engine.add_static_box(rx, ry, T, T, cr/255.0, cg/255.0, cb/255.0, tag='stair')
                self.stairs.append([rx, ry, T, T, rust_z])

        self.pop_coins = []

        self.goombas = []
        for xt in [22, 40, 51, 52, 80, 82, 97, 98]:
            self.goombas.append([float(xt*T), float(GROUND_Y-30), -1.2, True, 0])

        self.clouds = [(8,2,3),(19,1,2),(36,2,4),(55,1,3),(75,2,2),(90,1,3)]
        self.hills  = [(0,5),(16,3),(48,5),(64,3),(90,4)]
        self.bushes = [(11,3),(41,2),(73,3),(95,2)]
        self.flag_x = 105 * T

        print(f"🦀 Motor Rust tiene {self.rust_engine.count} elementos registrados "
              f"(bloques + tubos + monedas)")

    def _solids(self):
        s = []
        for gx, gw in self.grounds:
            s.append((gx, GROUND_Y, gw, 2*TILE))
        for b in self.blocks:
            s.append((b[0], b[1], TILE, TILE))
        for p in self.pipes:
            s.append((p[0], p[1], p[2], p[3]))
        for st in self.stairs:
            s.append((st[0], st[1], st[2], st[3]))
        return s

    # ─── Partículas ──────────────────────────────────────
    def _spawn_particles(self, x, y, color, count=8, speed=3.0):
        import random
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed * 0.3, speed)
            self.particles.append(Particle(
                x, y, math.cos(angle)*spd*random.uniform(0.5,1.5),
                math.sin(angle)*spd - random.uniform(1,3),
                random.randint(15,35), color, random.randint(2,5)))

    def _spawn_popup(self, x, y, text, color=P['txt']):
        self.score_popups.append([x, y, text, 45, color])

    # ─── Loop ────────────────────────────────────────────
    def _loop(self):
        if not self.running:
            return

        try:
            now = time.perf_counter()
            dt = now - self.last_time
            self.last_time = now
            if dt > 0:
                self.fps_samples.append(1.0/dt)
                if len(self.fps_samples) > 60:
                    self.fps_samples.pop(0)

            if self.show_title:
                self._render_title()
                if any(k in self.keys for k in ('space', 'return', 'up', 'w')):
                    self.show_title = False
            else:
                # Tick del motor Rust (procesa física de elementos del nivel)
                self.rust_render_data = self.rust_engine.tick(SW * 3, SH)
                self._update()
                self._render()

            self.frame += 1
            if self.running:
                self.root.after(16, self._loop)
        except tk.TclError:
            # Captura errores si el canvas se destruye durante el renderizado
            self.running = False
        except Exception as e:
            print(f"Error en el loop: {e}")
            self.running = False

    # ─── Lógica ──────────────────────────────────────────
    def _update(self):
        if self.won:
            if 'r' in self.keys: self.reset()
            return

        for p in self.particles[:]:
            p.x += p.vx; p.y += p.vy; p.vy += 0.15; p.life -= 1
            if p.life <= 0: self.particles.remove(p)

        for sp in self.score_popups[:]:
            sp[1] -= 1.2; sp[3] -= 1
            if sp[3] <= 0: self.score_popups.remove(sp)

        for pc in self.pop_coins[:]:
            pc[1] += pc[2]; pc[2] += 0.5; pc[3] -= 1
            if pc[3] <= 0: self.pop_coins.remove(pc)

        if self.dead:
            self.death_t += 1
            self.mvy += GRAVITY; self.my += self.mvy
            if 'r' in self.keys: self.reset()
            return

        if 'escape' in self.keys:
            self.root.destroy(); return

        # Input
        target_vx = 0.0
        if 'left' in self.keys or 'a' in self.keys:
            target_vx = -MOVE_SPD; self.face = -1
        if 'right' in self.keys or 'd' in self.keys:
            target_vx = MOVE_SPD;  self.face = 1

        if abs(target_vx) > 0:
            self.mvx += (target_vx - self.mvx) * ACCEL
        else:
            self.mvx *= (1.0 - DECEL)
            if abs(self.mvx) < 0.1: self.mvx = 0.0

        if abs(self.mvx) > 0.5 and self.on_gnd:
            self.walk_timer += 1
            if self.walk_timer >= 6:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % 3
        else:
            self.walk_frame = 0

        if ('space' in self.keys or 'up' in self.keys or 'w' in self.keys) and self.on_gnd:
            self.mvy = JUMP_VEL
            self.on_gnd = False
            self._spawn_particles(self.mx+self.mw/2, self.my+self.mh, '#d0d0d0', 5, 1.5)
        
        # Salto variable: si se suelta el botón de salto, Mario cae más rápido (frenado)
        if not ('space' in self.keys or 'up' in self.keys or 'w' in self.keys) and self.mvy < -4:
            self.mvy = -4

        self.mvy = min(self.mvy + GRAVITY, MAX_FALL)
        solids = self._solids()

        # Horizontal collision
        self.mx += self.mvx
        for sx, sy, sw, sh in solids:
            if aabb(self.mx, self.my, self.mw, self.mh, sx, sy, sw, sh):
                if self.mvx > 0: self.mx = sx - self.mw
                elif self.mvx < 0: self.mx = sx + sw
                self.mvx = 0

        # Vertical collision
        self.was_on_ground = self.on_gnd
        self.on_gnd = False
        self.my += self.mvy
        for sx, sy, sw, sh in solids:
            if aabb(self.mx, self.my, self.mw, self.mh, sx, sy, sw, sh):
                if self.mvy > 0:
                    self.my = sy - self.mh; self.mvy = 0; self.on_gnd = True
                    if not self.was_on_ground and self.mvy > 3:
                        self._spawn_particles(self.mx+self.mw/2, sy, '#d0c0a0', 4, 1.0)
                elif self.mvy < 0:
                    self.my = sy + sh; self.mvy = 1.0
                    self._bump(sx, sy)

        if self.my > SH + 60: self._die()

        # Coins
        for c in self.coins:
            if c[2] and aabb(self.mx, self.my, self.mw, self.mh, c[0], c[1], 16, 24):
                c[2] = False; self.score += 200; self.coin_n += 1
                self._spawn_particles(c[0]+8, c[1]+12, P['coin'], 10, 2.5)
                self._spawn_popup(c[0], c[1]-10, '+200', P['coin'])

        # Goombas
        for g in self.goombas:
            if not g[3]:
                if g[4] > 0: g[4] -= 1
                continue
            g[0] += g[2]
            for sx, sy, sw, sh in solids:
                if aabb(g[0], g[1], 28, 30, sx, sy, sw, sh):
                    g[2] *= -1; g[0] += g[2] * 3; break
            if aabb(self.mx, self.my, self.mw, self.mh, g[0], g[1], 28, 30):
                if self.mvy > 0 and self.my + self.mh < g[1] + 20:
                    g[3] = False; g[4] = 25; self.mvy = JUMP_VEL * 0.45
                    self.score += 100
                    self._spawn_particles(g[0]+14, g[1]+15, P['gmb'], 6)
                    self._spawn_popup(g[0]+5, g[1]-10, '+100')
                else:
                    self._die()

        for b in self.blocks:
            if b[4] > 0: b[4] -= 1

        if self.mx + self.mw > self.flag_x:
            self.won = True; self.score += 5000
            self._spawn_particles(self.flag_x, 100, P['star'], 25, 5)

        target = self.mx - SW * 0.35
        self.cam = max(self.cam, max(0.0, target))
        self.mx = max(self.cam, self.mx)

    def _bump(self, bx, by):
        for b in self.blocks:
            if abs(b[0]-bx) < 2 and abs(b[1]-by) < 2:
                b[4] = 8
                if b[2] == 'Q' and b[3] > 0:
                    b[3] -= 1; b[2] = 'D'
                    self.score += 200; self.coin_n += 1
                    self.pop_coins.append([b[0]+8, b[1]-16, -7.0, 22])
                    self._spawn_particles(b[0]+16, b[1], P['coin'], 8, 2)
                    self._spawn_popup(b[0]+5, b[1]-20, '+200', P['coin'])
                else:
                    self._spawn_particles(b[0]+16, b[1]+TILE, '#c0a080', 4, 1)
                break

    def _die(self):
        self.dead = True; self.death_t = 0; self.mvy = JUMP_VEL * 0.8
        self._spawn_particles(self.mx+self.mw/2, self.my+self.mh/2, P['hat'], 15, 4)

    # ─── Pantalla de título ──────────────────────────────
    def _render_title(self):
        cv = self.cv; cv.delete('all')
        f = self.frame

        for i in range(0, SH, 4):
            t = i / SH
            sr = int(92 - t * 30); sg = int(148 - t * 40); sb = int(252 - t * 20)
            cv.create_rectangle(0, i, SW, i+4, fill=f'#{sr:02x}{sg:02x}{sb:02x}', outline='')

        cv.create_rectangle(0, GROUND_Y, SW, SH, fill=P['gnd'], outline='')
        cv.create_rectangle(0, GROUND_Y+TILE, SW, SH, fill=P['gnd_dark'], outline='')

        title_y = 100 + math.sin(f * 0.04) * 6
        cv.create_text(SW//2+3, title_y+3, text='SUPER AETHERIS BROS.',
                       fill=P['txt_sh'], font=('Arial', 36, 'bold'))
        cv.create_text(SW//2, title_y, text='SUPER AETHERIS BROS.',
                       fill=P['title_r'], font=('Arial', 36, 'bold'))

        # Motor badge
        if RUST_ENGINE:
            badge = '🦀 Rust Engine (Rayon) — 17.2x más rápido'
            badge_col = '#ff8040'
        else:
            badge = '🐍 Python Engine (Fallback)'
            badge_col = '#60a0ff'
        cv.create_text(SW//2, title_y + 48, text=badge,
                       fill=badge_col, font=('Arial', 13, 'bold'))

        cv.create_text(SW//2, title_y + 75, text='— Powered by Aetheris UI Engine v1.6 —',
                       fill=P['title_y'], font=('Arial', 11, 'italic'))

        qx, qy = SW//2-16, 240
        bounce = math.sin(f * 0.08) * 4
        cv.create_rectangle(qx, qy+bounce, qx+TILE, qy+TILE+bounce,
                            fill=P['qb'], outline=P['qb_brd'], width=3)
        cv.create_text(qx+TILE//2, qy+TILE//2+bounce, text='?',
                       fill=P['qb_brd'], font=('Arial',18,'bold'))

        if (f // 30) % 2 == 0:
            cv.create_text(SW//2, 360, text='Presiona ESPACIO para jugar',
                           fill=P['txt'], font=('Arial', 16, 'bold'))

        cv.create_text(SW//2, 420, text='← → Mover  |  Espacio Saltar  |  R Reiniciar  |  ESC Salir',
                       fill='#a0a8c0', font=('Arial', 11))
        cv.create_text(SW//2, SH-70, text='© 2026 Carlos Ivan Obando Aure',
                       fill='#b0b0c0', font=('Arial', 10))
        cv.create_text(SW//2, SH-50, text='Aetheris UI — Physics-as-UI Engine',
                       fill='#808090', font=('Arial', 9))

    # ─── Renderizado ─────────────────────────────────────
    def _render(self):
        cv = self.cv; cv.delete('all')
        cx = self.cam; T = TILE; f = self.frame

        # Sky gradient
        for i in range(0, SH, 6):
            t = i / SH
            sr = int(92 - t*25); sg = int(148 - t*35); sb = int(252 - t*15)
            cv.create_rectangle(0, i, SW, i+6, fill=f'#{sr:02x}{sg:02x}{sb:02x}', outline='')

        # Hills (parallax)
        for hx, hw in self.hills:
            x = hx*T - cx*0.35; w = hw*T
            layers = max(1, int(w*0.35/6))
            for i in range(layers):
                lw = w - i*(w/layers); lx = x+(w-lw)/2
                shade = min(255, 128+i*8)
                cv.create_rectangle(lx, GROUND_Y-i*6-6, lx+lw, GROUND_Y-i*6,
                                    fill=f'#{shade//2:02x}{shade:02x}{shade//8:02x}', outline='')

        # Clouds (parallax)
        for clx, cly, clw in self.clouds:
            x = clx*T - cx*0.15; y = cly*T+30; w = clw*T
            cv.create_oval(x+6, y, x+w-6, y+T-2, fill=P['cloud'], outline='')
            cv.create_oval(x, y+8, x+w, y+T-6, fill=P['cloud'], outline='')

        # Bushes
        for bx, bw in self.bushes:
            x = bx*T - cx; w = bw*T
            cv.create_oval(x-6, GROUND_Y-24, x+w+6, GROUND_Y+4, fill=P['bush'], outline='')

        # Ground
        for gx, gw in self.grounds:
            sx = gx - cx
            cv.create_rectangle(sx, GROUND_Y, sx+gw, GROUND_Y+4, fill=P['gnd_top'], outline='')
            cv.create_rectangle(sx, GROUND_Y+4, sx+gw, SH, fill=P['gnd'], outline='')
            cv.create_rectangle(sx, GROUND_Y+T, sx+gw, SH, fill=P['gnd_dark'], outline='')

        # Pipes
        for p in self.pipes:
            sx = p[0]-cx; lip = 14
            cv.create_rectangle(sx+8, p[1]+lip, sx+p[2]-8, p[1]+p[3], fill=P['pipe'], outline='')
            cv.create_rectangle(sx+8, p[1]+lip, sx+16, p[1]+p[3], fill=P['pipe_d'], outline='')
            cv.create_rectangle(sx+p[2]-16, p[1]+lip, sx+p[2]-8, p[1]+p[3], fill=P['pipe_hi'], outline='')
            cv.create_rectangle(sx, p[1], sx+p[2], p[1]+lip, fill=P['pipe_lip'], outline='')

        # Blocks
        for b in self.blocks:
            sx = b[0]-cx; bump = -(min(b[4],5)) if b[4]>0 else 0; by = b[1]+bump
            if b[2] == 'Q':
                glow = 0.5 + math.sin(f*0.12)*0.3
                cr,cg,cb = hex_to_rgb(P['qb'])
                gr = int(min(255,cr+glow*60)); gg = int(min(255,cg+glow*40)); gb = int(min(255,cb+glow*20))
                cv.create_rectangle(sx+1,by+1,sx+T-1,by+T-1,fill=f'#{gr:02x}{gg:02x}{gb:02x}',
                                    outline=P['qb_brd'],width=2)
                cv.create_text(sx+T//2, by+T//2-1, text='?', fill=P['qb_brd'],font=('Arial',16,'bold'))
            elif b[2] == 'B':
                cv.create_rectangle(sx+1,by+1,sx+T-1,by+T-1,fill=P['brick'],outline=P['brick_ln'],width=2)
                cv.create_line(sx+1,by+T//2,sx+T-1,by+T//2,fill=P['brick_ln'])
                cv.create_line(sx+T//2,by+1,sx+T//2,by+T//2,fill=P['brick_ln'])
            elif b[2] == 'D':
                cv.create_rectangle(sx+1,by+1,sx+T-1,by+T-1,fill=P['qb_dead'],outline=P['brick_ln'],width=2)
        
        # Stairs
        for st in self.stairs:
            sx, sy = st[0] - cx, st[1]
            cv.create_rectangle(sx+1, sy+1, sx+T-1, sy+T-1, fill=P['brick'], outline=P['brick_ln'], width=1)

        # Coins
        for c in self.coins:
            if not c[2]: continue
            sx = c[0]-cx
            rot = abs(math.sin(f*0.08)); cw = max(2, int(14*rot)); center_x = sx+8
            cv.create_rectangle(center_x-cw//2, c[1]+2, center_x+cw//2, c[1]+22,
                                fill=P['coin'], outline=P['coin_brd'], width=2)

        # Pop coins
        for pc in self.pop_coins:
            sx = pc[0]-cx
            cv.create_rectangle(sx, pc[1], sx+12, pc[1]+16, fill=P['coin'], outline=P['coin_brd'])

        # Goombas
        for g in self.goombas:
            sx = g[0]-cx
            if g[3]:
                cv.create_oval(sx-3, g[1]-2, sx+31, g[1]+18, fill=P['gmb'], outline='')
                cv.create_rectangle(sx+2, g[1]+14, sx+26, g[1]+28, fill=P['gmb'], outline='')
                cv.create_rectangle(sx, g[1]+22, sx+10, g[1]+30, fill=P['gmb_d'], outline='')
                cv.create_rectangle(sx+18, g[1]+22, sx+28, g[1]+30, fill=P['gmb_d'], outline='')
                cv.create_oval(sx+4, g[1]+4, sx+12, g[1]+12, fill=P['gmb_eye'], outline='')
                cv.create_oval(sx+16, g[1]+4, sx+24, g[1]+12, fill=P['gmb_eye'], outline='')
                cv.create_oval(sx+6, g[1]+6, sx+10, g[1]+10, fill='#000', outline='')
                cv.create_oval(sx+18, g[1]+6, sx+22, g[1]+10, fill='#000', outline='')
                cv.create_line(sx+3,g[1]+3,sx+11,g[1]+5,fill=P['gmb_d'],width=2)
                cv.create_line(sx+25,g[1]+3,sx+17,g[1]+5,fill=P['gmb_d'],width=2)
            elif g[4] > 0:
                cv.create_rectangle(sx, g[1]+24, sx+28, g[1]+30, fill=P['gmb_d'], outline='')

        # Flag
        fx = self.flag_x - cx
        cv.create_rectangle(fx+3, 80, fx+7, GROUND_Y, fill=P['pole'], outline='')
        flag_wave = math.sin(f * 0.15) * 3
        cv.create_polygon(fx+3,82, fx-20+flag_wave,90, fx-18+flag_wave,108, fx-16,116, fx+3,110,
                          fill=P['flag'], outline='')
        cv.create_oval(fx, 72, fx+10, 82, fill=P['coin'], outline=P['coin_brd'])

        # Particles
        for p in self.particles:
            sx = p.x - cx; alpha = max(0.3, p.life/35.0); s = max(1, int(p.size*alpha))
            cv.create_rectangle(sx-s, p.y-s, sx+s, p.y+s, fill=p.color, outline='')

        # Score popups
        for sp in self.score_popups:
            sx = sp[0]-cx
            if sp[3] > 10:
                cv.create_text(sx+1,sp[1]+1,text=sp[2],fill=P['txt_sh'],font=('Arial',12,'bold'))
                cv.create_text(sx,sp[1],text=sp[2],fill=sp[4],font=('Arial',12,'bold'))

        # Mario
        if not self.dead or self.death_t < 90:
            sx = self.mx - cx; sy = self.my
            air = 0 if self.on_gnd else (1 if self.mvy < 0 else 2)
            self._draw_mario(cv, sx, sy, self.face, self.walk_frame, air)

        # HUD
        cv.create_rectangle(0, 0, SW, 36, fill='#000000', outline='')
        cv.create_rectangle(0, 36, SW, 38, fill='#333333', outline='')

        cv.create_text(14, 8, text='MARIO', fill=P['txt'], font=('Courier',11,'bold'), anchor='nw')
        cv.create_text(14, 22, text=f'{self.score:06d}', fill=P['txt'], font=('Courier',10), anchor='nw')

        cv.create_rectangle(SW//2-32, 10, SW//2-22, 24, fill=P['coin'], outline=P['coin_brd'])
        cv.create_text(SW//2-16, 10, text=f'×{self.coin_n:02d}', fill=P['txt'],
                       font=('Courier',12,'bold'), anchor='nw')

        cv.create_text(SW-14, 8, text='WORLD', fill=P['txt'], font=('Courier',11,'bold'), anchor='ne')
        cv.create_text(SW-14, 22, text='1-1', fill=P['txt'], font=('Courier',10), anchor='ne')

        # FPS + Engine badge
        avg_fps = sum(self.fps_samples) / max(1, len(self.fps_samples))
        engine_tag = '🦀 RUST' if RUST_ENGINE else '🐍 PY'
        cv.create_text(SW//2, 8, text=f'{engine_tag} | {avg_fps:.0f} FPS | {self.rust_engine.count} elementos',
                       fill='#60ff60' if RUST_ENGINE else '#60a0ff',
                       font=('Courier', 9, 'bold'), anchor='n')

        # Overlays
        if self.dead:
            cv.create_text(SW//2+2, SH//2-18, text='GAME OVER',
                           fill=P['txt_sh'], font=('Arial',34,'bold'))
            cv.create_text(SW//2, SH//2-20, text='GAME OVER',
                           fill=P['hat'], font=('Arial',34,'bold'))
            cv.create_text(SW//2, SH//2+24, text='Presiona R para reiniciar',
                           fill=P['txt'], font=('Arial',14))
        elif self.won:
            cv.create_text(SW//2+2, SH//2-18, text='¡NIVEL COMPLETO!',
                           fill=P['txt_sh'], font=('Arial',32,'bold'))
            cv.create_text(SW//2, SH//2-20, text='¡NIVEL COMPLETO!',
                           fill=P['star'], font=('Arial',32,'bold'))
            cv.create_text(SW//2, SH//2+24, text=f'Puntaje Final: {self.score}',
                           fill=P['txt'], font=('Arial',16))

    # ─── Mario sprite ────────────────────────────────────
    def _draw_mario(self, cv, sx, sy, face, walk_f, air):
        w, h = self.mw, self.mh
        # Gorra
        if face == 1:
            cv.create_rectangle(sx, sy+2, sx+w+6, sy+10, fill=P['hat'], outline='')
        else:
            cv.create_rectangle(sx-6, sy+2, sx+w, sy+10, fill=P['hat'], outline='')
        cv.create_rectangle(sx+2, sy, sx+w-2, sy+4, fill=P['hat'], outline='')
        # Cara
        cv.create_rectangle(sx+2, sy+10, sx+w-2, sy+18, fill=P['skin'], outline='')
        if face == 1:
            cv.create_rectangle(sx+15, sy+11, sx+19, sy+15, fill='#000', outline='')
        else:
            cv.create_rectangle(sx+5, sy+11, sx+9, sy+15, fill='#000', outline='')
        # Bigote
        if face == 1:
            cv.create_rectangle(sx+10, sy+15, sx+w, sy+17, fill='#6c3400', outline='')
        else:
            cv.create_rectangle(sx, sy+15, sx+14, sy+17, fill='#6c3400', outline='')
        # Cuerpo
        cv.create_rectangle(sx, sy+18, sx+w, sy+26, fill=P['hat'], outline='')
        arm_off = [0,-2,2][walk_f] if air==0 else 0
        if air == 1:
            cv.create_rectangle(sx-4, sy+14, sx+2, sy+22, fill=P['skin'], outline='')
            cv.create_rectangle(sx+w-2, sy+14, sx+w+4, sy+22, fill=P['skin'], outline='')
        elif air == 2:
            cv.create_rectangle(sx-3, sy+20, sx+3, sy+28, fill=P['skin'], outline='')
            cv.create_rectangle(sx+w-3, sy+20, sx+w+3, sy+28, fill=P['skin'], outline='')
        else:
            cv.create_rectangle(sx-3, sy+18+arm_off, sx+3, sy+26+arm_off, fill=P['skin'], outline='')
            cv.create_rectangle(sx+w-3, sy+18-arm_off, sx+w+3, sy+26-arm_off, fill=P['skin'], outline='')
        # Overol
        cv.create_rectangle(sx+2, sy+26, sx+w-2, sy+h-4, fill=P['blue'], outline='')
        cv.create_rectangle(sx+5, sy+22, sx+8, sy+28, fill=P['blue'], outline='')
        cv.create_rectangle(sx+w-8, sy+22, sx+w-5, sy+28, fill=P['blue'], outline='')
        cv.create_rectangle(sx+8, sy+27, sx+10, sy+29, fill=P['coin'], outline='')
        cv.create_rectangle(sx+w-10, sy+27, sx+w-8, sy+29, fill=P['coin'], outline='')
        # Zapatos
        if air == 1:
            cv.create_rectangle(sx+2, sy+h-6, sx+10, sy+h, fill=P['shoe'], outline='')
            cv.create_rectangle(sx+w-10, sy+h-6, sx+w-2, sy+h, fill=P['shoe'], outline='')
        elif air == 2:
            cv.create_rectangle(sx+4, sy+h-6, sx+w-4, sy+h, fill=P['shoe'], outline='')
        else:
            if walk_f == 1:
                cv.create_rectangle(sx, sy+h-6, sx+10, sy+h, fill=P['shoe'], outline='')
                cv.create_rectangle(sx+w-8, sy+h-8, sx+w, sy+h-2, fill=P['shoe'], outline='')
            elif walk_f == 2:
                cv.create_rectangle(sx+2, sy+h-8, sx+12, sy+h-2, fill=P['shoe'], outline='')
                cv.create_rectangle(sx+w-10, sy+h-6, sx+w-2, sy+h, fill=P['shoe'], outline='')
            else:
                cv.create_rectangle(sx+2, sy+h-6, sx+10, sy+h, fill=P['shoe'], outline='')
                cv.create_rectangle(sx+w-10, sy+h-6, sx+w-2, sy+h, fill=P['shoe'], outline='')


# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    Game()
