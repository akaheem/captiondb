"""
OAuthIdentityService — Application service.

Responsibilities:
  • link_identity()    — Link a new OAuth provider to an existing account.
  • unlink_identity()  — Remove a linked OAuth provider from an account.
  • list_identities()  — Return all identities linked to a user.
  • get_identity()     — Fetch one specific identity by provider.

Validations enforced here (domain rules, not HTTP rules):
  • Cannot link the same provider twice (duplicate provider guard).
  • Cannot unlink if it would leave the account with zero login methods
    (orphan account prevention).
  • Cannot unlink a provider that isn't actually linked.

Constraints:
  NO FastAPI imports.
  NO HTTP response types.
  NO JWT/token parsing.
  Uses OAuthAuthenticationService for the OAuth exchange step.
  Uses AuthenticationService for domain-level link/unlink.

Architecture:
  Routers → AuthenticationApiService → OAuthIdentityService → OAuthAuthenticationService → OAuthProvider → Infrastructure
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import List, Optional

from loguru import logger

from app.core.exceptions import (
    CaptionDBException,
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.domain.models.auth import (
    IdentityProvider,
    OAuthProvider,
    User,
    UserIdentity,
)
from app.services.auth import AuthenticationService
from app.services.oauth_auth import OAuthAuthenticationService


# ---------------------------------------------------------------------------
# Read model
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class LinkedIdentity:
    """
    Read model returned by list/get operations.
    Never used as a persistence model.
    """
    provider: IdentityProvider
    oauth_provider: Optional[OAuthProvider]
    provider_id: str
    linked_at: datetime
    last_login_at: Optional[datetime] = None


def _to_linked_identity(identity: UserIdentity) -> LinkedIdentity:
    return LinkedIdentity(
        provider=identity.provider,
        oauth_provider=identity.oauth_provider,
        provider_id=identity.provider_id,
        linked_at=identity.created_at,
        last_login_at=identity.last_login_at,
    )


class OAuthIdentityService:
    """
    Manages OAuth identity linking and unlinking for existing user accounts.
    """

    def __init__(
        self,
        auth_service: AuthenticationService,
        oauth_auth_service: OAuthAuthenticationService,
    ) -> None:
        self._auth = auth_service
        self._oauth = oauth_auth_service

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_identities(self, user: User) -> List[LinkedIdentity]:
        """Return all identities attached to the user — synchronous (no I/O)."""
        return [_to_linked_identity(i) for i in user.identities]

    def get_identity(
        self,
        user: User,
        provider: OAuthProvider,
    ) -> LinkedIdentity:
        """
        Return the identity for a specific OAuth provider.

        Raises NotFoundException if the provider is not linked.
        """
        for identity in user.identities:
            if identity.oauth_provider == provider:
                return _to_linked_identity(identity)
        raise NotFoundException(
            f"Provider '{provider.value}' is not linked to this account.",
            details={"provider": provider.value},
        )

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def link_identity(
        self,
        user: User,
        provider: OAuthProvider,
        code: str,
        redirect_uri: str,
    ) -> User:
        """
        Link a new OAuth provider to the user's account.

        Validation chain:
          1. Duplicate provider guard — same provider cannot be linked twice.
          2. Delegate to OAuthAuthenticationService for the OAuth exchange.
          3. Domain link via AuthenticationService.

        Returns the updated User.
        """
        logger.info(f"OAuthIdentityService.link_identity: user={user.id} provider={provider}")

        # 1. Duplicate provider guard
        self._assert_provider_not_linked(user, provider)

        # 2. Exchange code for profile + link via OAuthAuthenticationService
        # (which internally calls AuthenticationService.link_identity)
        try:
            updated_user = await self._oauth.link_oauth_identity(user, provider, code, redirect_uri)
        except CaptionDBException:
            raise
        except Exception as exc:
            raise CaptionDBException(
                f"Failed to link {provider.value} identity.",
                error_code="IDENTITY_LINK_ERROR",
            ) from exc

        logger.info(
            f"Identity {provider.value} linked to user {user.id}. "
            f"Total identities: {len(updated_user.identities)}"
        )
        return updated_user

    async def unlink_identity(
        self,
        user: User,
        provider: OAuthProvider,
    ) -> User:
        """
        Unlink an OAuth provider from the user's account.

        Validation chain:
          1. Provider must actually be linked.
          2. Orphan account guard — at least one identity must remain.
          3. Domain unlink via AuthenticationService.

        Returns the updated User.
        """
        logger.info(f"OAuthIdentityService.unlink_identity: user={user.id} provider={provider}")

        # 1. Provider must be linked
        self._assert_provider_is_linked(user, provider)

        # 2. Orphan account guard
        self._assert_not_last_identity(user)

        # 3. Delegate to AuthenticationService
        try:
            updated_user = await self._auth.unlink_identity(
                user, IdentityProvider.OAUTH, provider
            )
        except CaptionDBException:
            raise
        except Exception as exc:
            raise CaptionDBException(
                f"Failed to unlink {provider.value} identity.",
                error_code="IDENTITY_UNLINK_ERROR",
            ) from exc

        logger.info(
            f"Identity {provider.value} unlinked from user {user.id}. "
            f"Remaining identities: {len(updated_user.identities)}"
        )
        return updated_user

    # ------------------------------------------------------------------
    # Private domain guards
    # ------------------------------------------------------------------

    def _assert_provider_not_linked(self, user: User, provider: OAuthProvider) -> None:
        """Raise ConflictException if the provider is already linked."""
        already_linked = any(
            i.provider == IdentityProvider.OAUTH and i.oauth_provider == provider
            for i in user.identities
        )
        if already_linked:
            raise ConflictException(
                f"Provider '{provider.value}' is already linked to this account.",
                details={"provider": provider.value},
            )

    def _assert_provider_is_linked(self, user: User, provider: OAuthProvider) -> None:
        """Raise NotFoundException if the provider is not linked."""
        is_linked = any(
            i.provider == IdentityProvider.OAUTH and i.oauth_provider == provider
            for i in user.identities
        )
        if not is_linked:
            raise NotFoundException(
                f"Provider '{provider.value}' is not linked to this account.",
                details={"provider": provider.value},
            )

    def _assert_not_last_identity(self, user: User) -> None:
        """
        Raise ValidationException if unlinking would leave the account
        with zero authentication methods (orphan account prevention).
        """
        if len(user.identities) <= 1:
            raise ValidationException(
                "Cannot unlink the last authentication method. "
                "Add another identity (email or OAuth) before unlinking.",
                details={"current_count": len(user.identities)},
            )
