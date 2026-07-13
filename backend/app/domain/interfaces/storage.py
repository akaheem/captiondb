"""
Abstract Storage and File Management Interfaces.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class StorageProvider(ABC):
    """
    Abstract interface for persisting and retrieving blob data.
    
    Purpose: Decouples business logic from specific storage mechanisms (Local disk, AWS S3, etc.).
    Responsibilities: Save, read, and delete unstructured data (images, videos, JSON exports).
    Expected Inputs: Logical file paths and byte data.
    Expected Outputs: URIs or byte content on retrieval.
    Failure Behavior: Must raise specific domain StorageExceptions (e.g., FileNotFound) instead of generic OS errors.
    Extension Points: Implementations can be S3StorageAdapter, LocalStorageAdapter, or GCSStorageAdapter.
    """

    @abstractmethod
    async def save(self, path: str, content: bytes) -> str:
        """Saves content to the given path and returns the resolved URI."""
        pass

    @abstractmethod
    async def save_stream(self, path: str, stream: AsyncIterator[bytes]) -> str:
        """Saves streamed chunk content to the given path to avoid OOM."""
        pass

    @abstractmethod
    async def read(self, path: str) -> bytes:
        """Reads the entire content of a file into memory."""
        pass

    @abstractmethod
    async def stream(self, path: str, chunk_size: int = 1024 * 1024) -> AsyncIterator[bytes]:
        """Reads a file in chunks, crucial for large video processing without OOM."""
        pass
        
    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Deletes the resource at the specified path."""
        pass


class FileManager(ABC):
    """
    Abstract interface for managing temporary local file operations.
    
    Purpose: Some tools (like FFmpeg) explicitly require local file paths rather than byte streams.
    Responsibilities: Managing temporary directories and files safely.
    Expected Inputs: Prefixes and byte data.
    Expected Outputs: Absolute temporary file paths on disk.
    Failure Behavior: Gracefully handles disk full scenarios or permission errors.
    Extension Points: Can be implemented using Python's tempfile module securely.
    """
    
    @abstractmethod
    async def create_temp_dir(self, prefix: str = "captiondb_") -> str:
        """Creates a temporary directory and returns its absolute path."""
        pass

    @abstractmethod
    async def save_temp_file(self, content: bytes, suffix: str = ".tmp") -> str:
        """Saves temporary bytes to disk and returns the absolute path."""
        pass

    @abstractmethod
    async def cleanup(self, path: str) -> bool:
        """Safely removes a temporary file or directory."""
        pass
