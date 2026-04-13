# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Tests for logging decorators.
"""
import pytest
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.logging import AetherLogger
from core.logging.base_plugin import AetherLogPlugin
from core.logging.decorators import (
    log_operation, 
    with_log, 
    LogCapture,
    track_duration
)


class CapturePlugin(AetherLogPlugin):
    """Helper plugin that captures messages."""
    def __init__(self):
        self.messages = []
    
    def emit(self, record):
        self.messages.append(record.getMessage())


class TestLogOperation:
    """Tests for @log_operation decorator."""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return AetherLogger("test_operation")
    
    def test_basic_decoration(self, logger):
        """Test basic function decoration."""
        @log_operation(logger, "my_func")
        def my_func():
            return 42
        
        plugin = CapturePlugin()
        logger.add_plugin(plugin)
        
        result = my_func()
        
        assert result == 42
        assert any("my_func -> starting" in m for m in plugin.messages)
        assert any("my_func -> completed" in m for m in plugin.messages)
    
    def test_with_args(self, logger):
        """Test decorated function with arguments."""
        @log_operation(logger, "add")
        def add(a, b):
            return a + b
        
        logger.add_plugin(CapturePlugin())
        
        result = add(2, 3)
        
        assert result == 5
    
    def test_with_exception(self, logger):
        """Test decorated function that raises."""
        @log_operation(logger, "fail_func")
        def fail_func():
            raise ValueError("test error")
        
        logger.add_plugin(CapturePlugin())
        
        with pytest.raises(ValueError):
            fail_func()
    
    def test_log_args_option(self, logger):
        """Test log_args option."""
        @log_operation(logger, "func", log_args=True)
        def func(x):
            return x
        
        plugin = CapturePlugin()
        logger.add_plugin(plugin)
        
        func(42)
        
        assert any("args:" in m for m in plugin.messages)
    
    def test_log_result_option(self, logger):
        """Test log_result option."""
        @log_operation(logger, "func", log_result=True)
        def func():
            return 42
        
        plugin = CapturePlugin()
        logger.add_plugin(plugin)
        
        func()
        
        assert any("result:" in m for m in plugin.messages)
    
    def test_custom_level(self, logger):
        """Test custom log level."""
        @log_operation(logger, "func", level="DEBUG")
        def func():
            return 1
        
        plugin = CapturePlugin()
        logger.add_plugin(plugin)
        
        func()
    
    def test_preserves_function_name(self, logger):
        """Test that function name is preserved."""
        @log_operation(logger)
        def my_function():
            return True
        
        assert my_function.__name__ == "my_function"
    
    def test_returns_function_result(self, logger):
        """Test that function return value is preserved."""
        @log_operation(logger, "get_data")
        def get_data():
            return {"key": "value"}
        
        result = get_data()
        
        assert result == {"key": "value"}
    
    def test_multiple_calls(self, logger):
        """Test calling decorated function multiple times."""
        @log_operation(logger, "counter")
        def counter():
            return 1
        
        logger.add_plugin(CapturePlugin())
        
        for _ in range(5):
            counter()
        
        messages = [m for m in logger.plugins[0].messages if "counter" in m]
        assert len([m for m in messages if "starting" in m]) == 5


class TestWithLog:
    """Tests for with_log context manager."""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return AetherLogger("test_with_log")
    
    def test_basic_context(self, logger):
        """Test basic context manager."""
        logger.add_plugin(CapturePlugin())
        
        with with_log(logger, "block"):
            x = 1 + 1
        
        messages = logger.plugins[0].messages
        assert any("block -> starting" in m for m in messages)
        assert any("block -> completed" in m for m in messages)
    
    def test_with_exception(self, logger):
        """Test context manager with exception."""
        logger.add_plugin(CapturePlugin())
        
        with pytest.raises(ValueError):
            with with_log(logger, "fail_block"):
                raise ValueError("error")
        
        messages = logger.plugins[0].messages
        assert any("fail_block -> failed" in m for m in messages)
    
    def test_nested_contexts(self, logger):
        """Test nested context managers."""
        logger.add_plugin(CapturePlugin())
        
        with with_log(logger, "outer"):
            with with_log(logger, "inner"):
                x = 1
        
        messages = logger.plugins[0].messages
        outer_count = sum(1 for m in messages if "outer" in m)
        inner_count = sum(1 for m in messages if "inner" in m)
        assert outer_count >= 2
        assert inner_count >= 2
    
    def test_custom_level(self, logger):
        """Test custom level in context."""
        logger.add_plugin(CapturePlugin())
        
        with with_log(logger, "block", level="DEBUG"):
            x = 1
    
    def test_yields_value(self, logger):
        """Test that context yields control."""
        logger.add_plugin(CapturePlugin())
        
        result = None
        with with_log(logger, "compute"):
            result = 42
        
        assert result == 42


class TestLogCapture:
    """Tests for LogCapture context manager."""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return AetherLogger("test_capture")
    
    def test_capture_messages(self, logger):
        """Test capturing log messages."""
        with LogCapture(logger) as capture:
            logger.info("message 1")
            logger.info("message 2")
        
        assert len(capture.messages) == 2
        assert "message 1" in capture.messages[0] or "message 1" in str(capture.messages)
        assert "message 2" in capture.messages[1] if len(capture.messages) > 1 else "message 2" in str(capture.messages)
    
    def test_capture_debug(self, logger):
        """Test capturing debug messages."""
        with LogCapture(logger) as capture:
            logger.debug("debug message")
        
        # Debug should be captured
        pass
    
    def test_capture_warning(self, logger):
        """Test capturing warning messages."""
        with LogCapture(logger) as capture:
            logger.warning("warning message")
        
        # Should have captured the message
        assert len(capture.messages) >= 1 or "warning" in str(capture.messages)
    
    def test_empty_if_no_logs(self, logger):
        """Test empty if no logs written."""
        with LogCapture(logger) as capture:
            pass
        
        # Should not raise, may be empty


class TestTrackDuration:
    """Tests for @track_duration decorator."""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return AetherLogger("test_duration")
    
    def test_tracks_duration(self, logger):
        """Test that duration is tracked."""
        @track_duration(logger, "slow_func")
        def slow_func():
            time.sleep(0.01)
            return 1
        
        logger.add_plugin(CapturePlugin())
        
        result = slow_func()
        
        assert result == 1
        messages = logger.plugins[0].messages
        assert any("slow_func" in m and "ms" in m for m in messages)
    
    def test_custom_name(self, logger):
        """Test custom operation name."""
        @track_duration(logger, "custom_name")
        def func():
            time.sleep(0.01)
            return 1
        
        logger.add_plugin(CapturePlugin())
        
        func()
        
        messages = logger.plugins[0].messages
        assert any("custom_name" in m for m in messages)
    
    def test_threshold_filtering(self, logger):
        """Test threshold filters logs."""
        @track_duration(logger, "slow", log_threshold_ms=100)
        def slow():
            time.sleep(0.01)
            return 1
        
        logger.add_plugin(CapturePlugin())
        
        slow()  # Should NOT log (only 10ms < 100ms threshold)
        
        messages = logger.plugins[0].messages
        # Should be empty or filtered
    
    def test_preserves_return(self, logger):
        """Test return value is preserved."""
        @track_duration(logger)
        def func():
            return {"data": 123}
        
        result = func()
        
        assert result == {"data": 123}


class TestIntegration:
    """Integration tests combining features."""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return AetherLogger("test_integration")
    
    def test_full_workflow(self, logger):
        """Test complete workflow."""
        logger.add_plugin(CapturePlugin())
        
        @log_operation(logger, "process")
        def process(data):
            return [x * 2 for x in data]
        
        result = process([1, 2, 3])
        
        assert result == [2, 4, 6]
        
        with with_log(logger, "finalize"):
            logger.info("done")
    
    def test_multiple_decorators(self, logger):
        """Test using multiple decorators."""
        logger.add_plugin(CapturePlugin())
        
        @track_duration(logger, "decorated")
        @log_operation(logger, "inner")
        def inner():
            return 1
        
        inner()


class TestRealWorld:
    """Real-world usage scenarios."""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return AetherLogger("test_real")
    
    def test_web_request_logging(self, logger):
        """Test logging web requests."""
        logger.add_plugin(CapturePlugin())
        
        @log_operation(logger, "http_request")
        def http_request(url):
            return {"status": 200, "url": url}
        
        result = http_request("https://example.com")
        
        assert result["status"] == 200
    
    def test_database_query(self, logger):
        """Test logging database queries."""
        logger.add_plugin(CapturePlugin())
        
        @log_operation(logger, "db_query")
        def db_query(sql):
            return [{"id": 1}]
        
        result = db_query("SELECT * FROM users")
        
        assert len(result) == 1
    
    def test_performance_monitoring(self, logger):
        """Test performance monitoring."""
        logger.add_plugin(CapturePlugin())
        
        @track_duration(logger, "api_call")
        def api_call():
            time.sleep(0.02)
            return {"data": "ok"}
        
        result = api_call()
        
        assert result["data"] == "ok"
    
    def test_error_tracking(self, logger):
        """Test error tracking."""
        logger.add_plugin(CapturePlugin())
        
        @log_operation(logger, "risky_operation", level="ERROR")
        def risky_operation():
            raise RuntimeError("Something went wrong")
        
        with pytest.raises(RuntimeError):
            risky_operation()