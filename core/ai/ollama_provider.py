# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");

import httpx
import logging
import os
from typing import Dict, Any, List, Optional
from core.ai.base_provider import AIProvider

logger = logging.getLogger("aetheris.ai.ollama")

class OllamaProvider(AIProvider):
    """
    Provider implementation for local Ollama instances.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.environ.get("OLLAMA_URL", "http://localhost:11434")
        logger.info(f"Ollama provider initialized at {self.base_url}")

    async def generate_response(
        self, 
        prompt: str, 
        model: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt
        
        # Merge extra kwargs into payload (e.g. temperature)
        payload.update(kwargs)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=kwargs.get("timeout", 60.0)
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
                else:
                    logger.error(f"Ollama error {response.status_code}: {response.text}")
                    return f"Error: Ollama returned status {response.status_code}"
        except Exception as e:
            logger.error(f"Ollama connection failed: {str(e)}")
            return f"Error: Could not connect to Ollama at {self.base_url}"

    async def get_available_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return [m["name"] for m in models]
                return []
        except Exception:
            return []

    def get_provider_name(self) -> str:
        return "ollama"
