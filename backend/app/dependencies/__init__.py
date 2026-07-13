"""
CaptionDB Dependency Injection Package.
This package organizes all FastAPI Depends() providers.
"""
# Core dependencies
from .core import get_logger

# Infrastructure dependencies
from .infrastructure import get_storage_provider, get_ai_provider, get_cache_provider, get_db_session

# Re-export get_settings from core config for convenience
from app.core.config import get_settings
