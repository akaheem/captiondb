"""
GoogleOAuthAdapter — concrete OAuthProvider implementation for Google.

Authorization flow: OAuth 2.0 Authorization Code + OpenID Connect.
Token verification: id_token (JWT) issued by Google.
Profile source: https://www.googleapis.com/oauth2/v2/userinfo
"""
from loguru import logger

from app.core.config import OAuthProviderConfig
from app.domain.models.oauth import OAuthProviderMetadata, OAuthTokenBundle, OAuthUserProfile
from .base import BaseOAuthAdapter


class GoogleOAuthAdapter(BaseOAuthAdapter):
    def __init__(self, config: OAuthProviderConfig, timeout_seconds: int = 10) -> None:
        super().__init__(config, timeout_seconds)

    @property
    def metadata(self) -> OAuthProviderMetadata:
        return OAuthProviderMetadata(
            scopes=self._config.scopes,
            client_id=self._config.client_id,
            auth_url=self._config.authorization_endpoint,
            token_url=self._config.token_endpoint,
            userinfo_url=self._config.userinfo_endpoint,
        )

    async def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        # Google supports `access_type=offline` to receive a refresh token.
        return self._build_authorization_url(
            state, redirect_uri, extra={"access_type": "offline", "prompt": "consent"}
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokenBundle:
        data = {
            "code": code,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        payload = await self._post_token(data)
        return self._parse_token_bundle(payload)

    async def refresh_token(self, refresh_token: str) -> OAuthTokenBundle:
        data = {
            "refresh_token": refresh_token,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "grant_type": "refresh_token",
        }
        payload = await self._post_token(data)
        return self._parse_token_bundle(payload)

    async def fetch_user_profile(self, token: OAuthTokenBundle) -> OAuthUserProfile:
        raw = await self._get_userinfo(token.access_token)
        logger.debug(f"Google profile fetched for sub={raw.get('id')}")
        return OAuthUserProfile(
            provider_id=str(raw["id"]),
            email=raw.get("email"),
            username=raw.get("email", "").split("@")[0],
            display_name=raw.get("name"),
            avatar_url=raw.get("picture"),
            metadata={"verified_email": raw.get("verified_email", False)},
        )

    async def validate_identity(self, token: str) -> bool:
        """
        Validate via Google's tokeninfo endpoint.
        In production, prefer verifying the id_token JWT signature locally.
        """
        try:
            response = await self._client.get(
                "https://www.googleapis.com/oauth2/v2/tokeninfo",
                params={"access_token": token},
            )
            return response.is_success
        except Exception:
            return False
