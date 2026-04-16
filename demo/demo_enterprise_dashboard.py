# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Aetheris Enterprise Dashboard — Commercial Demo v1.0

A production-ready server infrastructure monitoring dashboard that showcases
the Aetheris UI framework's capabilities for enterprise clients.

Features:
- Real-time server monitoring with physics-driven layout
- Alert visualization (critical alerts sink to bottom)
- Interactive node inspection (click for details)
- Bilingual support (EN/ES)
- Professional dark-mode UI with glass-morphism effects

Usage:
    python3 demo/demo_enterprise_dashboard.py          # Kivy desktop
    python3 demo/demo_enterprise_dashboard.py --web    # Web hybrid
"""

import os, sys, time, json, random
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

# ── Core imports ───────────────────────────────────────────────────────────
from core.engine import AetherEngine
from core.aether_math import StateTensor, MAX_VELOCITY, clamp_magnitude, EPSILON
from core.elements import DifferentialElement
from core.state_manager import StateManager

# ── Constants ──────────────────────────────────────────────────────────────
WIN_W, WIN_H = 1440.0, 900.0
TOOLBAR_H = 60.0
NODE_RADIUS = 28.0
MAX_SERVERS = 24

# ── Localization ───────────────────────────────────────────────────────────
LANG = {
    "en": {
        "title": "AETHERIS ENTERPRISE",
        "subtitle": "Infrastructure Monitoring Dashboard",
        "servers": "Servers",
        "alerts": "Active Alerts",
        "cpu": "CPU Load",
        "memory": "Memory",
        "network": "Network I/O",
        "status": "System Status",
        "healthy": "All Systems Operational",
        "warning": "Warning — Elevated Load",
        "critical": "CRITICAL — Immediate Action Required",
        "lang": "Español",
        "refresh": "Refresh",
        "sort_alerts": "Sort by Severity",
        "reset": "Reset View",
        "node_details": "Node Details",
        "uptime": "Uptime",
        "region": "Region",
        "last_check": "Last Check",
    },
    "es": {
        "title": "AETHERIS ENTERPRISE",
        "subtitle": "Panel de Monitoreo de Infraestructura",
        "servers": "Servidores",
        "alerts": "Alertas Activas",
        "cpu": "Carga CPU",
        "memory": "Memoria",
        "network": "Red I/O",
        "status": "Estado del Sistema",
        "healthy": "Todos los Sistemas Operativos",
        "warning": "Advertencia — Carga Elevada",
        "critical": "CRÍTICO — Acción Inmediata Requerida",
        "lang": "English",
        "refresh": "Actualizar",
        "sort_alerts": "Ordenar por Severidad",
        "reset": "Restablecer Vista",
        "node_details": "Detalles del Nodo",
        "uptime": "Tiempo Activo",
        "region": "Región",
        "last_check": "Última Verificación",
    },
}

# ── Server Data Generator ──────────────────────────────────────────────────
REGIONS = ["US-East", "US-West", "EU-West", "EU-Central", "APAC-Tokyo", "APAC-Sydney"]
SERVER_NAMES = [
    "api-gateway", "auth-service", "user-db", "cache-redis", "worker-01",
    "worker-02", "ml-inference", "search-engine", "cdn-origin", "load-balancer",
    "payment-svc", "notification", "analytics-db", "logging-svc", "config-svc",
    "scheduler", "backup-svc", "monitoring", "ci-runner", "git-proxy",
    "storage-svc", "queue-mq", "gateway-ws", "admin-panel",
]


class ServerNode(DifferentialElement):
    """Represents a server as a physics-driven monitoring node."""

    def __init__(self, x: float, y: float, name: str, region: str, z: int = 0):
        size = NODE_RADIUS * 2
        super().__init__(x, y, size, size, color=(0.2, 0.6, 0.3, 0.9), z=z)
        self.name = name
        self.region = region
        self.cpu = random.uniform(10, 40)
        self.memory = random.uniform(30, 60)
        self.network = random.uniform(100, 500)
        self.uptime = random.randint(1, 365)
        self.status = "healthy"  # healthy, warning, critical
        self._target = np.array([x, y, size, size], dtype=np.float32)
        self._alert_weight = 0.0  # Additional gravity for alerts

    def calculate_asymptotes(self, cw: float, ch: float) -> np.ndarray:
        return self._target.copy()

    def update_metrics(self) -> None:
        """Simulate real-time metric changes."""
        self.cpu = max(5, min(98, self.cpu + random.gauss(0, 8)))
        self.memory = max(20, min(95, self.memory + random.gauss(0, 3)))
        self.network = max(50, min(2000, self.network + random.gauss(0, 50)))

        # Determine status based on metrics
        if self.cpu > 85 or self.memory > 90:
            self.status = "critical"
            self._alert_weight = 15.0
            self._color[:] = np.array([0.9, 0.15, 0.15, 0.95], dtype=np.float32)
        elif self.cpu > 70 or self.memory > 80:
            self.status = "warning"
            self._alert_weight = 5.0
            self._color[:] = np.array([0.9, 0.7, 0.1, 0.9], dtype=np.float32)
        else:
            self.status = "healthy"
            self._alert_weight = 0.0
            self._color[:] = np.array([0.15, 0.7, 0.3, 0.9], dtype=np.float32)

    def apply_alert_gravity(self) -> np.ndarray:
        """Apply downward force proportional to alert severity."""
        if self._alert_weight > 0:
            return np.array([0.0, self._alert_weight, 0.0, 0.0], dtype=np.float32)
        return np.zeros(4, dtype=np.float32)


# ── Enterprise Dashboard Engine ────────────────────────────────────────────
class EnterpriseDashboard:
    """Main engine for the enterprise monitoring dashboard."""

    def __init__(self, num_servers: int = 16):
        self.engine = AetherEngine()
        self.servers: List[ServerNode] = []
        self._selected_server: Optional[ServerNode] = None
        self._sort_mode = False
        self._last_w, self._last_h = WIN_W, WIN_H
        self._build_cluster(num_servers)

    def _build_cluster(self, n: int) -> None:
        """Create server nodes arranged in a physics cluster."""
        n = min(n, MAX_SERVERS)
        cols = int(np.ceil(np.sqrt(n)))
        spacing = 120.0
        start_x = (WIN_W - (cols - 1) * spacing) / 2
        start_y = TOOLBAR_H + 80

        for i in range(n):
            col = i % cols
            row = i // cols
            x = start_x + col * spacing
            y = start_y + row * spacing
            name = SERVER_NAMES[i % len(SERVER_NAMES)]
            region = REGIONS[i % len(REGIONS)]
            server = ServerNode(x, y, name, region, z=i)
            self.servers.append(server)
            self.engine.register_element(server)

        # Initialize metrics
        for s in self.servers:
            s.update_metrics()

    def update_all_metrics(self) -> None:
        """Simulate real-time metric updates for all servers."""
        for server in self.servers:
            server.update_metrics()

    def apply_sort_forces(self) -> None:
        """Apply forces to sort servers by alert severity (critical sinks)."""
        cx = WIN_W / 2
        for server in self.servers:
            # Alert gravity
            alert_force = server.apply_alert_gravity()
            server.tensor.apply_force(alert_force)

            # Center pull
            dx = cx - float(server.tensor.state[0])
            server.tensor.apply_force(np.array([dx * 0.003, 0.0, 0.0, 0.0], dtype=np.float32))

    def apply_normal_forces(self) -> None:
        """Normal mode: servers stay near their grid positions."""
        for server in self.servers:
            tx = float(server._target[0])
            ty = float(server._target[1])
            dx = tx - float(server.tensor.state[0])
            dy = ty - float(server.tensor.state[1])
            server.tensor.apply_force(np.array([dx * 0.05, dy * 0.05, 0.0, 0.0], dtype=np.float32))

    def tick(self, win_w: float = WIN_W, win_h: float = WIN_H) -> float:
        """Single physics tick."""
        t0 = time.perf_counter()

        if self._sort_mode:
            self.apply_sort_forces()
        else:
            self.apply_normal_forces()

        for server in self.servers:
            server.tensor.velocity *= np.float32(0.88)
            server.tensor.velocity = clamp_magnitude(server.tensor.velocity, MAX_VELOCITY)
            server.tensor.euler_integrate(1.0 / 60.0, viscosity=0.12)

        self.engine.tick(win_w, win_h)
        return (time.perf_counter() - t0) * 1000.0

    def handle_teleportation(self, new_w: float, new_h: float) -> None:
        """Handle window resize."""
        if self._last_w == 0:
            self._last_w, self._last_h = new_w, new_h
            return
        sx = new_w / self._last_w if self._last_w > 0 else 1.0
        sy = new_h / self._last_h if self._last_h > 0 else 1.0
        for server in self.servers:
            server.tensor.state[0] = np.float32(float(server.tensor.state[0]) * sx)
            server.tensor.state[1] = np.float32(float(server.tensor.state[1]) * sy)
            server._target[0] = np.float32(float(server._target[0]) * sx)
            server._target[1] = np.float32(float(server._target[1]) * sy)
        self._last_w, self._last_h = new_w, new_h

    def get_server_at(self, x: float, y: float) -> Optional[ServerNode]:
        """Find server node at cursor position."""
        for server in reversed(self.servers):
            s = server.tensor.state
            if float(s[0]) <= x <= float(s[0]) + float(s[2]) and \
               float(s[1]) <= y <= float(s[1]) + float(s[3]):
                return server
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        total = len(self.servers)
        healthy = sum(1 for s in self.servers if s.status == "healthy")
        warning = sum(1 for s in self.servers if s.status == "warning")
        critical = sum(1 for s in self.servers if s.status == "critical")
        avg_cpu = np.mean([s.cpu for s in self.servers])
        avg_mem = np.mean([s.memory for s in self.servers])
        return {
            "total": total,
            "healthy": healthy,
            "warning": warning,
            "critical": critical,
            "avg_cpu": avg_cpu,
            "avg_mem": avg_mem,
        }


# ── Kivy Renderer ──────────────────────────────────────────────────────────
def _run_kivy():
    os.environ["KIVY_LOG_LEVEL"] = "warning"
    from kivy.app import App
    from kivy.uix.widget import Widget
    from kivy.uix.label import Label
    from kivy.graphics import Color, Ellipse, Rectangle, Line
    from kivy.core.window import Window
    from kivy.clock import Clock

    Window.size = (int(WIN_W), int(WIN_H))
    Window.clearcolor = (0.04, 0.05, 0.08, 1.0)
    Window.title = "Aetheris Enterprise Dashboard"

    dashboard = EnterpriseDashboard(num_servers=16)
    lang_code = "en"
    update_counter = 0

    def _(key):
        return LANG[lang_code].get(key, key)

    class DashboardWidget(Widget):
        def __init__(self, **kw):
            super().__init__(**kw)
            self._title = Label(text=_("title"), pos=(20, WIN_H - 30),
                                color=(0.5, 0.55, 0.7, 1), font_size=18, bold=True)
            self._subtitle = Label(text=_("subtitle"), pos=(22, WIN_H - 55),
                                   color=(0.35, 0.38, 0.45, 1), font_size=11)
            self._stats = Label(text="", pos=(20, 10),
                                color=(0.4, 0.42, 0.5, 1), font_size=10)
            self._details = Label(text="", pos=(WIN_W - 320, WIN_H - 80),
                                  color=(0.7, 0.72, 0.8, 1), font_size=11,
                                  halign="left", valign="top", size=(300, 150))
            for lbl in [self._title, self._subtitle, self._stats, self._details]:
                self.add_widget(lbl)
            Clock.schedule_interval(self._tick, 1.0 / 60.0)

        def _tick(self, dt):
            nonlocal update_counter, lang_code
            cw, ch = self.width or WIN_W, self.height or WIN_H

            # Update metrics every 2 seconds
            update_counter += 1
            if update_counter % 120 == 0:
                dashboard.update_all_metrics()

            if abs(cw - dashboard._last_w) > 10 or abs(ch - dashboard._last_h) > 10:
                dashboard.handle_teleportation(cw, ch)

            dashboard.tick(cw, ch)

            # Render
            self.canvas.clear()
            with self.canvas:
                # Connection lines between nearby servers
                Color(0.15, 0.18, 0.25, 0.3)
                for i, s1 in enumerate(dashboard.servers):
                    for s2 in dashboard.servers[i+1:]:
                        dx = float(s1.tensor.state[0]) - float(s2.tensor.state[0])
                        dy = float(s1.tensor.state[1]) - float(s2.tensor.state[1])
                        dist = np.sqrt(dx*dx + dy*dy)
                        if dist < 200:
                            Line(points=[
                                float(s1.tensor.state[0]) + NODE_RADIUS,
                                float(s1.tensor.state[1]) + NODE_RADIUS,
                                float(s2.tensor.state[0]) + NODE_RADIUS,
                                float(s2.tensor.state[1]) + NODE_RADIUS,
                            ], width=1)

                # Server nodes
                for server in dashboard.servers:
                    s = server.tensor.state
                    cx = float(s[0]) + NODE_RADIUS
                    cy = float(s[1]) + NODE_RADIUS

                    # Glow
                    r, g, b, a = server._color
                    Color(r, g, b, 0.15)
                    Ellipse(pos=(cx - NODE_RADIUS - 6, cy - NODE_RADIUS - 6),
                            size=(NODE_RADIUS * 2 + 12, NODE_RADIUS * 2 + 12))

                    # Main circle
                    Color(r, g, b, a)
                    Ellipse(pos=(float(s[0]), float(s[1])),
                            size=(float(s[2]), float(s[3])))

                    # Inner highlight
                    Color(1, 1, 1, 0.1)
                    Ellipse(pos=(cx - NODE_RADIUS + 4, cy - NODE_RADIUS + 4),
                            size=(NODE_RADIUS * 2 - 8, NODE_RADIUS - 4))

                    # Server name
                    Color(0.9, 0.9, 0.95, 0.9)
                    Rectangle(pos=(cx - 40, cy - NODE_RADIUS - 18), size=(80, 14))
                    Color(0.05, 0.05, 0.08, 1)
                    Rectangle(pos=(cx - 39, cy - NODE_RADIUS - 17), size=(78, 12))

            # Update stats
            stats = dashboard.get_stats()
            status_text = _("healthy")
            if stats["critical"] > 0:
                status_text = _("critical")
            elif stats["warning"] > 0:
                status_text = _("warning")

            self._stats.text = (
                f"{_('servers')}: {stats['total']}  •  "
                f"{_('alerts')}: {stats['warning']}W / {stats['critical']}C  •  "
                f"CPU: {stats['avg_cpu']:.0f}%  •  "
                f"MEM: {stats['avg_mem']:.0f}%  •  "
                f"{_('status')}: {status_text}"
            )

            # Update details panel
            if dashboard._selected_server:
                srv = dashboard._selected_server
                self._details.text = (
                    f"┌─ {_('node_details')} ──────────┐\n"
                    f"│  Name:    {srv.name}\n"
                    f"│  Region:  {srv.region}\n"
                    f"│  Status:  {srv.status.upper()}\n"
                    f"│  CPU:     {srv.cpu:.1f}%\n"
                    f"│  Memory:  {srv.memory:.1f}%\n"
                    f"│  Network: {srv.network:.0f} MB/s\n"
                    f"│  {_('uptime')}:  {srv.uptime} days\n"
                    f"└──────────────────────────────┘"
                )
            else:
                self._details.text = ""

        def on_touch_down(self, touch):
            srv = dashboard.get_server_at(touch.x, touch.y)
            if srv:
                dashboard._selected_server = srv
                touch.grab(self)
                return True
            else:
                dashboard._selected_server = None
            return super().on_touch_down(touch)

    class DashboardApp(App):
        def build(self):
            return DashboardWidget(size=Window.size)

    DashboardApp().run()


# ── Web Hybrid Mode ────────────────────────────────────────────────────────
def _run_web():
    """Run dashboard in web hybrid mode."""
    from core.web_app import WebApp
    from core.web_elements import WebCard, WebText

    dashboard = EnterpriseDashboard(num_servers=16)
    app = WebApp(title="Aetheris Enterprise", width=WIN_W, height=WIN_H)

    # Create web elements for each server
    for i, server in enumerate(dashboard.servers):
        col = i % 4
        row = i // 4
        x = 100 + col * 300
        y = 100 + row * 180

        card = WebCard(
            title=server.name,
            x=x, y=y, w=250, h=140,
            mass=1.0 + server._alert_weight,
            z=i
        )
        app.add(card)

        # Metrics text
        metrics = WebText(
            text=f"CPU: {server.cpu:.0f}% | MEM: {server.memory:.0f}%",
            x=x + 10, y=y + 30, w=230, h=20,
            font_size=11, z=i + 100
        )
        app.add(metrics)

    print("[Enterprise Dashboard] Web mode — open http://localhost:8081 in browser")
    app.run(port=8080)


# ── Entry Point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--web" in sys.argv:
        _run_web()
    else:
        _run_kivy()
