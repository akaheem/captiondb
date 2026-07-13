"""
SQLAlchemy implementation of the Unit of Work.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.domain.interfaces.unit_of_work import AbstractUnitOfWork
from app.infrastructure.repositories.video_repository import VideoRepository
from app.infrastructure.repositories.scene_repository import SceneRepository
from app.infrastructure.repositories.caption_repository import CaptionRepository

class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    SQLAlchemy-backed Unit of Work.
    Instantiates repositories with a shared, transactional AsyncSession.
    """
    
    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory
        self._session: Optional[AsyncSession] = None
        
        # Repositories
        self.videos: Optional[VideoRepository] = None
        self.scenes: Optional[SceneRepository] = None
        self.captions: Optional[CaptionRepository] = None

    async def begin(self) -> None:
        """Starts the session and initializes the repositories."""
        if not self._session:
            self._session = self._session_factory()
            
        self.videos = VideoRepository(self._session)
        self.scenes = SceneRepository(self._session)
        self.captions = CaptionRepository(self._session)

    async def commit(self) -> None:
        """Commits the active transaction."""
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        """Rolls back the active transaction."""
        if self._session:
            await self._session.rollback()

    async def close(self) -> None:
        """Closes the session safely."""
        if self._session:
            await self._session.close()
            self._session = None
            
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        await self.close()
