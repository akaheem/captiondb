import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path

from app.services.frame import FrameSamplingService
from app.domain.models.video import Video, Scene, VideoMetadata
from app.domain.models.analysis import ProcessingContext
from app.domain.models.ai import AIImageContent
from app.core.exceptions import ValidationException, FrameExtractionError


@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage._provider = MagicMock()
    path_mock = MagicMock(spec=Path)
    path_mock.exists.return_value = True
    storage._provider._resolve_and_validate_path.return_value = path_mock
    return storage


@pytest.fixture
def mock_extractor():
    extractor = AsyncMock()
    # By default, mock successful extraction of an AIImageContent
    # Note: the mock must return a list of AIImageContent matching the requested timestamps
    async def side_effect(path, timestamps):
        return [AIImageContent(data_uri=f"data:image/jpeg;base64,dummy{i}") for i in range(len(timestamps))]
    extractor.extract_frames.side_effect = side_effect
    return extractor


def create_context(scenes):
    video = Video(
        project_name="test",
        original_filename="vid.mp4",
        logical_path="test/vid.mp4",
        metadata=VideoMetadata(
            size_bytes=1000,
            duration_seconds=100.0,
            fps=30.0,
            codec="h264",
            resolution="1080p"
        ),
        scenes=scenes
    )
    return ProcessingContext(video=video, current_stage_name="SceneDetection")


@pytest.mark.asyncio
async def test_normal_sampling(mock_storage, mock_extractor):
    # Scene is 10 seconds. At 0.5fps, we should request exactly 5 frames.
    scene = Scene(seconds_start=10.0, seconds_end=20.0, scene_id="scene-1")
    context = create_context([scene])
    
    service = FrameSamplingService(mock_extractor, mock_storage)
    updated_context = await service.process(context)
    
    assert updated_context.current_stage_name == "FrameSampling"
    assert "scene-1" in updated_context.extracted_frames
    assert len(updated_context.extracted_frames["scene-1"]) == 5
    
    mock_extractor.extract_frames.assert_called_once()
    
    # Check the requested timestamps
    call_args = mock_extractor.extract_frames.call_args
    timestamps = call_args[0][1]
    
    assert len(timestamps) == 5
    # The interval is 10 / 5 = 2.0s
    # The frames should be taken at midpoints: start + 1.0 + (i * 2.0)
    assert timestamps == [11.0, 13.0, 15.0, 17.0, 19.0]


@pytest.mark.asyncio
async def test_very_short_scenes(mock_storage, mock_extractor):
    # Scene is 0.5 seconds. At 0.5fps, this would be 0 frames, but it should floor to min_frames=1.
    scene = Scene(seconds_start=5.0, seconds_end=5.5, scene_id="scene-short")
    context = create_context([scene])
    
    service = FrameSamplingService(mock_extractor, mock_storage)
    updated_context = await service.process(context)
    
    assert len(updated_context.extracted_frames["scene-short"]) == 1
    
    call_args = mock_extractor.extract_frames.call_args
    timestamps = call_args[0][1]
    
    assert len(timestamps) == 1
    # Interval is 0.5. Midpoint is start + 0.25
    assert timestamps == [5.25]


@pytest.mark.asyncio
async def test_very_long_scenes(mock_storage, mock_extractor):
    # Scene is 60 seconds. At 0.5fps, this would be 30 frames. It should cap to max_frames=10.
    scene = Scene(seconds_start=0.0, seconds_end=60.0, scene_id="scene-long")
    context = create_context([scene])
    
    service = FrameSamplingService(mock_extractor, mock_storage)
    updated_context = await service.process(context)
    
    assert len(updated_context.extracted_frames["scene-long"]) == 10
    
    call_args = mock_extractor.extract_frames.call_args
    timestamps = call_args[0][1]
    assert len(timestamps) == 10


@pytest.mark.asyncio
async def test_empty_scenes(mock_storage, mock_extractor):
    # Video has no scenes
    context = create_context([])
    service = FrameSamplingService(mock_extractor, mock_storage)
    
    with pytest.raises(ValidationException) as exc:
        await service.process(context)
    assert "No scenes defined" in str(exc.value)


@pytest.mark.asyncio
async def test_invalid_timestamps(mock_storage, mock_extractor):
    # Scene duration is 0 or negative
    scene = Scene(seconds_start=15.0, seconds_end=15.0, scene_id="scene-invalid")
    context = create_context([scene])
    
    service = FrameSamplingService(mock_extractor, mock_storage)
    updated_context = await service.process(context)
    
    # Should fallback to exactly 1 frame at seconds_start
    assert len(updated_context.extracted_frames["scene-invalid"]) == 1
    
    call_args = mock_extractor.extract_frames.call_args
    timestamps = call_args[0][1]
    assert timestamps == [15.0]


@pytest.mark.asyncio
async def test_extractor_failure(mock_storage, mock_extractor):
    scene = Scene(seconds_start=0.0, seconds_end=10.0, scene_id="scene-1")
    context = create_context([scene])
    
    service = FrameSamplingService(mock_extractor, mock_storage)
    
    # Force underlying extraction error
    mock_extractor.extract_frames.side_effect = FrameExtractionError("Missing Codec")
    
    with pytest.raises(FrameExtractionError) as exc:
        await service.process(context)
        
    assert "Missing Codec" in str(exc.value)
