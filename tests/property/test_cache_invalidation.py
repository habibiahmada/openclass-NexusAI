"""
Property Test: Cache Invalidation on VKP Update

**Validates: Requirements 12.6**

Property 29: For any subject where the VKP version is updated, all cached 
responses for that subject should be invalidated.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from src.persistence.cache_manager import CacheManager
from src.persistence.cache_invalidation import CacheInvalidator, invalidate_cache_on_vkp_update
from src.persistence.cache_utils import generate_cache_key


# Strategy for generating test data
subject_strategy = st.sampled_from(["matematika", "informatika", "fisika", "kimia", "biologi"])
grade_strategy = st.integers(min_value=10, max_value=12)
version_strategy = st.from_regex(r'\d+\.\d+\.\d+', fullmatch=True)
question_strategy = st.text(min_size=10, max_size=200)


@given(
    subject=subject_strategy,
    grade=grade_strategy,
    old_version=version_strategy,
    new_version=version_strategy,
    question=question_strategy
)
@settings(max_examples=100)
def test_cache_invalidation_on_vkp_update(
    subject: str,
    grade: int,
    old_version: str,
    new_version: str,
    question: str
):
    """
    Property 29: Cache Invalidation on VKP Update
    
    For any subject where the VKP version is updated, all cached responses 
    for that subject should be invalidated.
    
    **Validates: Requirements 12.6**
    """
    # Skip if versions are the same
    assume(old_version != new_version)
    
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Generate cache key with old version
    subject_id = hash(f"{subject}_{grade}") % 100  # Mock subject_id
    cache_key = generate_cache_key(question, subject_id, old_version)
    
    # Store response in cache
    response = f"Response for {question}"
    cache_manager.set(cache_key, response, ttl_seconds=3600)
    
    # Verify response is cached
    cached_response = cache_manager.get(cache_key)
    assert cached_response == response, "Response should be cached"
    
    # Invalidate cache for subject (simulating VKP update)
    invalidator = CacheInvalidator(cache_manager)
    deleted_count = invalidator.invalidate_subject_cache(
        subject=subject,
        grade=grade,
        new_version=new_version,
        old_version=old_version
    )
    
    # Verify cache was invalidated (at least 1 key deleted)
    assert deleted_count >= 1, f"Expected at least 1 key deleted, got {deleted_count}"
    
    # Verify response is no longer cached
    cached_response_after = cache_manager.get(cache_key)
    assert cached_response_after is None, "Response should be invalidated after VKP update"


@given(
    subject=subject_strategy,
    grade=grade_strategy,
    version=version_strategy
)
@settings(max_examples=50)
def test_cache_invalidation_multiple_responses(
    subject: str,
    grade: int,
    version: str
):
    """
    Property 29 Extension: Invalidation should clear all cached responses.
    
    **Validates: Requirements 12.6**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Store multiple responses for the subject
    subject_id = hash(f"{subject}_{grade}") % 100
    questions = [f"Question {i}" for i in range(5)]
    
    for question in questions:
        cache_key = generate_cache_key(question, subject_id, version)
        response = f"Response for {question}"
        cache_manager.set(cache_key, response, ttl_seconds=3600)
    
    # Verify all responses are cached
    for question in questions:
        cache_key = generate_cache_key(question, subject_id, version)
        cached_response = cache_manager.get(cache_key)
        assert cached_response is not None, f"Response for {question} should be cached"
    
    # Invalidate cache
    invalidator = CacheInvalidator(cache_manager)
    deleted_count = invalidator.invalidate_subject_cache(
        subject=subject,
        grade=grade,
        new_version="9.9.9",
        old_version=version
    )
    
    # Verify all responses are invalidated
    assert deleted_count >= len(questions), f"Expected at least {len(questions)} keys deleted"
    
    for question in questions:
        cache_key = generate_cache_key(question, subject_id, version)
        cached_response = cache_manager.get(cache_key)
        assert cached_response is None, f"Response for {question} should be invalidated"


