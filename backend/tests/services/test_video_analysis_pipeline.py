import pytest
from unittest.mock import AsyncMock

from app.services.video_analysis_pipeline import VideoAnalysisPipeline
from app.domain.models.analysis import ProcessingContext, VisionInputPackage
from app.domain.models.video import Video, VideoMetadata, Scene
from app.core.exceptions import (
    SceneDetectionError,
    VideoAnalysisPipelineException
)

@pytest.fixture
def mock_scene_service():
    service = AsyncMock()
    async def side_effect(ctx):
        ctx.current_stage_name = "SceneDetection"
        return ctx
    service.process.side_effect = side_effect
    return service

@pytest.fixture
def mock_frame_service():
    service = AsyncMock()
    async def side_effect(ctx):
        ctx.current_stage_name = "FrameSampling"
        return ctx
    service.process.side_effect = side_effect
    return service

@pytest.fixture
def mock_keyframe_service():
    service = AsyncMock()
    async def side_effect(ctx):
        ctx.current_stage_name = "KeyframeSelection"
        return ctx
    service.process.side_effect = side_effect
    return service

@pytest.fixture
def mock_vision_prep_service():
    service = AsyncMock()
    async def side_effect(ctx):
        ctx.current_stage_name = "VisionInputPreparation"
        return [VisionInputPackage(
            video_id="test",
            scene=Scene(seconds_start=0.0, seconds_end=1.0, scene_id="s1"),
            video_context=VideoMetadata(0,0,0,"",""),
            target_tone=None,
            key_frames=[]
        )]
    service.process.side_effect = side_effect
    return service

def create_context():
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
        )
    )
    return ProcessingContext(video=video, current_stage_name="Init")


@pytest.mark.asyncio
async def test_pipeline_success(
    mock_scene_service,
    mock_frame_service,
    mock_keyframe_service,
    mock_vision_prep_service
):
    pipeline = VideoAnalysisPipeline(
        mock_scene_service,
        mock_frame_service,
        mock_keyframe_service,
        mock_vision_prep_service
    )
    
    context = create_context()
    result = await pipeline.run(context)
    
    # Assert successful orchestration
    assert result.is_success
    assert len(result.packages) == 1
    assert result.error_message is None
    
    mock_scene_service.process.assert_called_once()
    mock_frame_service.process.assert_called_once()
    mock_keyframe_service.process.assert_called_once()
    mock_vision_prep_service.process.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_domain_failure(
    mock_scene_service,
    mock_frame_service,
    mock_keyframe_service,
    mock_vision_prep_service
):
    pipeline = VideoAnalysisPipeline(
        mock_scene_service,
        mock_frame_service,
        mock_keyframe_service,
        mock_vision_prep_service
    )
    
    context = create_context()
    context.current_stage_name = "SceneDetection"
    
    # Simulate a domain failure gracefully aborting the pipeline
    mock_scene_service.process.side_effect = SceneDetectionError("FFprobe missing")
    
    result = await pipeline.run(context)
    
    assert not result.is_success
    assert "SceneDetection: FFprobe missing" in result.error_message
    
    # Should halt immediately
    mock_frame_service.process.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_unexpected_failure(
    mock_scene_service,
    mock_frame_service,
    mock_keyframe_service,
    mock_vision_prep_service
):
    pipeline = VideoAnalysisPipeline(
        mock_scene_service,
        mock_frame_service,
        mock_keyframe_service,
        mock_vision_prep_service
    )
    
    context = create_context()
    
    # Simulate an unexpected critical crash (e.g. TypeError or OutOfMemory)
    mock_scene_service.process.side_effect = ValueError("Out of memory")
    
    with pytest.raises(VideoAnalysisPipelineException) as exc:
        await pipeline.run(context)
        
    assert "Critical Pipeline Failure" in str(exc.value)
    assert "Out of memory" in str(exc.value)
