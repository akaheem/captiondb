from typing import Optional, Dict, Any
from loguru import logger

from app.domain.interfaces.auth import SessionProvider
from app.domain.exceptions import DomainException

class SessionService:
    def __init__(self, session_provider: SessionProvider):
        self._session_provider = session_provider

    async def create_session(self, user_id: str, metadata: Dict[str, Any]) -> str:
        logger.info(f"Creating session for user {user_id}")
        return await self._session_provider.create_session(user_id, metadata)

    async def refresh_session(self, session_id: str) -> None:
        logger.info(f"Refreshing session {session_id}")
        # Assuming provider will implement refresh_session to extend TTL
        if hasattr(self._session_provider, 'refresh_session'):
            await getattr(self._session_provider, 'refresh_session')(session_id)
        else:
            raise NotImplementedError("Session refresh not implemented by provider.")

    async def terminate_session(self, session_id: str) -> None:
        logger.info(f"Terminating session {session_id}")
        await self._session_provider.revoke_session(session_id)

    async def validate_session(self, session_id: str) -> Dict[str, Any]:
        session_data = await self._session_provider.get_session(session_id)
        if not session_data:
            raise DomainException("Session invalid or expired.")
        return session_data
