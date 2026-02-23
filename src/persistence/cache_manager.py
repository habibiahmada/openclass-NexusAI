"""
Cache Manager for OpenClass Nexus AI

Provides optional Redis caching with LRU fallback for repeated questions.
Reduces CPU load and improves response time.

Requirements: 12.1, 12.2
"""

from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    total_keys: int = 0
    backend: str = "unknown"
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheManager:
    """
    Manages cache operations with Redis/LRU fallback.
    
    Provides a unified interface for caching with automatic fallback
    from Redis to in-memory LRU cache if Redis is unavailable.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Optional Redis connection URL. If None or connection fails,
                      falls back to LRU cache.
        """
        self.backend = None
        self._stats = CacheStats()
        
        # Try Redis first if URL provided
        if redis_url:
            try:
                from .redis_cache import RedisCache
                self.backend = RedisCache(redis_url)
                self._stats.backend = "redis"
                logger.info("CacheManager initialized with Redis backend")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Falling back to LRU cache.")
                self.backend = None
        
        # Fallback to LRU if Redis not available
        if self.backend is None:
            from .lru_cache import LRUCache
            self.backend = LRUCache(max_size=1000)
            self._stats.backend = "lru"
            logger.info("CacheManager initialized with LRU backend")
    
    def get(self, key: str) -> Optional[str]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found, None otherwise
        """
        try:
            value = self.backend.get(key)
            if value is not None:
                self._stats.hits += 1
                logger.debug(f"Cache hit: {key}")
            else:
                self._stats.misses += 1
                logger.debug(f"Cache miss: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._stats.misses += 1
            return None
    
    def set(self, key: str, value: str, ttl_seconds: int = 86400) -> bool:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.backend.set(key, value, ttl_seconds)
            if result:
                logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
            return result
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.backend.delete(key)
            if result:
                logger.debug(f"Cache delete: {key}")
            return result
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Pattern to match (e.g., "cache:response:*:subject_5:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            count = self.backend.invalidate_pattern(pattern)
            logger.info(f"Invalidated {count} keys matching pattern: {pattern}")
            return count
        except Exception as e:
            logger.error(f"Cache invalidate_pattern error for pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.
        
        Returns:
            CacheStats object with hit/miss counts and backend info
        """
        # Update total keys from backend
        try:
            if hasattr(self.backend, 'get_size'):
                self._stats.total_keys = self.backend.get_size()
        except Exception as e:
            logger.error(f"Error getting cache size: {e}")
        
        return self._stats
    
    def clear_stats(self):
        """Reset cache statistics"""
        self._stats.hits = 0
        self._stats.misses = 0
