"""
Base OAuth adapter providing shared httpx connection pooling,
timeout configuration, and common error handling logic.

Every concrete adapter inherits from this class.
"""
import urllib.parse
from abc import abstractmethod
from typing import Any, Dict

import httpx
from loguru import logger

from app.core.config import OAuthProviderConfig
from app.domain.interfaces.oauth import OAuthProvider
from app.domain.models.oauth import OAuthProviderMetadata, OAuthTokenBundle


class OAuthHTTPError(Exception):
    """Raised when an upstream provider returns a non-2xx response."""
    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"OAuth HTTP {status_code}: {body}")


class BaseOAuthAdapter(OAuthProvider):
    """
    Shared HTTP plumbing for all OAuth adapters.

    Performance notes
    -----------------
    * A single ``httpx.AsyncClient`` is created once per adapter instance and
      reused across every request, enabling HTTP/1.1 keep-alive and HTTP/2
      connection pooling.
    * Adapters are registered as singletons in the DI registry, so the client
      is effectively process-scoped.
    """

    def __init__(self, config: OAuthProviderConfig, timeout_seconds: int = 10) -> None:
        self._config = config
        # Shared client — reused across all requests made by this adapter.
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
        )

    # ------------------------------------------------------------------
    # Concrete helpers
    # ------------------------------------------------------------------

    def _build_authorization_url(self, state: str, redirect_uri: str, extra: Dict[str, str] | None = None) -> str:
        """Constructs the authorization URL from config, never hardcoded."""
        params: Dict[str, Any] = {
            "client_id": self._config.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self._config.scopes),
            "state": state,
            "response_type": "code",
        }
        if extra:
            params.update(extra)
        return f"{self._config.authorization_endpoint}?{urllib.parse.urlencode(params)}"

    async def _post_token(self, data: Dict[str, str]) -> Dict[str, Any]:
        """POST to the provider's token endpoint and return parsed JSON."""
        logger.debug(f"Token exchange with {self._config.token_endpoint}")
        response = await self._client.post(
            self._config.token_endpoint,
            data=data,
            headers={"Accept": "application/json"},
        )
        if not response.is_success:
            raise OAuthHTTPError(response.status_code, response.text)
        return response.json()

    async def _get_userinfo(self, access_token: str, extra_headers: Dict[str, str] | None = None) -> Dict[str, Any]:
        """GET the provider's userinfo endpoint with a Bearer token."""
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        logger.debug(f"Fetching user profile from {self._config.userinfo_endpoint}")
        response = await self._client.get(self._config.userinfo_endpoint, headers=headers)
        if not response.is_success:
            raise OAuthHTTPError(response.status_code, response.text)
        return response.json()

    def _parse_token_bundle(self, data: Dict[str, Any]) -> OAuthTokenBundle:
        return OAuthTokenBundle(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in"),
            id_token=data.get("id_token"),
            token_type=data.get("token_type", "Bearer"),
        )

    # ------------------------------------------------------------------
    # OAuthProvider contract — subclasses implement the profile parsing
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        ...

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokenBundle:
        ...

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> OAuthTokenBundle:
        ...

    @property
    @abstractmethod
    def metadata(self) -> OAuthProviderMetadata:
        ...

    async def validate_identity(self, token: str) -> bool:
        """
        Default implementation: validate by attempting a userinfo fetch.
        Providers with id_token support (Google, Apple, Microsoft) should
        override this to verify the JWT signature instead.
        """
        try:
            await self._get_userinfo(token)
            return True
        except OAuthHTTPError:
            return False
