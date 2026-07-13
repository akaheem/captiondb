import pytest
from unittest.mock import MagicMock, AsyncMock

from app.services.vision_preparation import VisionInputPreparationService
from app.domain.models.video import Video, Scene, VideoMetadata, CaptionTone
from app.domain.models.analysis import ProcessingContext
from app.domain.models.ai import AIImageContent
from app.core.exceptions import ValidationException, ImagePreparationException


@pytest.fixture
def mock_preprocessor():
    preprocessor = AsyncMock()
    # By default, pass the frames back as if they were processed
    async def side_effect(frames):
        return [AIImageContent(data_uri=f"{f.data_uri}_processed") for f in frames]
    preprocessor.preprocess_images.side_effect = side_effect
    return preprocessor


def create_context(scenes_list, extracted_frames_map, tone=None):
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
        scenes=scenes_list
    )
    context = ProcessingContext(video=video, current_stage_name="KeyframeSelection")
    context.extracted_frames = extracted_frames_map
    if tone:
        context.runtime_metadata["target_tone"] = tone.value
    return context


@pytest.mark.asyncio
async def test_normal_preparation(mock_preprocessor):
    scene1 = Scene(seconds_start=0.0, seconds_end=10.0, scene_id="scene-1")
    scene2 = Scene(seconds_start=10.0, seconds_end=20.0, scene_id="scene-2")
    
    frames_map = {
        "scene-1": [AIImageContent(data_uri="img1"), AIImageContent(data_uri="img2")],
        "scene-2": [AIImageContent(data_uri="img3")]
    }
    
    context = create_context([scene1, scene2], frames_map, tone=CaptionTone.SARCASTIC)
    
    service = VisionInputPreparationService(mock_preprocessor)
    packages = await service.process(context)
    
    assert len(packages) == 2
    assert packages[0].scene.scene_id == "scene-1"
    assert len(packages[0].key_frames) == 2
    assert packages[0].key_frames[0].data_uri == "img1_processed"
    assert packages[0].target_tone == CaptionTone.SARCASTIC
    assert context.current_stage_name == "VisionInputPreparation"


@pytest.mark.asyncio
async def test_no_scenes_validation(mock_preprocessor):
    context = create_context([], {"foo": []})
    service = VisionInputPreparationService(mock_preprocessor)
    
    with pytest.raises(ValidationException) as exc:
        await service.process(context)
    assert "No scenes exist" in str(exc.value)


@pytest.mark.asyncio
async def test_no_keyframes_validation(mock_preprocessor):
    scene1 = Scene(seconds_start=0.0, seconds_end=10.0, scene_id="scene-1")
    context = create_context([scene1], {}) # Empty dictionary
    service = VisionInputPreparationService(mock_preprocessor)
    
    with pytest.raises(ValidationException) as exc:
        await service.process(context)
    assert "No keyframes exist" in str(exc.value)


@pytest.mark.asyncio
async def test_skip_empty_scene_keyframes(mock_preprocessor):
    scene1 = Scene(seconds_start=0.0, seconds_end=10.0, scene_id="scene-1")
    scene2 = Scene(seconds_start=10.0, seconds_end=20.0, scene_id="scene-2")
    
    frames_map = {
        "scene-1": [], # Empty list for this scene
        "scene-2": [AIImageContent(data_uri="img3")]
    }
    
    context = create_context([scene1, scene2], frames_map)
    
    service = VisionInputPreparationService(mock_preprocessor)
    packages = await service.process(context)
    
    # Only scene-2 should result in a package
    assert len(packages) == 1
    assert packages[0].scene.scene_id == "scene-2"


@pytest.mark.asyncio
async def test_preprocessor_failure(mock_preprocessor):
    scene1 = Scene(seconds_start=0.0, seconds_end=10.0, scene_id="scene-1")
    frames_map = {"scene-1": [AIImageContent(data_uri="img1")]}
    context = create_context([scene1], frames_map)
    
    mock_preprocessor.preprocess_images.side_effect = Exception("OpenCV Error")
    
    service = VisionInputPreparationService(mock_preprocessor)
    
    with pytest.raises(ImagePreparationException) as exc:
        await service.process(context)
    assert "Failed to prepare images" in str(exc.value)
