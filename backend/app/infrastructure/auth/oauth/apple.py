"""
AppleOAuthAdapter — concrete OAuthProvider implementation for Sign in with Apple.

Authorization flow: OAuth 2.0 Authorization Code + OpenID Connect.
Client secret: Apple requires a short-lived JWT signed with an ES256 private key.
               The _build_client_secret() method is a placeholder — production
               integration will use PyJWT + the ES256 private key from config.
Profile source: Apple only sends user info (name/email) on the FIRST sign-in;
               subsequent sign-ins only return the subject (sub) claim in the id_token.
"""
import json
from loguru import logger

from app.core.config import OAuthProviderConfig
from app.domain.models.oauth import OAuthProviderMetadata, OAuthTokenBundle, OAuthUserProfile
from .base import BaseOAuthAdapter, OAuthHTTPError


class AppleOAuthAdapter(BaseOAuthAdapter):
    def __init__(self, config: OAuthProviderConfig, timeout_seconds: int = 10) -> None:
        super().__init__(config, timeout_seconds)

    @property
    def metadata(self) -> OAuthProviderMetadata:
        return OAuthProviderMetadata(
            scopes=self._config.scopes,
            client_id=self._config.client_id,
            auth_url=self._config.authorization_endpoint,
            token_url=self._config.token_endpoint,
            userinfo_url=None,  # Apple has no separate userinfo endpoint
        )

    def _build_client_secret(self) -> str:
        """
        Apple requires a JWT signed with an ES256 key as the client_secret.

        Production implementation must use PyJWT:
            import jwt, time
            payload = {
                "iss": self._config.team_id,
                "iat": int(time.time()),
                "exp": int(time.time()) + 86400 * 180,  # max 6 months
                "aud": "https://appleid.apple.com",
                "sub": self._config.client_id,
            }
            return jwt.encode(payload, self._config.private_key_pem,
                              algorithm="ES256",
                              headers={"kid": self._config.key_id})

        Stub raises until the private key is configured.
        """
        if not self._config.private_key_pem:
            raise NotImplementedError(
                "AppleOAuthAdapter: private_key_pem is not configured. "
                "Set OAUTH__APPLE__PRIVATE_KEY_PEM, OAUTH__APPLE__TEAM_ID, "
                "and OAUTH__APPLE__KEY_ID in your environment."
            )
        # TODO: Replace with jwt.encode() once PyJWT is a declared dependency.
        raise NotImplementedError("Apple client-secret JWT signing not yet wired.")

    async def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        return self._build_authorization_url(
            state, redirect_uri,
            extra={"response_mode": "form_post"},
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokenBundle:
        client_secret = self._build_client_secret()
        data = {
            "code": code,
            "client_id": self._config.client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        payload = await self._post_token(data)
        return self._parse_token_bundle(payload)

    async def refresh_token(self, refresh_token: str) -> OAuthTokenBundle:
        client_secret = self._build_client_secret()
        data = {
            "refresh_token": refresh_token,
            "client_id": self._config.client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
        }
        payload = await self._post_token(data)
        return self._parse_token_bundle(payload)

    async def fetch_user_profile(self, token: OAuthTokenBundle) -> OAuthUserProfile:
        """
        Apple only provides user info (name/email) on the FIRST authorization.
        That data arrives in the POST body of the redirect, not from a userinfo endpoint.
        On subsequent logins, only the `sub` claim from the id_token is available.
        """
        if not token.id_token:
            raise ValueError("AppleOAuthAdapter: id_token is required to extract user profile.")

        # Decode the id_token WITHOUT verification for profile extraction.
        # Production code should verify the JWT signature against Apple's public keys.
        import base64
        payload_b64 = token.id_token.split(".")[1]
        # Add padding if needed
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_b64))

        logger.debug(f"Apple id_token claims extracted for sub={claims.get('sub')}")
        return OAuthUserProfile(
            provider_id=claims["sub"],
            email=claims.get("email"),
            username=None,  # Apple does not provide a username
            display_name=None,
            avatar_url=None,
            metadata={"email_verified": claims.get("email_verified", False)},
        )

    async def validate_identity(self, token: str) -> bool:
        """
        Production: verify id_token JWT against Apple's public JWKS.
        Stub: always returns False until JWT verification is wired.
        """
        logger.warning("AppleOAuthAdapter.validate_identity is a stub; returning False.")
        return False
