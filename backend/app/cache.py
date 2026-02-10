"""
Redis cache utilities for PayShield AI.
Handles prediction caching, session storage, and rate limiting.
"""

import logging
import json
import hashlib
from typing import Any, Optional
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import settings
from app.exceptions import CacheException

logger = logging.getLogger(__name__)

# Global redis client
_redis_client: Optional[Redis] = None


async def init_cache() -> None:
    """Initialize Redis connection."""
    global _redis_client
    try:
        _redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf8",
            decode_responses=True,
            socket_keepalive=settings.REDIS_SOCKET_KEEPALIVE,
            socket_keepalive_options=settings.REDIS_SOCKET_KEEPALIVE_OPTIONS,
        )
        # Test connection
        await _redis_client.ping()
        logger.info("Redis cache initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise


async def close_cache() -> None:
    """Close Redis connection."""
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis cache connection closed")


async def get_redis() -> Redis:
    """Get Redis client."""
    if _redis_client is None:
        raise CacheException("Redis client not initialized. Call init_cache() first.")
    return _redis_client


@asynccontextmanager
async def redis_context():
    """Redis context manager."""
    client = await get_redis()
    try:
        yield client
    except Exception as e:
        logger.error(f"Redis operation failed: {e}")
        raise


async def set_cache(
    key: str,
    value: Any,
    ttl_seconds: int = 3600,
) -> bool:
    """
    Set cache value with TTL.
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON-encoded if dict/list)
        ttl_seconds: Time-to-live in seconds
    
    Returns:
        True if successful
    """
    try:
        client = await get_redis()
        
        # JSON encode if needed
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        await client.setex(key, ttl_seconds, value)
        logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
        return True
    except Exception as e:
        logger.error(f"Cache set failed for {key}: {e}")
        return False


async def get_cache(key: str) -> Optional[Any]:
    """
    Get cache value.
    
    Args:
        key: Cache key
    
    Returns:
        Cached value or None if not found
    """
    try:
        client = await get_redis()
        value = await client.get(key)
        
        if value is None:
            logger.debug(f"Cache miss: {key}")
            return None
        
        # Try to JSON decode
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            pass
        
        logger.debug(f"Cache hit: {key}")
        return value
    except Exception as e:
        logger.error(f"Cache get failed for {key}: {e}")
        return None


async def delete_cache(key: str) -> bool:
    """
    Delete cache key.
    
    Args:
        key: Cache key
    
    Returns:
        True if key was deleted
    """
    try:
        client = await get_redis()
        result = await client.delete(key)
        logger.debug(f"Cache deleted: {key}")
        return result > 0
    except Exception as e:
        logger.error(f"Cache delete failed for {key}: {e}")
        return False


async def clear_cache_pattern(pattern: str) -> int:
    """
    Clear cache keys matching pattern.
    
    Args:
        pattern: Key pattern (e.g., "pred:*")
    
    Returns:
        Number of keys deleted
    """
    try:
        client = await get_redis()
        cursor = 0
        deleted = 0
        
        while True:
            cursor, keys = await client.scan(cursor, match=pattern)
            if keys:
                deleted += await client.delete(*keys)
            if cursor == 0:
                break
        
        logger.info(f"Cleared {deleted} cache keys matching {pattern}")
        return deleted
    except Exception as e:
        logger.error(f"Cache pattern clear failed for {pattern}: {e}")
        return 0


async def increment_counter(key: str, ttl_seconds: Optional[int] = None) -> int:
    """
    Increment counter (for rate limiting).
    
    Args:
        key: Counter key
        ttl_seconds: TTL for the key
    
    Returns:
        New counter value
    """
    try:
        client = await get_redis()
        value = await client.incr(key)
        
        if ttl_seconds and value == 1:
            # Set TTL on first increment
            await client.expire(key, ttl_seconds)
        
        logger.debug(f"Counter incremented: {key} = {value}")
        return value
    except Exception as e:
        logger.error(f"Counter increment failed for {key}: {e}")
        raise CacheException(f"Failed to increment counter: {e}")


async def get_counter(key: str) -> int:
    """
    Get counter value.
    
    Args:
        key: Counter key
    
    Returns:
        Counter value or 0 if not exists
    """
    try:
        client = await get_redis()
        value = await client.get(key)
        return int(value) if value else 0
    except Exception as e:
        logger.error(f"Counter get failed for {key}: {e}")
        return 0


def hash_dict(data: dict) -> str:
    """
    Create hash of dictionary (for cache keys).
    
    Args:
        data: Dictionary to hash
    
    Returns:
        Hex hash string
    """
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.md5(json_str.encode()).hexdigest()