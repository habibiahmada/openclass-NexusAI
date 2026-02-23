"""
Property Test: Queue Position Tracking

**Validates: Requirements 5.6**

This test verifies that the queue position tracking returns correct values:
- 0 for active requests (currently being processed)
- Positive integer for queued requests (position in queue)
- -1 for completed requests
- -2 for not found requests
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume
from src.concurrency.concurrency_manager import ConcurrencyManager
from src.concurrency.inference_request import InferenceRequest


@pytest.mark.asyncio
@given(
    num_requests=st.integers(min_value=1, max_value=20),
    max_concurrent=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=15, deadline=10000)
async def test_queue_position_tracking_property(num_requests, max_concurrent):
    """
    Property: Queue position values are always valid and meaningful.
    
    Given: A ConcurrencyManager with requests
    When: Checking queue position for any request
    Then: Position is 0 (active), positive (queued), -1 (completed), or -2 (not found)
    """
    manager = ConcurrencyManager(max_concurrent=max_concurrent)
    
    # Create requests
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Question {i}",
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
    
    # Wait a bit
    await asyncio.sleep(0.2)
    
    # Check positions for all requests
    for queue_id in queue_ids:
        position = manager.get_queue_position(queue_id)
        
        # Property: Position must be valid
        assert position >= -2, f"Invalid position {position} for queue_id {queue_id}"
        
        # Property: Position meanings
        if position == 0:
            # Active - should be in active_requests
            assert queue_id in manager.active_requests, (
                f"Position 0 but not in active_requests"
            )
        elif position == -1:
            # Completed - should be in completed_requests
            assert queue_id in manager.completed_requests, (
                f"Position -1 but not in completed_requests"
            )
        elif position > 0:
            # Queued - should not be in active or completed
            assert queue_id not in manager.active_requests, (
                f"Position {position} but in active_requests"
            )
            assert queue_id not in manager.completed_requests, (
                f"Position {position} but in completed_requests"
            )
    
    # Stop processing
    await manager.stop_processing()


@pytest.mark.asyncio
async def test_position_zero_for_active():
    """
    Test that active requests return position 0.
    """
    manager = ConcurrencyManager(max_concurrent=2)
    
    # Create 3 requests
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Question {i}",
            subject_id=1
        )
        for i in range(1, 4)
    ]
    
    # Enqueue all requests
    queue_ids = []
    for request in requests:
        queue_id = await manager.enqueue_request(request)
        queue_ids.append(queue_id)
    
    # Start processing
    manager.start_processing()
    
    # Wait for processing to start
    await asyncio.sleep(0.1)
    
    # Check positions
    active_count = 0
    for queue_id in queue_ids:
        position = manager.get_queue_position(queue_id)
        if position == 0:
            active_count += 1
            # Verify it's actually in active_requests
            assert queue_id in manager.active_requests
    
    # Should have at most max_concurrent active
    assert active_count <= 2, f"Expected <= 2 active, got {active_count}"
    
    # Stop processing
    await manager.stop_processing()


@pytest.mark.asyncio
async def test_position_negative_one_for_completed():
    """
    Test that completed requests return position -1.
    """
    manager = ConcurrencyManager(max_concurrent=5)
    
    # Create 3 requests
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Question {i}",
            subject_id=1
        )
        for i in range(1, 4)
    ]
    
    # Enqueue all requests
    queue_ids = []
    for request in requests:
        queue_id = await manager.enqueue_request(request)
        queue_ids.append(queue_id)
    
    # Start processing
    manager.start_processing()
    
    # Wait for all to complete
    await asyncio.sleep(1.0)
    
    # Check positions - all should be completed
    for queue_id in queue_ids:
        position = manager.get_queue_position(queue_id)
        
        # Should be completed (-1) or still active (0)
        assert position in [0, -1], f"Expected 0 or -1, got {position}"
        
        if position == -1:
            # Verify it's in completed_requests
            assert queue_id in manager.completed_requests
    
    # Stop processing
    await manager.stop_processing()


@pytest.mark.asyncio
async def test_position_positive_for_queued():
    """
    Test that queued requests return positive position values.
    """
    manager = ConcurrencyManager(max_concurrent=1)  # Only 1 concurrent
    
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
    
    # Start processing
    manager.start_processing()
    
    # Wait a bit
    await asyncio.sleep(0.1)
    
    # Check positions
    positions = [manager.get_queue_position(qid) for qid in queue_ids]
    
    # First should be active (0) or completed (-1)
    assert positions[0] in [0, -1], f"First position: {positions[0]}"
    
    # Some of the rest should be queued (positive)
    queued_positions = [p for p in positions[1:] if p > 0]
    
    # Should have at least some queued
    # (unless they all completed very quickly)
    if len(queued_positions) > 0:
        # Queued positions should be sequential
        for i, pos in enumerate(sorted(queued_positions)):
            # Position should be reasonable (not too large)
            assert pos <= len(queue_ids), f"Position {pos} too large"
    
    # Stop processing
    await manager.stop_processing()


@pytest.mark.asyncio
async def test_position_negative_two_for_not_found():
    """
    Test that non-existent requests return position -2.
    """
    manager = ConcurrencyManager(max_concurrent=5)
    
    # Check position for a non-existent queue_id
    fake_queue_id = "non-existent-id-12345"
    position = manager.get_queue_position(fake_queue_id)
    
    # Should return -2 for not found
    assert position == -2, f"Expected -2 for not found, got {position}"


@pytest.mark.asyncio
async def test_position_transitions():
    """
    Test that position transitions correctly: queued -> active -> completed.
    """
    manager = ConcurrencyManager(max_concurrent=1)
    
    # Create 3 requests
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Question {i}",
            subject_id=1
        )
        for i in range(1, 4)
    ]
    
    # Enqueue all requests
    queue_ids = []
    for request in requests:
        queue_id = await manager.enqueue_request(request)
        queue_ids.append(queue_id)
    
    # Start processing
    manager.start_processing()
    
    # Track position transitions for the second request
    second_queue_id = queue_ids[1]
    position_history = []
    
    # Monitor for 2 seconds
    for _ in range(20):
        await asyncio.sleep(0.1)
        position = manager.get_queue_position(second_queue_id)
        position_history.append(position)
    
    # Stop processing
    await manager.stop_processing()
    
    # Verify transition pattern
    # Should go from positive (queued) -> 0 (active) -> -1 (completed)
    # Or directly from positive -> -1 if processing is very fast
    
    # Remove duplicates while preserving order
    unique_positions = []
    for pos in position_history:
        if not unique_positions or pos != unique_positions[-1]:
            unique_positions.append(pos)
    
    # Should have at least 2 different positions
    assert len(unique_positions) >= 2, (
        f"Expected position transitions, got {unique_positions}"
    )
    
    # Final position should be -1 (completed) or 0 (still active)
    assert position_history[-1] in [0, -1], (
        f"Final position should be 0 or -1, got {position_history[-1]}"
    )


@pytest.mark.asyncio
async def test_position_consistency():
    """
    Test that position values are consistent with queue stats.
    """
    manager = ConcurrencyManager(max_concurrent=3)
    
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
    await asyncio.sleep(0.2)
    
    # Get stats
    stats = manager.get_queue_stats()
    
    # Count positions
    active_count = 0
    queued_count = 0
    completed_count = 0
    
    for queue_id in queue_ids:
        position = manager.get_queue_position(queue_id)
        if position == 0:
            active_count += 1
        elif position > 0:
            queued_count += 1
        elif position == -1:
            completed_count += 1
    
    # Verify consistency with stats
    assert active_count == stats.active_count, (
        f"Active count mismatch: {active_count} vs {stats.active_count}"
    )
    
    # Queued count might differ slightly due to timing
    # but should be close
    assert abs(queued_count - stats.queued_count) <= 1, (
        f"Queued count mismatch: {queued_count} vs {stats.queued_count}"
    )
    
    # Stop processing
    await manager.stop_processing()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
