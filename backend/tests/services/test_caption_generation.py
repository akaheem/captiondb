import pytest
from unittest.mock import AsyncMock

from app.services.caption_generation import CaptionGenerationService
from app.services.prompt_builder import PromptBuilder
from app.domain.models.video import CaptionTone
from app.domain.models.vision import VisionAnalysisResult
from app.domain.models.caption import (
    CaptionGenerationResult,
    CaptionCandidate,
    CaptionStatistics,
    CaptionMetadata
)
from app.domain.models.ai import AIUsage, AIModelInfo
from app.core.exceptions import ValidationException


@pytest.fixture
def mock_generator():
    return AsyncMock()

@pytest.fixture
def prompt_builder():
    return PromptBuilder()

def create_valid_analysis() -> VisionAnalysisResult:
    return VisionAnalysisResult(
        scene_summary="A cat jumping over a fence.",
        objects=["cat", "fence"],
        activities=["jumping"],
        environment="backyard",
        mood="playful",
        dominant_colors=["green", "orange"],
        safety_flags=[]
    )

def create_valid_result(texts: list[str]) -> CaptionGenerationResult:
    candidates = []
    for text in texts:
        candidates.append(
            CaptionCandidate(
                text=text,
                tone=CaptionTone.HUMOROUS_NON_TECH,
                statistics=CaptionStatistics(word_count=len(text.split()), character_count=len(text))
            )
        )
    return CaptionGenerationResult(
        candidates=candidates,
        metadata=CaptionMetadata(
            model_info=AIModelInfo(provider_name="Test", model_name="Test"),
            usage=AIUsage()
        )
    )


@pytest.mark.asyncio
async def test_successful_generation(mock_generator, prompt_builder):
    service = CaptionGenerationService(mock_generator, prompt_builder)
    analysis = create_valid_analysis()
    
    mock_generator.generate.return_value = create_valid_result(["This cat is crazy!", "Parkour cat!"])
    
    result = await service.process(analysis, CaptionTone.HUMOROUS_NON_TECH)
    
    assert len(result.candidates) == 2
    assert result.candidates[0].text == "This cat is crazy!"
    mock_generator.generate.assert_called_once()


@pytest.mark.asyncio
async def test_invalid_tone(mock_generator, prompt_builder):
    service = CaptionGenerationService(mock_generator, prompt_builder)
    analysis = create_valid_analysis()
    
    with pytest.raises(ValidationException) as exc:
        await service.process(analysis, "not-a-tone")
    assert "Invalid target tone" in str(exc.value)


@pytest.mark.asyncio
async def test_empty_analysis(mock_generator, prompt_builder):
    service = CaptionGenerationService(mock_generator, prompt_builder)
    analysis = create_valid_analysis()
    analysis.scene_summary = "   "
    
    with pytest.raises(ValidationException) as exc:
        await service.process(analysis, CaptionTone.FORMAL)
    assert "scene summary is empty" in str(exc.value)
    
    analysis = create_valid_analysis()
    analysis.objects = []
    with pytest.raises(ValidationException) as exc:
        await service.process(analysis, CaptionTone.FORMAL)
    assert "no objects detected" in str(exc.value)


@pytest.mark.asyncio
async def test_duplicate_caption_filtering(mock_generator, prompt_builder):
    service = CaptionGenerationService(mock_generator, prompt_builder)
    analysis = create_valid_analysis()
    
    # Provider returns identical captions
    mock_generator.generate.return_value = create_valid_result(["Wow!", "Wow!"])
    
    with pytest.raises(ValidationException) as exc:
        await service.process(analysis, CaptionTone.FORMAL)
    assert "duplicate captions" in str(exc.value)


@pytest.mark.asyncio
async def test_empty_caption_validation(mock_generator, prompt_builder):
    service = CaptionGenerationService(mock_generator, prompt_builder)
    analysis = create_valid_analysis()
    
    mock_generator.generate.return_value = create_valid_result(["   "])
    
    with pytest.raises(ValidationException) as exc:
        await service.process(analysis, CaptionTone.FORMAL)
    assert "empty caption" in str(exc.value)


@pytest.mark.asyncio
async def test_provider_failure(mock_generator, prompt_builder):
    service = CaptionGenerationService(mock_generator, prompt_builder)
    analysis = create_valid_analysis()
    
    mock_generator.generate.side_effect = Exception("API Timeout")
    
    with pytest.raises(Exception) as exc:
        await service.process(analysis, CaptionTone.FORMAL)
    assert "API Timeout" in str(exc.value)
