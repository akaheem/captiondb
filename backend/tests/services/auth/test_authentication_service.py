import pytest
from unittest.mock import AsyncMock
import dataclasses
from datetime import datetime

from app.domain.models.auth import (
    User,
    UserIdentity,
    AuthenticationRequest,
    AuthenticationResult,
    AuthenticatedUser,
    AuthenticationMetadata,
    AccountStatus,
    IdentityProvider,
    OAuthProvider,
    UserRole
)
from app.services.auth import AuthenticationService
from app.domain.exceptions import DomainException

@pytest.fixture
def auth_provider():
    return AsyncMock()

@pytest.fixture
def user_provider():
    return AsyncMock()

@pytest.fixture
def identity_provider():
    return AsyncMock()

@pytest.fixture
def auth_service(auth_provider, user_provider, identity_provider):
    return AuthenticationService(
        auth_provider=auth_provider,
        user_provider=user_provider,
        identity_provider=identity_provider
    )

@pytest.fixture
def mock_user():
    return User(
        id="user-123",
        email="test@example.com",
        username="testuser",
        display_name="Test User",
        avatar_url=None,
        role=UserRole.USER,
        status=AccountStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        verified=True,
        identities=[
            UserIdentity(
                id="id-1",
                user_id="user-123",
                provider=IdentityProvider.EMAIL,
                oauth_provider=None,
                provider_id="test@example.com",
                created_at=datetime.utcnow()
            )
        ]
    )

@pytest.mark.asyncio
async def test_successful_authentication(auth_service, auth_provider, mock_user):
    request = AuthenticationRequest(provider=IdentityProvider.EMAIL, email="test@example.com")
    
    auth_provider.authenticate.return_value = AuthenticationResult(
        success=True,
        authenticated_user=AuthenticatedUser(
            user=mock_user,
            metadata=AuthenticationMetadata(
                provider=IdentityProvider.EMAIL,
                oauth_provider=None,
                timestamp=datetime.utcnow()
            )
        )
    )
    
    result = await auth_service.authenticate(request)
    assert result.success is True
    assert result.authenticated_user.user.id == "user-123"

@pytest.mark.asyncio
async def test_suspended_account(auth_service, auth_provider, mock_user):
    request = AuthenticationRequest(provider=IdentityProvider.EMAIL, email="test@example.com")
    suspended_user = dataclasses.replace(mock_user, status=AccountStatus.SUSPENDED)
    
    auth_provider.authenticate.return_value = AuthenticationResult(
        success=True,
        authenticated_user=AuthenticatedUser(
            user=suspended_user,
            metadata=AuthenticationMetadata(
                provider=IdentityProvider.EMAIL,
                oauth_provider=None,
                timestamp=datetime.utcnow()
            )
        )
    )
    
    with pytest.raises(DomainException, match="User account is not active"):
        await auth_service.authenticate(request)

@pytest.mark.asyncio
async def test_link_duplicate_identity(auth_service, mock_user):
    # Attempting to link another EMAIL identity which the user already has
    new_identity = UserIdentity(
        id="id-2",
        user_id="user-123",
        provider=IdentityProvider.EMAIL,
        oauth_provider=None,
        provider_id="other@example.com",
        created_at=datetime.utcnow()
    )
    
    with pytest.raises(DomainException, match="Identity type is already linked"):
        await auth_service.link_identity(mock_user, new_identity)

@pytest.mark.asyncio
async def test_unlink_last_identity(auth_service, mock_user):
    # User only has 1 identity (EMAIL)
    with pytest.raises(DomainException, match="Cannot unlink the last remaining identity"):
        await auth_service.unlink_identity(mock_user, provider=IdentityProvider.EMAIL)

@pytest.mark.asyncio
async def test_successful_unlink_identity(auth_service, user_provider, mock_user):
    # Add a second identity so we can unlink one
    new_identity = UserIdentity(
        id="id-2",
        user_id="user-123",
        provider=IdentityProvider.OAUTH,
        oauth_provider=OAuthProvider.GOOGLE,
        provider_id="google-123",
        created_at=datetime.utcnow()
    )
    user_with_two_identities = dataclasses.replace(mock_user, identities=[mock_user.identities[0], new_identity])
    
    user_provider.update_user.return_value = dataclasses.replace(user_with_two_identities, identities=[mock_user.identities[0]])
    
    result = await auth_service.unlink_identity(user_with_two_identities, provider=IdentityProvider.OAUTH, oauth_provider=OAuthProvider.GOOGLE)
    
    assert len(result.identities) == 1
    assert result.identities[0].provider == IdentityProvider.EMAIL
