import pytest
from unittest.mock import AsyncMock

from app.domain.models.auth import User
from app.services.token import TokenService
from app.domain.exceptions import DomainException

@pytest.fixture
def token_provider():
    return AsyncMock()

@pytest.fixture
def token_service(token_provider):
    return TokenService(token_provider=token_provider)

@pytest.mark.asyncio
async def test_issue_access_token_delegation(token_service, token_provider):
    mock_user = AsyncMock(spec=User)
    token_provider.generate_token.return_value = "mock_access_token"
    
    token = await token_service.issue_access_token(mock_user)
    
    assert token == "mock_access_token"
    token_provider.generate_token.assert_called_once_with(mock_user)

@pytest.mark.asyncio
async def test_validate_token(token_service, token_provider):
    token_provider.verify_token.return_value = {"user_id": "123"}
    
    result = await token_service.validate_token("valid_token")
    assert result == {"user_id": "123"}

@pytest.mark.asyncio
async def test_validate_invalid_token(token_service, token_provider):
    token_provider.verify_token.return_value = None
    
    with pytest.raises(DomainException, match="Invalid or expired token"):
        await token_service.validate_token("invalid_token")
