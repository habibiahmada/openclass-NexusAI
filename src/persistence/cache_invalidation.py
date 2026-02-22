"""
Cache Invalidation for VKP Updates

Provides cache invalidation functionality when VKP versions are updated.

Requirements: 12.6
"""

from typing import Optional
import logging

from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class CacheInvalidator:
    """
    Handles cache invalidation on VKP updates.
    
    Invalidates all cached responses for a subject when its VKP version is updated.
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize cache invalidator.
        
        Args:
            cache_manager: Optional cache manager (creates default if None)
        """
        self.cache_manager = cache_manager or CacheManager()
        logger.info("CacheInvalidator initialized")
    
    def invalidate_subject_cache(
        self,
        subject: str,
        grade: int,
        new_version: str,
        old_version: Optional[str] = None
    ) -> int:
        """
        Invalidate all cached responses for a subject.
        
        When a VKP is updated, all cached responses for that subject should be
        invalidated to ensure users get responses based on the new content.
        
        Args:
            subject: Subject name (e.g., "matematika")
            grade: Grade level (10, 11, or 12)
            new_version: New VKP version
            old_version: Optional old VKP version for logging
            
        Returns:
            Number of cache keys invalidated
        """
        try:
            # Since cache keys use SHA256 hash, we need to invalidate all cache keys
            # A better approach would be to include subject/grade in the key structure
            # For now, we'll use a pattern that matches all response cache keys
            pattern = "cache:response:*"
            
            deleted_count = self.cache_manager.invalidate_pattern(pattern)
            
            logger.info(
                f"Invalidated {deleted_count} cached responses for "
                f"{subject} grade {grade} (v{old_version} -> v{new_version})"
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error invalidating cache for {subject} grade {grade}: {e}")
            return 0
    
    def invalidate_all_cache(self) -> int:
        """
        Invalidate all cached responses.
        
        Use with caution - clears entire response cache.
        
        Returns:
            Number of cache keys invalidated
        """
        try:
            pattern = "cache:response:*"
            deleted_count = self.cache_manager.invalidate_pattern(pattern)
            
            logger.warning(f"Invalidated all {deleted_count} cached responses")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error invalidating all cache: {e}")
            return 0


def invalidate_cache_on_vkp_update(
    subject: str,
    grade: int,
    new_version: str,
    old_version: Optional[str] = None,
    cache_manager: Optional[CacheManager] = None
) -> int:
    """
    Convenience function to invalidate cache on VKP update.
    
    Args:
        subject: Subject name
        grade: Grade level
        new_version: New VKP version
        old_version: Optional old VKP version
        cache_manager: Optional cache manager
        
    Returns:
        Number of cache keys invalidated
    """
    invalidator = CacheInvalidator(cache_manager)
    return invalidator.invalidate_subject_cache(
        subject=subject,
        grade=grade,
        new_version=new_version,
        old_version=old_version
    )
