import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock

from app.main import app
from app.dependencies.services import get_upload_service
from app.services.upload import UploadResult
from app.domain.models.video import Video, VideoStatus, ProcessingState, VideoMetadata, VideoDimensions, VideoFormat

@pytest.fixture
def mock_upload_service():
    service = AsyncMock()
    # By default, mock successful upload
    video = Video(
        id="vid-123",
        project_name="proj-alpha",
        original_filename="test.mp4",
        logical_path="projects/proj-alpha/uploads/vid-123/test.mp4",
        state=ProcessingState(status=VideoStatus.QUEUED),
        metadata=VideoMetadata(
            size_bytes=1000,
            duration_seconds=10.0,
            fps=30.0,
            codec="h264",
            resolution="1920x1080",
            dimensions=VideoDimensions(1920, 1080),
            format=VideoFormat.MP4
        )
    )
    service.process_upload.return_value = UploadResult(success=True, video=video)
    return service

@pytest.fixture
async def client(mock_upload_service):
    # Override dependency
    app.dependency_overrides[get_upload_service] = lambda: mock_upload_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_video_success(client, mock_upload_service):
    """Test successful multipart upload yielding 200 OK."""
    files = {"file": ("test.mp4", b"dummy_data", "video/mp4")}
    data = {"project_name": "proj-alpha"}
    
    response = await client.post("/api/v1/upload/", data=data, files=files)
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["video_id"] == "vid-123"
    assert res_data["project_name"] == "proj-alpha"
    assert res_data["status"] == "QUEUED"
    assert res_data["metadata"]["codec"] == "h264"
    assert res_data["metadata"]["resolution"] == "1920x1080"


@pytest.mark.asyncio
async def test_upload_missing_filename(client, mock_upload_service):
    """Test handling of upload without filename (though FastAPI usually prevents this)."""
    # Overriding the file tuple to omit filename
    files = {"file": ("", b"dummy_data", "video/mp4")}
    data = {"project_name": "proj-alpha"}
    
    response = await client.post("/api/v1/upload/", data=data, files=files)
    
    assert response.status_code == 400
    assert "Filename missing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_validation_failure(client, mock_upload_service):
    """Test when Domain Validation logic inside UploadService fails."""
    mock_upload_service.process_upload.return_value = UploadResult(
        success=False, 
        errors=["Invalid file extension. Expected .mp4, got .txt"]
    )
    
    files = {"file": ("test.txt", b"dummy_data", "text/plain")}
    data = {"project_name": "proj-alpha"}
    
    response = await client.post("/api/v1/upload/", data=data, files=files)
    
    assert response.status_code == 400
    assert response.json()["detail"]["errors"][0] == "Invalid file extension. Expected .mp4, got .txt"


@pytest.mark.asyncio
async def test_upload_missing_project_name(client):
    """Test schema validation (FastAPI level)."""
    files = {"file": ("test.mp4", b"dummy_data", "video/mp4")}
    
    response = await client.post("/api/v1/upload/", files=files)
    
    # Missing required Form field triggers 422 Unprocessable Entity
    assert response.status_code == 422
