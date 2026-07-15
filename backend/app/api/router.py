"""
Global API Router.
Aggregates all API versions into a single router.
This keeps main.py entirely free of endpoint registration logic.
"""
from fastapi import APIRouter
from app.core.config import get_settings
from app.api.v1.router import v1_router

# Future imports:
# from app.api.v2.router import v2_router

global_api_router = APIRouter()
settings = get_settings()

# Register API v1
# We inject the prefix from settings (e.g., "/api/v1") here.
global_api_router.include_router(v1_router, prefix=settings.api.v1_prefix)

# Future:
# global_api_router.include_router(v2_router, prefix=settings.api.v2_prefix)
