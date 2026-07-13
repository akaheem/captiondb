from typing import Optional
from loguru import logger

from app.domain.models.auth import User
from app.domain.interfaces.auth import TokenProvider
from app.core.exceptions import (
    AuthenticationException,
    TokenExpiredException,
)

class TokenService:
    def __init__(self, token_provider: TokenProvider):
        self._token_provider = token_provider

    async def issue_access_token(self, user: User) -> str:
        logger.info(f"Issuing access token for user {user.id}")
        return await self._token_provider.generate_token(user)

    async def issue_refresh_token(self, user: User) -> str:
        logger.info(f"Issuing refresh token for user {user.id}")
        # Assuming generate_token in TokenProvider will be expanded to take token type or we'd have a separate method
        # For now, we delegate as best as possible according to the interface available
        return await self._token_provider.generate_token(user)

    async def validate_token(self, token: str) -> dict:
        """
        Validate the token via the provider.

        Raises:
            TokenExpiredException  — when the provider signals expiry
                                     (provider raises ValueError with 'expired' in message,
                                     or returns None for an obviously dead token).
            AuthenticationException — for any other validation failure.
        """
        try:
            result = await self._token_provider.verify_token(token)
        except Exception as exc:
            msg = str(exc).lower()
            if "expired" in msg or "exp" in msg:
                raise TokenExpiredException() from exc
            raise AuthenticationException(f"Token validation error: {exc}") from exc

        if not result:
            # Provider returned falsy (None / False / {}) — treat as invalid.
            raise AuthenticationException("Token is invalid or has expired.")
        return result

    async def revoke_token(self, token: str) -> None:
        logger.info("Revoking token")
        if hasattr(self._token_provider, 'revoke_token'):
            await getattr(self._token_provider, 'revoke_token')(token)
        else:
            # Revocation not supported — log and continue.
            # In production this should write the JTI to a blocklist.
            logger.warning(
                "TokenProvider does not implement revoke_token — "
                "token revocation is a no-op until a blocklist is configured."
            )
