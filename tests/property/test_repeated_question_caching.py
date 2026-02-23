"""
Property Test: Repeated Question Caching

**Validates: Requirements 12.1**

Property 30: For any question asked multiple times with the same subject and 
VKP version, the second and subsequent requests should return the cached response.
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.persistence.cache_manager import CacheManager
from src.persistence.cache_utils import generate_cache_key


# Strategy for generating test data
question_strategy = st.text(min_size=10, max_size=200)
subject_id_strategy = st.integers(min_value=1, max_value=100)
version_strategy = st.from_regex(r'\d+\.\d+\.\d+', fullmatch=True)
response_strategy = st.text(min_size=50, max_size=1000)


@given(
    question=question_strategy,
    subject_id=subject_id_strategy,
    vkp_version=version_strategy,
    response=response_strategy
)
@settings(max_examples=100)
def test_repeated_question_caching(
    question: str,
    subject_id: int,
    vkp_version: str,
    response: str
):
    """
    Property 30: Repeated Question Caching
    
    For any question asked multiple times with the same subject and VKP version,
    the second and subsequent requests should return the cached response.
    
    **Validates: Requirements 12.1**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Generate cache key
    cache_key = generate_cache_key(question, subject_id, vkp_version)
    
    # First request - cache miss
    first_response = cache_manager.get(cache_key)
    assert first_response is None, "First request should be cache miss"
    
    # Store response (simulating RAG pipeline result)
    cache_manager.set(cache_key, response, ttl_seconds=3600)
    
    # Second request - should hit cache
    second_response = cache_manager.get(cache_key)
    assert second_response is not None, "Second request should hit cache"
    assert second_response == response, "Cached response should match original"
    
    # Third request - should also hit cache
    third_response = cache_manager.get(cache_key)
    assert third_response is not None, "Third request should hit cache"
    assert third_response == response, "Cached response should match original"
    
    # Verify cache stats
    stats = cache_manager.get_stats()
    assert stats.hits >= 2, f"Expected at least 2 cache hits, got {stats.hits}"


@given(
    question=question_strategy,
    subject_id=subject_id_strategy,
    vkp_version=version_strategy,
    response=response_strategy
)
@settings(max_examples=50)
def test_repeated_question_caching_many_requests(
    question: str,
    subject_id: int,
    vkp_version: str,
    response: str
):
    """
    Property 30 Extension: Many repeated requests should all hit cache.
    
    **Validates: Requirements 12.1**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Generate cache key
    cache_key = generate_cache_key(question, subject_id, vkp_version)
    
    # Store response
    cache_manager.set(cache_key, response, ttl_seconds=3600)
    
    # Make 10 repeated requests
    for i in range(10):
        cached_response = cache_manager.get(cache_key)
        assert cached_response is not None, f"Request {i+1} should hit cache"
        assert cached_response == response, f"Request {i+1} should return correct response"
    
    # Verify all requests hit cache
    stats = cache_manager.get_stats()
    assert stats.hits >= 10, f"Expected at least 10 cache hits, got {stats.hits}"


@given(
    question=question_strategy,
    subject_id=subject_id_strategy,
    vkp_version=version_strategy
)
@settings(max_examples=50)
def test_repeated_question_different_versions_no_cache(
    question: str,
    subject_id: int,
    vkp_version: str
):
    """
    Property 30 Extension: Same question with different VKP versions should not share cache.
    
    **Validates: Requirements 12.1**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Store response for version 1
    cache_key_v1 = generate_cache_key(question, subject_id, vkp_version)
    response_v1 = "Response for version 1"
    cache_manager.set(cache_key_v1, response_v1, ttl_seconds=3600)
    
    # Try to get response for version 2 (different version)
    different_version = "9.9.9" if vkp_version != "9.9.9" else "8.8.8"
    cache_key_v2 = generate_cache_key(question, subject_id, different_version)
    response_v2 = cache_manager.get(cache_key_v2)
    
    # Should be cache miss (different version)
    assert response_v2 is None, "Different VKP version should not hit cache"
    
    # Original version should still be cached
    cached_v1 = cache_manager.get(cache_key_v1)
    assert cached_v1 == response_v1, "Original version should still be cached"


