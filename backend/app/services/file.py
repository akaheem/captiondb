"""
File Management Service.
Coordinates file lifecycle operations at a higher abstraction than raw storage.
"""
import uuid
from typing import Optional, AsyncIterator
from loguru import logger

from app.core.config import Settings
from app.services.storage import StorageService
from app.domain.models.file import ManagedFile, FileInfo, FileOperationResult


class FileManagementService:
    """
    Orchestrates the lifecycle of files within the system.
    Depends exclusively on StorageService and Configuration, remaining completely
    decoupled from raw infrastructure (LocalStorage/S3).
    """
    
    def __init__(self, storage_service: StorageService, settings: Settings):
        """
        Injected constructor.
        """
        self._storage = storage_service
        self._settings = settings

    async def create_logical_file(
        self, content: bytes, prefix: str = "assets", extension: str = "bin", is_temporary: bool = False
    ) -> FileOperationResult:
        """
        Creates a new logical file, generating a unique ID and storing it securely.
        """
        try:
            # Generate a secure, unique identifier for the asset
            file_id = str(uuid.uuid4())
            logical_path = f"{prefix}/{file_id}.{extension}"
            
            # Delegate raw persistence to the StorageService
            result = await self._storage.save_file(logical_path, content)
            
            if not result.success:
                return FileOperationResult(success=False, error=result.error)
                
            info = FileInfo(logical_path=logical_path, size_bytes=len(content))
            managed_file = ManagedFile(file_id=file_id, info=info, is_temporary=is_temporary)
            
            if is_temporary:
                await self.track_temporary_file(logical_path)
            
            logger.info(f"File lifecycle started for {file_id} at {logical_path}")
            return FileOperationResult(success=True, file=managed_file)
            
        except Exception as e:
            logger.error(f"Failed to coordinate logical file creation: {str(e)}")
            return FileOperationResult(success=False, error="File creation lifecycle failed.")

    async def create_logical_file_from_stream(
        self, stream: AsyncIterator[bytes], prefix: str = "assets", extension: str = "bin", is_temporary: bool = False
    ) -> FileOperationResult:
        """
        Creates a new logical file from an asynchronous stream to avoid loading large files into memory.
        """
        try:
            file_id = str(uuid.uuid4())
            logical_path = f"{prefix}/{file_id}.{extension}"
            
            result = await self._storage.save_file_stream(logical_path, stream)
            
            if not result.success:
                return FileOperationResult(success=False, error=result.error)
                
            # For streamed files, we might not know the exact size upfront without tracking it during stream.
            # We assign 0 here, but in future iterations StorageService could return bytes_written.
            info = FileInfo(logical_path=logical_path, size_bytes=0)
            managed_file = ManagedFile(file_id=file_id, info=info, is_temporary=is_temporary)
            
            if is_temporary:
                await self.track_temporary_file(logical_path)
            
            logger.info(f"Streamed file lifecycle started for {file_id} at {logical_path}")
            return FileOperationResult(success=True, file=managed_file)
            
        except Exception as e:
            logger.error(f"Failed to coordinate streamed logical file creation: {str(e)}")
            return FileOperationResult(success=False, error="File stream creation lifecycle failed.")

    async def lookup_file(self, logical_path: str) -> FileOperationResult:
        """
        Looks up a file by its logical path and verifies its availability.
        """
        try:
            # For now, verify existence by attempting a read. 
            # In future phases, this will query the database metadata tables.
            content = await self._storage.read_file(logical_path)
            
            info = FileInfo(logical_path=logical_path, size_bytes=len(content))
            # file_id will be properly populated from the DB in Phase 3
            managed_file = ManagedFile(file_id="retrieved", info=info)
            
            return FileOperationResult(success=True, file=managed_file)
        except Exception as e:
            logger.warning(f"File lookup failed for {logical_path}: {str(e)}")
            return FileOperationResult(success=False, error="File not found or unreadable.")

    async def delete_logical_file(self, logical_path: str) -> bool:
        """
        Removes a file from storage and ends its lifecycle.
        """
        success = await self._storage.delete_file(logical_path)
        if success:
            logger.info(f"File lifecycle ended for {logical_path}")
        return success
        
    async def track_temporary_file(self, logical_path: str) -> None:
        """
        Registers a file as temporary.
        Future phases will insert this into a cleanup queue (e.g., Celery or Redis TTL).
        """
        logger.debug(f"Tracking {logical_path} as temporary. Pending future cleanup implementation.")
