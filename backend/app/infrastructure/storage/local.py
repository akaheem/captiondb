"""
Local Filesystem Storage Adapter.
Implements StorageProvider using the local filesystem.
"""
import asyncio
from pathlib import Path
from typing import AsyncIterator

from app.domain.interfaces.storage import StorageProvider
from app.core.exceptions import StorageException


class LocalStorageAdapter(StorageProvider):
    """
    Adapter for storing and retrieving files on the local filesystem.
    Ensures strict path traversal validation and avoids exposing absolute system paths.
    """
    
    def __init__(self, base_path: str):
        """
        Initializes the adapter with a configurable storage root.
        Does not rely on global settings.
        
        Args:
            base_path (str): The root directory where files will be stored.
        """
        self._base_path = Path(base_path).resolve()
        
        try:
            self._base_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            raise StorageException("Failed to initialize storage root.")

    def _resolve_and_validate_path(self, path: str) -> Path:
        """
        Safely resolves a logical path against the storage root.
        
        Raises:
            StorageException: If the path attempts to traverse outside the base path
                              or if an absolute path is provided.
        """
        requested_path = Path(path)
        
        if requested_path.is_absolute():
            raise StorageException("Absolute paths are not allowed. Provide a logical path.")
            
        target_path = (self._base_path / requested_path).resolve()
        
        try:
            # Ensures target_path is strictly within _base_path
            target_path.relative_to(self._base_path)
        except ValueError:
            raise StorageException("Path traversal attempt detected. Access denied.")
            
        return target_path

    async def save(self, path: str, content: bytes) -> str:
        """
        Saves byte content to the specified logical path.
        Automatically creates parent directories if they do not exist.
        """
        target_path = self._resolve_and_validate_path(path)
        
        def _write() -> None:
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(content)
            except Exception:
                # Catching OS errors to prevent leaking internal paths
                raise StorageException("Failed to write file to disk.")
                
        await asyncio.to_thread(_write)
        return path

    async def save_stream(self, path: str, stream: AsyncIterator[bytes]) -> str:
        """
        Saves streamed content to the specified logical path to avoid OOM.
        """
        target_path = self._resolve_and_validate_path(path)
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # We open the file and write chunks sequentially
            f = await asyncio.to_thread(target_path.open, 'wb')
            try:
                async for chunk in stream:
                    await asyncio.to_thread(f.write, chunk)
            finally:
                await asyncio.to_thread(f.close)
        except Exception:
            raise StorageException("Failed to stream file to disk.")
            
        return path

    async def read(self, path: str) -> bytes:
        """
        Reads the entire file into memory.
        """
        target_path = self._resolve_and_validate_path(path)
        
        if not target_path.exists():
            raise StorageException("File not found.")
            
        try:
            return await asyncio.to_thread(target_path.read_bytes)
        except Exception:
            raise StorageException("Failed to read file from disk.")

    async def stream(self, path: str, chunk_size: int = 1024 * 1024) -> AsyncIterator[bytes]:
        """
        Streams a file in chunks without loading it entirely into memory.
        Essential for reading large video files.
        """
        target_path = self._resolve_and_validate_path(path)
        
        if not target_path.exists():
            raise StorageException("File not found.")
            
        try:
            f = await asyncio.to_thread(target_path.open, 'rb')
            try:
                while True:
                    chunk = await asyncio.to_thread(f.read, chunk_size)
                    if not chunk:
                        break
                    yield chunk
            finally:
                await asyncio.to_thread(f.close)
        except Exception:
            raise StorageException("Failed to stream file.")

    async def delete(self, path: str) -> bool:
        """
        Deletes the specified file.
        Returns False if the file did not exist, True if successfully deleted.
        """
        target_path = self._resolve_and_validate_path(path)
        
        if not target_path.exists():
            return False
            
        try:
            await asyncio.to_thread(target_path.unlink)
            return True
        except Exception:
            raise StorageException("Failed to delete file.")
