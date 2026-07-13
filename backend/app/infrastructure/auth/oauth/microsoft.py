"""
MicrosoftOAuthAdapter — concrete OAuthProvider for Microsoft (Azure AD v2.0).

Authorization flow: OAuth 2.0 Authorization Code + OpenID Connect.
Token endpoint: /common/oauth2/v2.0/token — supports personal + work accounts.
Profile source: Microsoft Graph /v1.0/me
"""
from loguru import logger

from app.core.config import OAuthProviderConfig
from app.domain.models.oauth import OAuthProviderMetadata, OAuthTokenBundle, OAuthUserProfile
from .base import BaseOAuthAdapter, OAuthHTTPError


class MicrosoftOAuthAdapter(BaseOAuthAdapter):
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
        return self._build_authorization_url(state, redirect_uri)

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
        # Microsoft Graph returns `id` as the provider-level user ID.
        logger.debug(f"Microsoft profile fetched for id={raw.get('id')}")
        return OAuthUserProfile(
            provider_id=raw["id"],
            email=raw.get("mail") or raw.get("userPrincipalName"),
            username=raw.get("userPrincipalName", "").split("@")[0],
            display_name=raw.get("displayName"),
            avatar_url=None,  # Photo requires a separate Graph API call
            metadata={"job_title": raw.get("jobTitle"), "office_location": raw.get("officeLocation")},
        )

    async def validate_identity(self, token: str) -> bool:
        try:
            await self._get_userinfo(token)
            return True
        except OAuthHTTPError:
            return False
