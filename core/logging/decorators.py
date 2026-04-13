# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Decorators and context managers for logging.
Provides granular logging control for specific functions and code blocks.
"""
import functools
import logging
from typing import Optional, Callable, Union
from contextlib import contextmanager

from .manager import AetherLogger


def log_operation(
    logger: AetherLogger,
    name: Optional[str] = None,
    level: str = "INFO",
    log_args: bool = False,
    log_result: bool = False
):
    """Decorator to automatically log function execution.
    
    Usage:
        from core.logging import project_logger
        from core.logging.decorators import log_operation
        
        @log_operation(project_logger, "my_function")
        def my_function(x, y):
            return x + y
        
        # Or with custom name:
        @log_operation(project_logger, name="custom_name")
        def process_data(data):
            return transform(data)
    
    Args:
        logger: The AetherLogger instance to use
        name: Optional custom name for the log (defaults to function name)
        level: Log level ("DEBUG", "INFO", "WARNING", "ERROR")
        log_args: If True, logs function arguments
        log_result: If True, logs function return value
    """
    def decorator(func: Callable) -> Callable:
        op_name = name or func.__name__
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.log(log_level, f"{op_name} -> starting")
            
            if log_args:
                logger.debug(f"{op_name} | args: {args}, kwargs: {kwargs}")
            
            try:
                result = func(*args, **kwargs)
                logger.log(log_level, f"{op_name} -> completed")
                
                if log_result:
                    logger.debug(f"{op_name} | result: {result}")
                
                return result
            except Exception as e:
                logger.error(f"{op_name} -> failed: {e}")
                raise
        
        return wrapper
    return decorator


@contextmanager
def with_log(logger: AetherLogger, name: str, level: str = "INFO"):
    """Context manager for logging a block of code.
    
    Usage:
        from core.logging import framework_logger
        from core.logging.decorators import with_log
        
        with with_log(framework_logger, "load_data"):
            data = load_external_data()
            process(data)
    
    Args:
        logger: The AetherLogger instance to use
        name: Name for this operation
        level: Log level ("DEBUG", "INFO", "WARNING", "ERROR")
    """
    import logging
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    logger.log(log_level, f"{name} -> starting")
    try:
        yield
        logger.log(log_level, f"{name} -> completed")
    except Exception as e:
        logger.error(f"{name} -> failed: {e}")
        raise


class LogCapture:
    """Context manager that captures logs for inspection.
    
    Useful for testing logging behavior.
    
    Usage:
        from core.logging import project_logger
        from core.logging.decorators import LogCapture
        
        with LogCapture(project_logger) as capture:
            project_logger.info("test message")
        
        assert "test message" in capture.messages
    """
    
    def __init__(self, logger: AetherLogger):
        self.logger = logger
        self.messages = []
        self._original_dispatch = logger._dispatch
        self._capturing = False
    
    def __enter__(self):
        self._capturing = True
        self.messages = []
        
        original_dispatch = self.logger._dispatch
        
        def capture_dispatch(level, msg, *args, **kwargs):
            self.messages.append(msg)
        
        self.logger._dispatch = capture_dispatch
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger._dispatch = self._original_dispatch
        self._capturing = False
        return False


def track_duration(
    logger: AetherLogger,
    name: Optional[str] = None,
    level: str = "INFO",
    log_threshold_ms: Optional[float] = None
):
    """Decorator to log execution duration of a function.
    
    Usage:
        from core.logging import framework_logger
        from core.logging.decorators import track_duration
        
        @track_duration(framework_logger, "heavy_operation")
        def heavy_operation():
            import time
            time.sleep(0.1)
            return "done"
        
        # With threshold (only logs if slower than 100ms):
        @track_duration(framework_logger, slow_threshold_ms=100)
        def maybe_slow():
            import time
            time.sleep(0.05)
    
    Args:
        logger: The AetherLogger instance to use
        name: Optional custom name
        level: Log level
        log_threshold_ms: Only log if duration exceeds this (in milliseconds)
    """
    import time
    import logging
    
    def decorator(func: Callable) -> Callable:
        op_name = name or func.__name__
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                
                if log_threshold_ms is None or duration_ms > log_threshold_ms:
                    logger.log(
                        log_level,
                        f"{op_name} -> {duration_ms:.2f}ms"
                    )
        
        return wrapper
    return decorator