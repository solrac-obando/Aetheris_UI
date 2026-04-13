# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
WASM Adapters for Aetheris UI.

This package provides lightweight alternatives to Pyodide for web rendering,
implementing the Adapter Pattern to support multiple rendering backends.
"""
from wasm.adapters.base import AdapterInterface, RendererCapability, AdapterType

__all__ = [
    "AdapterInterface",
    "RendererCapability",
    "AdapterType",
]