import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.infrastructure.database.base import Base

@pytest_asyncio.fixture
async def async_db_engine():
    # Use an in-memory SQLite database for testing the ORM
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def async_session_factory(async_db_engine):
    return async_sessionmaker(async_db_engine, class_=AsyncSession, expire_on_commit=False)