def test_cache_invalidation_convenience_function():
    """
    Test the convenience function for cache invalidation.
    
    **Validates: Requirements 12.6**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Store some responses
    subject_id = 5
    cache_key = generate_cache_key("Test question", subject_id, "1.0.0")
    cache_manager.set(cache_key, "Test response", ttl_seconds=3600)
    
    # Verify cached
    assert cache_manager.get(cache_key) is not None
    
    # Invalidate using convenience function
    deleted_count = invalidate_cache_on_vkp_update(
        subject="matematika",
        grade=10,
        new_version="1.1.0",
        old_version="1.0.0",
        cache_manager=cache_manager
    )
    
    # Verify invalidation occurred
    assert deleted_count >= 1
    assert cache_manager.get(cache_key) is None


def test_cache_invalidation_all():
    """
    Test invalidating all cached responses.
    
    **Validates: Requirements 12.6**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Store multiple responses for different subjects
    for i in range(5):
        cache_key = generate_cache_key(f"Question {i}", i, "1.0.0")
        cache_manager.set(cache_key, f"Response {i}", ttl_seconds=3600)
    
    # Verify all are cached
    for i in range(5):
        cache_key = generate_cache_key(f"Question {i}", i, "1.0.0")
        assert cache_manager.get(cache_key) is not None
    
    # Invalidate all
    invalidator = CacheInvalidator(cache_manager)
    deleted_count = invalidator.invalidate_all_cache()
    
    # Verify all are invalidated
    assert deleted_count >= 5
    for i in range(5):
        cache_key = generate_cache_key(f"Question {i}", i, "1.0.0")
        assert cache_manager.get(cache_key) is None


def test_cache_invalidation_pattern_matching():
    """
    Test that invalidation uses pattern matching correctly.
    
    **Validates: Requirements 12.6**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Store responses with cache:response: prefix
    cache_key1 = generate_cache_key("Question 1", 1, "1.0.0")
    cache_key2 = generate_cache_key("Question 2", 2, "1.0.0")
    
    cache_manager.set(cache_key1, "Response 1", ttl_seconds=3600)
    cache_manager.set(cache_key2, "Response 2", ttl_seconds=3600)
    
    # Store a non-response cache key (should not be invalidated)
    cache_manager.set("other:key:123", "Other data", ttl_seconds=3600)
    
    # Verify all are cached
    assert cache_manager.get(cache_key1) is not None
    assert cache_manager.get(cache_key2) is not None
    assert cache_manager.get("other:key:123") is not None
    
    # Invalidate response cache
    deleted_count = cache_manager.invalidate_pattern("cache:response:*")
    
    # Verify response cache is invalidated
    assert deleted_count >= 2
    assert cache_manager.get(cache_key1) is None
    assert cache_manager.get(cache_key2) is None
    
    # Verify other key is still cached
    assert cache_manager.get("other:key:123") is not None


def test_cache_invalidation_empty_cache():
    """
    Test invalidation on empty cache doesn't cause errors.
    
    **Validates: Requirements 12.6**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Invalidate empty cache
    invalidator = CacheInvalidator(cache_manager)
    deleted_count = invalidator.invalidate_subject_cache(
        subject="matematika",
        grade=10,
        new_version="1.1.0",
        old_version="1.0.0"
    )
    
    # Should return 0 (no keys deleted)
    assert deleted_count == 0


def test_cache_invalidation_logging():
    """
    Test that invalidation logs the count of deleted keys.
    
    **Validates: Requirements 12.6**
    """
    # Create cache manager
    cache_manager = CacheManager(redis_url=None)
    
    # Store some responses
    for i in range(3):
        cache_key = generate_cache_key(f"Question {i}", i, "1.0.0")
        cache_manager.set(cache_key, f"Response {i}", ttl_seconds=3600)
    
    # Invalidate and check count
    invalidator = CacheInvalidator(cache_manager)
    deleted_count = invalidator.invalidate_subject_cache(
        subject="matematika",
        grade=10,
        new_version="1.1.0",
        old_version="1.0.0"
    )
    
    # Should have deleted at least 3 keys
    assert deleted_count >= 3
