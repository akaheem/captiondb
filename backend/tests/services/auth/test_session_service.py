import pytest
from unittest.mock import AsyncMock

from app.services.session import SessionService
from app.domain.exceptions import DomainException

@pytest.fixture
def session_provider():
    return AsyncMock()

@pytest.fixture
def session_service(session_provider):
    return SessionService(session_provider=session_provider)

@pytest.mark.asyncio
async def test_session_delegation(session_service, session_provider):
    session_provider.create_session.return_value = "session-123"
    
    sid = await session_service.create_session("user-123", {"ip": "127.0.0.1"})
    
    assert sid == "session-123"
    session_provider.create_session.assert_called_once_with("user-123", {"ip": "127.0.0.1"})

@pytest.mark.asyncio
async def test_validate_session(session_service, session_provider):
    session_provider.get_session.return_value = {"user_id": "user-123"}
    
    data = await session_service.validate_session("valid-session")
    assert data == {"user_id": "user-123"}

@pytest.mark.asyncio
async def test_invalid_session(session_service, session_provider):
    session_provider.get_session.return_value = None
    
    with pytest.raises(DomainException, match="Session invalid or expired"):
        await session_service.validate_session("invalid-session")
