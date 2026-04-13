# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/tutorial

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

# -- Project information -----------------------------------------------------
project = "Aetheris"
copyright = "2026, Carlos Ivan Obando Aure"
author = "Carlos Ivan Obando Aure"
release = "1.6.1"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output ---------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Autodoc configuration ---------------------------------------------------
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# Napoleon configuration
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True

# Intersphinx configuration
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}