# =============================================================================
# Aetheris UI Framework Documentation
# =============================================================================
#
# Welcome to the Aetheris documentation!
# This file uses reStructuredText format with Sphinx directives.
#
# To build the documentation:
#   pip install sphinx sphinx-rtd-theme
#   cd docs
#   make html
#
# =============================================================================

.. include:: ../README.md
   :parser: myst_parser.sphinx_

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   tutorials/quickstart
   tutorials/installation
   tutorials/first-app

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts

   api/core.engine
   api/core.elements
   api/core.aether_math
   api/core.logging

.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics

   tutorials/dual-engine
   tutorials/physics-model
   tutorials/web-deployment

.. toctree::
   :maxdepth: 1
   :caption: Reference

   api/modules
   CHANGELOG

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

License
=======
Apache License 2.0 - See LICENSE file for details.