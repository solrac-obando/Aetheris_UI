# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Base plugin contract for Aetheris logging system.
Any developer can create a custom plugin by inheriting from AetherLogPlugin.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any


class AetherLogPlugin(ABC):
    """Contract base class for any logging plugin in Aetheris.
    
    To create a custom plugin:
        1. Inherit from AetherLogPlugin
        2. Implement the emit() method
        3. Register it with framework_logger.add_plugin() or project_logger.add_plugin()
    
    Example:
        class CustomPlugin(AetherLogPlugin):
            def __init__(self, config):
                self.config = config
            
            def emit(self, record):
                # Custom logic to handle the log record
                pass
    """
    
    @abstractmethod
    def emit(self, record: logging.LogRecord) -> None:
        """Method that every plugin must implement to process the log.
        
        Args:
            record: A logging.LogRecord object containing:
                - levelname: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                - created: Unix timestamp
                - name: Logger name
                - message: The log message
                - module: Source module
                - funcName: Function name
                - exc_info: Exception info if any
        
        Example:
            def emit(self, record):
                if record.levelname == "ERROR":
                    self.send_alert(record.getMessage())
        """
        pass
    
    def cleanup(self) -> None:
        """Optional cleanup method called when the logger shuts down.
        
        Use this to close connections, flush buffers, etc.
        """
        pass