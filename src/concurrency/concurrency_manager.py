"""
ConcurrencyManager - Manages async queue and thread limiting for inference requests.

This module implements the core concurrency control system that limits maximum concurrent
inference threads to 5 and queues additional requests.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, AsyncIterator
from dataclasses import dataclass

from .inference_request import InferenceRequest

logger = logging.getLogger(__name__)


@dataclass
class QueueStats:
    """Statistics about the current queue state."""
    active_count: int
    queued_count: int
    completed_count: int
    max_concurrent: int


class ConcurrencyManager:
    """
    Manages concurrent inference requests with async queue and semaphore limiting.
    
    Limits maximum concurrent inference threads to 5 and queues additional requests.
    Provides queue position tracking and request statistics.
    """
    
    MAX_QUEUE_SIZE = 1000
    
    def __init__(self, max_concurrent: int = 5):
        """
        Initialize the concurrency manager.
        
        Args:
            max_concurrent: Maximum number of concurrent inference threads (default: 5)
        """
        self.max_concurrent = max_concurrent
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=self.MAX_QUEUE_SIZE)
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_requests: Dict[str, InferenceRequest] = {}
        self.completed_requests: Dict[str, datetime] = {}
        self._processing_task: Optional[asyncio.Task] = None
        
        logger.info(f"ConcurrencyManager initialized with max_concurrent={max_concurrent}")
    
    async def enqueue_request(self, request: InferenceRequest) -> str:
        """
        Enqueue an inference request for processing.
        
        Args:
            request: The inference request to enqueue
            
        Returns:
            The queue_id of the enqueued request
            
        Raises:
            asyncio.QueueFull: If the queue is at maximum capacity
        """
        # Check if queue is full before attempting to enqueue
        if self.queue.full():
            logger.error(f"Queue full (size: {self.queue.maxsize}), rejecting request {request.queue_id}")
            raise asyncio.QueueFull(f"Queue is at maximum capacity ({self.queue.maxsize})")
        
        try:
            # Use put_nowait to avoid blocking if queue becomes full between check and put
            self.queue.put_nowait(request)
            logger.info(f"Enqueued request {request.queue_id} (queue size: {self.queue.qsize()})")
            return request.queue_id
        except asyncio.QueueFull:
            logger.error(f"Queue full (size: {self.queue.maxsize}), rejecting request {request.queue_id}")
            raise
    
    async def process_queue(self) -> None:
        """
        Continuously process requests from the queue.
        
        This method should be run as a background task. It will continuously
        pull requests from the queue and process them with semaphore limiting.
        
        The key insight: We acquire the semaphore BEFORE dequeuing the next request.
        This ensures we only pull requests when we have capacity to process them,
        preventing queue buildup and excessive latency.
        """
        logger.info("Starting queue processing")
        
        while True:
            try:
                # CRITICAL: Acquire semaphore BEFORE getting request from queue
                # This ensures we only dequeue when we have processing capacity
                await self.semaphore.acquire()
                
                # Now get the next request - we know we have capacity
                request = await self.queue.get()
                
                # Process in background task
                # The semaphore is already acquired, so _process_request won't block
                asyncio.create_task(self._process_with_acquired_semaphore(request))
                
                # Mark queue task as done
                self.queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in queue processing: {e}", exc_info=True)
                # Release semaphore if we acquired it but failed
                try:
                    self.semaphore.release()
                except:
                    pass
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _process_with_acquired_semaphore(self, request: InferenceRequest) -> None:
        """
        Process a request with an already-acquired semaphore.
        
        This wrapper ensures the semaphore is released after processing.
        
        Args:
            request: The inference request to process
        """
        try:
            await self._process_request(request)
        finally:
            # Always release the semaphore
            self.semaphore.release()
    
    async def _process_request(self, request: InferenceRequest) -> None:
        """
        Process a single inference request.
        
        Note: When called from process_queue(), the semaphore is already acquired.
        When called directly (e.g., in tests), it will acquire the semaphore.
        
        Args:
            request: The inference request to process
        """
        # Mark as active
        self.active_requests[request.queue_id] = request
        logger.info(f"Processing request {request.queue_id} (active: {len(self.active_requests)})")
        
        try:
            # Placeholder for actual inference processing
            # This will be integrated with the RAG pipeline in task 7.5
            await asyncio.sleep(0.1)  # Simulate processing
            
        except Exception as e:
            logger.error(f"Error processing request {request.queue_id}: {e}", exc_info=True)
            
        finally:
            # Release and cleanup
            if request.queue_id in self.active_requests:
                del self.active_requests[request.queue_id]
            self.completed_requests[request.queue_id] = datetime.now()
            logger.info(f"Completed request {request.queue_id}")
    
    def get_queue_position(self, queue_id: str) -> int:
        """
        Get the position of a request in the queue.
        
        Args:
            queue_id: The unique identifier of the request
            
        Returns:
            - 0 if the request is currently being processed (active)
            - Positive integer for position in queue (1-based)
            - -1 if the request has been completed
            - -2 if the request is not found
        """
        # Check if active
        if queue_id in self.active_requests:
            return 0
        
        # Check if completed
        if queue_id in self.completed_requests:
            return -1
        
        # Calculate position in queue
        position = 0
        queue_list = list(self.queue._queue)
        
        for item in queue_list:
            if item.queue_id == queue_id:
                # Position is current position + number of active requests
                return position + len(self.active_requests) + 1
            position += 1
        
        # Not found
        return -2
    
    def get_queue_stats(self) -> QueueStats:
        """
        Get current queue statistics.
        
        Returns:
            QueueStats object with current queue state
        """
        return QueueStats(
            active_count=len(self.active_requests),
            queued_count=self.queue.qsize(),
            completed_count=len(self.completed_requests),
            max_concurrent=self.max_concurrent
        )
    
    def start_processing(self) -> None:
        """
        Start the background queue processing task.
        
        This should be called once when the application starts.
        """
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self.process_queue())
            logger.info("Queue processing task started")
        else:
            logger.warning("Queue processing task already running")
    
    async def stop_processing(self) -> None:
        """
        Stop the background queue processing task.
        
        This should be called when the application shuts down.
        """
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            logger.info("Queue processing task stopped")
    
    def is_queue_full(self) -> bool:
        """
        Check if the queue is at maximum capacity.
        
        Returns:
            True if queue is full, False otherwise
        """
        return self.queue.full()
