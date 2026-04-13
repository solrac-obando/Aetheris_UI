# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Standard logging plugins for Aetheris.
"""
from .file_plugin import StandardFilePlugin, RotatingFilePlugin
from .json_plugin import JsonDataPlugin, JsonLinesPlugin
from .console_plugin import ConsolePlugin, RichConsolePlugin

__all__ = [
    "StandardFilePlugin",
    "RotatingFilePlugin",
    "JsonDataPlugin", 
    "JsonLinesPlugin",
    "ConsolePlugin",
    "RichConsolePlugin",
]