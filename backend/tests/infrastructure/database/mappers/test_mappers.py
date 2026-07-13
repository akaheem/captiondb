import uuid
from datetime import datetime, timezone
import pytest

from app.domain.models.video import (
    Video, Scene, CaptionTone, VideoMetadata, VideoDimensions, 
    ProcessingState, VideoStatus, VideoFormat
)
from app.infrastructure.database.mappers.video_mapper import VideoMapper
from app.infrastructure.database.models.video import VideoORM


def test_mapper_roundtrip():
    """Verify Domain -> ORM -> Domain produces an equivalent object."""
    # Build complete domain model
    original = Video(
        project_name="Test Project",
        original_filename="test.mp4",
        logical_path="/storage/test.mp4",
        thumbnail_path="/storage/thumb.jpg",
        created_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        metadata=VideoMetadata(
            size_bytes=1024,
            duration_seconds=10.0,
            fps=30.0,
            codec="h264",
            resolution="1080p",
            dimensions=VideoDimensions(1920, 1080),
            format=VideoFormat.MP4
        ),
        state=ProcessingState(
            status=VideoStatus.COMPLETED,
            progress_percent=100.0,
            current_stage="Done",
            started_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
            completed_at=datetime(2023, 1, 1, tzinfo=timezone.utc)
        ),
        scenes=[
            Scene(
                seconds_start=0.0,
                seconds_end=5.0,
                title="Intro",
                transcript="Hello world",
                tags=["intro", "greeting"],
                captions={
                    CaptionTone.FORMAL: "Greetings to the world.",
                    CaptionTone.SARCASTIC: "Oh, hello world, like we haven't seen you before."
                },
                summary="A guy says hello",
                objects=["person", "camera"],
                activities=["talking"],
                colors=["blue", "green"],
                ocr_text="HELLO",
                ai_metadata={"confidence": 0.99}
            )
        ]
    )

    # To ORM
    orm_video = VideoMapper.to_orm(original)
    
    # Basic ORM checks
    assert orm_video.project_name == "Test Project"
    assert orm_video.state_status == "Completed"
    assert orm_video.metadata_payload["format"] == "mp4"
    assert len(orm_video.scenes) == 1
    assert len(orm_video.scenes[0].captions) == 2
    
    # Back to Domain
    restored = VideoMapper.to_domain(orm_video)

    # Verify equivalence
    assert restored.id == original.id
    assert restored.project_name == original.project_name
    assert restored.state.status == original.state.status
    assert restored.metadata.dimensions.width == original.metadata.dimensions.width
    assert len(restored.scenes) == 1
    
    restored_scene = restored.scenes[0]
    original_scene = original.scenes[0]
    assert restored_scene.scene_id == original_scene.scene_id
    assert restored_scene.tags == original_scene.tags
    assert restored_scene.captions[CaptionTone.FORMAL] == original_scene.captions[CaptionTone.FORMAL]
    assert restored_scene.ai_metadata == original_scene.ai_metadata

def test_mapper_empty_collections():
    """Verify mapper safely handles empty scenes, captions, and tags."""
    original = Video(
        project_name="Empty Project",
        original_filename="empty.mp4",
        logical_path="/storage/empty.mp4"
    )
    
    orm = VideoMapper.to_orm(original)
    restored = VideoMapper.to_domain(orm)
    
    assert restored.scenes == []
    assert restored.metadata is None
    assert restored.state.status == VideoStatus.IDLE

def test_caption_enum_fallback():
    """Verify unknown caption tones don't crash the mapper."""
    from app.infrastructure.database.models.caption import CaptionORM
    
    # Fake an ORM list with a bad tone string
    orm_captions = [
        CaptionORM(id=uuid.uuid4(), scene_id=uuid.uuid4(), tone="formal", text="Good"),
        CaptionORM(id=uuid.uuid4(), scene_id=uuid.uuid4(), tone="made_up_tone", text="Bad")
    ]
    
    from app.infrastructure.database.mappers.caption_mapper import CaptionMapper
    domain_dict = CaptionMapper.to_domain(orm_captions)
    
    # Only "formal" should survive
    assert CaptionTone.FORMAL in domain_dict
    assert len(domain_dict) == 1
