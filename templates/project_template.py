# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Project template with integrated logging.
This file is auto-generated when creating a new Aetheris project.

To customize logging:
    - Edit the plugin configuration below
    - Add custom plugins: framework_logger.add_plugin(YourPlugin())
    - Change log levels: framework_logger.set_level("DEBUG")
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# =============================================================================
# LOGGING SETUP - Framework (for developers)
# =============================================================================
from core.logging import framework_logger
from core.logging.plugins import StandardFilePlugin

# Configure framework logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Default: text file for framework logs
framework_plugin = StandardFilePlugin(
    str(log_dir / "aetheris_framework.log"),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
framework_logger.add_plugin(framework_plugin)

# Set framework log level (DEBUG for development, INFO for production)
# Can be overridden with AETHERIS_LOG_LEVEL env var
framework_logger.set_level("INFO")

# Log framework initialization
framework_logger.info("Framework logging initialized")


# =============================================================================
# LOGGING SETUP - Project (for end users)
# =============================================================================
from core.logging import project_logger

# Default: text file for project logs
project_plugin = StandardFilePlugin(
    str(log_dir / "mi_proyecto.log"),
    format="%(asctime)s | %(levelname)-8s | %(message)s"
)
project_logger.add_plugin(project_plugin)

# Set project log level
project_logger.set_level("INFO")


# =============================================================================
# YOUR APPLICATION CODE
# =============================================================================
def main():
    """Main entry point for the application."""
    project_logger.info("Application starting...")
    
    # Your code here
    from core.engine import AetherEngine
    
    engine = AetherEngine()
    project_logger.info(f"Engine created: {engine}")
    
    # Run the engine
    for frame in range(100):
        data = engine.tick(800, 600)
        if frame % 50 == 0:
            project_logger.debug(f"Frame {frame}: {len(data)} elements")
    
    project_logger.info("Application completed")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        project_logger.error(f"Application crashed: {e}")
        framework_logger.exception(f"Unhandled exception in main: {e}")
        sys.exit(1)
    finally:
        # Clean up logging on exit
        framework_logger.shutdown()
        project_logger.shutdown()