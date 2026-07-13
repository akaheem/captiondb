import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path

from app.services.scene import SceneDetectionService
from app.domain.models.video import Video, Scene, VideoMetadata
from app.domain.models.analysis import ProcessingContext
from app.core.exceptions import SceneDetectionException, MetadataExtractionError


@pytest.fixture
def mock_storage():
    storage = MagicMock()
    # Mock the internal provider validation
    storage._provider = MagicMock()
    path_mock = MagicMock(spec=Path)
    path_mock.exists.return_value = True
    storage._provider._resolve_and_validate_path.return_value = path_mock
    return storage


@pytest.fixture
def mock_detector():
    detector = AsyncMock()
    return detector


@pytest.fixture
def base_context():
    video = Video(
        project_name="test",
        original_filename="vid.mp4",
        logical_path="test/vid.mp4",
        metadata=VideoMetadata(
            size_bytes=1000,
            duration_seconds=10.5,
            fps=30.0,
            codec="h264",
            resolution="1080p"
        )
    )
    return ProcessingContext(video=video, current_stage_name="Init")


@pytest.mark.asyncio
async def test_normal_detection(mock_storage, mock_detector, base_context):
    service = SceneDetectionService(mock_detector, mock_storage)
    
    # Detector returns valid scenes
    mock_detector.detect_scenes.return_value = [
        Scene(seconds_start=0.0, seconds_end=5.1234),
        Scene(seconds_start=5.1234, seconds_end=10.5)
    ]
    
    context = await service.process(base_context)
    
    assert context.current_stage_name == "SceneDetection"
    assert len(context.video.scenes) == 2
    # Check normalization to 3 decimals
    assert context.video.scenes[0].seconds_end == 5.123


@pytest.mark.asyncio
async def test_empty_results_fallback(mock_storage, mock_detector, base_context):
    service = SceneDetectionService(mock_detector, mock_storage)
    
    # Detector finds nothing
    mock_detector.detect_scenes.return_value = []
    
    context = await service.process(base_context)
    
    assert len(context.video.scenes) == 1
    assert context.video.scenes[0].seconds_start == 0.0
    assert context.video.scenes[0].seconds_end == 10.5


@pytest.mark.asyncio
async def test_invalid_scene_boundaries(mock_storage, mock_detector, base_context):
    service = SceneDetectionService(mock_detector, mock_storage)
    
    mock_detector.detect_scenes.return_value = [
        Scene(seconds_start=-1.0, seconds_end=2.0), # Negative start (should become 0)
        Scene(seconds_start=3.0, seconds_end=2.0),  # End before start (should drop)
        Scene(seconds_start=5.0, seconds_end=20.0), # End beyond duration (should cap at 10.5)
    ]
    
    context = await service.process(base_context)
    
    assert len(context.video.scenes) == 2
    assert context.video.scenes[0].seconds_start == 0.0
    assert context.video.scenes[0].seconds_end == 2.0
    
    assert context.video.scenes[1].seconds_start == 5.0
    assert context.video.scenes[1].seconds_end == 10.5


@pytest.mark.asyncio
async def test_detector_failure(mock_storage, mock_detector, base_context):
    service = SceneDetectionService(mock_detector, mock_storage)
    
    mock_detector.detect_scenes.side_effect = MetadataExtractionError("OpenCV Crash")
    
    with pytest.raises(SceneDetectionException) as exc:
        await service.process(base_context)
        
    assert "Underlying detector failed" in str(exc.value)


@pytest.mark.asyncio
async def test_file_not_found(mock_storage, mock_detector, base_context):
    # Override storage to simulate missing file
    mock_storage._provider._resolve_and_validate_path.return_value.exists.return_value = False
    
    service = SceneDetectionService(mock_detector, mock_storage)
    
    with pytest.raises(SceneDetectionException) as exc:
        await service.process(base_context)
        
    assert "Video file not found" in str(exc.value)
