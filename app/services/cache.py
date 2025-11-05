"""Redis caching service."""

import json
from typing import Any, Optional

import redis
from redis.exceptions import RedisError

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """Redis caching service."""

    def __init__(self):
        """Initialize cache service."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=False,  # Keep bytes for binary data
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache service initialized", url=settings.REDIS_URL)
        except RedisError as e:
            logger.error("Failed to initialize Redis cache", error=str(e))
            self.redis_client = None

    def get(self, key: str) -> Optional[bytes]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug("Cache hit", key=key)
            return value
        except RedisError as e:
            logger.warning("Cache get error", key=key, error=str(e))
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (bytes, str, or JSON-serializable)
            ttl: Time to live in seconds (default from settings)

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        if ttl is None:
            ttl = settings.CACHE_TTL
        
        try:
            # Convert value to bytes if needed
            if isinstance(value, str):
                value_bytes = value.encode("utf-8")
            elif isinstance(value, bytes):
                value_bytes = value
            else:
                # Try JSON serialization
                value_bytes = json.dumps(value).encode("utf-8")
            
            result = self.redis_client.setex(key, ttl, value_bytes)
            if result:
                logger.debug("Cache set", key=key, ttl=ttl)
            return result
        except (RedisError, TypeError) as e:
            logger.warning("Cache set error", key=key, error=str(e))
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            if result:
                logger.debug("Cache delete", key=key)
            return bool(result)
        except RedisError as e:
            logger.warning("Cache delete error", key=key, error=str(e))
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except RedisError as e:
            logger.warning("Cache exists error", key=key, error=str(e))
            return False

    def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from cache.

        Args:
            key: Cache key

        Returns:
            Parsed JSON dict or None
        """
        value = self.get(key)
        if value is None:
            return None
        
        try:
            if isinstance(value, bytes):
                value = value.decode("utf-8")
            return json.loads(value)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning("Cache JSON decode error", key=key, error=str(e))
            return None

    def set_json(
        self,
        key: str,
        value: dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set JSON value in cache.

        Args:
            key: Cache key
            value: JSON-serializable dict
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            json_str = json.dumps(value)
            return self.set(key, json_str, ttl)
        except (TypeError, ValueError) as e:
            logger.warning("Cache JSON encode error", key=key, error=str(e))
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "model:*")

        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info("Cache cleared pattern", pattern=pattern, count=deleted)
                return deleted
            return 0
        except RedisError as e:
            logger.warning("Cache clear pattern error", pattern=pattern, error=str(e))
            return 0


# Global cache service instance
cache_service = CacheService()

