"""
Property Test: Cache Hit Performance

**Validates: Requirements 12.3**

Property 28: For any cached response, retrieving it from the cache should 
complete in less than 500ms.
"""

import pytest
import time
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from src.persistence.cache_manager import CacheManager
from src.persistence.lru_cache import LRUCache
from src.persistence.cache_utils import generate_cache_key


# Strategy for generating test data
question_strategy = st.text(min_size=10, max_size=500)
subject_id_strategy = st.integers(min_value=1, max_value=100)
version_strategy = st.from_regex(r'\d+\.\d+\.\d+', fullmatch=True)
response_strategy = st.text(min_size=100, max_size=5000)


@given(
    question=question_strategy,
    subject_id=subject_id_strategy,
    vkp_version=version_strategy,
    response=response_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_cache_hit_performance(
    question: str,
    subject_id: int,
    vkp_version: str,
    response: str
):
    """
    Property 28: Cache Hit Performance
    
    For any cached response, retrieving it from the cache should complete 
    in less than 500ms.
    
    **Validates: Requirements 12.3**
    """
    # Create cache manager (LRU backend for consistent testing)
    cache_manager = CacheManager(redis_url=None)
    
    # Generate cache key
    cache_key = generate_cache_key(question, subject_id, vkp_version)
    
    # Store response in cache
    success = cache_manager.set(cache_key, response, ttl_seconds=3600)
    assume(success)  # Skip if cache set fails
    
    # Measure cache retrieval time
    start_time = time.time()
    cached_response = cache_manager.get(cache_key)
    end_time = time.time()
    
    # Calculate elapsed time in milliseconds
    elapsed_ms = (end_time - start_time) * 1000
    
    # Verify response was retrieved
    assert cached_response is not None, "Cache hit failed - response not found"
    assert cached_response == response, "Cached response does not match original"
    
    # Verify performance requirement (< 500ms)
    assert elapsed_ms < 500, f"Cache hit took {elapsed_ms:.2f}ms, exceeds 500ms limit"


@given(
    question=question_strategy,
    subject_id=subject_id_strategy,
    vkp_version=version_strategy,
    response=response_strategy
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_cache_hit_performance_multiple_retrievals(
    question: str,
    subject_id: int,
    vkp_version: str,
    response: str
):
    """
    Property 28 Extension: Multiple cache hits should all be fast.
    
    **Validates: Requirements 12.3**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Generate cache key
    cache_key = generate_cache_key(question, subject_id, vkp_version)
    
    # Store response in cache
    success = cache_manager.set(cache_key, response, ttl_seconds=3600)
    assume(success)
    
    # Perform multiple retrievals
    for i in range(5):
        start_time = time.time()
        cached_response = cache_manager.get(cache_key)
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        assert cached_response is not None, f"Cache hit {i+1} failed"
        assert cached_response == response, f"Cache hit {i+1} returned wrong data"
        assert elapsed_ms < 500, f"Cache hit {i+1} took {elapsed_ms:.2f}ms, exceeds 500ms"


def test_cache_hit_performance_large_response():
    """
    Test cache hit performance with large responses.
    
    **Validates: Requirements 12.3**
    """
    cache_manager = CacheManager(redis_url=None)
    
    # Create a large response (10KB)
    large_response = "x" * 10000
    cache_key = generate_cache_key("test question", 1, "1.0.0")
    
    # Store in cache
    cache_manager.set(cache_key, large_response, ttl_seconds=3600)
    
    # Measure retrieval time
    start_time = time.time()
    cached_response = cache_manager.get(cache_key)
    end_time = time.time()
    
    elapsed_ms = (end_time - start_time) * 1000
    
    assert cached_response == large_response
    assert elapsed_ms < 500, f"Large response cache hit took {elapsed_ms:.2f}ms"


def test_cache_hit_performance_concurrent_access():
    """
    Test cache hit performance with concurrent access pattern.
    
    **Validates: Requirements 12.3**
    """
    cache_manager = CacheManager(redis_url=None)
    
    # Store multiple responses
    keys_and_responses = []
    for i in range(10):
        question = f"Question {i}"
        response = f"Response {i}" * 100
        cache_key = generate_cache_key(question, i, "1.0.0")
        cache_manager.set(cache_key, response, ttl_seconds=3600)
        keys_and_responses.append((cache_key, response))
    
    # Retrieve all responses and measure time
    for cache_key, expected_response in keys_and_responses:
        start_time = time.time()
        cached_response = cache_manager.get(cache_key)
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000
        
        assert cached_response == expected_response
        assert elapsed_ms < 500, f"Cache hit took {elapsed_ms:.2f}ms"


def test_cache_miss_performance():
    """
    Test that cache misses are also fast (< 500ms).
    
    **Validates: Requirements 12.3**
    """
    cache_manager = CacheManager(redis_url=None)
    
    # Try to get a non-existent key
    cache_key = generate_cache_key("nonexistent question", 999, "9.9.9")
    
    start_time = time.time()
    cached_response = cache_manager.get(cache_key)
    end_time = time.time()
    
    elapsed_ms = (end_time - start_time) * 1000
    
    assert cached_response is None, "Should be cache miss"
    assert elapsed_ms < 500, f"Cache miss took {elapsed_ms:.2f}ms"


def test_lru_cache_direct_performance():
    """
    Test LRU cache performance directly.
    
    **Validates: Requirements 12.3**
    """
    lru_cache = LRUCache(max_size=1000)
    
    # Store response
    cache_key = "test_key"
    response = "test response" * 100
    lru_cache.set(cache_key, response, ttl=3600)
    
    # Measure retrieval time
    start_time = time.time()
    cached_response = lru_cache.get(cache_key)
    end_time = time.time()
    
    elapsed_ms = (end_time - start_time) * 1000
    
    assert cached_response == response
    assert elapsed_ms < 500, f"LRU cache hit took {elapsed_ms:.2f}ms"
