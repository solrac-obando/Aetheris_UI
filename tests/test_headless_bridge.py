# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Tests for the Headless Texture Bridge.
"""
import pytest
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHeadlessBridgeCreation:
    """Test HeadlessTextureBridge creation and configuration."""
    
    def test_bridge_creation(self):
        """Test bridge can be created with mock engine."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = []
        
        bridge = HeadlessTextureBridge(
            mock_engine,
            output_format="numpy",
            frame_width=1280,
            frame_height=720,
        )
        
        assert bridge.frame_width == 1280
        assert bridge.frame_height == 720
        assert bridge.frame_count == 0
    
    def test_bridge_default_values(self):
        """Test bridge default values."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = []
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        assert bridge.frame_width == 1280
        assert bridge.frame_height == 720
        assert bridge._output_format == "numpy"


class TestElementStates:
    """Test element state extraction."""
    
    def test_empty_engine(self):
        """Test empty engine returns zero states."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = []
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        states = bridge.get_element_states()
        
        assert states.shape[0] == 0
        assert states.shape[1] == 11  # 11 float fields per element
    
    def test_single_element(self):
        """Test single element state extraction."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        import numpy as np
        
        mock_tensor = MagicMock()
        mock_tensor.state = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        mock_tensor.velocity = np.array([0.0, 0.0], dtype=np.float32)
        
        mock_element = MagicMock()
        mock_element.tensor = mock_tensor
        mock_element._color = np.array([1.0, 0.5, 0.0, 1.0], dtype=np.float32)
        mock_element._z_index = 0
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = [mock_element]
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        states = bridge.get_element_states()
        
        assert states.shape == (1, 11)
        # Check denormalization: 0.1 * 1280 = 128
        assert states[0][0] == pytest.approx(128.0, rel=1.0)
    
    def test_multiple_elements(self):
        """Test multiple element state extraction."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        import numpy as np
        
        def make_mock_element(x, y, w, h):
            mock_tensor = MagicMock()
            mock_tensor.state = np.array([x, y, w, h], dtype=np.float32)
            mock_tensor.velocity = np.array([0.0, 0.0], dtype=np.float32)
            
            mock_element = MagicMock()
            mock_element.tensor = mock_tensor
            mock_element._color = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
            mock_element._z_index = 0
            return mock_element
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = [
            make_mock_element(0.1, 0.1, 0.2, 0.1),
            make_mock_element(0.5, 0.5, 0.1, 0.1),
        ]
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        states = bridge.get_element_states()
        
        assert states.shape == (2, 11)


class TestFrameBuffer:
    """Test frame buffer generation."""
    
    def test_frame_buffer_numpy_format(self):
        """Test numpy format frame buffer."""
        from core.headless_bridge import HeadlessTextureBridge, FrameBuffer
        from unittest.mock import MagicMock
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = []
        
        bridge = HeadlessTextureBridge(mock_engine, output_format="numpy")
        
        frame = bridge.get_frame_buffer()
        
        assert isinstance(frame, FrameBuffer)
        assert frame.states is not None
        assert frame.metadata is not None
    
    def test_frame_buffer_json_format(self):
        """Test JSON format frame buffer."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = []
        
        bridge = HeadlessTextureBridge(mock_engine, output_format="json")
        
        frame = bridge.get_frame_buffer()
        
        assert frame.raw_bytes is not None
        json_str = frame.raw_bytes.decode('utf-8')
        data = json.loads(json_str)
        assert "frame" in data
    
    def test_frame_metadata(self):
        """Test frame metadata is populated."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = []
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        frame = bridge.get_frame_buffer()
        
        assert frame.metadata.frame_number == 1
        assert frame.metadata.element_count == 0
        assert frame.metadata.fps > 0


class TestJSONSnapshot:
    """Test JSON snapshot generation."""
    
    def test_json_snapshot_empty(self):
        """Test JSON snapshot for empty engine."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        import json
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = []
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        snapshot = bridge.get_json_snapshot()
        data = json.loads(snapshot)
        
        # JSON snapshot uses current frame count (not incremented)
        assert "frame" in data
        assert data["element_count"] == 0
        assert data["elements"] == []
    
    def test_json_snapshot_with_elements(self):
        """Test JSON snapshot with elements."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        import json
        import numpy as np
        
        mock_tensor = MagicMock()
        mock_tensor.state = np.array([0.5, 0.5, 0.2, 0.1], dtype=np.float32)
        mock_tensor.velocity = np.array([0.1, 0.0], dtype=np.float32)
        
        mock_element = MagicMock()
        mock_element.tensor = mock_tensor
        mock_element._color = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.float32)
        mock_element._z_index = 5
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = [mock_element]
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        snapshot = bridge.get_json_snapshot()
        data = json.loads(snapshot)
        
        assert data["element_count"] == 1
        assert len(data["elements"]) == 1
        assert data["elements"][0]["z"] == 5


class TestFlatBuffer:
    """Test flat buffer for GPU upload."""
    
    def test_flat_buffer_shape(self):
        """Test flat buffer has expected shape."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = []
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        flat = bridge.get_flat_buffer()
        
        # Should contain state data + 4 metadata floats
        # 0 elements * 11 + 4 = 4
        assert len(flat) >= 4
    
    def test_flat_buffer_with_elements(self):
        """Test flat buffer with elements includes metadata."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        import numpy as np
        
        mock_tensor = MagicMock()
        mock_tensor.state = np.array([0.5, 0.5, 0.2, 0.1], dtype=np.float32)
        mock_tensor.velocity = np.array([0.0, 0.0], dtype=np.float32)
        
        mock_element = MagicMock()
        mock_element.tensor = mock_tensor
        mock_element._color = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
        mock_element._z_index = 0
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = [mock_element]
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        flat = bridge.get_flat_buffer()
        
        # 1 element * 11 floats + 4 metadata = 15
        assert len(flat) == 15


class TestFrameCounting:
    """Test frame counting and FPS calculation."""
    
    def test_frame_count_increments(self):
        """Test frame count increments on each call."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = []
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        assert bridge.frame_count == 0
        
        bridge.get_frame_buffer()
        assert bridge.frame_count == 1
        
        bridge.get_frame_buffer()
        assert bridge.frame_count == 2
    
    def test_reset_clears_count(self):
        """Test reset clears frame count."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = []
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        bridge.get_frame_buffer()
        bridge.get_frame_buffer()
        
        assert bridge.frame_count == 2
        
        bridge.reset()
        
        assert bridge.frame_count == 0


class TestTick:
    """Test tick method."""
    
    def test_tick_calls_engine(self):
        """Test tick method calls engine tick."""
        from core.headless_bridge import HeadlessTextureBridge
        from unittest.mock import MagicMock
        
        mock_engine = MagicMock()
        mock_engine.get_all_elements.return_value = []
        
        bridge = HeadlessTextureBridge(mock_engine)
        
        result = bridge.tick()
        
        mock_engine.tick.assert_called_once()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])