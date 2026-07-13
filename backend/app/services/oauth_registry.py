from typing import Dict, List
from loguru import logger

from app.domain.models.auth import OAuthProvider as OAuthProviderEnum
from app.domain.interfaces.oauth import OAuthProvider
from app.domain.exceptions import DomainException

class OAuthProviderRegistry:
    def __init__(self):
        self._providers: Dict[OAuthProviderEnum, OAuthProvider] = {}

    def register_provider(self, provider_enum: OAuthProviderEnum, provider_instance: OAuthProvider) -> None:
        if provider_enum in self._providers:
            raise DomainException(f"Provider {provider_enum} is already registered.")
        
        self._providers[provider_enum] = provider_instance
        logger.info(f"Registered OAuth provider: {provider_enum}")

    def get_provider(self, provider_enum: OAuthProviderEnum) -> OAuthProvider:
        provider = self._providers.get(provider_enum)
        if not provider:
            raise DomainException(f"Provider {provider_enum} is not registered or supported.")
        return provider

    def list_providers(self) -> List[OAuthProviderEnum]:
        return list(self._providers.keys())
