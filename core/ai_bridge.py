# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");

import json
import logging
import os
from typing import Optional, Dict, Any, List

from core.ai.base_provider import AIProvider
from core.ai.ollama_provider import OllamaProvider

logger = logging.getLogger("aetheris.ai")

class AetherAI:
    """
    Agnostic AI Bridge for Aetheris UI.
    Acts as a facade for different AI providers (Ollama, OpenAI, etc.).
    """

    def __init__(self, provider_type: str = "auto"):
        self._provider: Optional[AIProvider] = None
        self._default_models = {
            "layout": os.environ.get("AETHERIS_MODEL_LAYOUT", "qwen2.5-coder:3b"),
            "physics": os.environ.get("AETHERIS_MODEL_PHYSICS", "deepseek-r1:1.5b"),
            "general": os.environ.get("AETHERIS_MODEL_GENERAL", "llama3.2:3b")
        }
        
        # Initialize provider
        self._init_provider(provider_type)

    def _init_provider(self, provider_type: str):
        if provider_type == "auto":
            # In development, default to Ollama if nothing else specified
            provider_type = os.environ.get("AETHERIS_AI_PROVIDER", "ollama")
        
        if provider_type == "ollama":
            self._provider = OllamaProvider()
        else:
            # Fallback to Ollama or Raise error in production
            logger.warning(f"Unknown AI provider '{provider_type}', falling back to Ollama")
            self._provider = OllamaProvider()

    async def generate_layout(self, description: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates an Aetheris UI Intent from a natural language description.
        """
        model = model or self._default_models["layout"]
        prompt = f"Generate an Aetheris UI Intent JSON for: {description}. Return ONLY the JSON."
        
        response_text = await self._provider.generate_response(prompt, model)
        
        try:
            # Simple JSON extraction in case the model adds chatter
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > 0:
                return json.loads(response_text[start:end])
        except Exception as e:
            logger.error(f"AI Layout parsing failed: {str(e)}")
            logger.debug(f"Raw response: {response_text}")
        
        return {"elements": []}

    async def analyze_performance(self, telemetry: Dict[str, Any]) -> str:
        """
        Analyzes engine telemetry and provides optimization advice.
        """
        model = self._default_models["physics"]
        prompt = f"Analyze this Aetheris telemetry and suggest optimizations: {json.dumps(telemetry)}"
        
        return await self._provider.generate_response(prompt, model)

    async def chat(self, prompt: str, model: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """
        General purpose chat interface.
        """
        model = model or self._default_models["general"]
        return await self._provider.generate_response(prompt, model, system_prompt=system_prompt)

    @property
    def provider(self) -> Optional[AIProvider]:
        return self._provider

# Singleton instance for easy access
ai = AetherAI()
