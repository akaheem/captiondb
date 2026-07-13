"""
Base Repository.
Provides a foundational boundary for persistence translation.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError


class RepositoryException(Exception):
    """Base exception for all repository-level persistence failures."""
    pass


class RecordNotFoundException(RepositoryException):
    """Raised when a specific requested record is not found."""
    pass


class BaseRepository:
    """
    Abstract base repository.
    Only depends on the scoped AsyncSession passed from the Unit of Work.
    """
    def __init__(self, session: AsyncSession):
        self._session = session
