"""
Cache Service.
Application service coordinating operations through the abstract CacheProvider.
"""
from typing import Any, Optional
from loguru import logger

from app.domain.interfaces.cache import CacheProvider
from app.domain.models.cache import CacheEntry, CacheResult


class CacheService:
    """
    Coordinates caching operations.
    Strictly depends on the abstract CacheProvider, entirely decoupled from Redis/Memory implementations.
    Guarantees graceful degradation: If the cache infrastructure goes down, the service returns failures 
    that the business logic can interpret as cache-misses, keeping the app alive.
    """
    
    def __init__(self, provider: CacheProvider):
        """
        Injected constructor.
        The specific provider is supplied by the Dependency Injection layer.
        """
        self._provider = provider

    async def get(self, key: str) -> CacheResult:
        """
        Retrieves a value from the underlying cache.
        """
        try:
            entry = await self._provider.get(key)
            if entry:
                logger.debug(f"Cache hit for key: {key}")
                return CacheResult(success=True, entry=entry)
            
            logger.debug(f"Cache miss for key: {key}")
            return CacheResult(success=True, entry=None)
            
        except Exception as e:
            # We trap generic exceptions to ensure infrastructure failures don't crash the orchestrator
            logger.warning(f"Cache provider failure on GET '{key}': {str(e)}")
            return CacheResult(success=False, error="Cache provider unavailable.")

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> CacheResult:
        """
        Stores a value in the underlying cache.
        """
        try:
            entry = CacheEntry(key=key, value=value)
            success = await self._provider.set(entry, ttl_seconds)
            
            if success:
                logger.debug(f"Successfully cached key: {key}")
            else:
                logger.warning(f"Cache provider rejected SET for key: {key}")
                
            return CacheResult(success=success, entry=entry if success else None)
            
        except Exception as e:
            logger.warning(f"Cache provider failure on SET '{key}': {str(e)}")
            return CacheResult(success=False, error="Cache provider unavailable.")

    async def delete(self, key: str) -> bool:
        """
        Deletes a value from the underlying cache.
        """
        try:
            return await self._provider.delete(key)
        except Exception as e:
            logger.warning(f"Cache provider failure on DELETE '{key}': {str(e)}")
            return False
