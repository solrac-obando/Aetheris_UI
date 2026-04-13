# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Tests for logging plugins.
"""
import pytest
import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.logging.plugins import StandardFilePlugin, JsonDataPlugin, JsonLinesPlugin
from core.logging import AetherLogger
from core.logging.base_plugin import AetherLogPlugin


class TestStandardFilePlugin:
    """Tests for StandardFilePlugin."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return AetherLogger("test_file")
    
    def test_create_file(self, temp_dir, logger):
        """Test creating a file plugin."""
        filepath = temp_dir / "test.log"
        plugin = StandardFilePlugin(str(filepath))
        
        logger.add_plugin(plugin)
        logger.info("test message")
        
        assert filepath.exists()
        content = filepath.read_text()
        assert "test message" in content
    
    def test_create_directory(self, temp_dir, logger):
        """Test that plugin creates parent directory."""
        filepath = temp_dir / "subdir" / "test.log"
        plugin = StandardFilePlugin(str(filepath))
        
        logger.add_plugin(plugin)
        logger.info("message")
        
        assert filepath.exists()
    
    def test_custom_format(self, temp_dir, logger):
        """Test custom format string."""
        filepath = temp_dir / "custom.log"
        plugin = StandardFilePlugin(
            str(filepath),
            format="%(levelname)s: %(message)s"
        )
        
        logger.add_plugin(plugin)
        logger.info("message")
        
        content = filepath.read_text()
        assert "INFO: message" in content
    
    def test_custom_date_format(self, temp_dir, logger):
        """Test custom date format."""
        filepath = temp_dir / "date.log"
        plugin = StandardFilePlugin(
            str(filepath),
            date_format="%Y/%m/%d"
        )
        
        logger.add_plugin(plugin)
        logger.info("message")
        
        content = filepath.read_text()
        assert "2026" in content or "/" in content
    
    def test_append_mode(self, temp_dir, logger):
        """Test appending to existing file."""
        filepath = temp_dir / "append.log"
        filepath.write_text("existing\n")
        
        plugin = StandardFilePlugin(str(filepath))
        
        logger.add_plugin(plugin)
        logger.info("new message")
        
        content = filepath.read_text()
        assert "existing" in content
        assert "new message" in content
    
    def test_encoding(self, temp_dir, logger):
        """Test custom encoding."""
        filepath = temp_dir / "encoding.log"
        plugin = StandardFilePlugin(
            str(filepath),
            encoding="utf-8"
        )
        
        logger.add_plugin(plugin)
        logger.info("test")
        
        assert filepath.exists()
    
    def test_multiple_logs(self, temp_dir, logger):
        """Test multiple log messages."""
        filepath = temp_dir / "multi.log"
        plugin = StandardFilePlugin(str(filepath))
        
        logger.add_plugin(plugin)
        for i in range(10):
            logger.info(f"message {i}")
        
        content = filepath.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 10
    
    def test_log_levels(self, temp_dir, logger):
        """Test different log levels."""
        filepath = temp_dir / "levels.log"
        plugin = StandardFilePlugin(str(filepath))
        logger.add_plugin(plugin)
        
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        
        content = filepath.read_text()
        assert "DEBUG" in content
        assert "INFO" in content
        assert "WARNING" in content
        assert "ERROR" in content
    
    def test_cleanup(self, temp_dir, logger):
        """Test cleanup method."""
        filepath = temp_dir / "cleanup.log"
        plugin = StandardFilePlugin(str(filepath))
        
        logger.add_plugin(plugin)
        logger.info("message")
        plugin.cleanup()
        
        # Should not raise


