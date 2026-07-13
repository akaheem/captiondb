import pytest
from unittest.mock import AsyncMock

from app.services.vision import VisionAnalysisService
from app.services.prompt_builder import PromptBuilder
from app.domain.models.analysis import VisionInputPackage
from app.domain.models.video import Scene, VideoMetadata, CaptionTone
from app.domain.models.ai import AIImageContent, AIModelInfo, AIUsage
from app.domain.models.vision import VisionAnalysisResult, VisionAnalysisMetadata
from app.core.exceptions import ValidationException, VisionAnalysisException


@pytest.fixture
def mock_analyzer():
    analyzer = AsyncMock()
    return analyzer


def create_package(num_frames=2):
    return VisionInputPackage(
        video_id="vid-1",
        scene=Scene(seconds_start=0.0, seconds_end=5.0, scene_id="scene-1"),
        video_context=VideoMetadata(0, 0, 0, "", ""),
        target_tone=CaptionTone.SARCASTIC,
        key_frames=[AIImageContent(data_uri=f"img{i}") for i in range(num_frames)]
    )


@pytest.mark.asyncio
async def test_analysis_success(mock_analyzer):
    prompt_builder = PromptBuilder()
    service = VisionAnalysisService(mock_analyzer, prompt_builder)
    package = create_package()
    
    mock_result = VisionAnalysisResult(
        scene_summary="A person laughing",
        objects=["person", "chair"],
        metadata=VisionAnalysisMetadata(
            model_info=AIModelInfo(provider_name="Test", model_name="TestVision"),
            usage=AIUsage()
        )
    )
    mock_analyzer.analyze.return_value = mock_result
    
    result = await service.process(package)
    
    # Assert successful orchestration
    assert result.scene_summary == "A person laughing"
    assert "person" in result.objects
    mock_analyzer.analyze.assert_called_once()
    
    # Verify the request was properly wrapped
    request = mock_analyzer.analyze.call_args[0][0]
    assert request.package == package
    assert request.max_tokens == 1500
    assert request.temperature == 0.2


@pytest.mark.asyncio
async def test_empty_package(mock_analyzer):
    prompt_builder = PromptBuilder()
    service = VisionAnalysisService(mock_analyzer, prompt_builder)
    package = create_package(num_frames=0)
    
    with pytest.raises(ValidationException) as exc:
        await service.process(package)
    assert "No keyframes present" in str(exc.value)


@pytest.mark.asyncio
async def test_provider_failure(mock_analyzer):
    prompt_builder = PromptBuilder()
    service = VisionAnalysisService(mock_analyzer, prompt_builder)
    package = create_package()
    
    # Simulate API timeout or parsing error
    mock_analyzer.analyze.side_effect = Exception("Fireworks HTTP 500")
    
    with pytest.raises(VisionAnalysisException) as exc:
        await service.process(package)
    assert "Fireworks HTTP 500" in str(exc.value)
