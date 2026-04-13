# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Central logging manager for Aetheris.
Provides dual logging: framework log (for developers) and project log (for end users).
Supports pluggable connectors (plugins) to handle logs.
"""
import logging
import os
from pathlib import Path
from typing import List, Optional, Union

from .base_plugin import AetherLogPlugin


class AetherLogger:
    """Central logger that manages plugins and dispatches log records.
    
    Usage:
        from core.logging import framework_logger, project_logger
        
        # Add plugins
        framework_logger.add_plugin(StandardFilePlugin("logs/aetheris_core.log"))
        project_logger.add_plugin(StandardFilePlugin("logs/my_project.log"))
        
        # Log messages
        framework_logger.info("Engine loaded successfully")
        project_logger.info("User logged in")
    """
    
    def __init__(self, name: str, level: int = logging.DEBUG):
        self._name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.propagate = False
        
        self._handlers: List[AetherLogPlugin] = []
        self._is_initialized = False
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def plugins(self) -> List[AetherLogPlugin]:
        return self._handlers
    
    def add_plugin(self, plugin: AetherLogPlugin) -> None:
        """Connect a new plugin to the log flow."""
        if not isinstance(plugin, AetherLogPlugin):
            raise TypeError(f"Plugin must inherit from AetherLogPlugin, got {type(plugin)}")
        self._handlers.append(plugin)
        self._logger.debug(f"Plugin {plugin.__class__.__name__} added to {self._name}")
    
    def remove_plugin(self, plugin: AetherLogPlugin) -> bool:
        """Remove a plugin from the log flow.
        
        Returns:
            True if plugin was found and removed, False otherwise.
        """
        try:
            self._handlers.remove(plugin)
            self._logger.debug(f"Plugin {plugin.__class__.__name__} removed from {self._name}")
            return True
        except ValueError:
            return False
    
    def set_level(self, level: Union[int, str]) -> None:
        """Set the minimum log level.
        
        Args:
            level: Can be an int (logging.DEBUG, etc.) or string ("DEBUG", "INFO", etc.)
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        self._logger.setLevel(level)
    
    def _dispatch(self, level: int, msg: str, *args, **kwargs) -> None:
        """Create a log record and dispatch to all connected plugins."""
        if not self._handlers:
            return
            
        record = self._logger.makeRecord(
            self._name, level, fn="", lno=0, msg=msg, args=args, exc_info=None
        )
        
        for plugin in self._handlers:
            try:
                plugin.emit(record)
            except Exception as e:
                self._logger.error(f"Plugin {plugin.__class__.__name__} failed: {e}")
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log a debug message."""
        self._dispatch(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Log an info message."""
        self._dispatch(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log a warning message."""
        self._dispatch(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Log an error message."""
        self._dispatch(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log a critical message."""
        self._dispatch(logging.CRITICAL, msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs) -> None:
        """Log an exception with traceback."""
        self._dispatch(logging.ERROR, msg, *args, exc_info=True, **kwargs)
    
    def log(self, level: int, msg: str, *args, **kwargs) -> None:
        """Log a message with custom level."""
        self._dispatch(level, msg, *args, **kwargs)
    
    def shutdown(self) -> None:
        """Clean up all plugins. Call when shutting down the application."""
        for plugin in self._handlers:
            try:
                plugin.cleanup()
            except Exception as e:
                self._logger.error(f"Plugin cleanup failed: {e}")
        self._handlers.clear()


def get_logger(name: str) -> AetherLogger:
    """Get or create a logger by name.
    
    Args:
        name: The name for the logger.
    
    Returns:
        A new AetherLogger instance.
    """
    return AetherLogger(name)


# Global instances
framework_logger = AetherLogger("AETHERIS_FRAMEWORK")
project_logger = AetherLogger("AETHERIS_PROJECT")


def init_framework_logging(
    log_dir: str = "logs",
    default_level: str = "INFO",
    create_default_plugins: bool = True
) -> None:
    """Initialize framework logging with default configuration.
    
    This is called automatically when importing from core.logging,
    but can be called manually to customize configuration.
    
    Args:
        log_dir: Directory to store log files (default: "logs")
        default_level: Default log level (default: "INFO")
        create_default_plugins: If True, creates StandardFilePlugin automatically
    """
    from .plugins import StandardFilePlugin
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    framework_logger.set_level(default_level)
    project_logger.set_level(default_level)
    
    if create_default_plugins:
        framework_file = StandardFilePlugin(str(log_path / "aetheris_framework.log"))
        framework_logger.add_plugin(framework_file)
        
        project_file = StandardFilePlugin(str(log_path / "aetheris_project.log"))
        project_logger.add_plugin(project_file)
    
    framework_logger.info(f"Framework logging initialized (level: {default_level})")


# Auto-initialize on import
def _auto_init():
    """Auto-initialize logging when module is imported."""
    env_level = os.getenv("AETHERIS_LOG_LEVEL", "INFO")
    init_framework_logging(
        log_dir=os.getenv("AETHERIS_LOG_DIR", "logs"),
        default_level=env_level,
        create_default_plugins=os.getenv("AETHERIS_AUTO_LOG", "1") == "1"
    )


# Only auto-init if explicitly enabled
if os.getenv("AETHERIS_AUTO_LOG", "0") == "1":
    _auto_init()