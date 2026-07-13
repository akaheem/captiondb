from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.domain.models.auth import (
    User,
    UserIdentity,
    AuthenticationRequest,
    AuthenticationResult,
    OAuthProvider,
)

class AuthenticationProvider(ABC):
    @abstractmethod
    async def authenticate(self, request: AuthenticationRequest) -> AuthenticationResult:
        pass

class IdentityProvider(ABC):
    @abstractmethod
    async def verify_oauth_token(self, provider: OAuthProvider, token: str) -> Dict[str, Any]:
        pass

class TokenProvider(ABC):
    @abstractmethod
    async def generate_token(self, user: User) -> str:
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> Optional[dict]:
        pass

    async def revoke_token(self, token: str) -> None:
        """
        Optional: Write the token's JTI to a blocklist.

        Not abstract — providers that support a blocklist override this;
        providers without blocklist support inherit the no-op.
        Default implementation is a no-op (acceptable for development only).
        """
        pass

class PasswordHasher(ABC):
    @abstractmethod
    def hash_password(self, password: str) -> str:
        pass

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        pass

class PasswordPolicyProvider(ABC):
    @abstractmethod
    def validate_strength(self, password: str) -> bool:
        pass

    @abstractmethod
    async def validate_history(self, user_id: str, new_password_hash: str) -> bool:
        pass

class PasswordCredentialProvider(ABC):
    """
    Abstracts the storage of password hashes so that User models remain clean.
    """
    @abstractmethod
    async def get_password_hash(self, user_id: str) -> Optional[str]:
        pass

    @abstractmethod
    async def set_password_hash(self, user_id: str, password_hash: str) -> None:
        pass

class UserProvider(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass
        
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    async def create_user(self, user: User) -> User:
        pass

    @abstractmethod
    async def update_user(self, user: User) -> User:
        pass

class SessionProvider(ABC):
    @abstractmethod
    async def create_session(self, user_id: str, metadata: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def revoke_session(self, session_id: str) -> None:
        pass

    async def list_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Return all sessions for a user, ordered newest-first.

        Not abstract — providers that store an index override this;
        providers without list support return an empty list.
        """
        return []

    async def revoke_all_sessions(self, user_id: str) -> int:
        """
        Terminate all sessions for a user in one operation.

        Not abstract — providers without bulk revoke fall back to
        SessionManagementService iterating list_sessions().
        Returns the number of sessions revoked.
        """
        return 0

    async def refresh_session(self, session_id: str) -> None:
        """
        Extend the TTL of a session.

        Not abstract — providers without TTL extension inherit a no-op.
        """
        pass

    async def cleanup_expired_sessions(self, user_id: str) -> int:
        """
        Remove expired sessions from the store.

        Not abstract — providers without explicit GC inherit a no-op.
        Returns the number of sessions removed.
        """
        return 0
