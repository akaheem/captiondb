from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models.oauth import (
    OAuthTokenBundle,
    OAuthUserProfile,
    OAuthProviderMetadata,
)

class OAuthProvider(ABC):
    @abstractmethod
    async def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        """Returns the authorization URL for the provider."""
        pass

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokenBundle:
        """Exchanges an authorization code for an access token."""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> OAuthTokenBundle:
        """Refreshes an access token using a refresh token."""
        pass

    @abstractmethod
    async def fetch_user_profile(self, token: OAuthTokenBundle) -> OAuthUserProfile:
        """Fetches the user profile from the provider."""
        pass

    @abstractmethod
    async def validate_identity(self, token: str) -> bool:
        """Validates an identity token (e.g. JWT id_token)."""
        pass
        
    @property
    @abstractmethod
    def metadata(self) -> OAuthProviderMetadata:
        """Returns the metadata configuration for this provider."""
        pass
