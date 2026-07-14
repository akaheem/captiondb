"""
Upload Service.
Orchestrates the logical flow of video ingestion.
Strictly decoupled from HTTP (FastAPI) and raw infrastructure (Filesystem/S3).
"""
import uuid
from typing import Any, Optional, AsyncIterator, List
from dataclasses import dataclass
from loguru import logger

from app.core.config import Settings
from app.domain.models.video import Video, VideoStatus, ProcessingState
from app.domain.services.validation import ValidationService
from app.services.file import FileManagementService
from app.services.storage import StorageService
from app.services.metadata import MetadataExtractionService
from app.domain.interfaces.unit_of_work import AbstractUnitOfWork


@dataclass
class UploadResult:
    """Value object encapsulating the result of an upload workflow."""
    success: bool
    video: Optional[Video] = None
    errors: Optional[List[str]] = None


class UploadService:
    """
    Coordinates the validation, logical registration, and persistence of an uploaded video.
    """
    
    def __init__(
        self,
        validation_service: ValidationService,
        file_management_service: FileManagementService,
        storage_service: StorageService,
        metadata_service: MetadataExtractionService,
        settings: Settings,
        unit_of_work: AbstractUnitOfWork
    ):
        """Injected dependencies."""
        self._validation = validation_service
        self._file_manager = file_management_service
        self._storage = storage_service
        self._metadata = metadata_service
        self._settings = settings
        self._uow = unit_of_work

    async def process_upload(
        self, 
        project_name: str, 
        original_filename: str, 
        content: bytes | AsyncIterator[bytes]
    ) -> UploadResult:
        """
        Executes the business rules for ingesting a new video asset.
        
        1. Generates a temporary logical path.
        2. Validates the incoming metadata using domain rules.
        3. Persists the bytes or stream via StorageService.
        4. Updates the logical path via FileManagementService tracking.
        5. Extracts intrinsic metadata (FFprobe) securely.
        6. Returns a unified Domain Entity representing the uploaded video.
        """
        # Step 1: Create a preliminary aggregate root with a logical ID
        video_id = str(uuid.uuid4())
        
        # We assign a preliminary logical path so validators (like PathValidator) can check it
        temp_logical_path = f"projects/{project_name}/uploads/{video_id}/{original_filename}"
        
        video = Video(
            id=video_id,
            project_name=project_name,
            original_filename=original_filename,
            logical_path=temp_logical_path,
            state=ProcessingState(status=VideoStatus.QUEUED)
        )
        
        # Step 2: Validate against business rules (PROJECT_SPEC.md FR-02)
        validation_result = self._validation.validate_video(video)
        if not validation_result.is_valid:
            logger.warning(f"Upload validation failed for {original_filename}: {validation_result.errors}")
            return UploadResult(success=False, errors=validation_result.errors)
            
        # Step 3 & 4: Persist the bytes logically, isolating infrastructure
        extension = original_filename.split('.')[-1] if '.' in original_filename else "bin"
        prefix = f"projects/{project_name}/uploads"
        
        if isinstance(content, bytes):
            file_result = await self._file_manager.create_logical_file(
                content=content, prefix=prefix, extension=extension, is_temporary=False
            )
        else:
            file_result = await self._file_manager.create_logical_file_from_stream(
                stream=content, prefix=prefix, extension=extension, is_temporary=False
            )
        
        if not file_result.success:
            logger.error(f"Storage operation failed for {original_filename}: {file_result.error}")
            return UploadResult(success=False, errors=["Storage operation failed due to an internal error."])
            
        # Update the Video entity with the confirmed, sanitized logical path
        video.logical_path = file_result.file.info.logical_path
        
        # Step 5: Extract intrinsic metadata via MetadataExtractionService
        # The extractor needs a host absolute path, so we resolve it safely through the storage service
        try:
            absolute_host_path = self._storage._provider._resolve_and_validate_path(video.logical_path)
            metadata = await self._metadata.get_metadata(str(absolute_host_path))
            if metadata:
                video.metadata = metadata
            else:
                return UploadResult(success=False, errors=["Failed to extract metadata from video."])
        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            return UploadResult(success=False, errors=["Failed to process video metadata."])
            
        logger.info(f"Video {video_id} successfully ingested and registered at {video.logical_path}")
        
        # Step 6: Persist the video aggregate using the Unit of Work
        try:
            async with self._uow:
                await self._uow.videos.add(video)
                await self._uow.commit()
            logger.info(f"Video {video_id} persisted to database successfully.")
        except Exception as e:
            logger.error(f"Failed to persist video {video_id} to database: {str(e)}")
            return UploadResult(success=False, errors=["Database persistence failed."])
        
        return UploadResult(success=True, video=video)
