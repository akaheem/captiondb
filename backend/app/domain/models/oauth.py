from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.domain.models.auth import OAuthProvider, User

@dataclass(frozen=True)
class OAuthAuthenticationRequest:
    provider: OAuthProvider
    code: Optional[str] = None
    state: Optional[str] = None
    redirect_uri: Optional[str] = None

@dataclass(frozen=True)
class OAuthTokenBundle:
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    id_token: Optional[str] = None
    token_type: str = "Bearer"

@dataclass(frozen=True)
class OAuthUserProfile:
    provider_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class OAuthAuthenticationResult:
    success: bool
    user: Optional[User] = None
    tokens: Optional[OAuthTokenBundle] = None
    error_message: Optional[str] = None
    is_new_user: bool = False

@dataclass(frozen=True)
class OAuthProviderMetadata:
    scopes: List[str]
    client_id: str
    auth_url: str
    token_url: str
    userinfo_url: Optional[str] = None
