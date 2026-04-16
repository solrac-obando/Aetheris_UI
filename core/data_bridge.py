# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Aether-Data: Unified Database Bridge for Aetheris UI.

Provides a unified interface for populating UI elements from local (SQLite)
and remote (PostgreSQL via REST proxy) data sources.

WASM Compatible: SQLiteProvider uses Pyodide's virtual filesystem paths.
Security: RemoteAetherProvider acts as a REST proxy - never exposes DB credentials.

Aether-Guard Compliance: All data normalization uses epsilon-protected division
and clamped output ranges to prevent physics engine explosions.
"""
import json
import os
import warnings
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np

# sqlite3 is unvendored in Pyodide — import lazily only when needed
_SQLITE_AVAILABLE = False
try:
    import sqlite3
    _SQLITE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    pass


# ============================================================================
# Aether-Data Configuration Constants
# ============================================================================

# Normalization defaults (Min-Max Scaling target range in pixels)
DATA_NORMALIZE_MIN = 10.0
DATA_NORMALIZE_MAX = 500.0

# Vector-to-tensor scaling factor (embedding units to physics force units)
VECTOR_TENSOR_SCALE = 100.0

# Network timeouts (seconds)
REMOTE_CONNECT_TIMEOUT = 5
REMOTE_REQUEST_TIMEOUT = 10

# Epsilon for safe division in normalization
NORMALIZATION_EPSILON = 1e-9


# ============================================================================
# Algebraic Data Normalization Utilities
# ============================================================================

def min_max_scale(value: float, data_min: float, data_max: float,
                  target_min: float = DATA_NORMALIZE_MIN,
                  target_max: float = DATA_NORMALIZE_MAX) -> float:
    """
    Min-Max Scaling (Linear Algebra normalization) with Aether-Guard protection.
    
    Scales a value from [data_min, data_max] to [target_min, target_max].
    Formula: scaled = target_min + (value - data_min) * (target_max - target_min) / (data_max - data_min)
    
    Aether-Guard: Uses epsilon-protected division to prevent division-by-zero
    when data_min equals data_max. Output is clamped to [target_min, target_max].
    
    Args:
        value: The value to scale
        data_min: Minimum value in the source data
        data_max: Maximum value in the source data
        target_min: Minimum of the target range (default: DATA_NORMALIZE_MIN)
        target_max: Maximum of the target range (default: DATA_NORMALIZE_MAX)
        
    Returns:
        Scaled value clamped to [target_min, target_max].
    """
    denom = data_max - data_min
    if abs(denom) < NORMALIZATION_EPSILON:
        return (target_min + target_max) / 2.0  # Return midpoint if no range
    
    ratio = (value - data_min) / denom
    ratio = max(0.0, min(1.0, ratio))  # Clamp to [0, 1]
    return target_min + ratio * (target_max - target_min)


def normalize_column(values: List[float], target_min: float = DATA_NORMALIZE_MIN,
                     target_max: float = DATA_NORMALIZE_MAX) -> List[float]:
    """
    Normalize an entire column of values using Min-Max scaling.
    
    Args:
        values: List of source values
        target_min: Minimum of target range
        target_max: Maximum of target range
        
    Returns:
        List of normalized values.
    """
    if not values:
        return []
    
    data_min = min(values)
    data_max = max(values)
    
    return [min_max_scale(v, data_min, data_max, target_min, target_max) for v in values]


def vector_to_tensor(vector: List[float], scale: float = VECTOR_TENSOR_SCALE) -> np.ndarray:
    """
    Convert a PostgreSQL vector (list of floats) into a StateTensor force.
    
    This allows "Visualizing AI Embeddings" as physical particles.
    The vector components are scaled and used as a force vector [fx, fy, fw, fh].
    
    For vectors longer than 4 dimensions, the first 4 components are used.
    For shorter vectors, remaining components are zero-padded.
    
    Args:
        vector: List of floats (AI embedding / PostgreSQL vector)
        scale: Scaling factor to convert embedding units to physics force units
        
    Returns:
        numpy.array of shape (4,) dtype float32 - force vector [fx, fy, fw, fh]
    """
    force = np.zeros(4, dtype=np.float32)
    
    for i in range(min(len(vector), 4)):
        force[i] = np.float32(vector[i] * scale)
    
    return force


# ============================================================================
# Provider Interface
# ============================================================================

class BaseAetherProvider(ABC):
    """
    Abstract base class for Aetheris UI data providers.
    
    Implementations must provide CRUD operations for UI element states
    and proper connection lifecycle management.
    """
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the data source."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the data source."""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a query and return results as list of dictionaries.
        
        Args:
            query: SQL query or API endpoint path
            params: Query parameters
            
        Returns:
            List of dictionaries, one per row/result.
        """
        pass
    
    @abstractmethod
    def insert_element_state(self, element_id: str, state: Dict[str, Any]) -> bool:
        """
        Save an element's state to the data source.
        
        Args:
            element_id: Unique identifier for the element
            state: Dictionary with x, y, w, h, color, z, etc.
            
        Returns:
            True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_element_state(self, element_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an element's state from the data source.
        
        Args:
            element_id: Unique identifier for the element
            
        Returns:
            Dictionary with element state, or None if not found.
        """
        pass
    
    @abstractmethod
    def delete_element_state(self, element_id: str) -> bool:
        """
        Delete an element's state from the data source.
        
        Args:
            element_id: Unique identifier for the element
            
        Returns:
            True if successful, False otherwise.
        """
        pass


# ============================================================================
# SQLite Provider (Local Persistence)
# ============================================================================

class SQLiteProvider(BaseAetherProvider):
    """
    SQLite-based data provider for local persistence.
    
    WASM Compatible: Uses Pyodide's virtual filesystem paths.
    Default path: /home/pyodide/aetheris_data.db (WASM) or ./aetheris_data.db (Desktop).
    
    Connection Safety: Implements __del__ and context manager protocol
    to ensure connections are always closed, even on exceptions.
    """
    
    DEFAULT_PATH_WASM = "/home/pyodide/aetheris_data.db"
    DEFAULT_PATH_DESKTOP = "./aetheris_data.db"
    
    CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS element_states (
            element_id TEXT PRIMARY KEY,
            x REAL NOT NULL DEFAULT 0.0,
            y REAL NOT NULL DEFAULT 0.0,
            w REAL NOT NULL DEFAULT 100.0,
            h REAL NOT NULL DEFAULT 100.0,
            r REAL NOT NULL DEFAULT 1.0,
            g REAL NOT NULL DEFAULT 1.0,
            b REAL NOT NULL DEFAULT 1.0,
            a REAL NOT NULL DEFAULT 1.0,
            z INTEGER NOT NULL DEFAULT 0,
            metadata TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the SQLite provider.
        
        Args:
            db_path: Path to the SQLite database file.
                     Defaults to WASM or Desktop path based on environment.
        """
        if db_path is None:
            # Detect WASM environment
            if os.path.exists("/home/pyodide"):
                db_path = self.DEFAULT_PATH_WASM
            else:
                db_path = self.DEFAULT_PATH_DESKTOP
        
        self.db_path = db_path
        self._conn = None
    
    def __del__(self):
        """Ensure connection is closed when provider is garbage collected."""
        self.disconnect()
    
    def __enter__(self):
        """Context manager entry - establishes connection."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes connection regardless of exception."""
        self.disconnect()
        return False  # Don't suppress exceptions
    
    def connect(self) -> None:
        """Establish connection to SQLite database."""
        if self._conn is not None:
            return  # Already connected
        
        if not _SQLITE_AVAILABLE:
            warnings.warn("sqlite3 is not available in this environment (Pyodide: run await pyodide.loadPackage('sqlite3'))")
            self._conn = None
            return
        
        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(self.db_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            
            # Create table if not exists
            cursor = self._conn.cursor()
            cursor.execute(self.CREATE_TABLE_SQL)
            self._conn.commit()
        except sqlite3.Error as e:
            warnings.warn(f"SQLite connection failed: {e}")
            self._conn = None
    
    def disconnect(self) -> None:
        """Close connection to SQLite database. Safe to call multiple times."""
        if self._conn:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            finally:
                self._conn = None
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as list of dictionaries.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries, one per row.
        """
        if not self._conn:
            self.connect()
        if not self._conn:
            return []
        
        try:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            return []
        except sqlite3.Error as e:
            warnings.warn(f"SQLite query failed: {e}")
            return []
    
    def insert_element_state(self, element_id: str, state: Dict[str, Any]) -> bool:
        """Save an element's state to SQLite."""
        if not self._conn:
            self.connect()
        if not self._conn:
            return False
        
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO element_states 
                (element_id, x, y, w, h, r, g, b, a, z, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                element_id,
                float(state.get('x', 0.0)),
                float(state.get('y', 0.0)),
                float(state.get('w', 100.0)),
                float(state.get('h', 100.0)),
                float(state.get('r', 1.0)),
                float(state.get('g', 1.0)),
                float(state.get('b', 1.0)),
                float(state.get('a', 1.0)),
                int(state.get('z', 0)),
                json.dumps(state.get('metadata', {})),
            ))
            self._conn.commit()
            return True
        except (sqlite3.Error, ValueError, TypeError) as e:
            warnings.warn(f"SQLite insert failed: {e}")
            return False
    
    def get_element_state(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an element's state from SQLite."""
        if not self._conn:
            self.connect()
        if not self._conn:
            return None
        
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM element_states WHERE element_id = ?", (element_id,))
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                if result.get('metadata'):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        result['metadata'] = {}
                return result
            return None
        except sqlite3.Error as e:
            warnings.warn(f"SQLite get failed: {e}")
            return None
    
    def delete_element_state(self, element_id: str) -> bool:
        """Delete an element's state from SQLite."""
        if not self._conn:
            self.connect()
        if not self._conn:
            return False
        
        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM element_states WHERE element_id = ?", (element_id,))
            self._conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            warnings.warn(f"SQLite delete failed: {e}")
            return False
    
    def get_all_states(self) -> List[Dict[str, Any]]:
        """Retrieve all element states."""
        return self.execute_query("SELECT * FROM element_states ORDER BY z ASC")


# ============================================================================
# Remote Aether Provider (PostgreSQL via REST Proxy)
# ============================================================================

class RemoteAetherProvider(BaseAetherProvider):
    """
    Remote data provider that communicates with a server-side PostgreSQL database
    via REST/JSON proxy.
    
    Security: This provider NEVER connects directly to PostgreSQL from the client.
    All database operations go through the server's /api/v1/db-bridge endpoint,
    protecting credentials and enabling server-side validation.
    
    WASM Compatible: Uses standard urllib requests (no external dependencies).
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the remote provider.
        
        Args:
            base_url: Base URL of the Aetheris server.
        """
        self.base_url = base_url.rstrip('/')
        self._connected = False
    
    def connect(self) -> None:
        """Verify connectivity to the server."""
        try:
            import urllib.request
            import urllib.error
            
            url = f"{self.base_url}/api/v1/db-bridge"
            req = urllib.request.Request(url, method='GET')
            req.add_header('Content-Type', 'application/json')
            
            response = urllib.request.urlopen(req, timeout=REMOTE_CONNECT_TIMEOUT)
            if response.status == 200:
                self._connected = True
                return
        except Exception:
            pass
        
        self._connected = False
        warnings.warn("Failed to connect to remote Aetheris server")
    
    def disconnect(self) -> None:
        """Mark connection as closed."""
        self._connected = False
    
    def _make_request(self, method: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a REST request to the server's db-bridge endpoint.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            payload: Request body
            
        Returns:
            Response JSON as dictionary.
        """
        import urllib.request
        import urllib.error
        
        url = f"{self.base_url}/api/v1/db-bridge"
        data = json.dumps(payload or {}).encode('utf-8') if payload else None
        
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header('Content-Type', 'application/json')
        
        try:
            response = urllib.request.urlopen(req, timeout=REMOTE_REQUEST_TIMEOUT)
            return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            warnings.warn(f"Remote request failed: {e.code} {e.reason}")
            return {"error": str(e), "data": []}
        except Exception as e:
            warnings.warn(f"Remote request error: {e}")
            return {"error": str(e), "data": []}
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query via the server proxy."""
        result = self._make_request('POST', {
            "action": "query",
            "query": query,
            "params": list(params),
        })
        return result.get("data", [])
    
    def insert_element_state(self, element_id: str, state: Dict[str, Any]) -> bool:
        """Save an element's state via the server proxy."""
        result = self._make_request('POST', {
            "action": "insert",
            "element_id": element_id,
            "state": state,
        })
        return result.get("success", False)
    
    def get_element_state(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an element's state via the server proxy."""
        result = self._make_request('POST', {
            "action": "get",
            "element_id": element_id,
        })
        data = result.get("data")
        return data[0] if data and len(data) > 0 else None
    
    def delete_element_state(self, element_id: str) -> bool:
        """Delete an element's state via the server proxy."""
        result = self._make_request('POST', {
            "action": "delete",
            "element_id": element_id,
        })
        return result.get("success", False)
