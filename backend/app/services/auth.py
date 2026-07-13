import dataclasses
from typing import Optional
from loguru import logger

from app.domain.models.auth import (
    User,
    UserIdentity,
    AuthenticationRequest,
    AuthenticationResult,
    AccountStatus,
    IdentityProvider,
    OAuthProvider
)
from app.domain.interfaces.auth import (
    AuthenticationProvider,
    UserProvider,
    IdentityProvider as IdpInterface
)
from app.core.exceptions import (
    AccountNotActiveException,
    IdentityAlreadyLinkedException,
    IdentityNotFoundException,
)

class AuthenticationService:
    def __init__(
        self,
        auth_provider: AuthenticationProvider,
        user_provider: UserProvider,
        identity_provider: IdpInterface
    ):
        self._auth_provider = auth_provider
        self._user_provider = user_provider
        self._identity_provider = identity_provider

    async def authenticate(self, request: AuthenticationRequest) -> AuthenticationResult:
        logger.info(f"Authenticating user via provider: {request.provider}")
        result = await self._auth_provider.authenticate(request)
        
        if result.success and result.authenticated_user:
            # Validate user account status
            await self.validate_user(result.authenticated_user.user)
            
        return result

    async def validate_user(self, user: User) -> None:
        if user.status != AccountStatus.ACTIVE:
            raise AccountNotActiveException(
                status=user.status.value,
                details={"user_id": user.id},
            )
        if not user.verified:
            raise AccountNotActiveException(
                status="unverified",
                details={"user_id": user.id, "reason": "email not verified"},
            )

    async def link_identity(self, user: User, new_identity: UserIdentity) -> User:
        logger.info(f"Linking identity {new_identity.provider} for user {user.id}")

        # Duplicate provider guard
        for identity in user.identities:
            if identity.provider == new_identity.provider and identity.oauth_provider == new_identity.oauth_provider:
                raise IdentityAlreadyLinkedException(
                    details={"provider": str(new_identity.oauth_provider or new_identity.provider)}
                )

        updated_identities = list(user.identities)
        updated_identities.append(new_identity)
        updated_user = dataclasses.replace(user, identities=updated_identities)
        return await self._user_provider.update_user(updated_user)

    async def unlink_identity(self, user: User, provider: IdentityProvider, oauth_provider: Optional[OAuthProvider] = None) -> User:
        logger.info(f"Unlinking identity {provider} for user {user.id}")

        if len(user.identities) <= 1:
            from app.core.exceptions import ValidationException
            raise ValidationException(
                "Cannot unlink the last remaining identity.",
                details={"user_id": user.id},
            )

        updated_identities = [
            i for i in user.identities
            if not (i.provider == provider and i.oauth_provider == oauth_provider)
        ]

        if len(updated_identities) == len(user.identities):
            raise IdentityNotFoundException(details={"provider": str(oauth_provider or provider)})

        updated_user = dataclasses.replace(user, identities=updated_identities)
        return await self._user_provider.update_user(updated_user)

    async def refresh_identity(self, identity: UserIdentity) -> UserIdentity:
        logger.info(f"Refreshing identity metadata for {identity.provider}")
        # Delegation logic goes here
        return identity
