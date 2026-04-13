# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Console plugin - writes colored logs to stdout/stderr.
Useful for development and debugging.
"""
import sys
import logging
from typing import Optional

from ..base_plugin import AetherLogPlugin


COLORS = {
    "DEBUG": "\033[36m",     # Cyan
    "INFO": "\033[32m",      # Green
    "WARNING": "\033[33m",   # Yellow
    "ERROR": "\033[31m",     # Red
    "CRITICAL": "\033[35m",   # Magenta
}
RESET = "\033[0m"


class ConsolePlugin(AetherLogPlugin):
    """Plugin that writes colored logs to console.
    
    Usage:
        from core.logging.plugins import ConsolePlugin
        from core.logging import project_logger
        
        project_logger.add_plugin(ConsolePlugin())
        
        # Or with custom stream:
        project_logger.add_plugin(ConsolePlugin(stream=sys.stderr))
    """
    
    def __init__(
        self,
        stream: Optional[object] = None,
        colorize: bool = True,
        format: Optional[str] = None
    ):
        self.stream = stream or sys.stdout
        self.colorize = colorize
        self.format = format or "[%(levelname)s] %(message)s"
        
        self._formatter = logging.Formatter(self.format)
    
    def emit(self, record: logging.LogRecord) -> None:
        if self.colorize and record.levelname in COLORS:
            color = COLORS[record.levelname]
            message = self._formatter.format(record)
            self.stream.write(f"{color}{message}{RESET}\n")
        else:
            message = self._formatter.format(record)
            self.stream.write(f"{message}\n")
        
        self.stream.flush()
    
    def cleanup(self) -> None:
        pass


class RichConsolePlugin(AetherLogPlugin):
    """Plugin that writes rich formatted logs using the rich library.
    
    Requires: pip install rich
    
    Usage:
        from core.logging.plugins import RichConsolePlugin
        from core.logging import framework_logger
        
        framework_logger.add_plugin(RichConsolePlugin())
    """
    
    def __init__(self, rich_console=None, log_levels: Optional[list] = None):
        try:
            from rich.console import Console
            from rich.logging import RichHandler
            self.rich_available = True
        except ImportError:
            self.rich_available = False
        
        if self.rich_available:
            console = rich_console or Console()
            self.handler = RichHandler(
                console=console,
                rich_tracebacks=True,
                markup=True,
                show_time=True,
                show_path=False
            )
            self._logger = logging.getLogger("rich_plugin")
            self._logger.addHandler(self.handler)
            self._logger.setLevel(logging.DEBUG)
    
    def emit(self, record: logging.LogRecord) -> None:
        if not self.rich_available:
            return
        
        level_map = {
            logging.DEBUG: self._logger.debug,
            logging.INFO: self._logger.info,
            logging.WARNING: self._logger.warning,
            logging.ERROR: self._logger.error,
            logging.CRITICAL: self._logger.critical,
        }
        
        log_func = level_map.get(record.levelno, self._logger.info)
        log_func(record.getMessage())
    
    def cleanup(self) -> None:
        pass