# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
JSON data plugin - writes logs in JSON format for data analysis.
Ideal for dashboards, data pipelines, and integration with external tools.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..base_plugin import AetherLogPlugin


class JsonDataPlugin(AetherLogPlugin):
    """Plugin that writes logs in JSON format.
    
    This is useful for:
    - Integration with data dashboards (Kibana, Grafana, etc.)
    - Web scraping data pipelines
    - Machine learning training logs
    - Analytics and metrics collection
    
    Usage:
        from core.logging.plugins import JsonDataPlugin
        from core.logging import project_logger
        
        project_logger.add_plugin(JsonDataPlugin("logs/events.json"))
        
        # Or with custom fields:
        project_logger.add_plugin(JsonDataPlugin(
            "logs/events.json",
            extra_fields={"app": "my-app", "env": "production"}
        ))
    """
    
    def __init__(
        self,
        filepath: str,
        extra_fields: Optional[Dict[str, Any]] = None,
        encoding: str = "utf-8"
    ):
        self.filepath = Path(filepath)
        self.extra_fields = extra_fields or {}
        self.encoding = encoding
        
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.filepath.exists():
            self._write_header()
    
    def _write_header(self) -> None:
        """Write JSON array opening."""
        with open(self.filepath, "w", encoding=self.encoding) as f:
            f.write("[\n")
    
    def emit(self, record: logging.LogRecord) -> None:
        log_entry = {
            "timestamp": record.created,
            "iso_timestamp": logging.Formatter().formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_entry["exception"] = self._format_exception(record.exc_info)
        
        log_entry.update(self.extra_fields)
        
        with open(self.filepath, "a", encoding=self.encoding) as f:
            f.write("  " + json.dumps(log_entry, ensure_ascii=False) + ",\n")
    
    def _format_exception(self, exc_info) -> str:
        """Format exception info as string."""
        import traceback
        return "".join(traceback.format_exception(*exc_info))
    
    def cleanup(self) -> None:
        """Fix JSON trailing comma."""
        try:
            with open(self.filepath, "r", encoding=self.encoding) as f:
                content = f.read()
            
            if content.rstrip().endswith(","):
                content = content.rstrip()[:-1] + "\n]"
                
                with open(self.filepath, "w", encoding=self.encoding) as f:
                    f.write(content)
        except Exception:
            pass


class JsonLinesPlugin(AetherLogPlugin):
    """Plugin that writes logs in JSON Lines format (one JSON per line).
    
    This is more efficient for streaming and large logs as it doesn't
    require fixing trailing commas.
    
    Usage:
        from core.logging.plugins import JsonLinesPlugin
        
        project_logger.add_plugin(JsonLinesPlugin("logs/events.jsonl"))
    """
    
    def __init__(
        self,
        filepath: str,
        extra_fields: Optional[Dict[str, Any]] = None,
        encoding: str = "utf-8"
    ):
        self.filepath = Path(filepath)
        self.extra_fields = extra_fields or {}
        self.encoding = encoding
        
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
    
    def emit(self, record: logging.LogRecord) -> None:
        log_entry = {
            "timestamp": record.created,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        
        if record.exc_info:
            log_entry["exception"] = self._format_exception(record.exc_info)
        
        log_entry.update(self.extra_fields)
        
        with open(self.filepath, "a", encoding=self.encoding) as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def _format_exception(self, exc_info) -> str:
        import traceback
        return "".join(traceback.format_exception(*exc_info))
    
    def cleanup(self) -> None:
        pass