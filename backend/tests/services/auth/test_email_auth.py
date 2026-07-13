import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from app.domain.models.auth import User, AccountStatus, UserRole
from app.services.email_auth import EmailAuthenticationService
from app.domain.exceptions import DomainException

@pytest.fixture
def user_provider():
    return AsyncMock()

@pytest.fixture
def password_hasher():
    return AsyncMock()

@pytest.fixture
def password_policy_provider():
    return AsyncMock()

@pytest.fixture
def credential_provider():
    return AsyncMock()

@pytest.fixture
def email_auth_service(user_provider, password_hasher, password_policy_provider, credential_provider):
    return EmailAuthenticationService(
        user_provider=user_provider,
        password_hasher=password_hasher,
        password_policy_provider=password_policy_provider,
        credential_provider=credential_provider
    )

@pytest.fixture
def mock_user():
    return User(
        id="user-123",
        email="test@example.com",
        username="testuser",
        display_name=None,
        avatar_url=None,
        role=UserRole.USER,
        status=AccountStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        verified=True,
        identities=[]
    )

@pytest.mark.asyncio
async def test_register_success(email_auth_service, user_provider, password_hasher, password_policy_provider, credential_provider, mock_user):
    user_provider.get_by_email.return_value = None
    user_provider.get_by_username.return_value = None
    password_policy_provider.validate_strength.return_value = True
    user_provider.create_user.return_value = mock_user
    password_hasher.hash_password.return_value = "hashed_pw"

    user = await email_auth_service.register("test@example.com", "testuser", "StrongP@ssw0rd")

    assert user.id == "user-123"
    password_policy_provider.validate_strength.assert_called_once_with("StrongP@ssw0rd")
    user_provider.create_user.assert_called_once()
    credential_provider.set_password_hash.assert_called_once_with("user-123", "hashed_pw")

@pytest.mark.asyncio
async def test_register_duplicate_email(email_auth_service, user_provider, mock_user):
    user_provider.get_by_email.return_value = mock_user

    with pytest.raises(DomainException, match="Email is already in use"):
        await email_auth_service.register("test@example.com", "testuser", "StrongP@ssw0rd")

@pytest.mark.asyncio
async def test_register_weak_password(email_auth_service, user_provider, password_policy_provider):
    user_provider.get_by_email.return_value = None
    user_provider.get_by_username.return_value = None
    password_policy_provider.validate_strength.return_value = False

    with pytest.raises(DomainException, match="Password does not meet strength requirements"):
        await email_auth_service.register("test@example.com", "testuser", "weak")

@pytest.mark.asyncio
async def test_login_success(email_auth_service, user_provider, password_hasher, credential_provider, mock_user):
    user_provider.get_by_email.return_value = mock_user
    credential_provider.get_password_hash.return_value = "hashed_pw"
    password_hasher.verify_password.return_value = True

    user = await email_auth_service.login("test@example.com", "StrongP@ssw0rd")
    assert user.id == "user-123"

@pytest.mark.asyncio
async def test_login_invalid_password(email_auth_service, user_provider, password_hasher, credential_provider, mock_user):
    user_provider.get_by_email.return_value = mock_user
    credential_provider.get_password_hash.return_value = "hashed_pw"
    password_hasher.verify_password.return_value = False

    with pytest.raises(DomainException, match="Invalid credentials"):
        await email_auth_service.login("test@example.com", "wrongpassword")

@pytest.mark.asyncio
async def test_change_password_success(email_auth_service, password_hasher, password_policy_provider, credential_provider, mock_user):
    credential_provider.get_password_hash.return_value = "old_hash"
    password_hasher.verify_password.return_value = True
    password_policy_provider.validate_strength.return_value = True
    password_hasher.hash_password.return_value = "new_hash"
    password_policy_provider.validate_history.return_value = True

    await email_auth_service.change_password(mock_user, "old_password", "new_password")

    credential_provider.set_password_hash.assert_called_once_with("user-123", "new_hash")
