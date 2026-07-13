"""
Abstract Caching Interface.
"""
from abc import ABC, abstractmethod
from typing import Optional
from app.domain.models.cache import CacheEntry


class CacheProvider(ABC):
    """
    Abstract interface for caching expensive computations or transient data.
    
    Purpose: Provides a uniform way to cache AI responses, OCR results, and heavy data.
    Responsibilities: Storing, retrieving, and expiring CacheEntry objects.
    Expected Inputs: CacheEntry objects and optional Time-To-Live (TTL).
    Expected Outputs: CacheEntry if present, else None.
    Failure Behavior: Should fail silently and return None/False on connection errors to avoid crashing the app.
    Extension Points: MemoryCacheAdapter, RedisCacheAdapter.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Retrieve a value from the cache as a standardized entry."""
        pass

    @abstractmethod
    async def set(self, entry: CacheEntry, ttl_seconds: Optional[int] = None) -> bool:
        """Store a standardized entry in the cache with an optional expiration time."""
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Remove a value from the cache."""
        pass
