# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Aetheris Logging System.

Dual logging:
- framework_logger: For framework developers and maintainers
- project_logger: For end-user projects

Usage:
    from core.logging import framework_logger, project_logger
    from core.logging.plugins import StandardFilePlugin
    
    # Add file output
    framework_logger.add_plugin(StandardFilePlugin("logs/framework.log"))
    project_logger.add_plugin(StandardFilePlugin("logs/project.log"))
    
    # Log messages
    framework_logger.info("Engine loaded")
    project_logger.info("App started")
"""
from .manager import AetherLogger, framework_logger, project_logger, init_framework_logging
from .base_plugin import AetherLogPlugin

__all__ = [
    "AetherLogger",
    "AetherLogPlugin", 
    "framework_logger",
    "project_logger",
    "init_framework_logging",
]