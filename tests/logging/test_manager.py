# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Tests for Aetheris Logging System.
"""
import pytest
import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logging import AetherLogger, framework_logger, project_logger
from core.logging.base_plugin import AetherLogPlugin
from core.logging.manager import get_logger, init_framework_logging


class TestAetherLogger:
    """Tests for the AetherLogger class."""
    
    def test_create_logger(self):
        """Test creating a new logger."""
        logger = AetherLogger("test_logger")
        assert logger.name == "test_logger"
        assert logger.plugins == []
    
    def test_add_plugin(self):
        """Test adding a plugin to logger."""
        logger = AetherLogger("test_add")
        
        class TestPlugin(AetherLogPlugin):
            def emit(self, record): pass
        
        plugin = TestPlugin()
        logger.add_plugin(plugin)
        
        assert len(logger.plugins) == 1
        assert logger.plugins[0] == plugin
    
    def test_add_plugin_wrong_type_raises(self):
        """Test that adding wrong type raises TypeError."""
        logger = AetherLogger("test_type")
        
        with pytest.raises(TypeError):
            logger.add_plugin("not a plugin")
    
    def test_remove_plugin(self):
        """Test removing a plugin."""
        logger = AetherLogger("test_remove")
        
        class TestPlugin(AetherLogPlugin):
            def emit(self, record): pass
        
        plugin = TestPlugin()
        logger.add_plugin(plugin)
        result = logger.remove_plugin(plugin)
        
        assert result is True
        assert len(logger.plugins) == 0
    
    def test_remove_nonexistent_plugin(self):
        """Test removing a plugin that doesn't exist."""
        logger = AetherLogger("test_remove_missing")
        
        class TestPlugin(AetherLogPlugin):
            def emit(self, record): pass
        
        plugin = TestPlugin()
        result = logger.remove_plugin(plugin)
        
        assert result is False
    
    def test_set_level_string(self):
        """Test setting level with string."""
        logger = AetherLogger("test_level")
        logger.set_level("DEBUG")
        
        # No error means success
        assert logger._logger.level == logging.DEBUG
    
    def test_set_level_int(self):
        """Test setting level with int."""
        logger = AetherLogger("test_level_int")
        logger.set_level(logging.WARNING)
        
        assert logger._logger.level == logging.WARNING
    
    def test_debug_log(self):
        """Test logging debug message."""
        logger = AetherLogger("test_debug")
        messages = []
        
        class CapturePlugin(AetherLogPlugin):
            def emit(self, record):
                messages.append(record.getMessage())
        
        logger.add_plugin(CapturePlugin())
        logger.debug("debug message")
        
        assert len(messages) == 1
        assert "debug message" in messages[0]
    
    def test_info_log(self):
        """Test logging info message."""
        logger = AetherLogger("test_info")
        messages = []
        
        class CapturePlugin(AetherLogPlugin):
            def emit(self, record):
                messages.append(record.getMessage())
        
        logger.add_plugin(CapturePlugin())
        logger.info("info message")
        
        assert len(messages) == 1
        assert "info message" in messages[0]
    
    def test_warning_log(self):
        """Test logging warning message."""
        logger = AetherLogger("test_warning")
        messages = []
        
        class CapturePlugin(AetherLogPlugin):
            def emit(self, record):
                messages.append(record.getMessage())
        
        logger.add_plugin(CapturePlugin())
        logger.warning("warning message")
        
        assert len(messages) == 1
        assert "warning message" in messages[0]
    
    def test_error_log(self):
        """Test logging error message."""
        logger = AetherLogger("test_error")
        messages = []
        
        class CapturePlugin(AetherLogPlugin):
            def emit(self, record):
                messages.append(record.getMessage())
        
        logger.add_plugin(CapturePlugin())
        logger.error("error message")
        
        assert len(messages) == 1
        assert "error message" in messages[0]
    
    def test_critical_log(self):
        """Test logging critical message."""
        logger = AetherLogger("test_critical")
        messages = []
        
        class CapturePlugin(AetherLogPlugin):
            def emit(self, record):
                messages.append(record.getMessage())
        
        logger.add_plugin(CapturePlugin())
        logger.critical("critical message")
        
        assert len(messages) == 1
        assert "critical message" in messages[0]
    
    def test_log_with_args(self):
        """Test logging with format args."""
        logger = AetherLogger("test_args")
        messages = []
        
        class CapturePlugin(AetherLogPlugin):
            def emit(self, record):
                messages.append(record.getMessage())
        
        logger.add_plugin(CapturePlugin())
        logger.info("value: %s", "test")
        
        assert len(messages) == 1
        assert "value: test" in messages[0]
    
    def test_exception_log(self):
        """Test logging exception with traceback."""
        logger = AetherLogger("test_exception")
        messages = []
        
        class CapturePlugin(AetherLogPlugin):
            def emit(self, record):
                messages.append(record.getMessage())
        
        logger.add_plugin(CapturePlugin())
        
        try:
            raise ValueError("test error")
        except ValueError:
            logger.exception("error occurred")
        
        assert len(messages) == 1
        assert "error occurred" in messages[0]
    
    def test_multiple_plugins(self):
        """Test multiple plugins receiving same log."""
        logger = AetherLogger("test_multi")
        counts = []
        
        class CountingPlugin(AetherLogPlugin):
            def __init__(self):
                self.count = 0
            def emit(self, record):
                self.count += 1
        
        p1 = CountingPlugin()
        p2 = CountingPlugin()
        logger.add_plugin(p1)
        logger.add_plugin(p2)
        
        logger.info("message")
        
        assert p1.count == 1
        assert p2.count == 1
    
    def test_shutdown(self):
        """Test shutdown calls plugin cleanup."""
        logger = AetherLogger("test_shutdown")
        cleaned = []
        
        class CleanPlugin(AetherLogPlugin):
            def emit(self, record): pass
            def cleanup(self):
                cleaned.append(True)
        
        logger.add_plugin(CleanPlugin())
        logger.shutdown()
        
        assert len(cleaned) == 1
        assert len(logger.plugins) == 0
    
    def test_log_without_plugins(self):
        """Test logging when no plugins added."""
        logger = AetherLogger("test_empty")
        # Should not raise
        logger.info("message")
        logger.debug("debug message")
    
    def test_get_logger_factory(self):
        """Test get_logger factory function."""
        logger = get_logger("factory_test")
        
        assert logger.name == "factory_test"
        assert isinstance(logger, AetherLogger)


class CapturePlugin(AetherLogPlugin):
    """Helper plugin for testing."""
    def __init__(self):
        self.messages = []
    
    def emit(self, record):
        self.messages.append(record.getMessage())


class TestFrameworkProjectLoggers:
    """Tests for framework_logger and project_logger."""
    
    def test_framework_logger_exists(self):
        """Test framework_logger exists."""
        assert framework_logger.name == "AETHERIS_FRAMEWORK"
    
    def test_project_logger_exists(self):
        """Test project_logger exists."""
        assert project_logger.name == "AETHERIS_PROJECT"
    
    def test_separate_loggers(self):
        """Test they are separate instances."""
        assert framework_logger.name != project_logger.name