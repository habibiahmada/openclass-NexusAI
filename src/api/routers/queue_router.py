"""
Queue Router
Handles concurrency queue statistics and monitoring
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict

from ..models import QueueStats
from ..state import AppState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/queue", tags=["queue"])


def create_queue_router(state: AppState, verify_token_dependency):
    """Create queue router with dependencies"""
    
    @router.get("/stats", response_model=QueueStats)
    async def get_queue_stats(token_data: Dict = Depends(verify_token_dependency)):
        """Get current queue statistics"""
        if not state.concurrency_initialized or not state.concurrency_manager:
            raise HTTPException(
                status_code=503,
                detail="Concurrency manager not available"
            )
        
        try:
            from src.concurrency.concurrency_manager import ConcurrencyManager
            
            stats = state.concurrency_manager.get_queue_stats()
            
            return QueueStats(
                active_count=stats.active_count,
                queued_count=stats.queued_count,
                completed_count=stats.completed_count,
                max_concurrent=stats.max_concurrent,
                queue_full=state.concurrency_manager.is_queue_full(),
                max_queue_size=ConcurrencyManager.MAX_QUEUE_SIZE
            )
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    return router
