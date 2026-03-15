"""
Tests for cache functionality.
"""

import pytest
import asyncio

from cache.cache_manager import InMemoryCache, CacheManager


@pytest.mark.asyncio
async def test_inmemory_set_get():
    """Test in-memory cache set and get."""
    cache = InMemoryCache(max_size=10, default_ttl=300)

    await cache.set("key1", "value1")
    value = await cache.get("key1")

    assert value == "value1"


@pytest.mark.asyncio
async def test_inmemory_get_nonexistent():
    """Test getting non-existent key."""
    cache = InMemoryCache()

    value = await cache.get("nonexistent")
    assert value is None


@pytest.mark.asyncio
async def test_inmemory_delete():
    """Test cache deletion."""
    cache = InMemoryCache()

    await cache.set("key1", "value1")
    await cache.delete("key1")

    value = await cache.get("key1")
    assert value is None


@pytest.mark.asyncio
async def test_inmemory_clear():
    """Test clearing all cache."""
    cache = InMemoryCache()

    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.clear()

    assert await cache.size() == 0


@pytest.mark.asyncio
async def test_inmemory_ttl_expiration():
    """Test TTL expiration."""
    cache = InMemoryCache(default_ttl=1)

    await cache.set("key1", "value1", ttl=1)

    # Should exist immediately
    value = await cache.get("key1")
    assert value == "value1"

    # Wait for expiration
    await asyncio.sleep(1.5)

    # Should be expired
    value = await cache.get("key1")
    assert value is None


@pytest.mark.asyncio
async def test_inmemory_lru_eviction():
    """Test LRU eviction when max size exceeded."""
    cache = InMemoryCache(max_size=3)

    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")

    # All should exist
    assert await cache.size() == 3

    # Add one more, should evict oldest (key1)
    await cache.set("key4", "value4")

    assert await cache.size() == 3
    assert await cache.get("key1") is None
    assert await cache.get("key4") == "value4"


@pytest.mark.asyncio
async def test_cache_manager_initialization(cache_manager: CacheManager):
    """Test cache manager initialization."""
    assert cache_manager is not None
    assert not cache_manager.is_using_redis()  # Test config has Redis disabled


@pytest.mark.asyncio
async def test_cache_manager_operations(cache_manager: CacheManager):
    """Test cache manager operations."""
    await cache_manager.set("test_key", {"data": "test_value"})

    value = await cache_manager.get("test_key")
    assert value == {"data": "test_value"}

    await cache_manager.delete("test_key")
    value = await cache_manager.get("test_key")
    assert value is None


@pytest.mark.asyncio
async def test_cache_manager_complex_data(cache_manager: CacheManager):
    """Test caching complex data structures."""
    complex_data = {
        "users": [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"}
        ],
        "metadata": {
            "total": 2,
            "cached": True
        }
    }

    await cache_manager.set("complex_key", complex_data)
    value = await cache_manager.get("complex_key")

    assert value == complex_data
    assert value["users"][0]["name"] == "Alice"
    assert value["metadata"]["total"] == 2
