"""
Storage Domain Models.
Value objects representing storage results and metadata.
"""
from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field


def _now_utc():
    return datetime.now(timezone.utc)


@dataclass
class StorageMetadata:
    """Metadata associated with a stored file."""
    content_type: str
    size_bytes: int
    created_at: datetime = field(default_factory=_now_utc)


@dataclass
class StorageInfo:
    """Represents logical file information agnostic to the underlying storage provider."""
    logical_path: str
    metadata: Optional[StorageMetadata] = None


@dataclass
class StorageResult:
    """Result object encapsulating the success or failure of a storage operation."""
    success: bool
    path: Optional[str] = None
    error: Optional[str] = None
