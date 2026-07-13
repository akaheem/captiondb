"""
Vision Analyzer Interface.
Defines the contract for interacting with remote Vision Language Models (e.g. Fireworks, OpenAI).
"""
from abc import ABC, abstractmethod

from app.domain.models.vision import VisionAnalysisRequest, VisionAnalysisResult


class VisionAnalyzer(ABC):
    """
    Abstract interface for Vision AI interpretation.
    
    Responsibilities:
    - Receive a standardized VisionAnalysisRequest.
    - Translate the request into a provider-specific payload (e.g., Fireworks REST schema).
    - Execute the API call.
    - Parse the provider-specific JSON response into a standardized VisionAnalysisResult.
    - Handle provider-specific rate limits and transient errors internally.
    """
    
    @abstractmethod
    async def analyze(self, request: VisionAnalysisRequest) -> VisionAnalysisResult:
        """
        Interprets a package of visual keyframes and returns a structured semantic understanding.
        
        Args:
            request: The provider-agnostic analysis request payload.
            
        Returns:
            The structured semantic analysis result.
            
        Raises:
            VisionAnalysisException: If the underlying API fails or returns unparseable schema.
        """
        pass
