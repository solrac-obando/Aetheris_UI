# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
AetherHTMLParser - Translates HTML/CSS into DifferentialElement JSON Intent.

Uses BeautifulSoup for DOM traversal and tinycss2 for CSS rule parsing.
Maps HTML tags and CSS properties to Aetheris UI element definitions with
physics-aware properties (spring transitions, easing, etc.).
"""
import re
import tinycss2
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple, Any


class AetherHTMLParser:
    """Parses HTML/CSS and produces Aetheris UI builder intent dictionaries."""

    TAG_TYPE_MAP = {
        'div': 'static_box',
        'section': 'static_box',
        'article': 'static_box',
        'main': 'static_box',
        'header': 'static_box',
        'footer': 'static_box',
        'aside': 'static_box',
        'nav': 'aether_navbar',
        'button': 'smart_button',
        'input': 'smart_button',
        'a': 'smart_button',
        'p': 'flexible_text',
        'span': 'flexible_text',
        'h1': 'canvas_text',
        'h2': 'canvas_text',
        'h3': 'canvas_text',
        'h4': 'canvas_text',
        'h5': 'canvas_text',
        'h6': 'canvas_text',
        'label': 'dom_text',
        'text': 'dom_text',
        'textarea': 'flexible_text',
        'img': 'static_box',
        'canvas': 'static_box',
        'video': 'static_box',
        'aether-gauge': 'aether_gauge',
        'aether-sparkline': 'aether_sparkline',
        'aether-bar-group': 'aether_bar_group',
        'aether-status-orb': 'aether_status_orb',
        'aether-heatmap': 'aether_heatmap',
        'aether-toggle': 'aether_kinetic_toggle',
        'aether-radial-progress': 'aether_radial_progress',
        'aether-value-metric': 'aether_value_metric',
        'aether-window': 'aether_window',
        'aether-side-nav': 'aether_side_nav',
        'aether-toolbar': 'aether_toolbar',
        'aether-modal': 'aether_modal',
        'aether-splitter': 'aether_splitter',
        'aether-scroll-panel': 'aether_scroll_panel',
        'aether-context-menu': 'aether_context_menu',
        'aether-tooltip': 'aether_tooltip',
        'aether-hero': 'aether_hero',
        'aether-pricing-card': 'aether_pricing_card',
        'aether-navbar': 'aether_navbar',
        'aether-toast': 'aether_toast',
        'aether-accordion': 'aether_accordion',
        'aether-drawer': 'aether_drawer',
        'aether-tabs': 'aether_tabs',
        'aether-pill-badge': 'aether_pill_badge',
        'aether-spring-box': 'aether_spring_box',
        'aether-attractor': 'aether_attractor',
        'aether-boundary': 'aether_boundary',
        'aether-surface': 'aether_surface',
        'aether-bouncy-label': 'aether_bouncy_label',
        'aether-magnet-link': 'aether_magnet_link',
        'aether-physics-divider': 'aether_physics_divider',
        'aether-teleport': 'aether_teleport',
    }

    FONT_SIZE_MAP = {
        'h1': 32,
        'h2': 28,
        'h3': 24,
        'h4': 20,
        'h5': 16,
        'h6': 14,
        'p': 16,
        'span': 14,
        'label': 14,
        'button': 14,
        'div': 14,
    }

    DEFAULT_DIMENSIONS = {
        'static_box': {'w': 200, 'h': 100},
        'smart_button': {'w': 100, 'h': 40},
        'flexible_text': {'w': 200, 'h': 40},
        'canvas_text': {'w': 200, 'h': 50},
        'dom_text': {'w': 200, 'h': 50},
    }

    RESERVED_ATTRS = frozenset({'id', 'class', 'style'})

    def __init__(self):
        self._element_counter = 0
        self._css_rules: List[dict] = []
        self._elements: List[dict] = []
        self._transitions: List[dict] = []

    @staticmethod
    def _parse_val(val):
        """Convert an HTML attribute value to the most appropriate Python type.

        Handles:
        - Single-item lists → unwrap then convert
        - Boolean strings ('true'/'false') → bool
        - Numeric strings → int or float
        - Everything else → str
        """
        if isinstance(val, list):
            if len(val) == 1:
                val = val[0]
            elif len(val) == 0:
                return None
            else:
                return val

        if isinstance(val, bool):
            return val

        if isinstance(val, str):
            low = val.lower()
            if low in ('true', 'yes', 'on', '1'):
                return True
            if low in ('false', 'no', 'off', '0'):
                return False
            if '.' in val:
                try:
                    return float(val)
                except ValueError:
                    pass
            else:
                try:
                    return int(val)
                except ValueError:
                    pass
            return val

        return val

    def parse(self, html_str: str, css_str: str = '') -> dict:
        """
        Parse HTML and CSS strings into a complete UI builder intent.

        Args:
            html_str: Raw HTML string
            css_str: Raw CSS string

        Returns:
            dict: JSON intent compatible with UIBuilder.build_from_intent()
        """
        self._element_counter = 0
        self._elements = []
        self._transitions = []

        self._parse_css(css_str)
        self._parse_dom(html_str)

        intent = {
            'elements': self._elements,
            'animation': {'style': 'organic'},
            'transitions': self._transitions if self._transitions else [],
        }

        return intent

    def _parse_css(self, css_str: str) -> None:
        """Parse CSS string using tinycss2 and store rules for later matching."""
        if not css_str:
            return
        rules = tinycss2.parse_stylesheet(css_str, skip_comments=True, skip_whitespace=True)
        for rule in rules:
            if rule.type == 'qualified-rule':
                selector_text = tinycss2.serialize(rule.prelude).strip()
                declarations = tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True)
                parsed_declarations = self._parse_declarations(declarations)
                if parsed_declarations:
                    self._css_rules.append({
                        'selector': selector_text,
                        'declarations': parsed_declarations,
                    })

    def _parse_declarations(self, declarations) -> dict:
        """Parse tinycss2 declaration list into a dictionary of properties."""
        result = {}
        for decl in declarations:
            if decl.type != 'declaration':
                continue
            name = decl.name.lower()
            value = tinycss2.serialize(decl.value).strip()
            if name == 'background-color' or name == 'color':
                parsed = self._parse_color(value)
                if parsed:
                    result[name] = parsed
            elif name == 'transition':
                parsed = self._parse_transition(value)
                if parsed:
                    result[name] = parsed
            elif name == 'transform':
                parsed = self._parse_transform(value)
                if parsed:
                    result[name] = parsed
            elif name in ('width', 'height', 'top', 'left', 'right', 'bottom',
                          'padding', 'padding-top', 'padding-right',
                          'padding-bottom', 'padding-left', 'margin',
                          'font-size', 'opacity'):
                result[name] = value
        return result

    def _parse_color(self, value: str) -> Optional[List[float]]:
        """Parse CSS color value to RGBA float list [0-1]."""
        value = value.strip()

        if value.startswith('#'):
            return self._parse_hex_color(value)

        if value.startswith('rgba('):
            return self._parse_rgba(value)

        if value.startswith('rgb('):
            return self._parse_rgb(value)

        named_colors = {
            'transparent': [0, 0, 0, 0],
            'black': [0, 0, 0, 1],
            'white': [1, 1, 1, 1],
            'red': [1, 0, 0, 1],
            'green': [0, 0.5, 0, 1],
            'blue': [0, 0, 1, 1],
            'yellow': [1, 1, 0, 1],
            'cyan': [0, 1, 1, 1],
            'magenta': [1, 0, 1, 1],
            'gray': [0.5, 0.5, 0.5, 1],
            'grey': [0.5, 0.5, 0.5, 1],
        }
        return named_colors.get(value.lower())

    def _parse_hex_color(self, hex_str: str) -> Optional[List[float]]:
        """Parse hex color to RGBA."""
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 8:
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            a = int(hex_str[6:8], 16) / 255.0
            return [r, g, b, a]
        elif len(hex_str) == 6:
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            return [r, g, b, 1.0]
        elif len(hex_str) == 4:
            r = int(hex_str[0] * 2, 16) / 255.0
            g = int(hex_str[1] * 2, 16) / 255.0
            b = int(hex_str[2] * 2, 16) / 255.0
            return [r, g, b, 1.0]
        elif len(hex_str) == 3:
            r = int(hex_str[0] * 2, 16) / 255.0
            g = int(hex_str[1] * 2, 16) / 255.0
            b = int(hex_str[2] * 2, 16) / 255.0
            return [r, g, b, 1.0]
        return None

    def _parse_rgba(self, value: str) -> Optional[List[float]]:
        """Parse rgba(r, g, b, a) to float list."""
        match = re.match(r'rgba\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)', value)
        if match:
            return [float(match.group(1)) / 255.0, float(match.group(2)) / 255.0,
                    float(match.group(3)) / 255.0, float(match.group(4))]
        return None

    def _parse_rgb(self, value: str) -> Optional[List[float]]:
        """Parse rgb(r, g, b) to float list with alpha=1."""
        match = re.match(r'rgb\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)', value)
        if match:
            return [float(match.group(1)) / 255.0, float(match.group(2)) / 255.0,
                    float(match.group(3)) / 255.0, 1.0]
        return None

    def _parse_transition(self, value: str) -> Optional[dict]:
        """Parse CSS transition value, including custom aether-spring() function."""
        value = re.sub(r'\(\s*', '(', value)
        value = re.sub(r'\s*\)', ')', value)
        value = re.sub(r',\s*', ',', value)

        parts = value.split()
        if len(parts) < 2:
            return None

        result = {
            'property': parts[0],
            'duration': self._parse_duration(parts[1]) if len(parts) > 1 else 0.3,
            'easing': 'linear',
            'spring_k': None,
            'spring_c': None,
        }

        for part in parts[2:]:
            spring_match = re.match(r'(?:aether-spring|spring)\(k=([\d.]+),c=([\d.]+)\)', part)
            if spring_match:
                result['easing'] = 'aether_spring'
                result['spring_k'] = float(spring_match.group(1))
                result['spring_c'] = float(spring_match.group(2))
                break

            if part in ('ease', 'ease-in', 'ease-out', 'ease-in-out', 'linear'):
                result['easing'] = part
            else:
                duration = self._parse_duration(part)
                if duration is not None:
                    result['duration'] = duration

        return result

    def _parse_duration(self, value: str) -> Optional[float]:
        """Parse CSS duration string to seconds."""
        if value.endswith('ms'):
            return float(value[:-2]) / 1000.0
        elif value.endswith('s'):
            return float(value[:-1])
        return None

    def _parse_transform(self, value: str) -> Optional[dict]:
        """Parse CSS transform value."""
        result = {}
        scale_match = re.search(r'scale\(([\d.]+)\)', value)
        if scale_match:
            result['scale'] = float(scale_match.group(1))
        rotate_match = re.search(r'rotate\(([\d.]+)(?:deg|rad)?\)', value)
        if rotate_match:
            result['rotate'] = float(rotate_match.group(1))
        translate_match = re.search(r'translate\(([\d.-]+)px?,\s*([\d.-]+)px?\)', value)
        if translate_match:
            result['translate_x'] = float(translate_match.group(1))
            result['translate_y'] = float(translate_match.group(2))
        return result if result else None

    def _parse_dom(self, html_str: str) -> None:
        """Parse HTML DOM tree and build element definitions."""
        soup = BeautifulSoup(html_str, 'html.parser')
        self._process_element(soup, parent_id=None, depth=0)

    def _process_element(self, bs4_elem, parent_id: Optional[str], depth: int) -> None:
        """Recursively process a BS4 element and its children."""
        if bs4_elem.name is None:
            return

        if bs4_elem.name == '[document]':
            for child in bs4_elem.children:
                self._process_element(child, parent_id, depth)
            return

        elem_type = self.TAG_TYPE_MAP.get(bs4_elem.name.lower(), 'static_box')
        elem_id = bs4_elem.get('id', f'aether_elem_{self._element_counter}')
        self._element_counter += 1

        css_props = self._match_css_rules(bs4_elem)

        element_def = self._build_element_def(bs4_elem, elem_type, elem_id, css_props, depth)

        if parent_id:
            element_def['parent'] = parent_id

        self._elements.append(element_def)

        if css_props.get('transition'):
            self._transitions.append({
                'element_id': elem_id,
                **css_props['transition'],
            })

        for child in bs4_elem.children:
            self._process_element(child, elem_id, depth + 1)

    def _match_css_rules(self, bs4_elem) -> dict:
        """Match CSS rules to a BS4 element based on its id, classes, and tag."""
        matched = {}
        elem_id = bs4_elem.get('id', '')
        classes = bs4_elem.get('class', [])
        if isinstance(classes, list):
            classes = classes
        else:
            classes = [classes]
        tag = bs4_elem.name.lower()

        for rule in self._css_rules:
            selector = rule['selector']
            score = 0

            if elem_id and f'#{elem_id}' in selector:
                score = 100
            elif any(f'.{c}' in selector for c in classes):
                score = 10
            elif selector == tag:
                score = 1
            elif selector.startswith(f'{tag}:'):
                score = 1

            if score > 0:
                for key, val in rule['declarations'].items():
                    if key not in matched or score > matched.get(f'_score_{key}', 0):
                        matched[key] = val
                        matched[f'_score_{key}'] = score

        return {k: v for k, v in matched.items() if not k.startswith('_score_')}

    def _build_element_def(self, bs4_elem, elem_type: str, elem_id: str,
                           css_props: dict, depth: int) -> dict:
        """Build a single element definition dictionary."""
        dims = self.DEFAULT_DIMENSIONS.get(elem_type, self.DEFAULT_DIMENSIONS['static_box'])
        text_content = self._extract_text(bs4_elem)

        element_def = {
            'id': elem_id,
            'type': elem_type,
            'tag': bs4_elem.name,
        }

        # Generic attribute extraction for component parameters
        for attr, val in bs4_elem.attrs.items():
            if attr in self.RESERVED_ATTRS:
                continue
            normalized = attr.replace('-', '_')
            parsed = self._parse_val(val)
            if parsed is not None:
                element_def[normalized] = parsed

        if 'background-color' in css_props:
            element_def['color'] = css_props['background-color']
        elif elem_type == 'static_box':
            element_def['color'] = [0.2, 0.2, 0.25, 0.9]

        if 'width' in css_props:
            element_def['w'] = self._parse_dimension(css_props['width'], dim='w')
        else:
            element_def['w'] = dims['w']

        if 'height' in css_props:
            element_def['h'] = self._parse_dimension(css_props['height'], dim='h')
        else:
            element_def['h'] = dims['h']

        if 'top' in css_props:
            element_def['y'] = self._parse_dimension(css_props['top'], dim='y')
        else:
            element_def['y'] = depth * 60

        if 'left' in css_props:
            element_def['x'] = self._parse_dimension(css_props['left'], dim='x')
        else:
            element_def['x'] = depth * 20

        if 'z-index' in css_props:
            try:
                element_def['z'] = int(css_props['z-index'])
            except (ValueError, TypeError):
                pass

        if elem_type in ('canvas_text', 'dom_text', 'flexible_text'):
            element_def['text_content'] = text_content or elem_id
            if 'font-size' in css_props:
                element_def['font_size'] = self._parse_font_size(css_props['font-size'])
            else:
                element_def['font_size'] = self.FONT_SIZE_MAP.get(bs4_elem.name, 16)

            if 'color' in css_props and elem_type == 'dom_text':
                element_def['text_color'] = css_props['color']

        if 'padding' in css_props:
            element_def['padding'] = self._parse_padding(css_props['padding'])

        if 'opacity' in css_props:
            try:
                opacity = float(css_props['opacity'])
                if 'color' in element_def and len(element_def['color']) == 4:
                    element_def['color'][3] = opacity
            except (ValueError, TypeError):
                pass

        return element_def

    def _parse_dimension(self, value: str, dim: str = 'w') -> float:
        """Parse a CSS dimension value to pixels."""
        value = value.strip()
        if value.endswith('%'):
            base = 800 if dim in ('w', 'x') else 600
            return float(value[:-1]) / 100.0 * base
        elif value.endswith('px'):
            return float(value[:-2])
        elif value.endswith('rem') or value.endswith('em'):
            unit = 'rem' if value.endswith('rem') else 'em'
            return float(value[:-len(unit)]) * 16.0
        try:
            return float(value)
        except ValueError:
            return self.DEFAULT_DIMENSIONS['static_box'][dim]

    def _parse_font_size(self, value: str) -> int:
        """Parse CSS font-size to integer pixels."""
        value = value.strip()
        if value.endswith('px'):
            return int(float(value[:-2]))
        elif value.endswith('rem') or value.endswith('em'):
            unit = 'rem' if value.endswith('rem') else 'em'
            return int(float(value[:-len(unit)]) * 16.0)
        elif value.endswith('pt'):
            return int(float(value[:-2]) * 1.333)
        try:
            return int(float(value))
        except ValueError:
            return 16

    def _parse_padding(self, value: str) -> float:
        """Parse CSS padding to a fraction (for SmartPanel padding)."""
        value = value.strip()
        if value.endswith('%'):
            return float(value[:-1]) / 100.0
        elif value.endswith('px'):
            return float(value[:-2]) / 800.0
        try:
            return float(value) / 800.0
        except ValueError:
            return 0.05

    def _extract_text(self, bs4_elem) -> Optional[str]:
        """Extract direct text content from a BS4 element."""
        texts = []
        for child in bs4_elem.children:
            if child.string and child.string.strip():
                texts.append(child.string.strip())
        return ' '.join(texts) if texts else None

    def _add_text_to_parent(self, parent_id: str, text: str) -> None:
        """Append text content to an existing element definition."""
        for elem in self._elements:
            if elem['id'] == parent_id:
                existing = elem.get('text_content', '')
                elem['text_content'] = f"{existing} {text}".strip() if existing else text
                break