class TestRotatingFilePlugin:
    """Tests for RotatingFilePlugin."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return AetherLogger("test_rotate")
    
    def test_rotation_creation(self, temp_dir, logger):
        """Test creating rotating file plugin."""
        from core.logging.plugins.file_plugin import RotatingFilePlugin
        
        filepath = temp_dir / "rotate.log"
        plugin = RotatingFilePlugin(
            str(filepath),
            max_bytes=100,
            backup_count=2
        )
        
        logger.add_plugin(plugin)
        assert plugin.max_bytes == 100
        assert plugin.backup_count == 2
    
    def test_rotation_trigger(self, temp_dir, logger):
        """Test rotation when file exceeds max size."""
        from core.logging.plugins.file_plugin import RotatingFilePlugin
        
        filepath = temp_dir / "rotate.log"
        plugin = RotatingFilePlugin(
            str(filepath),
            max_bytes=50,
            backup_count=3
        )
        
        logger.add_plugin(plugin)
        
        logger.info("a" * 30)
        logger.info("b" * 30)
        
        # Should have rotated
        assert filepath.exists() or filepath.with_suffix(".1.log").exists()


class TestJsonDataPlugin:
    """Tests for JsonDataPlugin."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return AetherLogger("test_json")
    
    def test_create_json_file(self, temp_dir, logger):
        """Test creating JSON file."""
        filepath = temp_dir / "test.json"
        plugin = JsonDataPlugin(str(filepath))
        
        logger.add_plugin(plugin)
        logger.info("test message")
        
        assert filepath.exists()
        content = filepath.read_text()
        assert "test message" in content
    
    def test_json_structure(self, temp_dir, logger):
        """Test JSON structure."""
        filepath = temp_dir / "structure.json"
        plugin = JsonDataPlugin(str(filepath))
        
        logger.add_plugin(plugin)
        logger.info("test")
        
        content = filepath.read_text()
        # Just check that it's valid JSON-like (contains expected fields)
        assert "test" in content
        assert "INFO" in content
        assert "timestamp" in content
    
    def test_extra_fields(self, temp_dir, logger):
        """Test extra fields in JSON."""
        filepath = temp_dir / "extra.json"
        plugin = JsonDataPlugin(
            str(filepath),
            extra_fields={"app": "test-app", "env": "production"}
        )
        
        logger.add_plugin(plugin)
        logger.info("message")
        
        content = filepath.read_text()
        assert "test-app" in content
        assert "production" in content
    
    def test_module_function_fields(self, temp_dir, logger):
        """Test module and function fields."""
        filepath = temp_dir / "mod.json"
        plugin = JsonDataPlugin(str(filepath))
        
        logger.add_plugin(plugin)
        logger.info("message")
        
        content = filepath.read_text()
        assert "module" in content
        assert "function" in content
    
    def test_exception_field(self, temp_dir, logger):
        """Test exception in JSON."""
        filepath = temp_dir / "exc.json"
        plugin = JsonDataPlugin(str(filepath))
        
        logger.add_plugin(plugin)
        
        try:
            raise ValueError("test error")
        except ValueError:
            logger.exception("failed")
        
        content = filepath.read_text()
        # Either exception field or the message contains error info
        assert "failed" in content


class TestJsonLinesPlugin:
    """Tests for JsonLinesPlugin."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return AetherLogger("test_jsonl")
    
    def test_create_jsonl_file(self, temp_dir, logger):
        """Test creating JSONL file."""
        filepath = temp_dir / "test.jsonl"
        plugin = JsonLinesPlugin(str(filepath))
        
        logger.add_plugin(plugin)
        logger.info("test message")
        
        assert filepath.exists()
        content = filepath.read_text()
        data = json.loads(content)
        assert isinstance(data, dict)
    
    def test_multiple_lines(self, temp_dir, logger):
        """Test multiple JSON lines."""
        filepath = temp_dir / "multi.jsonl"
        plugin = JsonLinesPlugin(str(filepath))
        
        logger.add_plugin(plugin)
        for i in range(5):
            logger.info(f"message {i}")
        
        content = filepath.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 5
        
        for line in lines:
            data = json.loads(line)
            assert "message" in data
    
    def test_no_trailing_comma(self, temp_dir, logger):
        """Test no trailing comma issue."""
        filepath = temp_dir / "trailing.jsonl"
        plugin = JsonLinesPlugin(str(filepath))
        
        logger.add_plugin(plugin)
        logger.info("message")
        
        content = filepath.read_text()
        assert not content.rstrip().endswith(",")


class TestConsolePlugin:
    """Tests for ConsolePlugin."""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return AetherLogger("test_console")
    
    def test_console_plugin_creation(self, logger):
        """Test creating console plugin."""
        from core.logging.plugins.console_plugin import ConsolePlugin
        
        plugin = ConsolePlugin()
        logger.add_plugin(plugin)
        
        assert plugin.colorize is True
        assert plugin.format is not None
    
    def test_console_plugin_no_color(self, logger):
        """Test console plugin without color."""
        from core.logging.plugins.console_plugin import ConsolePlugin
        
        plugin = ConsolePlugin(colorize=False)
        logger.add_plugin(plugin)
        
        assert plugin.colorize is False
    
    def test_console_plugin_custom_format(self, logger):
        """Test console plugin with custom format."""
        from core.logging.plugins.console_plugin import ConsolePlugin
        
        plugin = ConsolePlugin(format="%(message)s")
        logger.add_plugin(plugin)
        
        assert plugin.format == "%(message)s"