@given(
    question=question_strategy,
    subject_id=subject_id_strategy,
    vkp_version=version_strategy
)
@settings(max_examples=50)
def test_repeated_question_different_subjects_no_cache(
    question: str,
    subject_id: int,
    vkp_version: str
):
    """
    Property 30 Extension: Same question for different subjects should not share cache.
    
    **Validates: Requirements 12.1**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Store response for subject 1
    cache_key_s1 = generate_cache_key(question, subject_id, vkp_version)
    response_s1 = "Response for subject 1"
    cache_manager.set(cache_key_s1, response_s1, ttl_seconds=3600)
    
    # Try to get response for subject 2 (different subject)
    different_subject_id = subject_id + 1
    cache_key_s2 = generate_cache_key(question, different_subject_id, vkp_version)
    response_s2 = cache_manager.get(cache_key_s2)
    
    # Should be cache miss (different subject)
    assert response_s2 is None, "Different subject should not hit cache"
    
    # Original subject should still be cached
    cached_s1 = cache_manager.get(cache_key_s1)
    assert cached_s1 == response_s1, "Original subject should still be cached"


def test_repeated_question_case_insensitive():
    """
    Test that repeated questions with different cases hit the same cache.
    
    **Validates: Requirements 12.1**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Store response for lowercase question
    question_lower = "what is pythagoras theorem?"
    cache_key_lower = generate_cache_key(question_lower, 1, "1.0.0")
    response = "Pythagoras theorem states..."
    cache_manager.set(cache_key_lower, response, ttl_seconds=3600)
    
    # Try uppercase version
    question_upper = "WHAT IS PYTHAGORAS THEOREM?"
    cache_key_upper = generate_cache_key(question_upper, 1, "1.0.0")
    cached_response = cache_manager.get(cache_key_upper)
    
    # Should hit cache (case-insensitive)
    assert cached_response is not None, "Uppercase question should hit cache"
    assert cached_response == response, "Should return same response"


def test_repeated_question_whitespace_normalized():
    """
    Test that repeated questions with different whitespace hit the same cache.
    
    **Validates: Requirements 12.1**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Store response for trimmed question
    question_trimmed = "What is the formula?"
    cache_key_trimmed = generate_cache_key(question_trimmed, 1, "1.0.0")
    response = "The formula is..."
    cache_manager.set(cache_key_trimmed, response, ttl_seconds=3600)
    
    # Try with extra whitespace
    question_spaces = "  What is the formula?  "
    cache_key_spaces = generate_cache_key(question_spaces, 1, "1.0.0")
    cached_response = cache_manager.get(cache_key_spaces)
    
    # Should hit cache (whitespace normalized)
    assert cached_response is not None, "Question with extra whitespace should hit cache"
    assert cached_response == response, "Should return same response"


def test_repeated_question_cache_hit_rate():
    """
    Test that cache hit rate increases with repeated questions.
    
    **Validates: Requirements 12.1**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Clear stats
    cache_manager.clear_stats()
    
    # Store response
    cache_key = generate_cache_key("Test question", 1, "1.0.0")
    cache_manager.set(cache_key, "Test response", ttl_seconds=3600)
    
    # First get - should be hit
    cache_manager.get(cache_key)
    
    # Get stats
    stats = cache_manager.get_stats()
    assert stats.hits == 1, "Should have 1 hit"
    assert stats.misses == 0, "Should have 0 misses"
    assert stats.hit_rate == 1.0, "Hit rate should be 100%"
    
    # Make more requests
    for _ in range(9):
        cache_manager.get(cache_key)
    
    # Get updated stats
    stats = cache_manager.get_stats()
    assert stats.hits == 10, "Should have 10 hits"
    assert stats.hit_rate == 1.0, "Hit rate should still be 100%"


def test_repeated_question_cpu_reduction():
    """
    Test that repeated questions reduce CPU load by avoiding RAG pipeline.
    
    This is a conceptual test - in practice, we would measure actual CPU usage.
    
    **Validates: Requirements 12.1**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Simulate expensive RAG pipeline call
    expensive_call_count = 0
    
    def expensive_rag_pipeline(question: str) -> str:
        nonlocal expensive_call_count
        expensive_call_count += 1
        return f"Response for {question}"
    
    # First request - cache miss, call RAG pipeline
    question = "What is machine learning?"
    cache_key = generate_cache_key(question, 1, "1.0.0")
    
    cached = cache_manager.get(cache_key)
    if cached is None:
        response = expensive_rag_pipeline(question)
        cache_manager.set(cache_key, response, ttl_seconds=3600)
    
    assert expensive_call_count == 1, "RAG pipeline should be called once"
    
    # Subsequent requests - cache hit, no RAG pipeline call
    for _ in range(10):
        cached = cache_manager.get(cache_key)
        if cached is None:
            response = expensive_rag_pipeline(question)
            cache_manager.set(cache_key, response, ttl_seconds=3600)
    
    # RAG pipeline should still only be called once
    assert expensive_call_count == 1, "RAG pipeline should not be called again"
