"""
AI Service.
Application service coordinating AI generation through the abstract AIProvider.
"""
from loguru import logger

from app.domain.interfaces.ai import AIProvider
from app.domain.models.ai import AIRequest, AIResponse
from app.core.exceptions import AIProviderException, ValidationException


class AIService:
    """
    Coordinates AI requests through the abstract AIProvider.
    Strictly forbids dependency on concrete implementations (e.g., Fireworks SDK).
    """
    
    def __init__(self, provider: AIProvider):
        """
        Injected constructor.
        The specific provider is supplied by the Dependency Injection layer.
        """
        self._provider = provider

    async def generate_response(self, request: AIRequest) -> AIResponse:
        """
        Validates the domain request and forwards it to the abstract AIProvider.
        Returns a standardized AIResponse, stripping away any vendor-specific metadata.
        """
        if not request.prompt or not request.prompt.strip():
            raise ValidationException("AI prompt cannot be empty.")
            
        try:
            logger.info("Forwarding generation request to AI Provider.")
            response = await self._provider.generate(request)
            
            # Log token usage safely without exposing the raw prompt or response
            logger.info(
                f"AI generation successful. Provider: {response.model_info.provider_name} | "
                f"Model: {response.model_info.model_name} | "
                f"Total Tokens: {response.usage.total_tokens}"
            )
            return response
            
        except AIProviderException as e:
            logger.warning(f"AI Provider rejected or failed the request: {e.message}")
            raise
            
        except Exception as e:
            logger.error(f"Unexpected system error communicating with AI Provider: {str(e)}")
            # We mask the underlying HTTP or SDK stack trace from escaping the service boundary
            raise AIProviderException("An unexpected internal error occurred during AI generation.")
