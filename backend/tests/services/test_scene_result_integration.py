import pytest
from typing import List

from app.services.scene_result_integration import SceneResultIntegrationService
from app.domain.models.integration import IntegrationStatus
from app.domain.models.pipeline import VideoPipelineResult, ScenePipelineResult, PipelineStatus
from app.domain.models.analysis import ProcessingContext
from app.domain.models.video import Video, Scene, CaptionTone
from app.domain.models.vision import VisionAnalysisResult
from app.domain.models.caption import CaptionGenerationResult, CaptionCandidate, CaptionStatistics, CaptionMetadata
from app.domain.models.ai import AIUsage, AIModelInfo


@pytest.fixture
def integration_service():
    return SceneResultIntegrationService()


def create_mock_video(scene_count: int = 2) -> Video:
    video = Video(project_name="Test", original_filename="test.mp4", logical_path="/test")
    for i in range(scene_count):
        video.scenes.append(Scene(seconds_start=0.0, seconds_end=1.0, scene_id=f"scene_{i}"))
    return video


def create_pipeline_result(video_id: str, scene_count: int = 2) -> VideoPipelineResult:
    result = VideoPipelineResult(video_id=video_id, status=PipelineStatus.SUCCESS)
    for i in range(scene_count):
        
        vision = VisionAnalysisResult(
            scene_summary=f"Summary {i}",
            objects=["cat"],
            activities=["jumping"],
            environment="indoor",
            mood="happy",
            dominant_colors=["red"],
            safety_flags=[],
            ocr_text="Meow"
        )
        vision.metadata = type("Metadata", (), {"usage": AIUsage(100, 50, 150)})()
        
        caption = CaptionGenerationResult(
            candidates=[CaptionCandidate(text=f"Caption {i}", tone=CaptionTone.HUMOROUS_NON_TECH, statistics=CaptionStatistics(2, 10))],
            metadata=CaptionMetadata(model_info=AIModelInfo("Test", "Test"), usage=AIUsage(50, 20, 70))
        )
        
        scene_result = ScenePipelineResult(
            scene_id=f"scene_{i}",
            target_tone=CaptionTone.HUMOROUS_NON_TECH,
            is_success=True,
            vision_result=vision,
            caption_result=caption,
            processing_time_seconds=2.0
        )
        result.scene_results.append(scene_result)
        
    return result


def test_complete_integration(integration_service):
    video = create_mock_video()
    context = ProcessingContext(video=video, target_tone=CaptionTone.HUMOROUS_NON_TECH)
    pipeline_result = create_pipeline_result(video.id)
    
    result = integration_service.process(context, pipeline_result)
    
    assert result.status == IntegrationStatus.SUCCESS
    assert result.statistics.total_scenes == 2
    assert result.statistics.successful_scenes == 2
    assert result.statistics.failed_scenes == 0
    assert result.statistics.average_scene_latency_seconds == 2.0
    
    # 100+50 (vision) + 50+20 (caption) = 220 total usage tokens per scene. x2 = 440
    # Wait, the stats tracks total_prompt and total_completion.
    # Prompts: (100 + 50) * 2 = 300
    # Completions: (50 + 20) * 2 = 140
    assert result.statistics.total_prompt_tokens == 300
    assert result.statistics.total_completion_tokens == 140
    
    # Check enriched video
    assert len(result.enriched_video.scenes) == 2
    assert result.enriched_video.scenes[0].summary == "Summary 0"
    assert result.enriched_video.scenes[0].objects == ["cat"]
    assert result.enriched_video.scenes[0].ocr_text == "Meow"
    assert result.enriched_video.scenes[0].captions[CaptionTone.HUMOROUS_NON_TECH] == "Caption 0"
    assert result.enriched_video.scenes[0].ai_metadata["integrated"] is True


def test_partial_integration(integration_service):
    video = create_mock_video(3)
    context = ProcessingContext(video=video, target_tone=CaptionTone.HUMOROUS_NON_TECH)
    pipeline_result = create_pipeline_result(video.id, 3)
    
    # Fail scene 1
    pipeline_result.scene_results[1].is_success = False
    pipeline_result.scene_results[1].error_message = "Pipeline failed it."
    
    result = integration_service.process(context, pipeline_result)
    
    assert result.status == IntegrationStatus.PARTIAL_SUCCESS
    assert result.statistics.successful_scenes == 2
    assert result.statistics.failed_scenes == 1
    
    # Scene 0 is successful
    assert result.enriched_video.scenes[0].summary == "Summary 0"
    # Scene 1 is untouched
    assert result.enriched_video.scenes[1].summary is None
    assert CaptionTone.HUMOROUS_NON_TECH not in result.enriched_video.scenes[1].captions
    # Scene 2 is successful
    assert result.enriched_video.scenes[2].summary == "Summary 2"


def test_empty_pipeline_results(integration_service):
    video = create_mock_video(0)
    context = ProcessingContext(video=video, target_tone=CaptionTone.HUMOROUS_NON_TECH)
    pipeline_result = VideoPipelineResult(video_id=video.id, status=PipelineStatus.SUCCESS)
    
    result = integration_service.process(context, pipeline_result)
    
    assert result.status == IntegrationStatus.SUCCESS
    assert result.statistics.total_scenes == 0


def test_unknown_scene_id(integration_service):
    video = create_mock_video(1)
    context = ProcessingContext(video=video, target_tone=CaptionTone.HUMOROUS_NON_TECH)
    pipeline_result = create_pipeline_result(video.id, 1)
    
    # Tamper the scene ID
    pipeline_result.scene_results[0].scene_id = "unknown_scene_999"
    
    result = integration_service.process(context, pipeline_result)
    
    assert result.status == IntegrationStatus.FAILED
    assert result.statistics.failed_scenes == 1
    assert result.scene_results[0].is_success is False
    assert "not found in original video" in result.scene_results[0].error_message
