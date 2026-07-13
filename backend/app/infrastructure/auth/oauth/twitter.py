"""
TwitterOAuthAdapter — concrete OAuthProvider for Twitter/X (OAuth 2.0 with PKCE).

Authorization flow: OAuth 2.0 Authorization Code with PKCE (required by Twitter).
Token endpoint: https://api.twitter.com/2/oauth2/token
Profile source: https://api.twitter.com/2/users/me

PKCE notes
----------
* Twitter requires PKCE for public clients.
* The code_verifier must be generated per-request by the caller (e.g. OAuthAuthenticationService)
  and passed to get_authorization_url() so it can be stored server-side for the callback.
* For now, the adapter accepts an optional code_verifier/code_challenge pair via
  keyword arguments on get_authorization_url(), keeping PKCE wiring explicit and testable.
"""
import base64
import hashlib
import secrets
from typing import Optional

from loguru import logger

from app.core.config import OAuthProviderConfig
from app.domain.models.oauth import OAuthProviderMetadata, OAuthTokenBundle, OAuthUserProfile
from .base import BaseOAuthAdapter, OAuthHTTPError


def generate_pkce_pair() -> tuple[str, str]:
    """
    Utility to generate a (code_verifier, code_challenge) pair.

    Callers should store code_verifier in the session (keyed by state)
    and pass code_challenge to get_authorization_url().
    """
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


class TwitterOAuthAdapter(BaseOAuthAdapter):
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

    async def get_authorization_url(
        self,
        state: str,
        redirect_uri: str,
        code_challenge: Optional[str] = None,
    ) -> str:  # type: ignore[override]
        extra = {}
        if self._config.pkce_enabled:
            if not code_challenge:
                # Generate an ephemeral challenge — callers should generate and store
                # their own verifier for production use.
                _, code_challenge = generate_pkce_pair()
            extra = {
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        return self._build_authorization_url(state, redirect_uri, extra=extra)

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None,
    ) -> OAuthTokenBundle:  # type: ignore[override]
        data: dict = {
            "code": code,
            "client_id": self._config.client_id,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        if self._config.pkce_enabled and code_verifier:
            data["code_verifier"] = code_verifier
        elif not self._config.pkce_enabled and self._config.client_secret:
            data["client_secret"] = self._config.client_secret

        payload = await self._post_token(data)
        return self._parse_token_bundle(payload)

    async def refresh_token(self, refresh_token: str) -> OAuthTokenBundle:
        data = {
            "refresh_token": refresh_token,
            "client_id": self._config.client_id,
            "grant_type": "refresh_token",
        }
        payload = await self._post_token(data)
        return self._parse_token_bundle(payload)

    async def fetch_user_profile(self, token: OAuthTokenBundle) -> OAuthUserProfile:
        # Twitter v2 API requires explicit field expansions
        response = await self._client.get(
            self._config.userinfo_endpoint,
            params={"user.fields": "id,name,username,profile_image_url,verified"},
            headers={"Authorization": f"Bearer {token.access_token}", "Accept": "application/json"},
        )
        if not response.is_success:
            raise OAuthHTTPError(response.status_code, response.text)
        raw = response.json().get("data", {})
        logger.debug(f"Twitter profile fetched for id={raw.get('id')}")
        return OAuthUserProfile(
            provider_id=raw["id"],
            email=None,  # Twitter v2 does not expose email via userinfo
            username=raw.get("username"),
            display_name=raw.get("name"),
            avatar_url=raw.get("profile_image_url"),
            metadata={"verified": raw.get("verified", False)},
        )

    async def validate_identity(self, token: str) -> bool:
        try:
            response = await self._client.get(
                self._config.userinfo_endpoint,
                params={"user.fields": "id"},
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            )
            return response.is_success
        except Exception:
            return False
