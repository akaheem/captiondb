"""
Global Pytest Configuration and Reusable Fixtures.
Provides standard fixtures for the FastAPI application, settings, test clients, and logging.
"""
import pytest
import logging
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from pathlib import Path
from fastapi import FastAPI

# Adjust sys.path or simply import since pytest runs from backend root
from app.main import create_app
from app.core.config import Settings, get_settings
from app.dependencies.core import get_logger
from app.dependencies.infrastructure import get_storage_provider


@pytest.fixture
def temp_storage_dir(tmp_path: Path) -> Path:
    """Provides an isolated temporary directory for file operations."""
    storage_dir = tmp_path / "captiondb_storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


@pytest.fixture
def mock_settings(temp_storage_dir: Path) -> Settings:
    """
    Overrides environment variables to provide a stable configuration for tests.
    Ensures tests do not accidentally connect to production or development databases/storage.
    """
    return Settings(
        app={
            "name": "CaptionDB-Test",
            "environment": "testing"
        },
        storage={
            "provider": "local",
            "local_storage_path": str(temp_storage_dir)
        }
    )


@pytest.fixture
def mock_logger() -> logging.Logger:
    """Provides a null-logging implementation or a captured logger for test verification."""
    # We use a standard library logger here. It could be extended to use `loguru` captures.
    return logging.getLogger("test_logger")


@pytest.fixture
def app(mock_settings: Settings, mock_logger: logging.Logger) -> FastAPI:
    """
    Creates a fresh FastAPI application instance for each test.
    Injects the mock_settings into the dependency graph.
    """
    # 1. Create the FastAPI app
    app_instance = create_app()

    # 2. Clear global cache to prevent test pollution
    get_settings.cache_clear()

    # 3. Apply FastAPI dependency overrides
    app_instance.dependency_overrides[get_settings] = lambda: mock_settings
    app_instance.dependency_overrides[get_logger] = lambda: mock_logger

    return app_instance


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an asynchronous HTTP test client for making requests to the FastAPI application.
    Automatically manages application lifespan events (startup/shutdown).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
