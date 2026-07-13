"""
SQLAlchemy Async Engine Factory.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.core.config import DatabaseSettings

def create_db_engine(settings: DatabaseSettings) -> AsyncEngine:
    """
    Creates the SQLAlchemy asynchronous engine.
    Applies connection pooling settings from the application configuration.
    """
    return create_async_engine(
        url=settings.async_database_url,
        echo=settings.echo,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        # Ensure connections aren't held indefinitely if the DB restarts
        pool_pre_ping=True
    )
