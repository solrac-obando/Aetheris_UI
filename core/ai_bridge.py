# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");

import json
import logging
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger("aetheris.ai")

class AetherAI:
    """
    Native AI Bridge for Aetheris UI.
    Provides a simple interface to local AI models for layout generation and physics optimization.
    """

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self._default_models = {
            "layout": "qwen2.5-coder:3b",
            "physics": "deepseek-r1:1.5b",
            "general": "llama3.2:3b"
        }

    async def generate_layout(self, description: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates an Aetheris UI Intent from a natural language description.
        """
        model = model or self._default_models["layout"]
        prompt = f"Generate an Aetheris UI Intent JSON for: {description}. Return ONLY the JSON."
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                    timeout=30.0
                )
                if response.status_code == 200:
                    text = response.json().get("response", "{}")
                    # Simple JSON extraction in case the model adds chatter
                    start = text.find("{")
                    end = text.rfind("}") + 1
                    if start >= 0 and end > 0:
                        return json.loads(text[start:end])
        except Exception as e:
            logger.error(f"AI Generation failed: {str(e)}")
        
        return {"elements": []}

    async def analyze_performance(self, telemetry: Dict[str, Any]) -> str:
        """
        Analyzes engine telemetry and provides optimization advice.
        """
        model = self._default_models["physics"]
        prompt = f"Analyze this Aetheris telemetry and suggest optimizations: {json.dumps(telemetry)}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                    timeout=20.0
                )
                return response.json().get("response", "No suggestions available.")
        except Exception as e:
            return f"Analysis failed: {str(e)}"

# Singleton instance for easy access
ai = AetherAI()
