import pytest
from app.services.prompt_builder import PromptBuilder
from app.domain.models.video import CaptionTone, Scene, VideoMetadata
from app.domain.models.analysis import VisionInputPackage
from app.domain.models.ai import AIImageContent, AIMessageRole, AITextContent


def create_package(tone: CaptionTone = CaptionTone.NONE, num_frames: int = 2) -> VisionInputPackage:
    return VisionInputPackage(
        video_id="vid1",
        scene=Scene(seconds_start=0.0, seconds_end=2.0, scene_id="scn1"),
        video_context=VideoMetadata(0, 0, 0, "", ""),
        target_tone=tone,
        key_frames=[AIImageContent(data_uri=f"img{i}") for i in range(num_frames)]
    )


def test_build_system_prompt_tones():
    builder = PromptBuilder()
    
    # Test that different tones inject different modifiers
    formal_prompt = builder.build_system_prompt(CaptionTone.FORMAL)
    sarcastic_prompt = builder.build_system_prompt(CaptionTone.SARCASTIC)
    
    assert "strict, objective" in formal_prompt
    assert "absurdities, contradictions" in sarcastic_prompt
    assert formal_prompt != sarcastic_prompt
    
    # Base prompt rules must still be present
    assert "Do NOT hallucinate" in formal_prompt
    assert "structured JSON" in sarcastic_prompt


def test_build_messages():
    builder = PromptBuilder()
    package = create_package(num_frames=3)
    
    messages = builder.build_messages(package)
    
    assert len(messages) == 2
    
    system_msg = messages[0]
    user_msg = messages[1]
    
    assert system_msg.role == AIMessageRole.SYSTEM
    assert user_msg.role == AIMessageRole.USER
    
    # User message should have 1 text block + 3 image blocks
    assert len(user_msg.content) == 4
    assert isinstance(user_msg.content[0], AITextContent)
    assert isinstance(user_msg.content[1], AIImageContent)
    assert isinstance(user_msg.content[2], AIImageContent)
    assert isinstance(user_msg.content[3], AIImageContent)
    
    assert user_msg.content[1].data_uri == "img0"
    assert user_msg.content[3].data_uri == "img2"


def test_build_scene_analysis_prompt():
    builder = PromptBuilder()
    package = create_package(num_frames=1)
    
    request = builder.build_scene_analysis_prompt(package)
    
    # Verify standard request configuration
    assert request.max_tokens == 1500
    assert request.temperature == 0.2
    assert len(request.messages) == 2
    
    # Verify structured output schema is attached
    assert request.response_format is not None
    assert request.response_format["type"] == "json_schema"
    
    schema = request.response_format["json_schema"]["schema"]
    assert "scene_summary" in schema["required"]
    assert "safety_flags" in schema["required"]
    assert schema["additionalProperties"] is False
