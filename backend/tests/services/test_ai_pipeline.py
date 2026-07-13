import pytest
from unittest.mock import AsyncMock

from app.services.ai_pipeline import AIPipelineService
from app.domain.models.pipeline import PipelineStatus
from app.domain.models.analysis import ProcessingContext, VideoAnalysisPipelineResult, VisionInputPackage
from app.domain.models.vision import VisionAnalysisResult
from app.domain.models.caption import CaptionGenerationResult, CaptionCandidate, CaptionStatistics, CaptionMetadata
from app.domain.models.video import Video, Scene, CaptionTone, VideoMetadata
from app.domain.models.ai import AIUsage, AIModelInfo


@pytest.fixture
def mock_video_pipeline():
    return AsyncMock()

@pytest.fixture
def mock_vision_service():
    return AsyncMock()

@pytest.fixture
def mock_caption_service():
    return AsyncMock()

@pytest.fixture
def ai_service(mock_video_pipeline, mock_vision_service, mock_caption_service):
    return AIPipelineService(mock_video_pipeline, mock_vision_service, mock_caption_service)

def create_context():
    return ProcessingContext(
        video=Video(project_name="Test", original_filename="test.mp4", logical_path="/test"),
        target_tone=CaptionTone.HUMOROUS_NON_TECH
    )

def create_video_analysis_result(num_scenes: int, success: bool = True):
    packages = []
    for i in range(num_scenes):
        scene = Scene(seconds_start=0.0, seconds_end=1.0, scene_id=f"scene_{i}")
        pkg = VisionInputPackage(
            video_id="vid_1",
            scene=scene,
            video_context=VideoMetadata(0, 0.0, 0.0, "", ""),
            target_tone=CaptionTone.HUMOROUS_NON_TECH,
            key_frames=[]
        )
        packages.append(pkg)
    return VideoAnalysisPipelineResult(is_success=success, packages=packages, error_message=None if success else "Failed")

def create_vision_result():
    res = VisionAnalysisResult(
        scene_summary="A summary",
        objects=[], activities=[], environment="", mood="", dominant_colors=[], safety_flags=[]
    )
    res.metadata = type("Metadata", (), {"usage": AIUsage(10, 5, 15)})()
    return res

def create_caption_result():
    return CaptionGenerationResult(
        candidates=[CaptionCandidate(text="Caption", tone=CaptionTone.HUMOROUS_NON_TECH, statistics=CaptionStatistics(1, 1))],
        metadata=CaptionMetadata(model_info=AIModelInfo("Test", "Test"), usage=AIUsage(20, 10, 30))
    )


@pytest.mark.asyncio
async def test_full_success(ai_service, mock_video_pipeline, mock_vision_service, mock_caption_service):
    context = create_context()
    
    mock_video_pipeline.run.return_value = create_video_analysis_result(2)
    mock_vision_service.process.return_value = create_vision_result()
    mock_caption_service.process.return_value = create_caption_result()
    
    result = await ai_service.process(context)
    
    assert result.status == PipelineStatus.SUCCESS
    assert result.statistics.total_scenes == 2
    assert result.statistics.successful_scenes == 2
    assert result.statistics.failed_scenes == 0
    assert len(result.scene_results) == 2
    
    # Token usage aggregation check
    # Vision: 10 + 5 = 15. Caption: 20 + 10 = 30. Total per scene = 45. For 2 scenes = 90.
    assert result.usage.total_tokens == 90


@pytest.mark.asyncio
async def test_single_scene_failure_partial_success(ai_service, mock_video_pipeline, mock_vision_service, mock_caption_service):
    context = create_context()
    
    mock_video_pipeline.run.return_value = create_video_analysis_result(2)
    
    # First vision succeeds, second fails
    mock_vision_service.process.side_effect = [create_vision_result(), Exception("Vision failed")]
    mock_caption_service.process.return_value = create_caption_result()
    
    result = await ai_service.process(context)
    
    assert result.status == PipelineStatus.PARTIAL_SUCCESS
    assert result.statistics.successful_scenes == 1
    assert result.statistics.failed_scenes == 1
    
    # Ordering preservation
    assert result.scene_results[0].is_success is True
    assert result.scene_results[1].is_success is False
    assert result.scene_results[1].error_message == "Vision failed"


@pytest.mark.asyncio
async def test_multiple_scene_failure(ai_service, mock_video_pipeline, mock_vision_service, mock_caption_service):
    context = create_context()
    
    mock_video_pipeline.run.return_value = create_video_analysis_result(2)
    
    # All captions fail
    mock_vision_service.process.return_value = create_vision_result()
    mock_caption_service.process.side_effect = Exception("Caption failed")
    
    result = await ai_service.process(context)
    
    assert result.status == PipelineStatus.FAILED
    assert result.statistics.successful_scenes == 0
    assert result.statistics.failed_scenes == 2
    assert "All scenes failed" in result.error_message


@pytest.mark.asyncio
async def test_empty_video(ai_service, mock_video_pipeline):
    context = create_context()
    
    mock_video_pipeline.run.return_value = create_video_analysis_result(0)
    
    result = await ai_service.process(context)
    
    assert result.status == PipelineStatus.SUCCESS
    assert result.statistics.total_scenes == 0


@pytest.mark.asyncio
async def test_video_pipeline_failure(ai_service, mock_video_pipeline):
    context = create_context()
    
    mock_video_pipeline.run.return_value = create_video_analysis_result(2, success=False)
    
    result = await ai_service.process(context)
    
    assert result.status == PipelineStatus.FAILED
    assert result.statistics.total_scenes == 0
    assert result.error_message == "Failed"
