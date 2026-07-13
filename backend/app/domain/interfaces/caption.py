"""
Caption Generator Interface.
Defines the contract for interacting with AI Text Language Models (e.g. Fireworks Text, Llama 3).
"""
from abc import ABC, abstractmethod

from app.domain.models.caption import CaptionGenerationRequest, CaptionGenerationResult


class CaptionGenerator(ABC):
    """
    Abstract interface for AI Caption Generation.
    
    Responsibilities:
    - Receive a standardized CaptionGenerationRequest.
    - Translate the request into a provider-specific payload.
    - Execute the API call.
    - Parse the provider-specific response into a standardized CaptionGenerationResult.
    - Handle provider-specific rate limits and transient errors internally.
    """
    
    @abstractmethod
    async def generate(self, request: CaptionGenerationRequest) -> CaptionGenerationResult:
        """
        Generates captions based on a structured request.
        
        Args:
            request: The provider-agnostic generation request payload.
            
        Returns:
            The generated caption results.
            
        Raises:
            Exception: If the underlying API fails.
        """
        pass
