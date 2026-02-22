"""
LRU Cache Implementation for OpenClass Nexus AI

Provides in-memory LRU (Least Recently Used) cache as fallback when Redis is unavailable.

Requirements: 12.5
"""

from typing import Optional, Dict
from collections import OrderedDict
import logging
import threading
import time
import fnmatch

logger = logging.getLogger(__name__)


class LRUCache:
    """
    In-memory LRU cache with thread-safe operations.
    
    Implements Least Recently Used eviction policy with a maximum size limit.
    Thread-safe for concurrent access.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to store (default: 1000)
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._lock = threading.RLock()
        logger.info(f"LRU cache initialized with max_size={max_size}")
    
    def get(self, key: str) -> Optional[str]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            # Check if expired
            if expiry > 0 and time.time() > expiry:
                # Remove expired entry
                del self._cache[key]
                logger.debug(f"LRU cache expired: {key}")
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return value
    
    def set(self, key: str, value: str, ttl: int = 86400) -> bool:
        """
        Store value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if successful
        """
        with self._lock:
            # Calculate expiry time (0 means no expiry)
            expiry = time.time() + ttl if ttl > 0 else 0
            
            # If key exists, update and move to end
            if key in self._cache:
                self._cache[key] = (value, expiry)
                self._cache.move_to_end(key)
            else:
                # Check if we need to evict
                if len(self._cache) >= self.max_size:
                    self._evict_oldest()
                
                # Add new entry
                self._cache[key] = (value, expiry)
            
            return True
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if key not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Pattern to match (e.g., "cache:response:*:subject_5:*")
            
        Returns:
            Number of keys deleted
        """
        with self._lock:
            # Find matching keys
            matching_keys = [
                key for key in self._cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            
            # Delete matching keys
            for key in matching_keys:
                del self._cache[key]
            
            return len(matching_keys)
    
    def _evict_oldest(self):
        """
        Evict the least recently used item.
        
        Called internally when cache is full.
        """
        if self._cache:
            # Remove first item (least recently used)
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug(f"LRU cache evicted: {evicted_key}")
    
    def get_size(self) -> int:
        """
        Get current number of items in cache.
        
        Returns:
            Number of cached items
        """
        with self._lock:
            return len(self._cache)
    
    def clear(self):
        """Clear all items from cache"""
        with self._lock:
            self._cache.clear()
            logger.info("LRU cache cleared")
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of expired entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items()
                if expiry > 0 and current_time > expiry
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"LRU cache cleaned up {len(expired_keys)} expired entries")
            
            return len(expired_keys)
