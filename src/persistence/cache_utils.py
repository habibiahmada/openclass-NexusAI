"""
Cache Utilities for OpenClass Nexus AI

Provides cache key generation and related utilities.

Requirements: 12.2
"""

import hashlib
import logging

logger = logging.getLogger(__name__)


def generate_cache_key(question: str, subject_id: int, vkp_version: str) -> str:
    """
    Generate cache key using SHA256 hash.
    
    Creates a deterministic cache key from question text, subject ID, and VKP version.
    The question text is normalized (lowercase, stripped) to ensure consistent keys
    for semantically identical questions.
    
    Args:
        question: The question text
        subject_id: The subject identifier
        vkp_version: The VKP version string
        
    Returns:
        Cache key in format "cache:response:{sha256_hash}"
        
    Example:
        >>> generate_cache_key("What is Pythagoras theorem?", 5, "1.2.0")
        'cache:response:abc123def456...'
    """
    # Normalize question text
    normalized = question.lower().strip()
    
    # Include subject and version in key
    key_input = f"{normalized}:{subject_id}:{vkp_version}"
    
    # Generate SHA256 hash
    hash_value = hashlib.sha256(key_input.encode('utf-8')).hexdigest()
    
    # Return formatted cache key
    cache_key = f"cache:response:{hash_value}"
    
    logger.debug(f"Generated cache key for subject {subject_id}, version {vkp_version}")
    
    return cache_key


def normalize_question(question: str) -> str:
    """
    Normalize question text for consistent cache key generation.
    
    Args:
        question: The question text
        
    Returns:
        Normalized question (lowercase, stripped whitespace)
    """
    return question.lower().strip()


def extract_subject_from_cache_key(cache_key: str) -> str:
    """
    Extract subject pattern from cache key for invalidation.
    
    Args:
        cache_key: Cache key in format "cache:response:{hash}"
        
    Returns:
        Pattern for matching all keys for a subject
    """
    # Cache keys don't directly contain subject_id, so we return a pattern
    # that can be used with the hash approach
    return "cache:response:*"


def get_cache_pattern_for_subject(subject_id: int) -> str:
    """
    Get cache key pattern for invalidating all responses for a subject.
    
    Note: Since cache keys use SHA256 hash, we cannot directly pattern match
    by subject_id. This function is provided for documentation purposes.
    Actual invalidation requires tracking subject_id separately or using
    a different key structure.
    
    Args:
        subject_id: The subject identifier
        
    Returns:
        Pattern string (note: hash-based keys require alternative approach)
    """
    # With hash-based keys, we need to track subject_id -> cache_key mapping
    # or use a different key structure like "cache:response:subject_{id}:{hash}"
    logger.warning(
        "Hash-based cache keys require tracking for subject-based invalidation. "
        "Consider maintaining a subject_id -> cache_key mapping."
    )
    return f"cache:response:*"
