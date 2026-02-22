"""
Property Test: Cache Key Consistency

**Validates: Requirements 12.2**

Property 27: For any question text, subject ID, and VKP version, generating the 
cache key multiple times should always produce the same hash value.
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.persistence.cache_utils import generate_cache_key, normalize_question


# Strategy for generating test data
question_strategy = st.text(min_size=1, max_size=500)
subject_id_strategy = st.integers(min_value=1, max_value=100)
version_strategy = st.from_regex(r'\d+\.\d+\.\d+', fullmatch=True)


@given(
    question=question_strategy,
    subject_id=subject_id_strategy,
    vkp_version=version_strategy
)
@settings(max_examples=100)
def test_cache_key_consistency(question: str, subject_id: int, vkp_version: str):
    """
    Property 27: Cache Key Consistency
    
    For any question text, subject ID, and VKP version, generating the cache key
    multiple times should always produce the same hash value.
    
    **Validates: Requirements 12.2**
    """
    # Generate cache key multiple times
    key1 = generate_cache_key(question, subject_id, vkp_version)
    key2 = generate_cache_key(question, subject_id, vkp_version)
    key3 = generate_cache_key(question, subject_id, vkp_version)
    
    # All keys should be identical
    assert key1 == key2, "Cache key generation is not consistent (key1 != key2)"
    assert key2 == key3, "Cache key generation is not consistent (key2 != key3)"
    assert key1 == key3, "Cache key generation is not consistent (key1 != key3)"
    
    # Keys should follow expected format
    assert key1.startswith("cache:response:"), "Cache key does not have expected prefix"
    
    # Keys should be deterministic - same inputs always produce same output
    assert len(key1) > len("cache:response:"), "Cache key hash is empty"


@given(
    question=question_strategy,
    subject_id=subject_id_strategy,
    vkp_version=version_strategy
)
@settings(max_examples=100)
def test_cache_key_normalization_consistency(
    question: str,
    subject_id: int,
    vkp_version: str
):
    """
    Property 27 Extension: Cache key should be consistent regardless of
    whitespace variations in the question.
    
    **Validates: Requirements 12.2**
    """
    # Add various whitespace variations
    question_with_spaces = f"  {question}  "
    question_with_newlines = f"\n{question}\n"
    question_with_tabs = f"\t{question}\t"
    
    # Generate keys for all variations
    key_original = generate_cache_key(question, subject_id, vkp_version)
    key_spaces = generate_cache_key(question_with_spaces, subject_id, vkp_version)
    key_newlines = generate_cache_key(question_with_newlines, subject_id, vkp_version)
    key_tabs = generate_cache_key(question_with_tabs, subject_id, vkp_version)
    
    # All keys should be identical (normalization removes whitespace)
    assert key_original == key_spaces, "Whitespace normalization failed (spaces)"
    assert key_original == key_newlines, "Whitespace normalization failed (newlines)"
    assert key_original == key_tabs, "Whitespace normalization failed (tabs)"


@given(
    question=question_strategy,
    subject_id=subject_id_strategy,
    vkp_version=version_strategy
)
@settings(max_examples=100)
def test_cache_key_case_insensitive(
    question: str,
    subject_id: int,
    vkp_version: str
):
    """
    Property 27 Extension: Cache key should be case-insensitive for questions.
    
    **Validates: Requirements 12.2**
    """
    # Skip if question has no alphabetic characters
    if not any(c.isalpha() for c in question):
        return
    
    # Generate keys with different cases
    key_original = generate_cache_key(question, subject_id, vkp_version)
    key_upper = generate_cache_key(question.upper(), subject_id, vkp_version)
    key_lower = generate_cache_key(question.lower(), subject_id, vkp_version)
    
    # The key from lowercase should match the original (since normalization lowercases)
    # But upper case might differ for special Unicode characters
    # So we only assert that lowercase normalization is consistent
    assert key_original == key_lower, "Case normalization failed (lowercase)"
    
    # For ASCII-only strings, all should be identical
    if question.isascii():
        assert key_original == key_upper, "Case normalization failed (uppercase) for ASCII"


@given(
    question=question_strategy,
    subject_id=subject_id_strategy,
    vkp_version=version_strategy
)
@settings(max_examples=100)
def test_cache_key_uniqueness_by_subject(
    question: str,
    subject_id: int,
    vkp_version: str
):
    """
    Property 27 Extension: Different subject IDs should produce different cache keys.
    
    **Validates: Requirements 12.2**
    """
    # Generate keys for different subjects
    key1 = generate_cache_key(question, subject_id, vkp_version)
    key2 = generate_cache_key(question, subject_id + 1, vkp_version)
    
    # Keys should be different
    assert key1 != key2, "Cache keys should differ for different subjects"


@given(
    question=question_strategy,
    subject_id=subject_id_strategy,
    vkp_version=version_strategy
)
@settings(max_examples=100)
def test_cache_key_uniqueness_by_version(
    question: str,
    subject_id: int,
    vkp_version: str
):
    """
    Property 27 Extension: Different VKP versions should produce different cache keys.
    
    **Validates: Requirements 12.2**
    """
    # Generate keys for different versions
    key1 = generate_cache_key(question, subject_id, vkp_version)
    key2 = generate_cache_key(question, subject_id, "9.9.9")
    
    # Keys should be different (unless vkp_version happens to be "9.9.9")
    if vkp_version != "9.9.9":
        assert key1 != key2, "Cache keys should differ for different VKP versions"


def test_normalize_question_consistency():
    """
    Test that question normalization is consistent.
    
    **Validates: Requirements 12.2**
    """
    question = "What is Pythagoras Theorem?"
    
    # Normalize multiple times
    norm1 = normalize_question(question)
    norm2 = normalize_question(question)
    norm3 = normalize_question(question)
    
    # All should be identical
    assert norm1 == norm2 == norm3
    
    # Should be lowercase and stripped
    assert norm1 == "what is pythagoras theorem?"


def test_cache_key_format():
    """
    Test that cache keys follow the expected format.
    
    **Validates: Requirements 12.2**
    """
    question = "Test question"
    subject_id = 5
    vkp_version = "1.0.0"
    
    key = generate_cache_key(question, subject_id, vkp_version)
    
    # Should start with prefix
    assert key.startswith("cache:response:")
    
    # Should have hash after prefix
    hash_part = key.replace("cache:response:", "")
    assert len(hash_part) == 64, "SHA256 hash should be 64 characters"
    
    # Hash should be hexadecimal
    assert all(c in "0123456789abcdef" for c in hash_part), "Hash should be hexadecimal"
