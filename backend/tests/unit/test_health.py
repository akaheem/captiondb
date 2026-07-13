"""
Unit tests for the health, readiness, and root endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Verifies the root endpoint returns basic project metadata."""
    response = await client.get("/api/v1/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["project"] == "CaptionDB-Test"
    assert data["status"] == "online"


@pytest.mark.asyncio
async def test_liveness_probe(client: AsyncClient):
    """Verifies the liveness probe returns standard health schema without checking deep dependencies."""
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "CaptionDB-Test"
    assert "uptime_seconds" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_probe(client: AsyncClient):
    """Verifies the readiness probe maps component status correctly."""
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "components" in data
    
    # Check that placeholders return 'not_configured' as implemented in Phase 1.6
    components = data["components"]
    assert components["storage"]["status"] == "not_configured"
    assert components["database"]["status"] == "not_configured"
    assert components["ai_provider"]["status"] == "not_configured"


@pytest.mark.asyncio
async def test_app_info(client: AsyncClient):
    """Verifies safe metadata is returned without exposing configuration secrets."""
    response = await client.get("/api/v1/health/info")
    assert response.status_code == 200
    
    data = response.json()
    assert data["application_name"] == "CaptionDB-Test"
    assert data["environment"] == "testing"
    assert "python_version" in data
    assert "build_info" in data
