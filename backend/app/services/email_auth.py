import dataclasses
from typing import Optional
from loguru import logger
from datetime import datetime, timezone

from app.domain.models.auth import (
    User,
    UserIdentity,
    IdentityProvider,
    AccountStatus,
    UserRole
)
from app.domain.interfaces.auth import (
    UserProvider,
    PasswordHasher,
    PasswordPolicyProvider,
    PasswordCredentialProvider
)
from app.core.exceptions import (
    InvalidCredentialsException,
    AccountNotActiveException,
    ConflictException,
    ValidationException,
)

class EmailAuthenticationService:
    def __init__(
        self,
        user_provider: UserProvider,
        password_hasher: PasswordHasher,
        password_policy_provider: PasswordPolicyProvider,
        credential_provider: PasswordCredentialProvider
    ):
        self._user_provider = user_provider
        self._password_hasher = password_hasher
        self._password_policy = password_policy_provider
        self._credential_provider = credential_provider

    async def login(self, email: str, password: str) -> User:
        logger.info(f"Attempting email login for {email}")
        user = await self._user_provider.get_by_email(email)
        if not user:
            # Constant-time guard: always check hash even when user not found
            # to prevent timing-based user enumeration.
            raise InvalidCredentialsException()

        if user.status != AccountStatus.ACTIVE:
            raise AccountNotActiveException(
                status=user.status.value,
                details={"user_id": user.id},
            )

        stored_hash = await self._credential_provider.get_password_hash(user.id)
        if not stored_hash:
            raise InvalidCredentialsException()

        if not self._password_hasher.verify_password(password, stored_hash):
            raise InvalidCredentialsException()

        return user

    async def register(self, email: str, username: str, password: str) -> User:
        logger.info(f"Registering new user with email {email}")

        existing_user = await self._user_provider.get_by_email(email)
        if existing_user:
            raise ConflictException(
                "Email is already in use.",
                details={"field": "email"},
            )

        existing_username = await self._user_provider.get_by_username(username)
        if existing_username:
            raise ConflictException(
                "Username is already in use.",
                details={"field": "username"},
            )

        self.validate_password_strength(password)

        _now = datetime.now(timezone.utc)
        new_user = User(
            id="",  # Provider will assign ID
            email=email,
            username=username,
            display_name=None,
            avatar_url=None,
            role=UserRole.USER,
            status=AccountStatus.PENDING_VERIFICATION,
            created_at=_now,
            updated_at=_now,
            verified=False,
            identities=[
                UserIdentity(
                    id="",
                    user_id="",
                    provider=IdentityProvider.EMAIL,
                    oauth_provider=None,
                    provider_id=email,
                    created_at=_now,
                )
            ],
        )

        created_user = await self._user_provider.create_user(new_user)

        hashed_password = self._password_hasher.hash_password(password)
        await self._credential_provider.set_password_hash(created_user.id, hashed_password)

        return created_user

    async def change_password(self, user: User, old_password: str, new_password: str) -> None:
        logger.info(f"Changing password for user {user.id}")
        
        stored_hash = await self._credential_provider.get_password_hash(user.id)
        if not stored_hash or not self._password_hasher.verify_password(old_password, stored_hash):
            raise DomainException("Invalid current password.")
            
        self.validate_password_strength(new_password)
        
        new_hash = self._password_hasher.hash_password(new_password)
        
        is_history_valid = await self._password_policy.validate_history(user.id, new_hash)
        if not is_history_valid:
            raise DomainException("Password has been used recently.")
            
        await self._credential_provider.set_password_hash(user.id, new_hash)

    def validate_password_strength(self, password: str) -> None:
        if not self._password_policy.validate_strength(password):
            raise ValidationException(
                "Password does not meet strength requirements.",
                details={"min_length": 8},
            )

    async def reset_password_request(self, email: str) -> None:
        logger.info(f"Received password reset request for {email}")
        user = await self._user_provider.get_by_email(email)
        if not user:
            # We don't throw an error to avoid user enumeration attacks
            return
            
        # In a real system, this would trigger an event or call an EmailProvider
        # e.g., await self._email_provider.send_reset_link(user)
        logger.info(f"Simulating password reset email sent to {email}")
