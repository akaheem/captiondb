"""
OAuthAuthenticationService — Application service.

Handles OAuth JIT provisioning, account linking and token exchange.
Delegates all OAuth HTTP calls to the OAuthProvider adapters via the registry.
"""
import dataclasses
from typing import Optional
from loguru import logger
from datetime import datetime, timezone

from app.domain.models.auth import (
    User,
    UserIdentity,
    IdentityProvider,
    OAuthProvider as OAuthProviderEnum,
    AccountStatus,
    UserRole,
)
from app.domain.models.oauth import (
    OAuthAuthenticationResult,
    OAuthTokenBundle,
    OAuthUserProfile,
)
from app.domain.interfaces.auth import UserProvider
from app.services.auth import AuthenticationService
from app.services.oauth_registry import OAuthProviderRegistry
from app.core.exceptions import CaptionDBException


class OAuthAuthenticationService:
    def __init__(
        self,
        registry: OAuthProviderRegistry,
        auth_service: AuthenticationService,
        user_provider: UserProvider,
    ):
        self._registry = registry
        self._auth_service = auth_service
        self._user_provider = user_provider

    async def begin_login(self, provider: OAuthProviderEnum, state: str, redirect_uri: str) -> str:
        logger.info(f"Beginning OAuth login for {provider}")
        adapter = self._registry.get_provider(provider)
        return await adapter.get_authorization_url(state, redirect_uri)

    async def complete_login(self, provider: OAuthProviderEnum, code: str, redirect_uri: str) -> OAuthAuthenticationResult:
        logger.info(f"Completing OAuth login for {provider}")
        adapter = self._registry.get_provider(provider)

        tokens = await adapter.exchange_code(code, redirect_uri)
        profile = await adapter.fetch_user_profile(tokens)

        # JIT Provisioning / Lookup
        user = await self._user_provider.get_by_email(profile.email)
        is_new_user = False

        if not user:
            is_new_user = True
            logger.info(f"Creating new user for {profile.email}")
            _now = datetime.now(timezone.utc)
            new_user = User(
                id="",  # Assigned by provider
                email=profile.email,
                username=profile.username or profile.email.split("@")[0],
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
                role=UserRole.USER,
                status=AccountStatus.ACTIVE,
                created_at=_now,
                updated_at=_now,
                verified=True,  # OAuth emails are generally verified
                identities=[],
            )
            user = await self._user_provider.create_user(new_user)

        # Check if this specific identity is linked
        identity_linked = any(
            i.provider == IdentityProvider.OAUTH
            and i.oauth_provider == provider
            and i.provider_id == profile.provider_id
            for i in user.identities
        )

        if not identity_linked:
            new_identity = UserIdentity(
                id="",
                user_id=user.id,
                provider=IdentityProvider.OAUTH,
                oauth_provider=provider,
                provider_id=profile.provider_id,
                created_at=datetime.now(timezone.utc),
                metadata=profile.metadata,
            )
            # Use core auth service to link it safely
            user = await self._auth_service.link_identity(user, new_identity)

        await self._auth_service.validate_user(user)

        return OAuthAuthenticationResult(
            success=True,
            user=user,
            tokens=tokens,
            is_new_user=is_new_user,
        )

    async def refresh_oauth(self, provider: OAuthProviderEnum, refresh_token: str) -> OAuthTokenBundle:
        adapter = self._registry.get_provider(provider)
        return await adapter.refresh_token(refresh_token)

    async def link_oauth_identity(self, user: User, provider: OAuthProviderEnum, code: str, redirect_uri: str) -> User:
        logger.info(f"Linking OAuth identity {provider} for user {user.id}")
        adapter = self._registry.get_provider(provider)

        tokens = await adapter.exchange_code(code, redirect_uri)
        profile = await adapter.fetch_user_profile(tokens)

        new_identity = UserIdentity(
            id="",
            user_id=user.id,
            provider=IdentityProvider.OAUTH,
            oauth_provider=provider,
            provider_id=profile.provider_id,
            created_at=datetime.now(timezone.utc),
            metadata=profile.metadata,
        )

        return await self._auth_service.link_identity(user, new_identity)

    async def unlink_oauth_identity(self, user: User, provider: OAuthProviderEnum) -> User:
        return await self._auth_service.unlink_identity(user, IdentityProvider.OAUTH, provider)
