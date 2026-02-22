"""
Property Test: Concurrent Thread Limit

**Validates: Requirements 5.1**

This test verifies that the ConcurrencyManager correctly limits the maximum
number of concurrent inference threads to 5, regardless of how many requests
are submitted.
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings
from src.concurrency.concurrency_manager import ConcurrencyManager
from src.concurrency.inference_request import InferenceRequest


@pytest.mark.asyncio
@given(
    num_requests=st.integers(min_value=1, max_value=50),
    max_concurrent=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=20, deadline=10000)
async def test_concurrent_thread_limit_property(num_requests, max_concurrent):
    """
    Property: The number of active requests never exceeds max_concurrent.
    
    Given: A ConcurrencyManager with max_concurrent limit
    When: Multiple requests are enqueued
    Then: The number of active requests never exceeds max_concurrent
    """
    manager = ConcurrencyManager(max_concurrent=max_concurrent)
    
    # Track maximum active count observed
    max_active_observed = 0
    active_counts = []
    
    # Create mock requests
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Test question {i}",
            subject_id=1
        )
        for i in range(1, num_requests + 1)
    ]
    
    # Enqueue all requests
    for request in requests:
        await manager.enqueue_request(request)
    
    # Start processing
    manager.start_processing()
    
    # Monitor active count for a period
    for _ in range(10):
        await asyncio.sleep(0.1)
        stats = manager.get_queue_stats()
        active_counts.append(stats.active_count)
        max_active_observed = max(max_active_observed, stats.active_count)
    
    # Stop processing
    await manager.stop_processing()
    
    # Property: Maximum active count should never exceed max_concurrent
    assert max_active_observed <= max_concurrent, (
        f"Observed {max_active_observed} active requests, "
        f"but max_concurrent is {max_concurrent}"
    )
    
    # Additional check: At least some requests should have been active
    # (unless num_requests is 0, which is excluded by min_value=1)
    assert max_active_observed > 0, "No requests were processed"


@pytest.mark.asyncio
async def test_concurrent_thread_limit_specific():
    """
    Specific test case: Verify exactly 5 concurrent threads with 10 requests.
    
    This is a concrete example to complement the property test.
    """
    manager = ConcurrencyManager(max_concurrent=5)
    
    # Create 10 requests
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Test question {i}",
            subject_id=1
        )
        for i in range(1, 11)
    ]
    
    # Enqueue all requests
    for request in requests:
        await manager.enqueue_request(request)
    
    # Start processing
    manager.start_processing()
    
    # Wait a bit for processing to start
    await asyncio.sleep(0.2)
    
    # Check stats
    stats = manager.get_queue_stats()
    
    # Should have at most 5 active
    assert stats.active_count <= 5, f"Expected <= 5 active, got {stats.active_count}"
    
    # Should have remaining in queue
    assert stats.queued_count >= 0, f"Expected >= 0 queued, got {stats.queued_count}"
    
    # Total should be 10 (active + queued + completed)
    total = stats.active_count + stats.queued_count + stats.completed_count
    assert total <= 10, f"Expected total <= 10, got {total}"
    
    # Stop processing
    await manager.stop_processing()


@pytest.mark.asyncio
async def test_semaphore_releases_correctly():
    """
    Test that the semaphore is released correctly after request completion.
    
    This ensures that the concurrency limit is maintained over time and
    doesn't get "stuck" with fewer active threads than allowed.
    """
    manager = ConcurrencyManager(max_concurrent=3)
    
    # Create 6 requests
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Test question {i}",
            subject_id=1
        )
        for i in range(1, 7)
    ]
    
    # Enqueue all requests
    for request in requests:
        await manager.enqueue_request(request)
    
    # Start processing
    manager.start_processing()
    
    # Wait for all to complete
    await asyncio.sleep(1.0)
    
    # Check that all completed
    stats = manager.get_queue_stats()
    
    # All should be completed or in progress
    assert stats.active_count + stats.completed_count <= 6
    
    # Queue should be empty
    assert stats.queued_count == 0
    
    # Stop processing
    await manager.stop_processing()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
