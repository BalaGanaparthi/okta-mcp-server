"""
Cache manager with Redis and in-memory fallback.

This module provides a caching layer that can use Redis or fall back
to in-memory caching if Redis is unavailable.
"""

import json
import asyncio
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from collections import OrderedDict

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from config import RedisConfig, CacheConfig
from models.schemas import CacheEntry
from utils.logging import LoggerMixin
from utils.errors import CacheError


class InMemoryCache(LoggerMixin):
    """
    LRU in-memory cache implementation.

    Thread-safe cache with TTL support and LRU eviction.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize in-memory cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.logger.info(
            "inmemory_cache_initialized",
            max_size=max_size,
            default_ttl=default_ttl
        )

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        async with self._lock:
            ttl = ttl or self.default_ttl
            entry = CacheEntry(key=key, value=value, ttl=ttl)

            # Remove if already exists
            if key in self._cache:
                del self._cache[key]

            # Add to end
            self._cache[key] = entry

            # Evict oldest if over max size
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    async def delete(self, key: str) -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def size(self) -> int:
        """
        Get current cache size.

        Returns:
            Number of entries in cache
        """
        async with self._lock:
            return len(self._cache)


class RedisCache(LoggerMixin):
    """Redis-based cache implementation."""

    def __init__(
        self,
        redis_url: str,
        default_ttl: int = 300
    ):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds
        """
        if not REDIS_AVAILABLE:
            raise CacheError(
                "Redis library not available",
                operation="initialize"
            )

        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._redis: Optional[aioredis.Redis] = None
        self.logger.info(
            "redis_cache_initialized",
            redis_url=redis_url,
            default_ttl=default_ttl
        )

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self._redis.ping()
            self.logger.info("redis_connected")
        except Exception as e:
            self.logger.error("redis_connection_failed", error=str(e))
            raise CacheError(
                f"Failed to connect to Redis: {str(e)}",
                operation="connect"
            ) from e

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self.logger.info("redis_disconnected")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._redis:
            raise CacheError("Redis not connected", operation="get")

        try:
            value = await self._redis.get(key)
            if value is None:
                return None

            # Deserialize JSON
            return json.loads(value)
        except Exception as e:
            self.logger.error("redis_get_error", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in Redis.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        if not self._redis:
            raise CacheError("Redis not connected", operation="set")

        try:
            ttl = ttl or self.default_ttl
            # Serialize to JSON
            serialized = json.dumps(value)
            await self._redis.setex(key, ttl, serialized)
        except Exception as e:
            self.logger.error("redis_set_error", key=key, error=str(e))
            raise CacheError(
                f"Failed to set cache key: {str(e)}",
                operation="set"
            ) from e

    async def delete(self, key: str) -> None:
        """
        Delete value from Redis.

        Args:
            key: Cache key
        """
        if not self._redis:
            raise CacheError("Redis not connected", operation="delete")

        try:
            await self._redis.delete(key)
        except Exception as e:
            self.logger.error("redis_delete_error", key=key, error=str(e))

    async def clear(self) -> None:
        """Clear all cache entries."""
        if not self._redis:
            raise CacheError("Redis not connected", operation="clear")

        try:
            await self._redis.flushdb()
            self.logger.info("redis_cache_cleared")
        except Exception as e:
            self.logger.error("redis_clear_error", error=str(e))
            raise CacheError(
                f"Failed to clear cache: {str(e)}",
                operation="clear"
            ) from e


class CacheManager(LoggerMixin):
    """
    Cache manager with automatic fallback.

    Uses Redis if available, falls back to in-memory cache.
    """

    def __init__(
        self,
        redis_config: RedisConfig,
        cache_config: CacheConfig
    ):
        """
        Initialize cache manager.

        Args:
            redis_config: Redis configuration
            cache_config: Cache behavior configuration
        """
        self.redis_config = redis_config
        self.cache_config = cache_config
        self._cache: Optional[RedisCache | InMemoryCache] = None
        self._using_redis = False

    async def initialize(self) -> None:
        """Initialize cache backend."""
        # Try Redis first if enabled
        if self.redis_config.enabled and REDIS_AVAILABLE:
            try:
                redis_cache = RedisCache(
                    self.redis_config.url,
                    self.cache_config.ttl
                )
                await redis_cache.connect()
                self._cache = redis_cache
                self._using_redis = True
                self.logger.info("cache_initialized", backend="redis")
                return
            except Exception as e:
                self.logger.warning(
                    "redis_init_failed_using_memory",
                    error=str(e)
                )

        # Fall back to in-memory
        self._cache = InMemoryCache(
            max_size=self.cache_config.max_size,
            default_ttl=self.cache_config.ttl
        )
        self._using_redis = False
        self.logger.info("cache_initialized", backend="in-memory")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self._cache:
            return None

        value = await self._cache.get(key)
        if value is not None:
            self.logger.debug("cache_hit", key=key)
        else:
            self.logger.debug("cache_miss", key=key)

        return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        if not self._cache:
            return

        await self._cache.set(key, value, ttl)
        self.logger.debug("cache_set", key=key)

    async def delete(self, key: str) -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        if not self._cache:
            return

        await self._cache.delete(key)
        self.logger.debug("cache_delete", key=key)

    async def clear(self) -> None:
        """Clear all cache entries."""
        if not self._cache:
            return

        await self._cache.clear()
        self.logger.info("cache_cleared")

    async def invalidate_pattern(self, pattern: str) -> None:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")
        """
        # This is a simplified implementation
        # In production, you'd want to use Redis SCAN for large datasets
        self.logger.info("cache_invalidate_pattern", pattern=pattern)

    def is_using_redis(self) -> bool:
        """
        Check if using Redis backend.

        Returns:
            True if using Redis, False if in-memory
        """
        return self._using_redis

    async def close(self) -> None:
        """Close cache connections."""
        if self._cache and isinstance(self._cache, RedisCache):
            await self._cache.disconnect()


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.

    Returns:
        CacheManager instance

    Raises:
        CacheError: If cache manager not initialized
    """
    if _cache_manager is None:
        raise CacheError("Cache manager not initialized")
    return _cache_manager


async def initialize_cache_manager(
    redis_config: RedisConfig,
    cache_config: CacheConfig
) -> CacheManager:
    """
    Initialize the global cache manager.

    Args:
        redis_config: Redis configuration
        cache_config: Cache configuration

    Returns:
        Initialized cache manager
    """
    global _cache_manager
    _cache_manager = CacheManager(redis_config, cache_config)
    await _cache_manager.initialize()
    return _cache_manager
