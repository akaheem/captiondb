import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.domain.models.auth import OAuthProvider as OAuthProviderEnum, User, AccountStatus, UserRole
from app.domain.models.oauth import OAuthTokenBundle, OAuthUserProfile, OAuthAuthenticationResult
from app.domain.interfaces.oauth import OAuthProvider
from app.services.oauth_registry import OAuthProviderRegistry
from app.services.oauth_auth import OAuthAuthenticationService
from app.domain.exceptions import DomainException

@pytest.fixture
def mock_provider():
    provider = AsyncMock(spec=OAuthProvider)
    return provider

@pytest.fixture
def registry(mock_provider):
    reg = OAuthProviderRegistry()
    reg.register_provider(OAuthProviderEnum.GOOGLE, mock_provider)
    return reg

@pytest.fixture
def auth_service():
    return AsyncMock()

@pytest.fixture
def user_provider():
    return AsyncMock()

@pytest.fixture
def oauth_auth_service(registry, auth_service, user_provider):
    return OAuthAuthenticationService(
        registry=registry,
        auth_service=auth_service,
        user_provider=user_provider
    )

def test_registry_register_and_get(registry, mock_provider):
    assert registry.get_provider(OAuthProviderEnum.GOOGLE) == mock_provider
    assert OAuthProviderEnum.GOOGLE in registry.list_providers()

def test_registry_register_duplicate(registry, mock_provider):
    with pytest.raises(DomainException, match="already registered"):
        registry.register_provider(OAuthProviderEnum.GOOGLE, mock_provider)

def test_registry_get_missing(registry):
    with pytest.raises(DomainException, match="not registered or supported"):
        registry.get_provider(OAuthProviderEnum.GITHUB)

@pytest.mark.asyncio
async def test_begin_login(oauth_auth_service, mock_provider):
    mock_provider.get_authorization_url.return_value = "http://auth.url"
    url = await oauth_auth_service.begin_login(OAuthProviderEnum.GOOGLE, "state123", "http://redirect")
    assert url == "http://auth.url"
    mock_provider.get_authorization_url.assert_called_once_with("state123", "http://redirect")

@pytest.mark.asyncio
async def test_complete_login_existing_user_linked(oauth_auth_service, mock_provider, user_provider, auth_service):
    tokens = OAuthTokenBundle(access_token="acc")
    profile = OAuthUserProfile(provider_id="123", email="test@example.com")
    
    mock_provider.exchange_code.return_value = tokens
    mock_provider.fetch_user_profile.return_value = profile
    
    mock_user = User(
        id="user-123",
        email="test@example.com",
        username="test",
        display_name=None,
        avatar_url=None,
        role=UserRole.USER,
        status=AccountStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        verified=True,
        identities=[
            MagicMock(provider="OAUTH", oauth_provider=OAuthProviderEnum.GOOGLE, provider_id="123")
        ]
    )
    user_provider.get_by_email.return_value = mock_user

    result = await oauth_auth_service.complete_login(OAuthProviderEnum.GOOGLE, "code123", "http://redirect")
    
    assert result.success is True
    assert result.user == mock_user
    assert result.is_new_user is False
    auth_service.link_identity.assert_not_called()
    auth_service.validate_user.assert_called_once_with(mock_user)

@pytest.mark.asyncio
async def test_complete_login_new_user(oauth_auth_service, mock_provider, user_provider, auth_service):
    tokens = OAuthTokenBundle(access_token="acc")
    profile = OAuthUserProfile(provider_id="123", email="test@example.com", username="test")
    
    mock_provider.exchange_code.return_value = tokens
    mock_provider.fetch_user_profile.return_value = profile
    
    user_provider.get_by_email.return_value = None
    
    mock_user = User(
        id="user-123",
        email="test@example.com",
        username="test",
        display_name=None,
        avatar_url=None,
        role=UserRole.USER,
        status=AccountStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        verified=True,
        identities=[]
    )
    user_provider.create_user.return_value = mock_user
    auth_service.link_identity.return_value = mock_user

    result = await oauth_auth_service.complete_login(OAuthProviderEnum.GOOGLE, "code123", "http://redirect")
    
    assert result.success is True
    assert result.is_new_user is True
    user_provider.create_user.assert_called_once()
    auth_service.link_identity.assert_called_once()
    auth_service.validate_user.assert_called_once_with(mock_user)
