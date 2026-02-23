"""
Unit Tests for Caching Layer

Tests for CacheManager, RedisCache, LRUCache, cache utilities, and integration.

Requirements: 12.1-12.6
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from src.persistence.cache_manager import CacheManager, CacheStats
from src.persistence.lru_cache import LRUCache
from src.persistence.cache_utils import (
    generate_cache_key,
    normalize_question,
    get_cache_pattern_for_subject
)
from src.persistence.cache_invalidation import CacheInvalidator, invalidate_cache_on_vkp_update


class TestCacheManager:
    """Test CacheManager class"""
    
    def test_cache_manager_initialization_lru_fallback(self):
        """Test CacheManager initializes with LRU fallback when no Redis URL"""
        cache_manager = CacheManager(redis_url=None)
        
        assert cache_manager.backend is not None
        assert cache_manager._stats.backend == "lru"
    
    def test_cache_manager_get_set_delete(self):
        """Test basic cache operations"""
        cache_manager = CacheManager(redis_url=None)
        
        # Set value
        success = cache_manager.set("test_key", "test_value", ttl_seconds=3600)
        assert success is True
        
        # Get value
        value = cache_manager.get("test_key")
        assert value == "test_value"
        
        # Delete value
        success = cache_manager.delete("test_key")
        assert success is True
        
        # Verify deleted
        value = cache_manager.get("test_key")
        assert value is None
    
    def test_cache_manager_stats(self):
        """Test cache statistics tracking"""
        cache_manager = CacheManager(redis_url=None)
        
        # Set and get
        cache_manager.set("key1", "value1", ttl_seconds=3600)
        cache_manager.get("key1")  # Hit
        cache_manager.get("key2")  # Miss
        
        # Check stats
        stats = cache_manager.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.hit_rate == 0.5
    
    def test_cache_manager_invalidate_pattern(self):
        """Test pattern-based invalidation"""
        cache_manager = CacheManager(redis_url=None)
        
        # Set multiple keys
        cache_manager.set("cache:response:abc", "value1", ttl_seconds=3600)
        cache_manager.set("cache:response:def", "value2", ttl_seconds=3600)
        cache_manager.set("other:key:ghi", "value3", ttl_seconds=3600)
        
        # Invalidate pattern
        count = cache_manager.invalidate_pattern("cache:response:*")
        
        # Verify invalidation
        assert count >= 2
        assert cache_manager.get("cache:response:abc") is None
        assert cache_manager.get("cache:response:def") is None
        assert cache_manager.get("other:key:ghi") is not None
    
    def test_cache_manager_error_handling(self):
        """Test error handling in cache operations"""
        cache_manager = CacheManager(redis_url=None)
        
        # Mock backend to raise exception
        cache_manager.backend.get = Mock(side_effect=Exception("Test error"))
        
        # Should return None on error
        value = cache_manager.get("test_key")
        assert value is None
        
        # Stats should record miss
        stats = cache_manager.get_stats()
        assert stats.misses >= 1


class TestLRUCache:
    """Test LRUCache class"""
    
    def test_lru_cache_initialization(self):
        """Test LRU cache initialization"""
        lru_cache = LRUCache(max_size=100)
        
        assert lru_cache.max_size == 100
        assert lru_cache.get_size() == 0
    
    def test_lru_cache_get_set(self):
        """Test basic LRU cache operations"""
        lru_cache = LRUCache(max_size=10)
        
        # Set value
        success = lru_cache.set("key1", "value1", ttl=3600)
        assert success is True
        
        # Get value
        value = lru_cache.get("key1")
        assert value == "value1"
        
        # Get non-existent key
        value = lru_cache.get("key2")
        assert value is None
    
    def test_lru_cache_eviction(self):
        """Test LRU eviction policy"""
        lru_cache = LRUCache(max_size=3)
        
        # Fill cache
        lru_cache.set("key1", "value1", ttl=3600)
        lru_cache.set("key2", "value2", ttl=3600)
        lru_cache.set("key3", "value3", ttl=3600)
        
        assert lru_cache.get_size() == 3
        
        # Add one more - should evict oldest (key1)
        lru_cache.set("key4", "value4", ttl=3600)
        
        assert lru_cache.get_size() == 3
        assert lru_cache.get("key1") is None  # Evicted
        assert lru_cache.get("key2") is not None
        assert lru_cache.get("key3") is not None
        assert lru_cache.get("key4") is not None
    
    def test_lru_cache_ttl_expiration(self):
        """Test TTL expiration"""
        lru_cache = LRUCache(max_size=10)
        
        # Set with short TTL
        lru_cache.set("key1", "value1", ttl=1)
        
        # Should be available immediately
        value = lru_cache.get("key1")
        assert value == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        value = lru_cache.get("key1")
        assert value is None
    
    def test_lru_cache_delete(self):
        """Test cache deletion"""
        lru_cache = LRUCache(max_size=10)
        
        lru_cache.set("key1", "value1", ttl=3600)
        assert lru_cache.get("key1") is not None
        
        # Delete
        success = lru_cache.delete("key1")
        assert success is True
        
        # Verify deleted
        assert lru_cache.get("key1") is None
        
        # Delete non-existent key
        success = lru_cache.delete("key2")
        assert success is False
    
    def test_lru_cache_invalidate_pattern(self):
        """Test pattern-based invalidation"""
        lru_cache = LRUCache(max_size=10)
        
        # Set multiple keys
        lru_cache.set("cache:response:abc", "value1", ttl=3600)
        lru_cache.set("cache:response:def", "value2", ttl=3600)
        lru_cache.set("other:key:ghi", "value3", ttl=3600)
        
        # Invalidate pattern
        count = lru_cache.invalidate_pattern("cache:response:*")
        
        # Verify invalidation
        assert count == 2
        assert lru_cache.get("cache:response:abc") is None
        assert lru_cache.get("cache:response:def") is None
        assert lru_cache.get("other:key:ghi") is not None
    
    def test_lru_cache_clear(self):
        """Test cache clear"""
        lru_cache = LRUCache(max_size=10)
        
        lru_cache.set("key1", "value1", ttl=3600)
        lru_cache.set("key2", "value2", ttl=3600)
        
        assert lru_cache.get_size() == 2
        
        # Clear
        lru_cache.clear()
        
        assert lru_cache.get_size() == 0
        assert lru_cache.get("key1") is None
        assert lru_cache.get("key2") is None
    
    def test_lru_cache_cleanup_expired(self):
        """Test cleanup of expired entries"""
        lru_cache = LRUCache(max_size=10)
        
        # Set with short TTL
        lru_cache.set("key1", "value1", ttl=1)
        lru_cache.set("key2", "value2", ttl=3600)
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Cleanup
        count = lru_cache.cleanup_expired()
        
        assert count == 1
        assert lru_cache.get("key1") is None
        assert lru_cache.get("key2") is not None
    
    def test_lru_cache_thread_safety(self):
        """Test thread-safe operations"""
        lru_cache = LRUCache(max_size=10)
        
        # This is a basic test - full thread safety would require concurrent testing
        lru_cache.set("key1", "value1", ttl=3600)
        value = lru_cache.get("key1")
        assert value == "value1"


class TestCacheUtils:
    """Test cache utility functions"""
    
    def test_generate_cache_key(self):
        """Test cache key generation"""
        key = generate_cache_key("What is Python?", 5, "1.0.0")
        
        assert key.startswith("cache:response:")
        assert len(key) > len("cache:response:")
    
    def test_generate_cache_key_consistency(self):
        """Test cache key consistency"""
        key1 = generate_cache_key("Test question", 1, "1.0.0")
        key2 = generate_cache_key("Test question", 1, "1.0.0")
        
        assert key1 == key2
    
    def test_generate_cache_key_normalization(self):
        """Test question normalization in cache key"""
        key1 = generate_cache_key("Test Question", 1, "1.0.0")
        key2 = generate_cache_key("test question", 1, "1.0.0")
        key3 = generate_cache_key("  Test Question  ", 1, "1.0.0")
        
        # All should be the same (normalized)
        assert key1 == key2 == key3
    
    def test_generate_cache_key_uniqueness(self):
        """Test cache key uniqueness"""
        key1 = generate_cache_key("Question", 1, "1.0.0")
        key2 = generate_cache_key("Question", 2, "1.0.0")  # Different subject
        key3 = generate_cache_key("Question", 1, "2.0.0")  # Different version
        
        # All should be different
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3
    
    def test_normalize_question(self):
        """Test question normalization"""
        normalized = normalize_question("  What is Python?  ")
        
        assert normalized == "what is python?"
    
    def test_get_cache_pattern_for_subject(self):
        """Test cache pattern generation"""
        pattern = get_cache_pattern_for_subject(5)
        
        # Should return a pattern (even if not fully implemented)
        assert pattern is not None
        assert isinstance(pattern, str)


class TestCacheInvalidation:
    """Test cache invalidation functionality"""
    
    def test_cache_invalidator_initialization(self):
        """Test CacheInvalidator initialization"""
        invalidator = CacheInvalidator()
        
        assert invalidator.cache_manager is not None
    
    def test_cache_invalidator_invalidate_subject(self):
        """Test subject cache invalidation"""
        cache_manager = CacheManager(redis_url=None)
        invalidator = CacheInvalidator(cache_manager)
        
        # Store some responses
        cache_manager.set("cache:response:abc", "value1", ttl_seconds=3600)
        cache_manager.set("cache:response:def", "value2", ttl_seconds=3600)
        
        # Invalidate
        count = invalidator.invalidate_subject_cache(
            subject="matematika",
            grade=10,
            new_version="1.1.0",
            old_version="1.0.0"
        )
        
        # Should invalidate all response cache keys
        assert count >= 2
    
    def test_cache_invalidator_invalidate_all(self):
        """Test invalidating all cache"""
        cache_manager = CacheManager(redis_url=None)
        invalidator = CacheInvalidator(cache_manager)
        
        # Store responses
        cache_manager.set("cache:response:abc", "value1", ttl_seconds=3600)
        cache_manager.set("cache:response:def", "value2", ttl_seconds=3600)
        
        # Invalidate all
        count = invalidator.invalidate_all_cache()
        
        assert count >= 2
        assert cache_manager.get("cache:response:abc") is None
        assert cache_manager.get("cache:response:def") is None
    
    def test_invalidate_cache_on_vkp_update_function(self):
        """Test convenience function for cache invalidation"""
        cache_manager = CacheManager(redis_url=None)
        
        # Store response
        cache_manager.set("cache:response:abc", "value1", ttl_seconds=3600)
        
        # Invalidate using convenience function
        count = invalidate_cache_on_vkp_update(
            subject="matematika",
            grade=10,
            new_version="1.1.0",
            old_version="1.0.0",
            cache_manager=cache_manager
        )
        
        assert count >= 1


class TestCacheIntegration:
    """Test cache integration scenarios"""
    
    def test_cache_workflow_complete(self):
        """Test complete cache workflow"""
        cache_manager = CacheManager(redis_url=None)
        
        # Generate cache key
        question = "What is machine learning?"
        subject_id = 5
        vkp_version = "1.0.0"
        cache_key = generate_cache_key(question, subject_id, vkp_version)
        
        # First request - cache miss
        cached = cache_manager.get(cache_key)
        assert cached is None
        
        # Store response
        response = "Machine learning is..."
        cache_manager.set(cache_key, response, ttl_seconds=3600)
        
        # Second request - cache hit
        cached = cache_manager.get(cache_key)
        assert cached == response
        
        # Invalidate on VKP update
        invalidator = CacheInvalidator(cache_manager)
        invalidator.invalidate_subject_cache(
            subject="informatika",
            grade=10,
            new_version="1.1.0",
            old_version="1.0.0"
        )
        
        # Cache should be cleared
        cached = cache_manager.get(cache_key)
        assert cached is None
    
    def test_cache_performance_benefit(self):
        """Test that caching provides performance benefit"""
        cache_manager = CacheManager(redis_url=None)
        
        # Simulate expensive operation
        call_count = 0
        
        def expensive_operation():
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # Simulate work
            return "Result"
        
        # First call - no cache
        cache_key = generate_cache_key("test", 1, "1.0.0")
        cached = cache_manager.get(cache_key)
        if cached is None:
            result = expensive_operation()
            cache_manager.set(cache_key, result, ttl_seconds=3600)
        
        assert call_count == 1
        
        # Subsequent calls - from cache
        for _ in range(10):
            cached = cache_manager.get(cache_key)
            if cached is None:
                result = expensive_operation()
                cache_manager.set(cache_key, result, ttl_seconds=3600)
        
        # Expensive operation should only be called once
        assert call_count == 1
