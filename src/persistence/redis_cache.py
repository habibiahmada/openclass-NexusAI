"""
Redis Cache Implementation for OpenClass Nexus AI

Provides Redis-based caching with TTL support and pattern-based deletion.

Requirements: 12.1
"""

from typing import Optional
import logging
import redis
import fnmatch

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based caching implementation.
    
    Provides cache operations with TTL support and pattern-based deletion.
    Handles connection errors gracefully.
    """
    
    def __init__(self, redis_url: str):
        """
        Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
            
        Raises:
            redis.ConnectionError: If connection to Redis fails
        """
        try:
            self.client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"Redis cache connected: {redis_url}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis initialization error: {e}")
            raise
    
    def get(self, key: str) -> Optional[str]:
        """
        Retrieve value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found, None otherwise
        """
        try:
            value = self.client.get(key)
            return value
        except redis.RedisError as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: int) -> bool:
        """
        Store value in Redis with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.setex(key, ttl, value)
            return result is True
        except redis.RedisError as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False otherwise
        """
        try:
            result = self.client.delete(key)
            return result > 0
        except redis.RedisError as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Uses Redis SCAN command for efficient pattern matching.
        
        Args:
            pattern: Pattern to match (e.g., "cache:response:*:subject_5:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            deleted_count = 0
            cursor = 0
            
            # Use SCAN to iterate through keys matching pattern
            while True:
                cursor, keys = self.client.scan(cursor, match=pattern, count=100)
                
                if keys:
                    # Delete keys in batch
                    deleted_count += self.client.delete(*keys)
                
                # Break when cursor returns to 0
                if cursor == 0:
                    break
            
            return deleted_count
        except redis.RedisError as e:
            logger.error(f"Redis invalidate_pattern error for pattern {pattern}: {e}")
            return 0
    
    def get_size(self) -> int:
        """
        Get total number of keys in Redis.
        
        Returns:
            Number of keys
        """
        try:
            return self.client.dbsize()
        except redis.RedisError as e:
            logger.error(f"Redis get_size error: {e}")
            return 0
    
    def flush_all(self) -> bool:
        """
        Clear all keys from Redis (use with caution).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.flushdb()
            logger.warning("Redis cache flushed (all keys deleted)")
            return True
        except redis.RedisError as e:
            logger.error(f"Redis flush_all error: {e}")
            return False
    
    def ping(self) -> bool:
        """
        Check Redis connection health.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            return self.client.ping()
        except redis.RedisError as e:
            logger.error(f"Redis ping error: {e}")
            return False
