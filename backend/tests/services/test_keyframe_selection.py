import pytest
from unittest.mock import MagicMock, AsyncMock

from app.services.keyframe import KeyframeSelectionService
from app.domain.models.video import Video, Scene, VideoMetadata
from app.domain.models.analysis import ProcessingContext
from app.domain.models.ai import AIImageContent
from app.core.exceptions import ValidationException, KeyframeSelectionError


@pytest.fixture
def mock_selector():
    selector = AsyncMock()
    return selector


def create_context(extracted_frames_map):
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
        scenes=[Scene(seconds_start=0.0, seconds_end=10.0, scene_id=k) for k in extracted_frames_map.keys()]
    )
    context = ProcessingContext(video=video, current_stage_name="FrameSampling")
    context.extracted_frames = extracted_frames_map
    return context


@pytest.mark.asyncio
async def test_normal_selection(mock_selector):
    # Setup context with 3 candidates
    candidates = [
        AIImageContent(data_uri="data1"),
        AIImageContent(data_uri="data2"),
        AIImageContent(data_uri="data3")
    ]
    context = create_context({"scene-1": candidates})
    
    # Mock selector returns only 2 of them
    mock_selector.select_keyframes.return_value = [candidates[0], candidates[2]]
    
    service = KeyframeSelectionService(mock_selector)
    updated_context = await service.process(context)
    
    assert updated_context.current_stage_name == "KeyframeSelection"
    assert len(updated_context.extracted_frames["scene-1"]) == 2
    assert updated_context.extracted_frames["scene-1"] == [candidates[0], candidates[2]]
    mock_selector.select_keyframes.assert_called_once_with(candidates)


@pytest.mark.asyncio
async def test_empty_candidate_list(mock_selector):
    # Setup context with empty list
    context = create_context({"scene-empty": []})
    
    service = KeyframeSelectionService(mock_selector)
    updated_context = await service.process(context)
    
    # It should skip the selector and keep it empty
    assert len(updated_context.extracted_frames["scene-empty"]) == 0
    mock_selector.select_keyframes.assert_not_called()


@pytest.mark.asyncio
async def test_no_extracted_frames(mock_selector):
    # Setup context with no dictionary
    context = create_context({})
    
    service = KeyframeSelectionService(mock_selector)
    with pytest.raises(ValidationException) as exc:
        await service.process(context)
        
    assert "No candidate frames exist" in str(exc.value)


@pytest.mark.asyncio
async def test_selector_failure(mock_selector):
    candidates = [AIImageContent(data_uri="data1")]
    context = create_context({"scene-1": candidates})
    
    # Force selector exception
    mock_selector.select_keyframes.side_effect = Exception("OpenCV Crash")
    
    service = KeyframeSelectionService(mock_selector)
    
    with pytest.raises(KeyframeSelectionError) as exc:
        await service.process(context)
        
    assert "OpenCV Crash" in str(exc.value)
