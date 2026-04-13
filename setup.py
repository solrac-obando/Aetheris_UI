# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Aetheris v1.0 - Setup Configuration

This setup.py compiles ONLY core/aether_math.py to C for maximum performance
while keeping the rest of the framework as readable Python.
"""
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
from Cython.Build import cythonize
import numpy as np


class CustomBuildExt(build_ext):
    """Custom build_ext to handle Cython compilation properly."""

    def build_extensions(self):
        # Compile with optimization flags
        for ext in self.extensions:
            ext.extra_compile_args.extend(["-O3", "-ffast-math", "-march=native"])
        super().build_extensions()


# ============================================================
# CYTHON EXTENSION: Only compile core/aether_math.py
# ============================================================
aether_math_extension = Extension(
    name="core._aether_math",  # Results in core/_aether_math.so
    sources=["core/aether_math.py"],
    include_dirs=[np.get_include()],
    language="c",
)

setup(
    name="aetheris",
    version="1.6.1",
    description=(
        "High-performance physics-based UI engine driven by linear algebra "
        "for Python & WebAssembly"
    ),
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Carlos Ivan Obando Aure",
    author_email="solracivan.aure@gmail.com",
    url="https://github.com/carlosobando/aetheris-ui",

    # SEO-optimized keywords for PyPI discoverability
    keywords=[
        "physics-engine", "linear-algebra", "ui-framework", "rendering-engine",
        "scientific-visualization", "gpu-rendering", "webassembly",
        "data-visualization", "dashboard", "data-science", "charts",
        "real-time-graphics", "animation", "interactive-ui",
        "pyodide", "kivy", "moderngl", "webgl", "flask",
        "cython", "numba", "gpu-acceleration", "high-performance",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Cython",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries",
        "Operating System :: OS Independent",
    ],
    license="Apache-2.0",
    license_files=["LICENSE"],
    
    # Find all public packages (excludes stress/attacks automatically via MANIFEST.in)
    packages=find_packages(include=["core*", "demo*", "wasm*", "templates*"]),
    
    python_requires=">=3.12",
    
    # Core dependencies
    install_requires=[
        "numpy>=1.26.4",
        "numba>=0.59.1",
        "moderngl>=5.10.0",
        "moderngl-window>=2.4.6",
        "Pillow>=10.2.0",
        "kivy>=2.3.0",
        "Flask>=3.0.2",
    ],
    
    # Build dependencies (required for Cython)
    setup_requires=[
        "Cython>=3.0.0",
        "numpy>=1.26.4",
    ],
    
    extras_require={
        "web": ["xvfbwrapper>=0.2.9"],
        "dev": [
            "pytest>=8.1.1",
            "pytest-asyncio>=0.23.6",
            "pytest-cov>=4.0.0",
        ],
    },
    
    entry_points={
        "console_scripts": [
            "aetheris=main:main",
        ],
    },
    
    # Cython: compile ONLY core/aether_math.py
    ext_modules=cythonize(
        [aether_math_extension],
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
        },
        force=False,  # Only rebuild if needed
    ),
    
    cmdclass={"build_ext": CustomBuildExt},
)