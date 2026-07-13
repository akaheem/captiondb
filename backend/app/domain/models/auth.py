from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

class OAuthProvider(str, Enum):
    GOOGLE = "google"
    GITHUB = "github"
    APPLE = "apple"
    MICROSOFT = "microsoft"
    TWITTER = "twitter"

class IdentityProvider(str, Enum):
    EMAIL = "email"
    OAUTH = "oauth"

class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

@dataclass(frozen=True)
class UserIdentity:
    id: str
    user_id: str
    provider: IdentityProvider
    oauth_provider: Optional[OAuthProvider]
    provider_id: str
    created_at: datetime
    last_login_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class UserProfile:
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

@dataclass(frozen=True)
class User:
    id: str
    email: str
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    role: UserRole
    status: AccountStatus
    created_at: datetime
    updated_at: datetime
    verified: bool
    identities: List[UserIdentity]
    profile: Optional[UserProfile] = None

@dataclass(frozen=True)
class AuthenticationRequest:
    email: Optional[str] = None
    password: Optional[str] = None
    provider: Optional[IdentityProvider] = None
    oauth_provider: Optional[OAuthProvider] = None
    oauth_token: Optional[str] = None

@dataclass(frozen=True)
class UserSessionMetadata:
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None

@dataclass(frozen=True)
class AuthenticationMetadata:
    provider: IdentityProvider
    oauth_provider: Optional[OAuthProvider]
    timestamp: datetime
    session_metadata: Optional[UserSessionMetadata] = None

@dataclass(frozen=True)
class AuthenticatedUser:
    user: User
    metadata: AuthenticationMetadata

@dataclass(frozen=True)
class AuthenticationResult:
    success: bool
    authenticated_user: Optional[AuthenticatedUser] = None
    error_message: Optional[str] = None
    requires_mfa: bool = False
