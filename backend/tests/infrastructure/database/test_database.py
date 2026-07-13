import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.core.config import DatabaseSettings, Settings
from app.infrastructure.database.engine import create_db_engine
from app.infrastructure.database.session import get_sessionmaker
from app.dependencies.infrastructure import get_engine, get_db_sessionmaker


def test_database_settings_url():
    """Verify DatabaseSettings correctly formats the connection string."""
    settings = DatabaseSettings(
        host="test_host",
        port=5432,
        username="test_user",
        password="test_password",
        database="test_db"
    )
    assert settings.async_database_url == "postgresql+asyncpg://test_user:test_password@test_host:5432/test_db"


def test_create_db_engine():
    """Verify engine is created with correct settings."""
    settings = DatabaseSettings(
        pool_size=5,
        max_overflow=10,
        echo=True
    )
    engine = create_db_engine(settings)
    
    assert isinstance(engine, AsyncEngine)
    assert engine.name == "postgresql"
    assert engine.driver == "asyncpg"
    assert engine.echo is True
    # The pool object can be checked for size parameters
    assert engine.pool.size() == 5


def test_get_sessionmaker():
    """Verify async_sessionmaker is properly configured."""
    settings = DatabaseSettings()
    engine = create_db_engine(settings)
    session_maker = get_sessionmaker(engine)
    
    assert isinstance(session_maker, async_sessionmaker)
    assert session_maker.kw["autoflush"] is False
    assert session_maker.kw["expire_on_commit"] is False


def test_dependency_injection_singletons():
    """Verify DI methods reuse the same singletons for engine and sessionmaker."""
    # This requires resetting the global singletons in infrastructure.py
    import app.dependencies.infrastructure as infra
    infra._engine = None
    infra._sessionmaker = None
    
    settings = Settings()
    
    engine1 = get_engine(settings)
    engine2 = get_engine(settings)
    
    assert engine1 is engine2
    
    maker1 = get_db_sessionmaker(engine1)
    maker2 = get_db_sessionmaker(engine1)
    
    assert maker1 is maker2
