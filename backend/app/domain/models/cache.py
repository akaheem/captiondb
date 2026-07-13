"""
Cache Domain Models.
Value objects representing provider-agnostic cache entries and results.
"""
from typing import Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field


def _now_utc():
    return datetime.now(timezone.utc)


@dataclass
class CacheMetadata:
    """Metadata regarding a cached item's lifecycle."""
    created_at: datetime = field(default_factory=_now_utc)
    expires_at: Optional[datetime] = None


@dataclass
class CacheEntry:
    """A standardized unit of cached data, agnostic to Redis or Memory implementation."""
    key: str
    value: Any
    metadata: CacheMetadata = field(default_factory=CacheMetadata)


@dataclass
class CacheResult:
    """Result object encapsulating the success/failure of a cache operation."""
    success: bool
    entry: Optional[CacheEntry] = None
    error: Optional[str] = None
