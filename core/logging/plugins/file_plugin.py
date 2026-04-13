# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Standard file plugin - writes logs to a plain text file.
This is the classic .log format that most developers expect.
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..base_plugin import AetherLogPlugin


class StandardFilePlugin(AetherLogPlugin):
    """Plugin that writes logs to a plain text file.
    
    Usage:
        from core.logging.plugins import StandardFilePlugin
        from core.logging import framework_logger
        
        framework_logger.add_plugin(StandardFilePlugin("logs/my_app.log"))
        
        # Or with custom format:
        framework_logger.add_plugin(StandardFilePlugin(
            "logs/my_app.log",
            format="%(asctime)s [%(levelname)s] %(message)s"
        ))
    """
    
    DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    def __init__(
        self,
        filepath: str,
        format: Optional[str] = None,
        date_format: Optional[str] = None,
        encoding: str = "utf-8"
    ):
        self.filepath = Path(filepath)
        self.format = format or self.DEFAULT_FORMAT
        self.date_format = date_format or self.DATE_FORMAT
        self.encoding = encoding
        
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
        self._formatter = logging.Formatter(self.format, self.date_format)
        self._is_first_write = not self.filepath.exists()
    
    def emit(self, record: logging.LogRecord) -> None:
        log_entry = self._formatter.format(record)
        
        with open(self.filepath, "a", encoding=self.encoding) as f:
            f.write(log_entry + "\n")
    
    def cleanup(self) -> None:
        pass


class RotatingFilePlugin(AetherLogPlugin):
    """Plugin that writes logs with rotation (keeps N backup files).
    
    Usage:
        from core.logging.plugins import RotatingFilePlugin
        
        framework_logger.add_plugin(RotatingFilePlugin(
            "logs/app.log",
            max_bytes=1_000_000,  # 1 MB
            backup_count=3       # Keep 3 backups
        ))
    """
    
    DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    def __init__(
        self,
        filepath: str,
        max_bytes: int = 1_000_000,
        backup_count: int = 3,
        format: Optional[str] = None,
        date_format: Optional[str] = None,
        encoding: str = "utf-8"
    ):
        self.filepath = Path(filepath)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.format = format or self.DEFAULT_FORMAT
        self.date_format = date_format or self.DATE_FORMAT
        self.encoding = encoding
        
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
        self._formatter = logging.Formatter(self.format, self.date_format)
    
    def _rotate_if_needed(self) -> None:
        if not self.filepath.exists():
            return
            
        if self.filepath.stat().st_size >= self.max_bytes:
            self._rotate()
    
    def _rotate(self) -> None:
        for i in range(self.backup_count - 1, 0, -1):
            src = self.filepath.with_suffix(f".{i}.log")
            dst = self.filepath.with_suffix(f".{i + 1}.log")
            if src.exists():
                src.rename(dst)
        
        base = self.filepath.with_suffix(".1.log")
        self.filepath.rename(base)
    
    def emit(self, record: logging.LogRecord) -> None:
        self._rotate_if_needed()
        
        log_entry = self._formatter.format(record)
        
        with open(self.filepath, "a", encoding=self.encoding) as f:
            f.write(log_entry + "\n")
    
    def cleanup(self) -> None:
        pass