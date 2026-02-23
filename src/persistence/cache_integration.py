"""
Cache Integration for RAG Pipeline

Provides caching wrapper for RAG pipeline to reduce CPU load and improve response time.

Requirements: 12.1, 12.3, 12.4
"""

from typing import Optional, Callable, Any
import logging
import json
from datetime import datetime

from .cache_manager import CacheManager
from .cache_utils import generate_cache_key

logger = logging.getLogger(__name__)

# Default TTL: 24 hours (86400 seconds)
DEFAULT_CACHE_TTL = 86400


class CachedRAGPipeline:
    """
    Wrapper for RAG pipeline with caching support.
    
    Checks cache before RAG query and stores response after generation.
    """
    
    def __init__(
        self,
        rag_pipeline: Any,
        cache_manager: Optional[CacheManager] = None,
        ttl_seconds: int = DEFAULT_CACHE_TTL
    ):
        """
        Initialize cached RAG pipeline.
        
        Args:
            rag_pipeline: The RAG pipeline instance to wrap
            cache_manager: Optional cache manager (creates default if None)
            ttl_seconds: Cache TTL in seconds (default: 24 hours)
        """
        self.rag_pipeline = rag_pipeline
        self.cache_manager = cache_manager or CacheManager()
        self.ttl_seconds = ttl_seconds
        logger.info(f"CachedRAGPipeline initialized with TTL={ttl_seconds}s")
    
    def process_query_with_cache(
        self,
        query: str,
        subject_id: int,
        vkp_version: str,
        **kwargs
    ) -> Any:
        """
        Process query with caching.
        
        Checks cache first, falls back to RAG pipeline on cache miss.
        
        Args:
            query: The question text
            subject_id: The subject identifier
            vkp_version: The VKP version string
            **kwargs: Additional arguments for RAG pipeline
            
        Returns:
            QueryResult from cache or RAG pipeline
        """
        # Generate cache key
        cache_key = generate_cache_key(query, subject_id, vkp_version)
        
        # Check cache
        cached_response = self.cache_manager.get(cache_key)
        if cached_response:
            logger.info(f"Cache hit for query: {query[:50]}...")
            try:
                # Deserialize cached response
                result = self._deserialize_result(cached_response)
                return result
            except Exception as e:
                logger.error(f"Error deserializing cached response: {e}")
                # Fall through to RAG pipeline
        
        # Cache miss - run RAG pipeline
        logger.info(f"Cache miss for query: {query[:50]}...")
        result = self.rag_pipeline.process_query(query, **kwargs)
        
        # Store in cache
        try:
            serialized = self._serialize_result(result)
            self.cache_manager.set(cache_key, serialized, ttl_seconds=self.ttl_seconds)
            logger.debug(f"Cached response for query: {query[:50]}...")
        except Exception as e:
            logger.error(f"Error caching response: {e}")
        
        return result
    
    def invalidate_subject_cache(self, subject_id: int) -> int:
        """
        Invalidate all cached responses for a subject.
        
        Note: With hash-based cache keys, this requires tracking
        subject_id -> cache_key mappings. For now, this is a placeholder.
        
        Args:
            subject_id: The subject identifier
            
        Returns:
            Number of keys invalidated
        """
        # With hash-based keys, we need a different approach
        # Option 1: Track subject_id -> cache_key mapping in a separate structure
        # Option 2: Use a different key structure that includes subject_id
        # For now, log a warning
        logger.warning(
            f"Subject-based cache invalidation not fully implemented for hash-based keys. "
            f"Subject ID: {subject_id}"
        )
        return 0
    
    def _serialize_result(self, result: Any) -> str:
        """
        Serialize QueryResult to JSON string.
        
        Args:
            result: QueryResult object
            
        Returns:
            JSON string
        """
        # Convert QueryResult to dict
        result_dict = {
            'query': result.query,
            'response': result.response,
            'context_used': result.context_used,
            'sources': result.sources,
            'processing_time_ms': result.processing_time_ms,
            'context_stats': result.context_stats,
            'timestamp': result.timestamp.isoformat() if result.timestamp else None,
            'is_fallback': result.is_fallback,
            'fallback_reason': result.fallback_reason.value if result.fallback_reason else None,
            'cached': True,
            'cache_timestamp': datetime.now().isoformat()
        }
        return json.dumps(result_dict)
    
    def _deserialize_result(self, serialized: str) -> Any:
        """
        Deserialize JSON string to QueryResult.
        
        Args:
            serialized: JSON string
            
        Returns:
            QueryResult object (as dict for simplicity)
        """
        result_dict = json.loads(serialized)
        
        # Convert timestamp back to datetime if present
        if result_dict.get('timestamp'):
            result_dict['timestamp'] = datetime.fromisoformat(result_dict['timestamp'])
        
        # Mark as cached
        result_dict['from_cache'] = True
        
        return result_dict
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return self.cache_manager.get_stats()


def get_current_vkp_version(subject_id: int, book_repository: Any) -> str:
    """
    Get current VKP version for a subject.
    
    Args:
        subject_id: The subject identifier
        book_repository: BookRepository instance
        
    Returns:
        VKP version string or "unknown" if not found
    """
    try:
        books = book_repository.get_books_by_subject(subject_id)
        if books:
            # Return the latest version (assuming books are ordered)
            return books[0].vkp_version or "unknown"
        return "unknown"
    except Exception as e:
        logger.error(f"Error getting VKP version for subject {subject_id}: {e}")
        return "unknown"
