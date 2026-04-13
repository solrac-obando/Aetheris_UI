Aetheris Logging System
======================

Aetheris includes a native dual-logging system with plugin architecture.

Dual Logging
------------

Aetheris provides TWO separate logs:

1. **Framework Logger** (``framework_logger``) - For developers
2. **Project Logger** (``project_logger``) - For end users

Basic Usage
----------

.. code-block:: python

   from core.logging import framework_logger, project_logger
   from core.logging.plugins import StandardFilePlugin
   
   # Framework log (for developer debug)
   framework_logger.add_plugin(StandardFilePlugin("logs/aetheris.log"))
   framework_logger.info("Engine initialized")
   
   # Project log (for application)
   project_logger.add_plugin(StandardFilePlugin("logs/my_app.log"))
   project_logger.info("User logged in")

Logging Decorators
------------------

Aetheris provides decorators for granular logging:

.. code-block:: python

   from core.logging.decorators import log_operation, track_duration
   
   @log_operation(project_logger, "process_data")
   def process(data):
       return transform(data)
   
   @track_duration(framework_logger, "heavy_operation")
   def heavy_operation():
       return compute()

Available Plugins
-----------------

- ``StandardFilePlugin`` - Plain text log file
- ``RotatingFilePlugin`` - Log with rotation
- ``JsonDataPlugin`` - JSON format for analytics
- ``ConsolePlugin`` - Colored console output

API Reference
------------

.. automodule:: core.logging.manager
   :members:

.. automodule:: core.logging.base_plugin
   :members:

.. automodule:: core.logging.decorators
   :members:

Web Security
------------

The logging system automatically converts NaN/Inf to ``null`` for JavaScript compatibility:

.. code-block:: python

   from core.json_utils import to_json
   
   data = {"x": float('nan'), "value": 42}
   json_str = to_json(data)
   # Result: {"x": null, "value": 42}