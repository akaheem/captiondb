import pytest
from app.infrastructure.database.uow.unit_of_work import SQLAlchemyUnitOfWork
from app.domain.models.video import Video

@pytest.mark.asyncio
async def test_uow_commit_and_rollback(async_session_factory):
    """Verifies that the UoW commits correctly and rolls back on exception."""
    uow = SQLAlchemyUnitOfWork(async_session_factory)
    
    video = Video(
        project_name="Test UoW",
        original_filename="uow.mp4",
        logical_path="/storage/uow.mp4"
    )
    
    # Test successful commit
    async with uow:
        await uow.videos.add(video)
        await uow.commit()
        
    # Verify it was persisted
    async with uow:
        persisted = await uow.videos.get_by_id(video.id)
        assert persisted is not None
        assert persisted.project_name == "Test UoW"

    # Test automatic rollback
    try:
        async with uow:
            persisted.project_name = "Should Rollback"
            await uow.videos.update(persisted)
            raise ValueError("Intentional crash")
    except ValueError:
        pass
        
    # Verify rollback occurred
    async with uow:
        re_persisted = await uow.videos.get_by_id(video.id)
        assert re_persisted.project_name == "Test UoW"  # Did not update

@pytest.mark.asyncio
async def test_uow_repository_sharing(async_session_factory):
    """Verifies all repositories share the same session under the UoW."""
    uow = SQLAlchemyUnitOfWork(async_session_factory)
    async with uow:
        assert uow.videos._session is uow.scenes._session
        assert uow.videos._session is uow.captions._session
