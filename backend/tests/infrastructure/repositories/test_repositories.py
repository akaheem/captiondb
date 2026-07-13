import pytest
from app.infrastructure.database.uow.unit_of_work import SQLAlchemyUnitOfWork
from app.domain.models.video import Video, Scene, CaptionTone

@pytest.mark.asyncio
async def test_video_repository_add_and_get(async_session_factory):
    """Verifies that the video repository saves and retrieves aggregates natively."""
    uow = SQLAlchemyUnitOfWork(async_session_factory)
    
    # Create the aggregate
    video = Video(
        project_name="Repo Test",
        original_filename="repo.mp4",
        logical_path="/repo.mp4"
    )
    video.scenes.append(
        Scene(
            seconds_start=0.0,
            seconds_end=1.0,
            title="S1",
            captions={CaptionTone.FORMAL: "Testing formal captions."}
        )
    )
    
    # Save the aggregate
    async with uow:
        await uow.videos.add(video)
        await uow.commit()
        
    # Read the aggregate
    async with uow:
        loaded = await uow.videos.get_by_id(video.id)
        assert loaded is not None
        assert loaded.project_name == "Repo Test"
        assert len(loaded.scenes) == 1
        assert loaded.scenes[0].title == "S1"
        assert loaded.scenes[0].captions[CaptionTone.FORMAL] == "Testing formal captions."

@pytest.mark.asyncio
async def test_video_repository_update_cascade(async_session_factory):
    """Verifies update merges changes down to children."""
    uow = SQLAlchemyUnitOfWork(async_session_factory)
    
    video = Video(
        project_name="Update Test",
        original_filename="upd.mp4",
        logical_path="/upd.mp4"
    )
    
    async with uow:
        await uow.videos.add(video)
        await uow.commit()
        
    # Modify aggregate in memory
    video.project_name = "Update Mutated"
    video.scenes.append(
        Scene(seconds_start=1.0, seconds_end=2.0, title="New Scene")
    )
    
    # Save aggregate
    async with uow:
        await uow.videos.update(video)
        await uow.commit()
        
    # Verify aggregate
    async with uow:
        loaded = await uow.videos.get_by_id(video.id)
        assert loaded.project_name == "Update Mutated"
        assert len(loaded.scenes) == 1
        assert loaded.scenes[0].title == "New Scene"

@pytest.mark.asyncio
async def test_video_repository_delete_cascade(async_session_factory):
    """Verifies deleting the aggregate deletes the scenes and captions."""
    uow = SQLAlchemyUnitOfWork(async_session_factory)
    
    video = Video(
        project_name="Delete Test",
        original_filename="del.mp4",
        logical_path="/del.mp4"
    )
    scene = Scene(seconds_start=1.0, seconds_end=2.0)
    video.scenes.append(scene)
    
    async with uow:
        await uow.videos.add(video)
        await uow.commit()
        
    async with uow:
        # Check it exists
        assert await uow.videos.exists(video.id) is True
        # Check scene exists via specialized repository
        scenes = await uow.scenes.get_by_video(video.id)
        assert len(scenes) == 1
        
        # Delete video
        await uow.videos.delete(video.id)
        await uow.commit()
        
    async with uow:
        # Verify video gone
        assert await uow.videos.exists(video.id) is False
        # Verify scene gone (cascaded by ORM)
        scenes = await uow.scenes.get_by_video(video.id)
        assert len(scenes) == 0
