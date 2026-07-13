"""
Unit of Work Domain Interface.
Abstracts transaction boundaries and repository access.
"""
from abc import ABC, abstractmethod
from typing import AsyncContextManager, Any

# Import only domain-level repository concepts (as abstractions) if needed,
# or we can use the concrete ones from infrastructure as long as we don't leak ORM.
# Wait, repositories are currently only in infrastructure. 
# We should probably define Repository interfaces in domain, but the instructions didn't mention it.
# The instructions state: "It should expose VideoRepository, SceneRepository, CaptionRepository".
# It is acceptable in this phase to return `Any` or type-hint them lazily to avoid circular imports.

class AbstractUnitOfWork(ABC):
    """
    Abstract Unit of Work.
    Provides a consistent boundary for transactions.
    """
    # Repositories (To be initialized by concrete implementations)
    # We use string type hints to avoid direct coupling if needed, 
    # but the domain interface serves as the contract.
    videos: Any
    scenes: Any
    captions: Any

    async def __aenter__(self) -> "AbstractUnitOfWork":
        await self.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        # The concrete class will decide if it commits automatically or requires explicit commit
        # For safety, explicit commit is usually better, but we close.
        await self.close()

    @abstractmethod
    async def begin(self) -> None:
        """Starts a transaction."""
        pass

    @abstractmethod
    async def commit(self) -> None:
        """Commits the active transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rolls back the active transaction."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Closes the unit of work resources."""
        pass
