# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Aetheris 32-Component Library — Physics-driven UI elements.

Phase A: 8 Dashboard Components
Phase B: 8 Desktop Components
Phase C: 8 Web Components
Phase D: 8 Core Physics Utilities

Each component extends DifferentialElement and defines unique
calculate_asymptotes() behavior for physics-based animation.
"""
import numpy as np
from typing import Optional, List, Dict, Any
from core.elements import DifferentialElement


# =============================================================================
# Phase A: 8 Dashboard Components
# =============================================================================

class AetherGauge(DifferentialElement):
    """Rotational spring needle gauge.

    Displays a value [0-1] via an angular needle that oscillates
    with spring physics before settling at the target angle.
    """
    _element_type = "aether_gauge"

    def __init__(self, x=0, y=0, w=120, h=120, color=(0.2, 0.6, 0.9, 1.0), z=0,
                 value=0.0, min_val=0.0, max_val=100.0, label="Gauge", sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._value = float(value)
        self._min_val = float(min_val)
        self._max_val = float(max_val)
        self._label = label
        self._needle_angle = 0.0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = np.clip(v, self._min_val, self._max_val)

    def normalized_value(self):
        return (self._value - self._min_val) / max(self._max_val - self._min_val, 1e-6)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def gauge_metadata(self):
        return {
            "type": "aether_gauge",
            "label": self._label,
            "value": self._value,
            "min": self._min_val,
            "max": self._max_val,
            "normalized": self.normalized_value(),
            "color": self._color.tolist(),
        }


class AetherSparkline(DifferentialElement):
    """Real-time minimal k-vector plot.

    Renders a sparkline chart within its bounding box.
    The vector of data points drives the visual height of the line.
    """
    _element_type = "aether_sparkline"

    def __init__(self, x=0, y=0, w=200, h=60, color=(0.2, 0.8, 0.5, 1.0), z=0,
                 data=None, label="Sparkline", sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._data = list(data) if data else [0.0]
        self._label = label

    def push_value(self, v):
        self._data.append(float(v))
        if len(self._data) > 64:
            self._data = self._data[-64:]

    @property
    def data(self):
        return list(self._data)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def sparkline_metadata(self):
        arr = np.array(self._data, dtype=np.float32)
        return {
            "type": "aether_sparkline",
            "label": self._label,
            "data": self._data,
            "min": float(arr.min()) if len(arr) else 0,
            "max": float(arr.max()) if len(arr) else 0,
            "color": self._color.tolist(),
        }


class AetherBarGroup(DifferentialElement):
    """Clamped velocity bar charts.

    Displays multiple bars with physics-driven heights.
    Each bar clamps to a maximum velocity (height).
    """
    _element_type = "aether_bar_group"

    def __init__(self, x=0, y=0, w=300, h=200, color=(0.6, 0.3, 0.8, 1.0), z=0,
                 values=None, labels=None, max_height=None, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._values = list(values) if values else [0.0]
        self._labels = list(labels) if labels else [f"Bar {i}" for i in range(len(self._values))]
        self._max_height = max_height if max_height else float(h)

    def set_values(self, values):
        self._values = [float(v) for v in values]

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def bar_metadata(self):
        return {
            "type": "aether_bar_group",
            "values": self._values,
            "labels": self._labels,
            "max_height": self._max_height,
            "bar_count": len(self._values),
            "color": self._color.tolist(),
        }


class AetherStatusOrb(DifferentialElement):
    """Pulsing frequency-based light.

    A circular indicator that pulses at a frequency proportional
    to its status value. Green=ok, Yellow=warning, Red=critical.
    """
    _element_type = "aether_status_orb"

    STATUS_COLORS = {
        "ok": (0.2, 0.8, 0.3, 1.0),
        "warning": (0.9, 0.7, 0.1, 1.0),
        "critical": (0.9, 0.2, 0.2, 1.0),
        "inactive": (0.3, 0.3, 0.35, 0.5),
    }

    def __init__(self, x=0, y=0, w=40, h=40, status="ok", z=0,
                 pulse_frequency=1.0, label="Status", sound_trigger=None):
        color = self.STATUS_COLORS.get(status, self.STATUS_COLORS["inactive"])
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._status = status
        self._pulse_frequency = float(pulse_frequency)
        self._label = label

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, s):
        self._status = s
        self._color = np.array(self.STATUS_COLORS.get(s, self.STATUS_COLORS["inactive"]), dtype=np.float32)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def orb_metadata(self):
        return {
            "type": "aether_status_orb",
            "label": self._label,
            "status": self._status,
            "pulse_frequency": self._pulse_frequency,
            "color": self._color.tolist(),
        }


class AetherHeatMap(DifferentialElement):
    """Physics-normalized grid cells.

    Displays a 2D grid where each cell's color intensity is
    normalized from raw data values.
    """
    _element_type = "aether_heatmap"

    def __init__(self, x=0, y=0, w=400, h=300, color=(0.1, 0.1, 0.15, 1.0), z=0,
                 rows=5, cols=8, data=None, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._rows = rows
        self._cols = cols
        if data is not None:
            self._data = np.array(data, dtype=np.float32).reshape(rows, cols)
        else:
            self._data = np.zeros((rows, cols), dtype=np.float32)

    def set_data(self, data):
        self._data = np.array(data, dtype=np.float32).reshape(self._rows, self._cols)

    def normalized_data(self):
        vmin = self._data.min()
        vmax = self._data.max()
        if vmax - vmin < 1e-6:
            return np.zeros_like(self._data)
        return (self._data - vmin) / (vmax - vmin)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def heatmap_metadata(self):
        return {
            "type": "aether_heatmap",
            "rows": self._rows,
            "cols": self._cols,
            "data": self._data.tolist(),
            "normalized": self.normalized_data().tolist(),
            "color": self._color.tolist(),
        }


class AetherKineticToggle(DifferentialElement):
    """Binary switch with inertia.

    A toggle that physically slides between on/off positions
    with momentum-based animation.
    """
    _element_type = "aether_kinetic_toggle"

    def __init__(self, x=0, y=0, w=80, h=40, color=(0.3, 0.3, 0.35, 1.0), z=0,
                 is_on=False, label="Toggle", sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._is_on = bool(is_on)
        self._label = label
        self._knob_ratio = 0.0 if not is_on else 1.0

    def toggle(self):
        self._is_on = not self._is_on
        self._knob_ratio = 1.0 if self._is_on else 0.0
        if self._is_on:
            self._color = np.array([0.2, 0.7, 0.3, 1.0], dtype=np.float32)
        else:
            self._color = np.array([0.3, 0.3, 0.35, 1.0], dtype=np.float32)

    @property
    def is_on(self):
        return self._is_on

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def toggle_metadata(self):
        return {
            "type": "aether_kinetic_toggle",
            "label": self._label,
            "is_on": self._is_on,
            "knob_ratio": self._knob_ratio,
            "color": self._color.tolist(),
        }


class AetherRadialProgress(DifferentialElement):
    """Circular fill with damping.

    Displays a progress ring that fills with damped spring physics.
    """
    _element_type = "aether_radial_progress"

    def __init__(self, x=0, y=0, w=100, h=100, color=(0.2, 0.6, 0.9, 1.0), z=0,
                 progress=0.0, label="Progress", sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._progress = np.clip(float(progress), 0.0, 1.0)
        self._label = label

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, p):
        self._progress = np.clip(float(p), 0.0, 1.0)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def radial_metadata(self):
        return {
            "type": "aether_radial_progress",
            "label": self._label,
            "progress": self._progress,
            "color": self._color.tolist(),
        }


class AetherValueMetric(DifferentialElement):
    """Unit-aware big number node.

    Displays a large numeric value with automatic unit formatting
    (K, M, B) and trend indicator.
    """
    _element_type = "aether_value_metric"

    def __init__(self, x=0, y=0, w=200, h=100, color=(0.9, 0.9, 0.95, 1.0), z=0,
                 value=0.0, unit="", label="Metric", trend=0.0, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._value = float(value)
        self._unit = unit
        self._label = label
        self._trend = float(trend)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = float(v)

    def formatted_value(self):
        abs_val = abs(self._value)
        if abs_val >= 1e9:
            return f"{self._value / 1e9:.1f}B"
        elif abs_val >= 1e6:
            return f"{self._value / 1e6:.1f}M"
        elif abs_val >= 1e3:
            return f"{self._value / 1e3:.1f}K"
        return f"{self._value:.1f}"

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def metric_metadata(self):
        return {
            "type": "aether_value_metric",
            "label": self._label,
            "value": self._value,
            "formatted": self.formatted_value(),
            "unit": self._unit,
            "trend": self._trend,
            "color": self._color.tolist(),
        }


# =============================================================================
# Phase B: 8 Desktop Components
# =============================================================================

class AetherWindow(DifferentialElement):
    """Container with gravity-anchored title bar.

    A draggable window with a title bar that stays anchored to the top
    via spring physics.
    """
    _element_type = "aether_window"

    def __init__(self, x=0, y=0, w=600, h=400, color=(0.12, 0.12, 0.18, 0.95), z=0,
                 title="Window", resizable=True, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._title = title
        self._resizable = resizable
        self._title_bar_h = 32.0

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def window_metadata(self):
        return {
            "type": "aether_window",
            "title": self._title,
            "resizable": self._resizable,
            "title_bar_height": self._title_bar_h,
            "color": self._color.tolist(),
        }


class AetherSideNav(DifferentialElement):
    """Sliding panel with elastic friction.

    A side navigation panel that slides in/out with elastic
    friction-based animation.
    """
    _element_type = "aether_side_nav"

    def __init__(self, x=0, y=0, w=250, h=600, color=(0.1, 0.1, 0.15, 0.98), z=0,
                 is_open=False, position="left", sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._is_open = is_open
        self._position = position

    def toggle(self):
        self._is_open = not self._is_open

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        if self._position == "left":
            target_x = 0.0 if self._is_open else -self.tensor.state[2]
        else:
            target_x = container_w - self.tensor.state[2] if self._is_open else container_w
        return np.array([target_x, self.tensor.state[1],
                         self.tensor.state[2], self.tensor.state[3]], dtype=np.float32)

    @property
    def sidenav_metadata(self):
        return {
            "type": "aether_side_nav",
            "is_open": self._is_open,
            "position": self._position,
            "color": self._color.tolist(),
        }


class AetherToolbar(DifferentialElement):
    """Horizontal button array with staggered entry.

    A toolbar that arranges child buttons horizontally with
    staggered spring-based entrance animations.
    """
    _element_type = "aether_toolbar"

    def __init__(self, x=0, y=0, w=800, h=48, color=(0.15, 0.15, 0.2, 1.0), z=0,
                 items=None, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._items = list(items) if items else []

    def add_item(self, label, icon=""):
        self._items.append({"label": label, "icon": icon})

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def toolbar_metadata(self):
        return {
            "type": "aether_toolbar",
            "items": self._items,
            "item_count": len(self._items),
            "color": self._color.tolist(),
        }


class AetherModal(DifferentialElement):
    """Scaled overlay with critical damping.

    A modal dialog that scales in from center with critically
    damped spring physics.
    """
    _element_type = "aether_modal"

    def __init__(self, x=0, y=0, w=500, h=350, color=(0.15, 0.15, 0.2, 0.97), z=0,
                 title="Modal", is_visible=False, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._title = title
        self._is_visible = is_visible
        self._scale = 1.0 if is_visible else 0.0

    def show(self):
        self._is_visible = True
        self._scale = 1.0

    def hide(self):
        self._is_visible = False
        self._scale = 0.0

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        if self._is_visible:
            cx = (container_w - self.tensor.state[2]) / 2
            cy = (container_h - self.tensor.state[3]) / 2
            return np.array([cx, cy, self.tensor.state[2], self.tensor.state[3]], dtype=np.float32)
        return np.array([container_w / 2, container_h / 2, 0.0, 0.0], dtype=np.float32)

    @property
    def modal_metadata(self):
        return {
            "type": "aether_modal",
            "title": self._title,
            "is_visible": self._is_visible,
            "scale": self._scale,
            "color": self._color.tolist(),
        }


class AetherSplitter(DifferentialElement):
    """Proportional divider with handle physics.

    A splitter that divides space proportionally and has a
    draggable handle with resistance physics.
    """
    _element_type = "aether_splitter"

    def __init__(self, x=0, y=0, w=800, h=600, color=(0.2, 0.2, 0.25, 1.0), z=0,
                 orientation="vertical", ratio=0.5, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._orientation = orientation
        self._ratio = np.clip(float(ratio), 0.1, 0.9)
        self._handle_size = 6.0

    @property
    def ratio(self):
        return self._ratio

    @ratio.setter
    def ratio(self, r):
        self._ratio = np.clip(float(r), 0.1, 0.9)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def splitter_metadata(self):
        return {
            "type": "aether_splitter",
            "orientation": self._orientation,
            "ratio": self._ratio,
            "handle_size": self._handle_size,
            "color": self._color.tolist(),
        }


class AetherScrollPanel(DifferentialElement):
    """Kinetic viewport with bounce-back edges.

    A scrollable panel with kinetic scrolling and bounce-back
    when reaching content boundaries.
    """
    _element_type = "aether_scroll_panel"

    def __init__(self, x=0, y=0, w=400, h=300, color=(0.1, 0.1, 0.15, 1.0), z=0,
                 content_h=600, scroll_y=0.0, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._content_h = float(content_h)
        self._scroll_y = float(scroll_y)
        self._max_scroll = max(content_h - h, 0.0)

    def scroll_to(self, y):
        self._scroll_y = np.clip(float(y), 0.0, self._max_scroll)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def scroll_metadata(self):
        return {
            "type": "aether_scroll_panel",
            "scroll_y": self._scroll_y,
            "content_height": self._content_h,
            "viewport_height": self.tensor.state[3],
            "max_scroll": self._max_scroll,
            "color": self._color.tolist(),
        }


class AetherContextMenu(DifferentialElement):
    """Elastic-pop item list.

    A context menu that pops in with elastic animation and
    lists items with staggered delays.
    """
    _element_type = "aether_context_menu"

    def __init__(self, x=0, y=0, w=200, h=150, color=(0.12, 0.12, 0.18, 0.97), z=0,
                 items=None, is_visible=False, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._items = list(items) if items else []
        self._is_visible = is_visible

    def add_item(self, label, shortcut=""):
        self._items.append({"label": label, "shortcut": shortcut})

    def show_at(self, x, y):
        self._x = x
        self._y = y
        self._is_visible = True

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        if not self._is_visible:
            return np.array([self.tensor.state[0], self.tensor.state[1], 0.0, 0.0], dtype=np.float32)
        return self.tensor.state.copy()

    @property
    def context_menu_metadata(self):
        return {
            "type": "aether_context_menu",
            "items": self._items,
            "is_visible": self._is_visible,
            "color": self._color.tolist(),
        }


class AetherTooltipBox(DifferentialElement):
    """Lag-follower hint (L2 clamped).

    A tooltip that follows its target with L2-norm clamped lag,
    creating a smooth trailing effect.
    """
    _element_type = "aether_tooltip"

    def __init__(self, x=0, y=0, w=150, h=40, color=(0.1, 0.1, 0.15, 0.95), z=0,
                 text="", target_x=0, target_y=0, offset_y=-10, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._text = text
        self._target_x = float(target_x)
        self._target_y = float(target_y)
        self._offset_y = float(offset_y)

    def follow(self, tx, ty):
        self._target_x = float(tx)
        self._target_y = float(ty)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        tx = self._target_x - self.tensor.state[2] / 2
        ty = self._target_y + self._offset_y - self.tensor.state[3]
        return np.array([tx, ty, self.tensor.state[2], self.tensor.state[3]], dtype=np.float32)

    @property
    def tooltip_metadata(self):
        return {
            "type": "aether_tooltip",
            "text": self._text,
            "target_x": self._target_x,
            "target_y": self._target_y,
            "color": self._color.tolist(),
        }


# =============================================================================
# Phase C: 8 Web Components
# =============================================================================

class AetherHero(DifferentialElement):
    """Full-width section with parallax support.

    A hero section that spans the full container width with
    parallax scrolling effect.
    """
    _element_type = "aether_hero"

    def __init__(self, x=0, y=0, w=1280, h=500, color=(0.05, 0.05, 0.1, 1.0), z=0,
                 title="Hero", subtitle="", parallax_factor=0.3, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._title = title
        self._subtitle = subtitle
        self._parallax_factor = float(parallax_factor)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return np.array([0.0, self.tensor.state[1], container_w, self.tensor.state[3]], dtype=np.float32)

    @property
    def hero_metadata(self):
        return {
            "type": "aether_hero",
            "title": self._title,
            "subtitle": self._subtitle,
            "parallax_factor": self._parallax_factor,
            "color": self._color.tolist(),
        }


class AetherPricingCard(DifferentialElement):
    """3D-effect hover card.

    A pricing card with 3D perspective tilt on hover state.
    """
    _element_type = "aether_pricing_card"

    def __init__(self, x=0, y=0, w=300, h=400, color=(0.12, 0.12, 0.18, 1.0), z=0,
                 plan="Basic", price=0.0, features=None, is_featured=False, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._plan = plan
        self._price = float(price)
        self._features = list(features) if features else []
        self._is_featured = is_featured
        self._hover_scale = 1.0

    def set_hover(self, is_hovering):
        self._hover_scale = 1.05 if is_hovering else 1.0

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        s = self._hover_scale
        cx = self.tensor.state[0] + self.tensor.state[2] / 2
        cy = self.tensor.state[1] + self.tensor.state[3] / 2
        nw = self.tensor.state[2] * s
        nh = self.tensor.state[3] * s
        return np.array([cx - nw / 2, cy - nh / 2, nw, nh], dtype=np.float32)

    @property
    def pricing_metadata(self):
        return {
            "type": "aether_pricing_card",
            "plan": self._plan,
            "price": self._price,
            "features": self._features,
            "is_featured": self._is_featured,
            "hover_scale": self._hover_scale,
            "color": self._color.tolist(),
        }


class AetherNavbar(DifferentialElement):
    """Sticky header with scrolling triggers.

    A navigation bar that sticks to the top and responds to
    scroll position with physics-driven transitions.
    """
    _element_type = "aether_navbar"

    def __init__(self, x=0, y=0, w=1280, h=64, color=(0.08, 0.08, 0.12, 0.95), z=0,
                 items=None, is_sticky=True, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._items = list(items) if items else []
        self._is_sticky = is_sticky
        self._scroll_offset = 0.0

    def add_item(self, label, href="#"):
        self._items.append({"label": label, "href": href})

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        y = 0.0 if self._is_sticky else self.tensor.state[1]
        return np.array([0.0, y, container_w, self.tensor.state[3]], dtype=np.float32)

    @property
    def navbar_metadata(self):
        return {
            "type": "aether_navbar",
            "items": self._items,
            "is_sticky": self._is_sticky,
            "scroll_offset": self._scroll_offset,
            "color": self._color.tolist(),
        }


class AetherToastAlert(DifferentialElement):
    """Slide-in notification with decay.

    A toast notification that slides in from the edge and
    decays (fades out) after a timeout.
    """
    _element_type = "aether_toast"

    def __init__(self, x=0, y=0, w=350, h=60, color=(0.15, 0.15, 0.2, 0.95), z=0,
                 message="", toast_type="info", duration=5.0, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._message = message
        self._toast_type = toast_type
        self._duration = float(duration)
        self._elapsed = 0.0
        self._is_visible = True

        type_colors = {
            "info": (0.2, 0.5, 0.9, 0.95),
            "success": (0.2, 0.7, 0.3, 0.95),
            "warning": (0.9, 0.7, 0.1, 0.95),
            "error": (0.9, 0.2, 0.2, 0.95),
        }
        self._type_color = type_colors.get(toast_type, type_colors["info"])

    def tick(self, dt):
        self._elapsed += dt
        if self._elapsed >= self._duration:
            self._is_visible = False

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        if not self._is_visible:
            return np.array([container_w + 100, self.tensor.state[1],
                             self.tensor.state[2], self.tensor.state[3]], dtype=np.float32)
        x = container_w - self.tensor.state[2] - 20
        y = 20
        return np.array([x, y, self.tensor.state[2], self.tensor.state[3]], dtype=np.float32)

    @property
    def toast_metadata(self):
        remaining = max(self._duration - self._elapsed, 0.0)
        return {
            "type": "aether_toast",
            "message": self._message,
            "toast_type": self._toast_type,
            "is_visible": self._is_visible,
            "remaining": remaining,
            "color": list(self._type_color),
        }


class AetherAccordionItem(DifferentialElement):
    """Physics-expanded information block.

    An accordion item that expands/collapses with spring physics.
    """
    _element_type = "aether_accordion"

    def __init__(self, x=0, y=0, w=600, h=50, color=(0.12, 0.12, 0.18, 1.0), z=0,
                 title="Section", content="", is_expanded=False, expanded_h=200, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._title = title
        self._content = content
        self._is_expanded = is_expanded
        self._collapsed_h = float(h)
        self._expanded_h = float(expanded_h)

    def toggle(self):
        self._is_expanded = not self._is_expanded

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        target_h = self._expanded_h if self._is_expanded else self._collapsed_h
        return np.array([self.tensor.state[0], self.tensor.state[1],
                         self.tensor.state[2], target_h], dtype=np.float32)

    @property
    def accordion_metadata(self):
        return {
            "type": "aether_accordion",
            "title": self._title,
            "content": self._content,
            "is_expanded": self._is_expanded,
            "color": self._color.tolist(),
        }


class AetherDrawer(DifferentialElement):
    """Side-slide menu with 'throw' physics.

    A drawer that slides from the side with momentum-based
    throw physics.
    """
    _element_type = "aether_drawer"

    def __init__(self, x=0, y=0, w=300, h=600, color=(0.1, 0.1, 0.15, 0.98), z=0,
                 is_open=False, position="left", sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._is_open = is_open
        self._position = position

    def open(self):
        self._is_open = True

    def close(self):
        self._is_open = False

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        w = self.tensor.state[2]
        if self._position == "left":
            target_x = 0.0 if self._is_open else -w
        elif self._position == "right":
            target_x = container_w - w if self._is_open else container_w
        elif self._position == "bottom":
            target_x = self.tensor.state[0]
        else:
            target_x = self.tensor.state[0]
        return np.array([target_x, self.tensor.state[1], w, self.tensor.state[3]], dtype=np.float32)

    @property
    def drawer_metadata(self):
        return {
            "type": "aether_drawer",
            "is_open": self._is_open,
            "position": self._position,
            "color": self._color.tolist(),
        }


class AetherTabs(DifferentialElement):
    """Sliding indicator highlight bar.

    A tab bar with a sliding indicator that moves to the
    active tab with spring physics.
    """
    _element_type = "aether_tabs"

    def __init__(self, x=0, y=0, w=600, h=48, color=(0.12, 0.12, 0.18, 1.0), z=0,
                 tabs=None, active_index=0, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._tabs = list(tabs) if tabs else ["Tab 1"]
        self._active_index = max(0, min(int(active_index), len(self._tabs) - 1))

    def set_active(self, index):
        self._active_index = max(0, min(int(index), len(self._tabs) - 1))

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def tabs_metadata(self):
        tab_w = self.tensor.state[2] / max(len(self._tabs), 1)
        indicator_x = self.tensor.state[0] + self._active_index * tab_w
        return {
            "type": "aether_tabs",
            "tabs": self._tabs,
            "active_index": self._active_index,
            "indicator_x": indicator_x,
            "indicator_w": tab_w,
            "color": self._color.tolist(),
        }


class AetherPillBadge(DifferentialElement):
    """Floating label with parent anchoring.

    A small pill-shaped badge anchored to a parent element's corner.
    """
    _element_type = "aether_pill_badge"

    def __init__(self, x=0, y=0, w=24, h=24, color=(0.9, 0.2, 0.2, 1.0), z=0,
                 text="0", parent=None, anchor="top-right", sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._text = str(text)
        self._parent = parent
        self._anchor = anchor

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        if self._parent is not None:
            ps = self._parent.tensor.state
            if self._anchor == "top-right":
                tx = ps[0] + ps[2] - self.tensor.state[2] / 2
                ty = ps[1] - self.tensor.state[3] / 2
            elif self._anchor == "top-left":
                tx = ps[0] - self.tensor.state[2] / 2
                ty = ps[1] - self.tensor.state[3] / 2
            elif self._anchor == "bottom-right":
                tx = ps[0] + ps[2] - self.tensor.state[2] / 2
                ty = ps[1] + ps[3] - self.tensor.state[3] / 2
            else:
                tx = ps[0] - self.tensor.state[2] / 2
                ty = ps[1] + ps[3] - self.tensor.state[3] / 2
            return np.array([tx, ty, self.tensor.state[2], self.tensor.state[3]], dtype=np.float32)
        return self.tensor.state.copy()

    @property
    def pill_metadata(self):
        return {
            "type": "aether_pill_badge",
            "text": self._text,
            "anchor": self._anchor,
            "color": self._color.tolist(),
        }


# =============================================================================
# Phase D: 8 Core Physics Utilities
# =============================================================================

class AetherSpringBox(DifferentialElement):
    """Customizable k/c elastic container.

    A box with configurable spring constant (k) and damping (c)
    for fine-tuned elastic behavior.
    """
    _element_type = "aether_spring_box"

    def __init__(self, x=0, y=0, w=200, h=100, color=(0.2, 0.6, 0.9, 1.0), z=0,
                 spring_k=10.0, damping_c=2.0, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._spring_k = float(spring_k)
        self._damping_c = float(damping_c)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def spring_box_metadata(self):
        return {
            "type": "aether_spring_box",
            "spring_k": self._spring_k,
            "damping_c": self._damping_c,
            "color": self._color.tolist(),
        }


class AetherAttractor(DifferentialElement):
    """Invisible node that pulls neighbors.

    An invisible gravitational attractor that pulls nearby elements
    toward its position with inverse-square falloff.
    """
    _element_type = "aether_attractor"

    def __init__(self, x=0, y=0, w=1, h=1, color=(0, 0, 0, 0), z=0,
                 strength=1.0, radius=200.0, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._strength = float(strength)
        self._radius = float(radius)

    def force_on(self, other_x, other_y) -> np.ndarray:
        dx = self.tensor.state[0] - other_x
        dy = self.tensor.state[1] - other_y
        dist_sq = dx * dx + dy * dy + 1.0
        dist = np.sqrt(dist_sq)
        if dist > self._radius:
            return np.array([0.0, 0.0], dtype=np.float32)
        magnitude = self._strength / dist_sq
        return np.array([dx / dist * magnitude, dy / dist * magnitude], dtype=np.float32)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def attractor_metadata(self):
        return {
            "type": "aether_attractor",
            "strength": self._strength,
            "radius": self._radius,
        }


class AetherBoundary(DifferentialElement):
    """Hard-limit collision edge.

    A boundary element that enforces hard limits on other elements,
    preventing them from crossing its edges.
    """
    _element_type = "aether_boundary"

    def __init__(self, x=0, y=0, w=800, h=600, color=(0, 0, 0, 0), z=0,
                 clamp_inside=True, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._clamp_inside = clamp_inside

    def clamp_point(self, px, py, pw, ph) -> np.ndarray:
        if self._clamp_inside:
            cx = np.clip(px, self.tensor.state[0], self.tensor.state[0] + self.tensor.state[2] - pw)
            cy = np.clip(py, self.tensor.state[1], self.tensor.state[1] + self.tensor.state[3] - ph)
        else:
            cx = px
            cy = py
        return np.array([cx, cy, pw, ph], dtype=np.float32)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def boundary_metadata(self):
        return {
            "type": "aether_boundary",
            "clamp_inside": self._clamp_inside,
            "bounds": self.tensor.state.tolist(),
        }


class AetherSurface(DifferentialElement):
    """Draggable area with customizable friction.

    A surface area that elements can be dragged on, with
    configurable friction coefficient.
    """
    _element_type = "aether_surface"

    def __init__(self, x=0, y=0, w=400, h=300, color=(0.15, 0.15, 0.2, 0.5), z=0,
                 friction=0.3, is_draggable=True, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._friction = float(friction)
        self._is_draggable = is_draggable

    def apply_friction(self, vx, vy) -> np.ndarray:
        f = self._friction
        return np.array([vx * (1 - f), vy * (1 - f)], dtype=np.float32)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def surface_metadata(self):
        return {
            "type": "aether_surface",
            "friction": self._friction,
            "is_draggable": self._is_draggable,
            "color": self._color.tolist(),
        }


class AetherBouncyLabel(DifferentialElement):
    """Text that oscillates on content change.

    A label that bounces with spring physics when its text
    content changes.
    """
    _element_type = "aether_bouncy_label"

    def __init__(self, x=0, y=0, w=200, h=40, color=(0.9, 0.9, 0.95, 1.0), z=0,
                 text="Label", font_size=16, font_family="Arial", sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._text = text
        self._font_size = font_size
        self._font_family = font_family
        self._bounce_amplitude = 0.0
        self._bounce_phase = 0.0

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if value != self._text:
            self._text = value
            self._bounce_amplitude = 8.0
            self._bounce_phase = 0.0

    def tick_bounce(self, dt):
        if self._bounce_amplitude > 0.1:
            self._bounce_phase += dt * 15.0
            self._bounce_amplitude *= np.exp(-dt * 5.0)
        else:
            self._bounce_amplitude = 0.0

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        bounce_y = self._bounce_amplitude * np.sin(self._bounce_phase)
        return np.array([self.tensor.state[0], self.tensor.state[1] + bounce_y,
                         self.tensor.state[2], self.tensor.state[3]], dtype=np.float32)

    @property
    def bouncy_label_metadata(self):
        return {
            "type": "aether_bouncy_label",
            "text": self._text,
            "font_size": self._font_size,
            "font_family": self._font_family,
            "bounce_amplitude": self._bounce_amplitude,
            "color": self._color.tolist(),
        }


class AetherMagnetLink(DifferentialElement):
    """Elements that snap together.

    A magnetic link that causes connected elements to snap together
    when within proximity threshold.
    """
    _element_type = "aether_magnet_link"

    def __init__(self, x=0, y=0, w=100, h=100, color=(0.3, 0.3, 0.35, 0.5), z=0,
                 snap_distance=20.0, linked_ids=None, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._snap_distance = float(snap_distance)
        self._linked_ids = list(linked_ids) if linked_ids else []

    def should_snap(self, other_x, other_y, other_w, other_h) -> bool:
        dx = abs((self.tensor.state[0] + self.tensor.state[2] / 2) - (other_x + other_w / 2))
        dy = abs((self.tensor.state[1] + self.tensor.state[3] / 2) - (other_y + other_h / 2))
        return dx < self._snap_distance and dy < self._snap_distance

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def magnet_metadata(self):
        return {
            "type": "aether_magnet_link",
            "snap_distance": self._snap_distance,
            "linked_ids": self._linked_ids,
            "color": self._color.tolist(),
        }


class AetherPhysicsDivider(DifferentialElement):
    """Layout spacer that resists compression.

    A divider that acts as a spring-loaded spacer, resisting
    compression when layout space is tight.
    """
    _element_type = "aether_physics_divider"

    def __init__(self, x=0, y=0, w=20, h=600, color=(0.2, 0.2, 0.25, 0.8), z=0,
                 min_size=10.0, preferred_size=40.0, stiffness=5.0, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._min_size = float(min_size)
        self._preferred_size = float(preferred_size)
        self._stiffness = float(stiffness)

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        target_w = max(self._min_size, min(self._preferred_size, self.tensor.state[2]))
        return np.array([self.tensor.state[0], self.tensor.state[1],
                         target_w, self.tensor.state[3]], dtype=np.float32)

    @property
    def divider_metadata(self):
        return {
            "type": "aether_physics_divider",
            "min_size": self._min_size,
            "preferred_size": self._preferred_size,
            "stiffness": self._stiffness,
            "color": self._color.tolist(),
        }


class AetherTeleport(DifferentialElement):
    """Cross-fade element for state transitions.

    An element that cross-fades between two states using
    physics-driven opacity transitions.
    """
    _element_type = "aether_teleport"

    def __init__(self, x=0, y=0, w=200, h=200, color=(0.2, 0.6, 0.9, 1.0), z=0,
                 state_a=None, state_b=None, blend=0.0, sound_trigger=None):
        super().__init__(x, y, w, h, color, z, sound_trigger=sound_trigger)
        self._state_a = state_a if state_a else {}
        self._state_b = state_b if state_b else {}
        self._blend = np.clip(float(blend), 0.0, 1.0)

    def set_blend(self, b):
        self._blend = np.clip(float(b), 0.0, 1.0)

    def teleport_to_b(self):
        self._blend = 1.0

    def teleport_to_a(self):
        self._blend = 0.0

    def blended_state(self):
        result = {}
        for key in set(list(self._state_a.keys()) + list(self._state_b.keys())):
            a = self._state_a.get(key, 0.0)
            b = self._state_b.get(key, 0.0)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                result[key] = a * (1 - self._blend) + b * self._blend
            else:
                result[key] = b if self._blend > 0.5 else a
        return result

    def calculate_asymptotes(self, container_w, container_h) -> np.ndarray:
        return self.tensor.state.copy()

    @property
    def teleport_metadata(self):
        return {
            "type": "aether_teleport",
            "blend": self._blend,
            "state_a": self._state_a,
            "state_b": self._state_b,
            "blended": self.blended_state(),
            "color": self._color.tolist(),
        }
