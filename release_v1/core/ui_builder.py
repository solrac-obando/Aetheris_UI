# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
UI Builder - Translates JSON Intent into registered AetherEngine elements.

This module bridges the gap between server-driven UI configuration (JSON)
and the physics engine's element registry. It parses layout definitions
and instantiates the appropriate DifferentialElement subclasses.
"""
import numpy as np
from typing import Dict, List, Optional
from core.elements import DifferentialElement, StaticBox, SmartPanel, SmartButton, FlexibleTextNode, CanvasTextNode, DOMTextNode
from core.engine import AetherEngine
from core.tensor_compiler import TensorCompiler
from core.data_bridge import BaseAetherProvider, min_max_scale


class UIBuilder:
    """Builds AetherEngine element graphs from JSON intent definitions."""
    
    # Mapping of element type strings to classes
    ELEMENT_TYPES = {
        'static_box': StaticBox,
        'smart_panel': SmartPanel,
        'smart_button': SmartButton,
        'flexible_text': FlexibleTextNode,
        'canvas_text': CanvasTextNode,
    }
    
    # Default properties for each element type
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
    
    def build_from_intent(self, engine: AetherEngine, intent: dict) -> None:
        """
        Parse JSON intent and register all elements with the engine.
        
        Args:
            engine: Target AetherEngine instance
            intent: JSON intent dictionary with 'layout' and 'elements' keys
        """
        elements_def = intent.get('elements', [])
        
        # First pass: create all non-button elements (they may be parents)
        non_buttons = [e for e in elements_def if e.get('type') != 'smart_button']
        buttons = [e for e in elements_def if e.get('type') == 'smart_button']
        
        # Create non-button elements
        for elem_def in non_buttons:
            self._create_element(elem_def)
        
        # Create button elements (they need parent references)
        for elem_def in buttons:
            self._create_element(elem_def)
        
        # Register all elements with the engine
        for elem_id, element in self._element_refs.items():
            engine.register_element(element)
        
        # Apply physics coefficients from the compiler
        if 'animation' in intent or 'transition_speed_ms' in intent:
            compiler = TensorCompiler()
            coefficients = compiler.compile_intent(intent)
            compiler.apply_coefficients(engine, coefficients)
    
    def build_from_datasource(self, engine: AetherEngine, provider: BaseAetherProvider,
                               query: str, template_json: dict) -> int:
        """
        Build UI elements from a database query result.
        
        Executes the query via the provider, iterates through rows, and
        instantiates DifferentialElement objects where DB columns map to
        physics properties (x, y, w, h, color).
        
        Supports algebraic data normalization via min_max_scale for
        columns with large value ranges.
        
        Args:
            engine: Target AetherEngine instance
            provider: Data provider (SQLiteProvider or RemoteAetherProvider)
            query: SQL query or API query string
            template_json: Template defining how DB columns map to element properties.
                          Example:
                          {
                              "type": "static_box",
                              "columns": {
                                  "x": {"source": "pos_x", "scale": [0, 1000, 10, 790]},
                                  "y": {"source": "pos_y", "scale": [0, 1000, 10, 590]},
                                  "w": {"source": "width", "scale": [0, 10000, 50, 500]},
                                  "h": {"source": "height", "scale": [0, 10000, 50, 500]},
                                  "color": {"source": ["r", "g", "b", "a"]},
                                  "z": {"source": "layer"},
                              },
                              "metadata_fields": ["title", "rating", "year"]
                          }
                          
        Returns:
            Number of elements created.
        """
        if not getattr(provider, '_connected', True):
            provider.connect()
        
        rows = provider.execute_query(query)
        if not rows:
            return 0
        
        elem_type = template_json.get('type', 'static_box')
        columns_map = template_json.get('columns', {})
        metadata_fields = template_json.get('metadata_fields', [])
        defaults = self.DEFAULTS.get(elem_type, self.DEFAULTS['static_box']).copy()
        
        # Pre-compute column ranges for normalization
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
            
            # Map columns to element properties
            for prop, mapping in columns_map.items():
                src = mapping.get('source', prop)
                
                if isinstance(src, list):
                    # Multi-column mapping (e.g., color from [r, g, b, a])
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
            
            # Extract metadata fields
            for field in metadata_fields:
                if field in row:
                    metadata[field] = row[field]
            
            # Build element definition
            elem_def = {**props, 'type': elem_type, 'id': elem_id}
            if metadata:
                elem_def['metadata'] = metadata
                if 'title' in metadata:
                    elem_def['text_content'] = str(metadata['title'])
            
            # Create and register element
            element = self._create_element(elem_def)
            if element is not None:
                engine.register_element(element)
                created += 1
        
        # Apply physics coefficients
        if 'animation' in template_json or 'transition_speed_ms' in template_json:
            compiler = TensorCompiler()
            coefficients = compiler.compile_intent(template_json)
            compiler.apply_coefficients(engine, coefficients)
        
        return created
    
    def _create_element(self, elem_def: dict) -> Optional[DifferentialElement]:
        """
        Create a single element from its definition.
        
        Args:
            elem_def: Element definition dictionary
            
        Returns:
            Created DifferentialElement instance
        """
        elem_type = elem_def.get('type', 'static_box')
        elem_id = elem_def.get('id', f'element_{len(self._element_refs)}')
        
        # Merge with defaults
        defaults = self.DEFAULTS.get(elem_type, self.DEFAULTS['static_box']).copy()
        props = {**defaults, **elem_def}
        
        # Parse color (handle both list and tuple)
        color = props.get('color', [1, 1, 1, 1])
        if isinstance(color, str):
            # Handle hex colors like "#ff0000"
            color = self._hex_to_rgba(color)
        
        element = None
        
        if elem_type == 'static_box':
            element = StaticBox(
                x=float(props['x']),
                y=float(props['y']),
                w=float(props['w']),
                h=float(props['h']),
                color=tuple(color),
                z=int(props.get('z', 0)),
            )
            
        elif elem_type == 'smart_panel':
            element = SmartPanel(
                x=float(props['x']),
                y=float(props['y']),
                w=float(props['w']),
                h=float(props['h']),
                color=tuple(color),
                z=int(props.get('z', 1)),
                padding=float(props.get('padding', 0.05)),
            )
            
        elif elem_type == 'smart_button':
            # Find parent element
            parent_id = props.get('parent')
            parent = self._element_refs.get(parent_id)
            if parent is None:
                # Fallback: create a dummy parent if not found
                parent = self._element_refs.get(list(self._element_refs.keys())[0])
            
            if parent is not None:
                element = SmartButton(
                    parent=parent,
                    offset_x=float(props.get('offset_x', 0)),
                    offset_y=float(props.get('offset_y', 0)),
                    offset_w=float(props.get('offset_w', 100)),
                    offset_h=float(props.get('offset_h', 50)),
                    color=tuple(color),
                    z=int(props.get('z', 2)),
                )
                
        elif elem_type == 'flexible_text':
            element = FlexibleTextNode(
                x=float(props['x']),
                y=float(props['y']),
                w=float(props['w']),
                h=float(props['h']),
                color=tuple(color),
                z=int(props.get('z', 2)),
                text=str(props.get('text', 'Text')),
            )
        
        elif elem_type == 'canvas_text':
            text_color = props.get('text_color', props.get('color', [1, 1, 1, 1]))
            if isinstance(text_color, str):
                text_color = self._hex_to_rgba(text_color)
            element = CanvasTextNode(
                x=float(props['x']),
                y=float(props['y']),
                w=float(props['w']),
                h=float(props['h']),
                color=tuple(color),
                z=int(props.get('z', 5)),
                text=str(props.get('text_content', props.get('text', 'Text'))),
                font_size=int(props.get('font_size', 24)),
                font_family=str(props.get('font_family', 'Arial')),
            )
        
        elif elem_type == 'dom_text':
            text_color = props.get('text_color', [1, 1, 1, 1])
            if isinstance(text_color, str):
                text_color = self._hex_to_rgba(text_color)
            element = DOMTextNode(
                x=float(props['x']),
                y=float(props['y']),
                w=float(props['w']),
                h=float(props['h']),
                color=tuple(color),
                z=int(props.get('z', 10)),
                text=str(props.get('text_content', props.get('text', 'Text'))),
                font_size=int(props.get('font_size', 16)),
                font_family=str(props.get('font_family', 'Arial')),
                text_color=tuple(text_color),
            )
        
        if element is not None:
            element._id = elem_id
            self._element_refs[elem_id] = element
            
        return element
    
    @staticmethod
    def _hex_to_rgba(hex_color: str) -> List[float]:
        """Convert hex color string to RGBA float list [0-1]."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return [r, g, b, 1.0]
        elif len(hex_color) == 8:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            a = int(hex_color[6:8], 16) / 255.0
            return [r, g, b, a]
        return [1.0, 1.0, 1.0, 1.0]
    
    @property
    def element_count(self) -> int:
        return len(self._element_refs)
