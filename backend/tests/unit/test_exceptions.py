"""
Unit tests for the global exception handling framework.
"""
import pytest
from httpx import AsyncClient
from fastapi import APIRouter
from app.core.exceptions import ValidationException, StorageException, NotFoundException


def test_exception_handler_registration(app):
    """
    Dynamically adds test routes to the app to verify global exception handlers
    transform domain exceptions into safe JSON responses.
    """
    router = APIRouter()
    
    @router.get("/trigger-validation-error")
    async def trigger_validation():
        raise ValidationException("Video duration exceeds limit.")
        
    @router.get("/trigger-storage-error")
    async def trigger_storage():
        raise StorageException("Disk full.")
        
    @router.get("/trigger-unhandled")
    async def trigger_unhandled():
        raise KeyError("Unexpected key missing.")
        
    app.include_router(router, prefix="/test-errors")


@pytest.mark.asyncio
async def test_validation_exception_maps_to_400(client: AsyncClient, app):
    """Verifies ValidationException returns HTTP 400."""
    test_exception_handler_registration(app)
    
    response = await client.get("/test-errors/trigger-validation-error")
    assert response.status_code == 400
    
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert data["message"] == "Video duration exceeds limit."


@pytest.mark.asyncio
async def test_storage_exception_maps_to_500(client: AsyncClient, app):
    """Verifies internal infrastructure exceptions return HTTP 500 without leaking details."""
    test_exception_handler_registration(app)
    
    response = await client.get("/test-errors/trigger-storage-error")
    assert response.status_code == 500
    
    data = response.json()
    assert data["error_code"] == "STORAGE_ERROR"
    assert data["message"] == "Disk full."


@pytest.mark.asyncio
async def test_unhandled_exception_maps_to_500(client: AsyncClient, app):
    """Verifies raw Python exceptions are caught and sanitized."""
    test_exception_handler_registration(app)
    
    response = await client.get("/test-errors/trigger-unhandled")
    assert response.status_code == 500
    
    data = response.json()
    assert data["error_code"] == "INTERNAL_SERVER_ERROR"
    assert data["message"] == "An unexpected internal server error occurred."
    assert "KeyError" not in response.text  # Stack trace must not leak
