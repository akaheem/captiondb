"""
SQLAlchemy Async Session Management.
"""
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

def get_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Creates an async session maker bound to the provided engine.
    Ensures autoflush is disabled to prevent accidental partial writes.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )
