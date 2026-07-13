"""
Storage Service.
Application service coordinating operations through the abstract StorageProvider.
"""
import re
from typing import AsyncIterator
from loguru import logger

from app.domain.interfaces.storage import StorageProvider
from app.domain.models.storage import StorageResult
from app.core.exceptions import ValidationException, StorageException


class StorageService:
    """
    Coordinates file persistence, retrieval, and validation.
    Strictly depends on the abstract StorageProvider, ensuring decoupling from LocalStorage/S3.
    """
    
    def __init__(self, provider: StorageProvider):
        """
        Injected constructor. 
        The specific provider (e.g., LocalStorageAdapter) is supplied by the Dependency Injection layer.
        """
        self._provider = provider

    def _validate_logical_path(self, path: str) -> None:
        """
        Validates that a path string is safe before passing it to infrastructure.
        This provides a domain-level defense-in-depth layer against path traversal.
        """
        if not path or not path.strip():
            raise ValidationException("Logical path cannot be empty.")
            
        if ".." in path or path.startswith("/"):
            raise ValidationException("Invalid path: Absolute paths and directory traversal are strictly forbidden.")
            
        # Enforce safe character sets (alphanumeric, underscores, hyphens, periods, and forward slashes)
        if not re.match(r'^[\w\-\./]+$', path):
            raise ValidationException("Invalid path: Contains unsupported characters.")

    async def save_file(self, logical_path: str, content: bytes) -> StorageResult:
        """
        Safely saves file content via the underlying provider.
        Catches domain exceptions to return a standardized StorageResult value object.
        """
        try:
            self._validate_logical_path(logical_path)
            saved_path = await self._provider.save(logical_path, content)
            logger.info(f"Successfully stored file at {saved_path}")
            return StorageResult(success=True, path=saved_path)
            
        except (ValidationException, StorageException) as e:
            logger.warning(f"Storage operation failed: {e.message}")
            return StorageResult(success=False, error=e.message)
            
        except Exception as e:
            logger.error(f"Unexpected error during storage save: {str(e)}")
            return StorageResult(success=False, error="An unexpected internal error occurred.")

    async def save_file_stream(self, logical_path: str, stream: AsyncIterator[bytes]) -> StorageResult:
        """
        Safely saves a stream via the underlying provider to prevent memory exhaustion.
        """
        try:
            self._validate_logical_path(logical_path)
            saved_path = await self._provider.save_stream(logical_path, stream)
            logger.info(f"Successfully stored stream at {saved_path}")
            return StorageResult(success=True, path=saved_path)
            
        except (ValidationException, StorageException) as e:
            logger.warning(f"Storage stream operation failed: {e.message}")
            return StorageResult(success=False, error=e.message)
            
        except Exception as e:
            logger.error(f"Unexpected error during storage stream save: {str(e)}")
            return StorageResult(success=False, error="An unexpected internal error occurred.")

    async def read_file(self, logical_path: str) -> bytes:
        """
        Reads a file entirely into memory.
        Raises Domain Exceptions if the file is invalid or unavailable.
        """
        self._validate_logical_path(logical_path)
        return await self._provider.read(logical_path)

    async def stream_file(self, logical_path: str, chunk_size: int = 1024 * 1024) -> AsyncIterator[bytes]:
        """
        Streams a file in chunks to prevent memory exhaustion on large video assets.
        """
        self._validate_logical_path(logical_path)
        async for chunk in self._provider.stream(logical_path, chunk_size):
            yield chunk

    async def delete_file(self, logical_path: str) -> bool:
        """
        Deletes a file via the underlying provider.
        """
        self._validate_logical_path(logical_path)
        return await self._provider.delete(logical_path)
