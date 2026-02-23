"""
Cache Management Router

Provides endpoints for cache statistics and management.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def create_cache_router(app_state, require_admin):
    """
    Create cache management router
    
    Args:
        app_state: Application state instance
        require_admin: Admin authentication dependency
        
    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/api/cache", tags=["cache"])
    
    @router.get("/stats")
    async def get_cache_stats(current_user: Dict = Depends(require_admin)):
        """
        Get cache statistics
        
        Requires admin authentication.
        """
        if not app_state.cache_initialized or not app_state.cache_manager:
            raise HTTPException(
                status_code=503,
                detail="Cache manager not available"
            )
        
        try:
            stats = app_state.cache_manager.get_stats()
            
            return {
                "backend": stats.backend,
                "hits": stats.hits,
                "misses": stats.misses,
                "hit_rate": stats.hit_rate,
                "total_keys": stats.total_keys,
                "status": "operational"
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get cache stats: {str(e)}"
            )
    
    @router.post("/invalidate")
    async def invalidate_cache(
        pattern: str = "cache:response:*",
        current_user: Dict = Depends(require_admin)
    ):
        """
        Invalidate cache by pattern
        
        Requires admin authentication.
        
        Args:
            pattern: Cache key pattern to invalidate (default: all responses)
        """
        if not app_state.cache_initialized or not app_state.cache_manager:
            raise HTTPException(
                status_code=503,
                detail="Cache manager not available"
            )
        
        try:
            deleted_count = app_state.cache_manager.invalidate_pattern(pattern)
            
            logger.info(f"Admin {current_user.get('username')} invalidated {deleted_count} cache keys with pattern: {pattern}")
            
            return {
                "status": "success",
                "pattern": pattern,
                "deleted_count": deleted_count,
                "message": f"Invalidated {deleted_count} cache entries"
            }
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to invalidate cache: {str(e)}"
            )
    
    @router.post("/clear-stats")
    async def clear_cache_stats(current_user: Dict = Depends(require_admin)):
        """
        Clear cache statistics
        
        Requires admin authentication.
        """
        if not app_state.cache_initialized or not app_state.cache_manager:
            raise HTTPException(
                status_code=503,
                detail="Cache manager not available"
            )
        
        try:
            app_state.cache_manager.clear_stats()
            
            logger.info(f"Admin {current_user.get('username')} cleared cache statistics")
            
            return {
                "status": "success",
                "message": "Cache statistics cleared"
            }
        except Exception as e:
            logger.error(f"Error clearing cache stats: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to clear cache stats: {str(e)}"
            )
    
    return router
