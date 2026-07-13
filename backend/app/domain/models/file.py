"""
File Management Domain Models.
Value objects representing managed files and file lifecycle operations.
"""
from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field


def _now_utc():
    return datetime.now(timezone.utc)


@dataclass
class FileInfo:
    """Core metadata for a logical file."""
    logical_path: str
    size_bytes: Optional[int] = None
    created_at: datetime = field(default_factory=_now_utc)


@dataclass
class ManagedFile:
    """
    A file tracked by the application lifecycle.
    Differentiates between permanent assets and temporary processing artifacts.
    """
    file_id: str
    info: FileInfo
    is_temporary: bool = False


@dataclass
class FileOperationResult:
    """Result object encapsulating success/failure of a file management operation."""
    success: bool
    file: Optional[ManagedFile] = None
    error: Optional[str] = None
