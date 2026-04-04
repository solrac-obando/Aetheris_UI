# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Web Elements Tests — Strict validation of HTML-native physics elements.
Tests are immutable. Code must be fixed to pass.
"""
import os, sys, json
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.web_elements import WebElement, WebButton, WebText, WebCard, WebInput
from core.elements import DifferentialElement


class TestWebElements:
    """Tests for web-renderable physics elements."""

    def test_web_element_init(self):
        """Test 7: WebElement initializes with correct defaults."""
        elem = WebElement(100.0, 200.0, 50.0, 30.0, z=5)
        assert elem._html_tag == "div"
        assert elem._css_classes == []
        assert elem._html_id.startswith("ae_")
        assert elem._target[0] == 100.0
        assert elem._target[1] == 200.0

    def test_web_element_inheritance(self):
        """Test 11: Inherits correctly from DifferentialElement without breaking physics."""
        elem = WebElement(100.0, 200.0, 50.0, 30.0, z=5)
        assert isinstance(elem, DifferentialElement)
        assert hasattr(elem, 'tensor')
        assert hasattr(elem, 'calculate_asymptotes')
        assert hasattr(elem, 'rendering_data')

    def test_web_element_custom_html_id(self):
        """Test 7b: Custom HTML ID is preserved."""
        elem = WebElement(0, 0, 10, 10, html_id="my_custom_id")
        assert elem._html_id == "my_custom_id"

    def test_web_element_metadata(self):
        """Test 7c: HTML metadata is correctly structured."""
        elem = WebElement(0, 0, 10, 10, html_tag="section",
                          css_classes=["card", "highlight"],
                          styles={"color": "red"})
        meta = elem.html_metadata
        assert meta["tag"] == "section"
        assert meta["classes"] == ["card", "highlight"]
        assert meta["styles"]["color"] == "red"

    def test_web_button_render(self):
        """Test 7: Generates <button> with id, class, style correct."""
        btn = WebButton(text="Click Me", x=50.0, y=50.0, w=120.0, h=40.0)
        meta = btn.html_metadata
        assert meta["tag"] == "button"
        assert meta["text"] == "Click Me"
        assert "aether-button" in meta["classes"]
        assert "cursor" in meta["styles"]
        assert meta["styles"]["cursor"] == "pointer"

    def test_web_text_render(self):
        """Test 8: Generates <span> with innerText and font-size."""
        txt = WebText(text="Hello World", x=0, y=0, font_size=16)
        meta = txt.html_metadata
        assert meta["tag"] == "span"
        assert meta["text"] == "Hello World"
        assert meta["styles"]["font-size"] == "16px"
        assert "aether-text" in meta["classes"]

    def test_web_card_render(self):
        """Test 9: Generates <div> container with border-radius and background."""
        card = WebCard(title="Dashboard", x=0, y=0, w=300, h=200)
        meta = card.html_metadata
        assert meta["tag"] == "div"
        assert meta["text"] == "Dashboard"
        assert "aether-card" in meta["classes"]
        assert "border-radius" in meta["styles"]
        assert "backdrop-filter" in meta["styles"]

    def test_web_input_render(self):
        """Test 10: Generates native <input> (not simulated in Canvas)."""
        inp = WebInput(placeholder="Enter name...", input_type="text")
        meta = inp.html_metadata
        assert meta["tag"] == "input"
        assert meta["placeholder"] == "Enter name..."
        assert meta["input_type"] == "text"
        assert "aether-input" in meta["classes"]

    def test_web_element_physics_state(self):
        """Test 11b: Element physics state is independent of HTML metadata."""
        elem = WebElement(100.0, 200.0, 50.0, 30.0, z=0)
        # Modify physics state
        elem.tensor.state[0] = np.float32(500.0)
        # HTML metadata should be unaffected
        meta = elem.html_metadata
        assert meta["tag"] == "div"
        # Target should still be original
        assert elem._target[0] == 100.0

    def test_web_element_asymptotes(self):
        """Test 11c: calculate_asymptotes returns correct target."""
        elem = WebElement(100.0, 200.0, 50.0, 30.0)
        target = elem.calculate_asymptotes(1280.0, 720.0)
        assert np.allclose(target, [100.0, 200.0, 50.0, 30.0])
