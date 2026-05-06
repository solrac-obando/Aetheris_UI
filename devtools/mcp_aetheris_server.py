# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");

import os
import sys
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
import numpy as np

# Add project root to path for local imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: 'mcp' library not found. Install it with: pip install mcp")
    sys.exit(1)

from core.engine_selector import EngineSelector
from core.dynamic_limits import get_system_profile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-aetheris")

# Initialize FastMCP server
mcp = FastMCP("Aetheris AI Bridge")

# Global engine instance (shared across MCP calls)
_ENGINE: Optional[EngineSelector] = None
_PREFERRED_MODELS: Dict[str, str] = {
    "layout": "qwen2.5-coder:3b",
    "physics": "deepseek-r1:1.5b",
    "general": "llama3.2:3b"
}

def get_engine() -> EngineSelector:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = EngineSelector(engine_type="auto")
    return _ENGINE

# ── Tools ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_engine_telemetry() -> str:
    """
    Returns real-time telemetry from the Aetheris engine.
    Includes active engine type (Python/Rust), element count, and system limits.
    """
    engine = get_engine()
    profile = get_system_profile()
    
    telemetry = {
        "active_engine": engine.engine_type,
        "element_count": engine.element_count,
        "dt_ms": engine.dt * 1000.0,
        "fps_theoretical": 1.0 / engine.dt if engine.dt > 0 else 0,
        "system_limits": {
            "max_elements": profile["engine_limit"],
            "performance_mode": profile["performance_mode"],
            "safety_margin": profile["safety_margin"]
        }
    }
    return json.dumps(telemetry, indent=2)

@mcp.tool()
async def switch_engine(engine_type: str) -> str:
    """
    Switches the physics engine in real-time.
    
    Args:
        engine_type: 'python' (stable, flexible) or 'rust' (high-performance)
    """
    global _ENGINE
    if engine_type not in ["python", "rust"]:
        return f"Error: Invalid engine type '{engine_type}'. Use 'python' or 'rust'."
    
    try:
        # Re-initialize engine with selected type
        _ENGINE = EngineSelector(engine_type=engine_type)
        return f"Successfully switched to {engine_type} engine."
    except Exception as e:
        return f"Failed to switch engine: {str(e)}"

@mcp.tool()
async def query_ai_suggestion(prompt: str, model: str = "qwen2.5-coder:3b") -> str:
    """
    Asks a local AI model (via Ollama or OpenCode) for UI/Physics suggestions.
    
    Args:
        prompt: The request for the AI (e.g. 'Generate a physics-based card layout')
        model: The model to use (default: qwen2.5-coder:3b)
    """
    import httpx
    
    # Try Ollama local API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": f"As an Aetheris UI expert, solve this: {prompt}. Return only valid JSON for the layout intent if possible.",
                    "stream": False
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json().get("response", "No response from model.")
    except Exception as e:
        logger.error(f"Ollama error: {str(e)}")
        return f"Error connecting to AI model ({model}): {str(e)}"

    return "No AI model found at localhost:11434"

@mcp.tool()
async def optimize_workload() -> str:
    """
    Analyzes the current element count and automatically selects the best engine.
    - < 100 elements: Python (Lower overhead)
    - > 100 elements: Rust (HPC)
    """
    engine = get_engine()
    count = engine.element_count
    
    current = engine.engine_type
    target = "rust" if count > 100 else "python"
    
    if current != target:
        await switch_engine(target)
        return f"Optimized: Switched from {current} to {target} due to {count} elements."
    
    return f"Already optimized: Using {current} for {count} elements."

@mcp.tool()
async def get_current_layout() -> str:
    """
    Returns the current UI layout (intent) as a JSON string.
    This allows the AI to see what elements are currently in the engine.
    """
    engine = get_engine()
    # In Aetheris, the current layout is often driven by the metadata bridge
    metadata_json = engine.get_ui_metadata()
    return metadata_json

@mcp.tool()
async def set_preferred_model(task: str, model: str) -> str:
    """
    Sets the preferred AI model for a specific task.
    
    Args:
        task: 'layout', 'physics', or 'general'
        model: Model name (e.g. 'qwen2.5-coder:3b')
    """
    if task not in _PREFERRED_MODELS:
        return f"Error: Task '{task}' not recognized. Use 'layout', 'physics', or 'general'."
    
    _PREFERRED_MODELS[task] = model
    return f"Preferred model for {task} set to {model}."

@mcp.tool()
async def query_aether_expert(prompt: str, task: str = "general") -> str:
    """
    Queries the Aetheris expert using the preferred model for the given task.
    
    Args:
        prompt: Your question or instruction.
        task: 'layout', 'physics', or 'general' (defaults to 'general')
    """
    model = _PREFERRED_MODELS.get(task, _PREFERRED_MODELS["general"])
    return await query_ai_suggestion(prompt, model=model)

@mcp.tool()
async def apply_ui_intent(intent_json: str) -> str:
    """
    Applies a new UI Intent (layout definition) to the active engine.
    
    Args:
        intent_json: A valid Aetheris UI Intent JSON string.
    """
    from core.ui_builder import UIBuilder
    
    try:
        intent = json.loads(intent_json)
        engine = get_engine()
        builder = UIBuilder()
        
        # Clear existing elements if needed? (Depends on engine capability)
        # For now, we just build on top or replace
        builder.build_from_intent(engine, intent)
        
        return f"Successfully applied intent with {len(intent.get('elements', []))} elements."
    except Exception as e:
        return f"Failed to apply intent: {str(e)}"

# ── Entry Point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
