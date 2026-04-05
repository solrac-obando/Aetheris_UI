# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
UI Builder - Translates JSON Intent into registered AetherEngine elements.

Uses a registry pattern for scalable element creation. Each component type
registers a factory function that receives (props, color, builder) and returns
a DifferentialElement instance.
"""
import numpy as np
from typing import Dict, List, Optional, Callable
from core.elements import DifferentialElement, StaticBox, SmartPanel, SmartButton, FlexibleTextNode, CanvasTextNode, DOMTextNode
from core.engine import AetherEngine
from core.tensor_compiler import TensorCompiler
from core.data_bridge import BaseAetherProvider, min_max_scale


class UIBuilder:
    """Builds AetherEngine element graphs from JSON intent definitions."""

    ELEMENT_TYPES = {
        'static_box': StaticBox,
        'smart_panel': SmartPanel,
        'smart_button': SmartButton,
        'flexible_text': FlexibleTextNode,
        'canvas_text': CanvasTextNode,
    }

    DEFAULTS = {
        'static_box': {'x': 0, 'y': 0, 'w': 100, 'h': 100, 'color': [1, 1, 1, 1], 'z': 0},
        'smart_panel': {'x': 0, 'y': 0, 'w': 100, 'h': 100, 'color': [0.9, 0.2, 0.6, 0.8], 'z': 1, 'padding': 0.05},
        'smart_button': {'offset_x': 0, 'offset_y': 0, 'offset_w': 100, 'offset_h': 50, 'color': [0.8, 0.8, 0.2, 1.0], 'z': 2},
        'flexible_text': {'x': 0, 'y': 10, 'w': 200, 'h': 40, 'color': [0.2, 0.6, 0.9, 1.0], 'z': 2, 'text': 'Text'},
        'canvas_text': {'x': 0, 'y': 10, 'w': 200, 'h': 40, 'color': [1.0, 1.0, 1.0, 1.0], 'z': 5, 'text': 'Text', 'font_size': 24, 'font_family': 'Arial'},
        'dom_text': {'x': 0, 'y': 10, 'w': 200, 'h': 50, 'color': [0, 0, 0, 0], 'z': 10, 'text': 'Text', 'font_size': 16, 'font_family': 'Arial', 'text_color': [1.0, 1.0, 1.0, 1.0]},
    }

    def __init__(self):
        self._element_refs: Dict[str, DifferentialElement] = {}
        self._registry: Dict[str, Callable] = {}
        self._register_builtin_factories()

    def register_factory(self, elem_type: str, factory: Callable) -> None:
        """Register a factory function for a custom element type.

        Factory signature: factory(props: dict, color: tuple, builder: UIBuilder) -> DifferentialElement
        """
        self._registry[elem_type] = factory

    def _register_builtin_factories(self) -> None:
        """Register all built-in element factories."""
        self.register_factory('static_box', self._factory_static_box)
        self.register_factory('smart_panel', self._factory_smart_panel)
        self.register_factory('smart_button', self._factory_smart_button)
        self.register_factory('flexible_text', self._factory_flexible_text)
        self.register_factory('canvas_text', self._factory_canvas_text)
        self.register_factory('dom_text', self._factory_dom_text)

        self._register_component_factories()

    def _register_component_factories(self) -> None:
        """Register all 32 component factories."""
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

        self.register_factory('aether_gauge',
            lambda p, c, b: AetherGauge(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), value=float(p.get('value', 0)),
                min_val=float(p.get('min_val', 0)), max_val=float(p.get('max_val', 100)),
                label=str(p.get('text_content', p.get('label', 'Gauge')))))

        self.register_factory('aether_sparkline',
            lambda p, c, b: AetherSparkline(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), data=p.get('data'),
                label=str(p.get('text_content', p.get('label', 'Sparkline')))))

        self.register_factory('aether_bar_group',
            lambda p, c, b: AetherBarGroup(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), values=p.get('values'), labels=p.get('labels'),
                max_height=p.get('max_height')))

        self.register_factory('aether_status_orb',
            lambda p, c, b: AetherStatusOrb(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                status=str(p.get('status', 'ok')), z=int(p.get('z', 0)),
                pulse_frequency=float(p.get('pulse_frequency', 1.0)),
                label=str(p.get('text_content', p.get('label', 'Status')))))

        self.register_factory('aether_heatmap',
            lambda p, c, b: AetherHeatMap(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), rows=int(p.get('rows', 5)),
                cols=int(p.get('cols', 8)), data=p.get('data')))

        self.register_factory('aether_kinetic_toggle',
            lambda p, c, b: AetherKineticToggle(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), is_on=bool(p.get('is_on', False)),
                label=str(p.get('text_content', p.get('label', 'Toggle')))))

        self.register_factory('aether_radial_progress',
            lambda p, c, b: AetherRadialProgress(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), progress=float(p.get('progress', 0)),
                label=str(p.get('text_content', p.get('label', 'Progress')))))

        self.register_factory('aether_value_metric',
            lambda p, c, b: AetherValueMetric(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), value=float(p.get('value', 0)),
                unit=str(p.get('unit', '')), label=str(p.get('text_content', p.get('label', 'Metric'))),
                trend=float(p.get('trend', 0))))

        self.register_factory('aether_window',
            lambda p, c, b: AetherWindow(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), title=str(p.get('text_content', p.get('title', 'Window'))),
                resizable=bool(p.get('resizable', True))))

        self.register_factory('aether_side_nav',
            lambda p, c, b: AetherSideNav(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), is_open=bool(p.get('is_open', False)),
                position=str(p.get('position', 'left'))))

        self.register_factory('aether_toolbar',
            lambda p, c, b: AetherToolbar(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), items=p.get('items')))

        self.register_factory('aether_modal',
            lambda p, c, b: AetherModal(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), title=str(p.get('text_content', p.get('title', 'Modal'))),
                is_visible=bool(p.get('is_visible', False))))

        self.register_factory('aether_splitter',
            lambda p, c, b: AetherSplitter(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), orientation=str(p.get('orientation', 'vertical')),
                ratio=float(p.get('ratio', 0.5))))

        self.register_factory('aether_scroll_panel',
            lambda p, c, b: AetherScrollPanel(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), content_h=float(p.get('content_h', p.get('h', 300))),
                scroll_y=float(p.get('scroll_y', 0))))

        self.register_factory('aether_context_menu',
            lambda p, c, b: AetherContextMenu(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), items=p.get('items'),
                is_visible=bool(p.get('is_visible', False))))

        self.register_factory('aether_tooltip',
            lambda p, c, b: AetherTooltipBox(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), text=str(p.get('text_content', p.get('text', ''))),
                target_x=float(p.get('target_x', p['x'])), target_y=float(p.get('target_y', p['y'])),
                offset_y=float(p.get('offset_y', -10))))

        self.register_factory('aether_hero',
            lambda p, c, b: AetherHero(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), title=str(p.get('text_content', p.get('title', 'Hero'))),
                subtitle=str(p.get('subtitle', '')), parallax_factor=float(p.get('parallax_factor', 0.3))))

        self.register_factory('aether_pricing_card',
            lambda p, c, b: AetherPricingCard(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), plan=str(p.get('plan', 'Basic')),
                price=float(p.get('price', 0)), features=p.get('features'),
                is_featured=bool(p.get('is_featured', False))))

        self.register_factory('aether_navbar',
            lambda p, c, b: AetherNavbar(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), items=p.get('items'),
                is_sticky=bool(p.get('is_sticky', True))))

        self.register_factory('aether_toast',
            lambda p, c, b: AetherToastAlert(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), message=str(p.get('text_content', p.get('message', ''))),
                toast_type=str(p.get('toast_type', 'info')), duration=float(p.get('duration', 5.0))))

        self.register_factory('aether_accordion',
            lambda p, c, b: AetherAccordionItem(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), title=str(p.get('text_content', p.get('title', 'Section'))),
                content=str(p.get('content', '')), is_expanded=bool(p.get('is_expanded', False)),
                expanded_h=float(p.get('expanded_h', 200))))

        self.register_factory('aether_drawer',
            lambda p, c, b: AetherDrawer(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), is_open=bool(p.get('is_open', False)),
                position=str(p.get('position', 'left'))))

        self.register_factory('aether_tabs',
            lambda p, c, b: AetherTabs(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), tabs=p.get('tabs', ['Tab 1']),
                active_index=int(p.get('active_index', 0))))

        self.register_factory('aether_pill_badge',
            lambda p, c, b: AetherPillBadge(x=float(p['x']), y=float(p['y']),
                w=float(p.get('w', 24)), h=float(p.get('h', 24)), color=c, z=int(p.get('z', 0)),
                text=str(p.get('text_content', p.get('text', '0'))),
                parent=b._element_refs.get(p['parent']) if p.get('parent') else None,
                anchor=str(p.get('anchor', 'top-right'))))

        self.register_factory('aether_spring_box',
            lambda p, c, b: AetherSpringBox(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), spring_k=float(p.get('spring_k', 10.0)),
                damping_c=float(p.get('damping_c', 2.0))))

        self.register_factory('aether_attractor',
            lambda p, c, b: AetherAttractor(x=float(p['x']), y=float(p['y']), w=1.0, h=1.0,
                color=(0, 0, 0, 0), z=int(p.get('z', 0)),
                strength=float(p.get('strength', 1.0)), radius=float(p.get('radius', 200.0))))

        self.register_factory('aether_boundary',
            lambda p, c, b: AetherBoundary(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=(0, 0, 0, 0), z=int(p.get('z', 0)),
                clamp_inside=bool(p.get('clamp_inside', True))))

        self.register_factory('aether_surface',
            lambda p, c, b: AetherSurface(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), friction=float(p.get('friction', 0.3)),
                is_draggable=bool(p.get('is_draggable', True))))

        self.register_factory('aether_bouncy_label',
            lambda p, c, b: AetherBouncyLabel(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), text=str(p.get('text_content', p.get('text', 'Label'))),
                font_size=int(p.get('font_size', 16)), font_family=str(p.get('font_family', 'Arial'))))

        self.register_factory('aether_magnet_link',
            lambda p, c, b: AetherMagnetLink(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), snap_distance=float(p.get('snap_distance', 20.0)),
                linked_ids=p.get('linked_ids')))

        self.register_factory('aether_physics_divider',
            lambda p, c, b: AetherPhysicsDivider(x=float(p['x']), y=float(p['y']),
                w=float(p.get('w', 20)), h=float(p['h']), color=c, z=int(p.get('z', 0)),
                min_size=float(p.get('min_size', 10.0)), preferred_size=float(p.get('preferred_size', 40.0)),
                stiffness=float(p.get('stiffness', 5.0))))

        self.register_factory('aether_teleport',
            lambda p, c, b: AetherTeleport(x=float(p['x']), y=float(p['y']), w=float(p['w']), h=float(p['h']),
                color=c, z=int(p.get('z', 0)), state_a=p.get('state_a', {}),
                state_b=p.get('state_b', {}), blend=float(p.get('blend', 0.0))))

    def build_from_intent(self, engine: AetherEngine, intent: dict) -> None:
        elements_def = intent.get('elements', [])
        non_buttons = [e for e in elements_def if e.get('type') != 'smart_button']
        buttons = [e for e in elements_def if e.get('type') == 'smart_button']
        for elem_def in non_buttons:
            self._create_element(elem_def)
        for elem_def in buttons:
            self._create_element(elem_def)
        for elem_id, element in self._element_refs.items():
            engine.register_element(element)
        if 'animation' in intent or 'transition_speed_ms' in intent:
            compiler = TensorCompiler()
            coefficients = compiler.compile_intent(intent)
            compiler.apply_coefficients(engine, coefficients)

    def build_from_datasource(self, engine: AetherEngine, provider: BaseAetherProvider,
                               query: str, template_json: dict) -> int:
        if not getattr(provider, '_connected', True):
            provider.connect()
        rows = provider.execute_query(query)
        if not rows:
            return 0
        elem_type = template_json.get('type', 'static_box')
        columns_map = template_json.get('columns', {})
        metadata_fields = template_json.get('metadata_fields', [])
        defaults = self.DEFAULTS.get(elem_type, self.DEFAULTS['static_box']).copy()
        col_ranges = {}
        for prop, mapping in columns_map.items():
            if 'scale' in mapping:
                src = mapping['source']
                if isinstance(src, str):
                    values = [float(row.get(src, 0)) for row in rows if row.get(src) is not None]
                    if values:
                        col_ranges[src] = (min(values), max(values))
        created = 0
        for row in rows:
            elem_id = str(row.get('id', f'db_element_{created}'))
            props = defaults.copy()
            metadata = {}
            for prop, mapping in columns_map.items():
                src = mapping.get('source', prop)
                if isinstance(src, list):
                    values = []
                    for col_name in src:
                        val = row.get(col_name, 1.0)
                        if col_name in col_ranges and 'scale' in mapping:
                            s = mapping['scale']
                            val = min_max_scale(float(val), s[0], s[1], s[2], s[3])
                        values.append(float(val))
                    if len(values) == 4:
                        props[prop] = values
                elif isinstance(src, str):
                    val = row.get(src, props.get(prop, 0))
                    if src in col_ranges and 'scale' in mapping:
                        s = mapping['scale']
                        val = min_max_scale(float(val), s[0], s[1], s[2], s[3])
                    props[prop] = float(val) if prop in ('x', 'y', 'w', 'h', 'z') else val
            for field in metadata_fields:
                if field in row:
                    metadata[field] = row[field]
            elem_def = {**props, 'type': elem_type, 'id': elem_id}
            if metadata:
                elem_def['metadata'] = metadata
                if 'title' in metadata:
                    elem_def['text_content'] = str(metadata['title'])
            element = self._create_element(elem_def)
            if element is not None:
                engine.register_element(element)
                created += 1
        if 'animation' in template_json or 'transition_speed_ms' in template_json:
            compiler = TensorCompiler()
            coefficients = compiler.compile_intent(template_json)
            compiler.apply_coefficients(engine, coefficients)
        return created

    def _create_element(self, elem_def: dict) -> Optional[DifferentialElement]:
        elem_type = elem_def.get('type', 'static_box')
        elem_id = elem_def.get('id', f'element_{len(self._element_refs)}')
        defaults = self.DEFAULTS.get(elem_type, self.DEFAULTS['static_box']).copy()
        props = {**defaults, **elem_def}
        color = props.get('color', [1, 1, 1, 1])
        if isinstance(color, str):
            color = self._hex_to_rgba(color)
        factory = self._registry.get(elem_type)
        if factory is None:
            return None
        element = factory(props, tuple(color), self)
        if element is not None:
            element._id = elem_id
            if hasattr(element, '_sound_trigger') and 'sound_trigger' in props:
                element._sound_trigger = props['sound_trigger']
            self._element_refs[elem_id] = element
        return element

    @staticmethod
    def _hex_to_rgba(hex_color: str) -> List[float]:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return [int(hex_color[0:2], 16) / 255.0, int(hex_color[2:4], 16) / 255.0,
                    int(hex_color[4:6], 16) / 255.0, 1.0]
        elif len(hex_color) == 8:
            return [int(hex_color[0:2], 16) / 255.0, int(hex_color[2:4], 16) / 255.0,
                    int(hex_color[4:6], 16) / 255.0, int(hex_color[6:8], 16) / 255.0]
        return [1.0, 1.0, 1.0, 1.0]

    def build_from_html(self, engine: AetherEngine, html_str: str, css_str: str = '') -> int:
        from core.html_parser import AetherHTMLParser
        parser = AetherHTMLParser()
        intent = parser.parse(html_str, css_str)
        self.build_from_intent(engine, intent)
        return len(intent.get('elements', []))

    @property
    def element_count(self) -> int:
        return len(self._element_refs)

    # ── Individual factory methods (kept for clarity and extensibility) ──

    def _factory_static_box(self, props, color, builder):
        return StaticBox(x=float(props['x']), y=float(props['y']), w=float(props['w']),
                         h=float(props['h']), color=color, z=int(props.get('z', 0)))

    def _factory_smart_panel(self, props, color, builder):
        return SmartPanel(x=float(props['x']), y=float(props['y']), w=float(props['w']),
                          h=float(props['h']), color=color, z=int(props.get('z', 1)),
                          padding=float(props.get('padding', 0.05)))

    def _factory_smart_button(self, props, color, builder):
        parent_id = props.get('parent')
        parent = builder._element_refs.get(parent_id)
        if parent is None and builder._element_refs:
            parent = list(builder._element_refs.values())[0]
        if parent is None:
            return None
        return SmartButton(parent=parent, offset_x=float(props.get('offset_x', 0)),
                           offset_y=float(props.get('offset_y', 0)),
                           offset_w=float(props.get('offset_w', 100)),
                           offset_h=float(props.get('offset_h', 50)),
                           color=color, z=int(props.get('z', 2)))

    def _factory_flexible_text(self, props, color, builder):
        return FlexibleTextNode(x=float(props['x']), y=float(props['y']), w=float(props['w']),
                                h=float(props['h']), color=color, z=int(props.get('z', 2)),
                                text=str(props.get('text', 'Text')))

    def _factory_canvas_text(self, props, color, builder):
        text_color = props.get('text_color', props.get('color', [1, 1, 1, 1]))
        if isinstance(text_color, str):
            text_color = self._hex_to_rgba(text_color)
        return CanvasTextNode(x=float(props['x']), y=float(props['y']), w=float(props['w']),
                              h=float(props['h']), color=color, z=int(props.get('z', 5)),
                              text=str(props.get('text_content', props.get('text', 'Text'))),
                              font_size=int(props.get('font_size', 24)),
                              font_family=str(props.get('font_family', 'Arial')))

    def _factory_dom_text(self, props, color, builder):
        text_color = props.get('text_color', [1, 1, 1, 1])
        if isinstance(text_color, str):
            text_color = self._hex_to_rgba(text_color)
        return DOMTextNode(x=float(props['x']), y=float(props['y']), w=float(props['w']),
                           h=float(props['h']), color=color, z=int(props.get('z', 10)),
                           text=str(props.get('text_content', props.get('text', 'Text'))),
                           font_size=int(props.get('font_size', 16)),
                           font_family=str(props.get('font_family', 'Arial')),
                           text_color=tuple(text_color))
