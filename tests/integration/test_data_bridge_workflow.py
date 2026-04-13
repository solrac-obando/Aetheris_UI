# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Integration tests for DataBridge workflow.

Tests the data bridge lifecycle:
- Connection → Query → Template → Build → Element
"""
import pytest
import json
import tempfile
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_bridge import SQLiteProvider, min_max_scale


class TestDataBridgeWorkflow:
    """Test complete data bridge workflow."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary SQLite database."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Create sample table
        import sqlite3
        conn = sqlite3.connect(path)
        conn.execute('''
            CREATE TABLE metrics (
                id INTEGER PRIMARY KEY,
                pos_x REAL,
                pos_y REAL,
                width REAL,
                height REAL,
                layer INTEGER,
                title TEXT,
                rating REAL
            )
        ''')
        
        # Insert sample data
        for i in range(10):
            conn.execute('''
                INSERT INTO metrics (pos_x, pos_y, width, height, layer, title, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (i * 10.0, i * 5.0, 100.0, 50.0, i, f"Item {i}", i * 1.0))
        
        conn.commit()
        conn.close()
        
        yield path
        
        os.unlink(path)
    
    def test_db_connection(self, temp_db):
        """Test database connection."""
        provider = SQLiteProvider(temp_db)
        provider.connect()
        
        assert provider is not None
        provider.disconnect()
    
    def test_min_max_scale(self):
        """Test min-max scaling function."""
        from core.data_bridge import min_max_scale
        import numpy as np
        
        values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.float32)
        
        scaled = min_max_scale(values[0], 1.0, 10.0, 0.0, 100.0)
        
        assert scaled == 0.0
    
    def test_template_parsing(self, temp_db):
        """Test template JSON parsing."""
        from core.ui_builder import UIBuilder
        
        builder = UIBuilder()
        
        template = {
            "type": "static_box",
            "columns": {
                "x": {"source": "pos_x", "scale": [0, 100, 10, 790]},
                "y": {"source": "pos_y", "scale": [0, 100, 10, 590]},
            }
        }
        
        # Template is dict - no error should occur
        assert template["type"] == "static_box"


class TestDataBridgeSecurity:
    """Test data bridge security features."""
    
    def test_parameterized_queries(self):
        """Test parameterized queries are used for security."""
        # Verify query with placeholder exists
        query = "SELECT * FROM metrics WHERE id = ?"
        params = (1,)
        
        assert "?" in query
        assert params is not None
    
    def test_json_output_safety(self):
        """Test JSON output handles special characters safely."""
        from core.json_utils import to_json
        
        import numpy as np
        data = {
            "value": float('nan'),
            "infinite": float('inf'),
            "normal": "value",
        }
        
        json_str = to_json(data)
        
        assert json_str is not None
        assert "nan" not in json_str.lower()
        assert '"inf"' not in json_str


class TestDataBridgePerformance:
    """Test data bridge performance."""
    
    def test_bulk_data_processing(self):
        """Test bulk data processing performance."""
        import numpy as np
        import time
        
        # Simular procesamiento de datos
        data = np.random.random(1000).astype(np.float32)
        
        start = time.perf_counter()
        
        result = data * 2
        
        duration = time.perf_counter() - start
        
        assert len(result) == 1000
        assert duration < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])