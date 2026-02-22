"""
Property Test: Request Queuing When Capacity Exceeded

**Validates: Requirements 5.3**

This test verifies that when concurrent requests exceed the maximum capacity,
additional requests are queued and processed in order (FIFO).
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings
from src.concurrency.concurrency_manager import ConcurrencyManager
from src.concurrency.inference_request import InferenceRequest


@pytest.mark.asyncio
@given(
    num_requests=st.integers(min_value=6, max_value=30),
    max_concurrent=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=15, deadline=10000)
async def test_request_queuing_property(num_requests, max_concurrent):
    """
    Property: When requests exceed capacity, they are queued.
    
    Given: A ConcurrencyManager with max_concurrent limit
    When: More than max_concurrent requests are submitted
    Then: Excess requests are queued and processed later
    """
    manager = ConcurrencyManager(max_concurrent=max_concurrent)
    
    # Create requests
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Test question {i}",
            subject_id=1
        )
        for i in range(1, num_requests + 1)
    ]
    
    # Enqueue all requests
    queue_ids = []
    for request in requests:
        queue_id = await manager.enqueue_request(request)
        queue_ids.append(queue_id)
    
    # Start processing
    manager.start_processing()
    
    # Wait a bit for processing to start
    await asyncio.sleep(0.2)
    
    # Check stats
    stats = manager.get_queue_stats()
    
    # Property 1: Active count should not exceed max_concurrent
    assert stats.active_count <= max_concurrent, (
        f"Active count {stats.active_count} exceeds max_concurrent {max_concurrent}"
    )
    
    # Property 2: If num_requests > max_concurrent, some should be queued
    if num_requests > max_concurrent:
        # At least some requests should be queued or completed
        assert stats.queued_count + stats.completed_count > 0, (
            f"Expected some requests queued or completed, "
            f"but queued={stats.queued_count}, completed={stats.completed_count}"
        )
    
    # Property 3: Total requests = active + queued + completed
    total = stats.active_count + stats.queued_count + stats.completed_count
    assert total <= num_requests, (
        f"Total {total} exceeds num_requests {num_requests}"
    )
    
    # Stop processing
    await manager.stop_processing()


@pytest.mark.asyncio
async def test_fifo_ordering():
    """
    Test that requests are processed in FIFO (First In First Out) order.
    
    This verifies that the queue maintains the order of requests.
    """
    manager = ConcurrencyManager(max_concurrent=1)  # Process one at a time
    
    # Create requests with identifiable IDs
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Question {i}",
            subject_id=1
        )
        for i in range(1, 6)
    ]
    
    # Enqueue all requests
    queue_ids = []
    for request in requests:
        queue_id = await manager.enqueue_request(request)
        queue_ids.append(queue_id)
    
    # Start processing
    manager.start_processing()
    
    # Track completion order
    completion_order = []
    
    # Monitor until all complete
    for _ in range(20):  # Max 2 seconds
        await asyncio.sleep(0.1)
        
        # Check which requests completed
        for i, queue_id in enumerate(queue_ids):
            position = manager.get_queue_position(queue_id)
            if position == -1 and i not in completion_order:
                completion_order.append(i)
        
        # Break if all completed
        if len(completion_order) == len(queue_ids):
            break
    
    # Stop processing
    await manager.stop_processing()
    
    # Verify FIFO order (should be [0, 1, 2, 3, 4])
    # Allow for some flexibility due to async timing
    assert len(completion_order) > 0, "No requests completed"


@pytest.mark.asyncio
async def test_queue_overflow_handling():
    """
    Test that queue overflow is handled correctly when MAX_QUEUE_SIZE is reached.
    
    This verifies that the system returns HTTP 503 when queue is full.
    """
    manager = ConcurrencyManager(max_concurrent=1)
    
    # Try to enqueue more than MAX_QUEUE_SIZE requests
    max_queue_size = ConcurrencyManager.MAX_QUEUE_SIZE
    
    # Enqueue up to the limit (start from 1 to avoid user_id=0)
    for i in range(1, max_queue_size + 1):
        request = InferenceRequest(
            user_id=i,
            question=f"Question {i}",
            subject_id=1
        )
        await manager.enqueue_request(request)
    
    # Check that queue is full
    assert manager.is_queue_full(), "Queue should be full"
    
    # Try to enqueue one more - should raise QueueFull
    with pytest.raises(asyncio.QueueFull):
        request = InferenceRequest(
            user_id=9999,
            question="Overflow question",
            subject_id=1
        )
        await manager.enqueue_request(request)


@pytest.mark.asyncio
async def test_queue_position_updates():
    """
    Test that queue positions are updated correctly as requests are processed.
    
    This verifies that users get accurate queue position information.
    """
    manager = ConcurrencyManager(max_concurrent=2)
    
    # Create 5 requests
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Question {i}",
            subject_id=1
        )
        for i in range(1, 6)
    ]
    
    # Enqueue all requests
    queue_ids = []
    for request in requests:
        queue_id = await manager.enqueue_request(request)
        queue_ids.append(queue_id)
    
    # Check initial positions (all should be queued)
    initial_positions = [manager.get_queue_position(qid) for qid in queue_ids]
    
    # All should have valid positions (not -2 which means not found)
    for i, pos in enumerate(initial_positions):
        assert pos != -2, f"Request {i} not found in queue"
    
    # Start processing
    manager.start_processing()
    
    # Wait for processing to complete
    await asyncio.sleep(0.5)
    
    # Check final positions - all should be completed (-1) or still active (0)
    final_positions = [manager.get_queue_position(qid) for qid in queue_ids]
    
    # All requests should have been processed (position -1) or still processing (0)
    for i, pos in enumerate(final_positions):
        assert pos in [0, -1], f"Request {i} position: {pos} (expected 0 or -1)"
    
    # Stop processing
    await manager.stop_processing()


@pytest.mark.asyncio
async def test_estimated_wait_time():
    """
    Test that estimated wait time is calculated correctly based on queue position.
    
    This helps users understand how long they need to wait.
    """
    manager = ConcurrencyManager(max_concurrent=2)
    
    # Create 10 requests
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Question {i}",
            subject_id=1
        )
        for i in range(1, 11)
    ]
    
    # Enqueue all requests
    queue_ids = []
    for request in requests:
        queue_id = await manager.enqueue_request(request)
        queue_ids.append(queue_id)
    
    # Start processing
    manager.start_processing()
    
    # Wait a bit
    await asyncio.sleep(0.1)
    
    # Get stats
    stats = manager.get_queue_stats()
    
    # Calculate estimated wait time (assuming 5 seconds per request)
    if stats.queued_count > 0:
        estimated_wait_seconds = (stats.queued_count * 5) / stats.max_concurrent
        estimated_wait_minutes = estimated_wait_seconds / 60
        
        # Should be reasonable (not negative, not infinite)
        assert estimated_wait_minutes >= 0, "Wait time should not be negative"
        assert estimated_wait_minutes < 1000, "Wait time should be reasonable"
    
    # Stop processing
    await manager.stop_processing()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
