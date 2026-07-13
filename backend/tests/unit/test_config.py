"""
Unit tests for application configuration loading.
"""
from pathlib import Path
from app.core.config import Settings


def test_settings_initialization(tmp_path: Path):
    """
    Tests that the Pydantic Settings model can be instantiated and 
    provides correct defaults or accepts overrides.
    """
    custom_path = str(tmp_path / "custom_storage")
    
    settings = Settings(
        app={"name": "CustomAppName", "environment": "staging"},
        storage={"provider": "local", "local_storage_path": custom_path}
    )
    
    assert settings.app.name == "CustomAppName"
    assert settings.app.environment == "staging"
    assert settings.storage.provider == "local"
    assert settings.storage.local_storage_path == custom_path
