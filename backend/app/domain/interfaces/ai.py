"""
Abstract AI Provider Interfaces.
"""
from abc import ABC, abstractmethod
from app.domain.models.ai import AIRequest, AIResponse


class AIProvider(ABC):
    """
    Abstract interface for interacting with Vision Language Models (VLMs) and LLMs.
    
    Purpose: Prevents the application from being tightly coupled to a single vendor (e.g., Fireworks).
    Responsibilities: Forwarding prompts and images to an AI inference endpoint and returning parsed text.
    Expected Inputs: Provider-agnostic AIRequest object.
    Expected Outputs: Provider-agnostic AIResponse object containing text, usage, and model info.
    Failure Behavior: Should catch provider-specific errors (e.g., rate limits, network timeouts) 
                      and raise unified domain AIProviderException.
    Extension Points: Can be implemented as FireworksAdapter, OpenAIAdapter, or LocalVLMAdapter.
    """
    
    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """
        Generate a text response based on a prompt and optional images.
        """
        pass
