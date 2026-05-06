# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class AIProvider(ABC):
    """
    Abstract base class for Aetheris AI providers.
    Allows the framework to switch between different AI models (Ollama, OpenAI, etc.)
    without changing the core engine logic.
    """

    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        model: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generates a text response from the AI model."""
        pass

    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """Returns a list of models available through this provider."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the name of the provider."""
        pass
