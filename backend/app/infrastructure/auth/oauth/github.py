"""
GitHubOAuthAdapter — concrete OAuthProvider implementation for GitHub.

Authorization flow: OAuth 2.0 Authorization Code.
Note: GitHub tokens are opaque (not JWTs); no id_token is issued.
Email privacy: GitHub may not expose the primary email on /user;
               a secondary fetch to /user/emails is performed when needed.
"""
from loguru import logger

from app.core.config import OAuthProviderConfig
from app.domain.models.oauth import OAuthProviderMetadata, OAuthTokenBundle, OAuthUserProfile
from .base import BaseOAuthAdapter, OAuthHTTPError


class GitHubOAuthAdapter(BaseOAuthAdapter):
    _EMAILS_ENDPOINT = "https://api.github.com/user/emails"

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
        }
        payload = await self._post_token(data)
        # GitHub returns `access_token=...&scope=...` form-encoded OR JSON
        # depending on Accept header — we force JSON via _post_token headers.
        return self._parse_token_bundle(payload)

    async def refresh_token(self, refresh_token: str) -> OAuthTokenBundle:
        # GitHub only issues refresh tokens for GitHub Apps (not OAuth Apps).
        # This is a no-op stub that raises clearly rather than silently failing.
        raise NotImplementedError(
            "GitHub OAuth Apps do not support refresh tokens. "
            "Use GitHub Apps with fine-grained tokens if refresh is required."
        )

    async def fetch_user_profile(self, token: OAuthTokenBundle) -> OAuthUserProfile:
        raw = await self._get_userinfo(
            token.access_token,
            extra_headers={"X-GitHub-Api-Version": "2022-11-28"},
        )
        email = raw.get("email")
        if not email:
            # Primary email is private — fetch from /user/emails
            email = await self._fetch_primary_email(token.access_token)

        logger.debug(f"GitHub profile fetched for id={raw.get('id')}")
        return OAuthUserProfile(
            provider_id=str(raw["id"]),
            email=email,
            username=raw.get("login"),
            display_name=raw.get("name"),
            avatar_url=raw.get("avatar_url"),
            metadata={"html_url": raw.get("html_url", "")},
        )

    async def _fetch_primary_email(self, access_token: str) -> str | None:
        """Fetch the verified primary email from /user/emails."""
        try:
            response = await self._client.get(
                self._EMAILS_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            if not response.is_success:
                logger.warning(f"Could not fetch GitHub emails: {response.status_code}")
                return None
            emails = response.json()
            primary = next(
                (e["email"] for e in emails if e.get("primary") and e.get("verified")), None
            )
            return primary
        except Exception as exc:
            logger.warning(f"GitHub email fetch failed: {exc}")
            return None

    async def validate_identity(self, token: str) -> bool:
        """GitHub tokens are opaque — validate by hitting the userinfo endpoint."""
        try:
            await self._get_userinfo(token, extra_headers={"X-GitHub-Api-Version": "2022-11-28"})
            return True
        except OAuthHTTPError:
            return False
