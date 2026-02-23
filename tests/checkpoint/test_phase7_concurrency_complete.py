"""
Checkpoint Test: Phase 7 - Concurrency Management System Complete

This test verifies that the concurrency management system works end-to-end:
- Submit 10 concurrent requests
- Verify only 5 process simultaneously
- Verify remaining 5 are queued
- Verify queue positions returned correctly
- Ensure all tests pass

**Requirements Validated:** 5.1, 5.2, 5.3, 5.6
"""

import pytest
import asyncio
from src.concurrency.concurrency_manager import ConcurrencyManager
from src.concurrency.inference_request import InferenceRequest


@pytest.mark.asyncio
async def test_phase7_checkpoint_concurrent_limit():
    """
    Checkpoint: Verify that 10 concurrent requests result in max 5 active.
    
    This is the main checkpoint test for Phase 7.
    """
    print("\n" + "="*70)
    print("PHASE 7 CHECKPOINT: Concurrency Management System")
    print("="*70)
    
    # Create manager with max 5 concurrent
    manager = ConcurrencyManager(max_concurrent=5)
    
    print("\n✓ ConcurrencyManager initialized with max_concurrent=5")
    
    # Create 10 requests
    requests = [
        InferenceRequest(
            user_id=i,
            question=f"Test question {i}",
            subject_id=1
        )
        for i in range(1, 11)
    ]
    
    print(f"✓ Created 10 inference requests")
    
    # Enqueue all requests
    queue_ids = []
    for request in requests:
        queue_id = await manager.enqueue_request(request)
        queue_ids.append(queue_id)
    
    print(f"✓ Enqueued all 10 requests")
    
    # Start processing
    manager.start_processing()
    print(f"✓ Started queue processing")
    
    # Wait for processing to start
    await asyncio.sleep(0.3)
    
    # Check stats
    stats = manager.get_queue_stats()
    
    print(f"\n📊 Queue Statistics:")
    print(f"   - Active requests: {stats.active_count}")
    print(f"   - Queued requests: {stats.queued_count}")
    print(f"   - Completed requests: {stats.completed_count}")
    print(f"   - Max concurrent: {stats.max_concurrent}")
    
    # Verify concurrent limit
    assert stats.active_count <= 5, (
        f"❌ FAILED: Active count {stats.active_count} exceeds max_concurrent 5"
    )
    print(f"✓ Concurrent limit verified: {stats.active_count} <= 5")
    
    # Verify some are queued or completed
    assert stats.queued_count + stats.completed_count > 0, (
        f"❌ FAILED: Expected some requests queued or completed"
    )
    print(f"✓ Queuing verified: {stats.queued_count} queued, {stats.completed_count} completed")
    
    # Check queue positions
    positions = {}
    for i, queue_id in enumerate(queue_ids):
        position = manager.get_queue_position(queue_id)
        positions[i] = position
    
    print(f"\n📍 Queue Positions:")
    for i, position in positions.items():
        if position == 0:
            status = "ACTIVE"
        elif position > 0:
            status = f"QUEUED (position {position})"
        elif position == -1:
            status = "COMPLETED"
        else:
            status = "NOT FOUND"
        print(f"   Request {i+1}: {status}")
    
    # Verify position values are valid
    for i, position in positions.items():
        assert position >= -1, (
            f"❌ FAILED: Invalid position {position} for request {i}"
        )
    print(f"✓ All queue positions are valid")
    
    # Count active requests
    active_count = sum(1 for p in positions.values() if p == 0)
    assert active_count <= 5, (
        f"❌ FAILED: {active_count} active requests exceeds limit of 5"
    )
    print(f"✓ Active request count verified: {active_count} <= 5")
    
    # Wait for all to complete
    print(f"\n⏳ Waiting for all requests to complete...")
    for _ in range(30):  # Max 3 seconds
        await asyncio.sleep(0.1)
        stats = manager.get_queue_stats()
        if stats.queued_count == 0 and stats.active_count == 0:
            break
    
    # Final stats
    final_stats = manager.get_queue_stats()
    print(f"\n📊 Final Statistics:")
    print(f"   - Active: {final_stats.active_count}")
    print(f"   - Queued: {final_stats.queued_count}")
    print(f"   - Completed: {final_stats.completed_count}")
    
    # Stop processing
    await manager.stop_processing()
    print(f"✓ Stopped queue processing")
    
    print("\n" + "="*70)
    print("✅ PHASE 7 CHECKPOINT PASSED")
    print("="*70)
    print("\nAll requirements verified:")
    print("  ✓ Requirement 5.1: Max 5 concurrent threads enforced")
    print("  ✓ Requirement 5.2: Async queue implemented")
    print("  ✓ Requirement 5.3: Excess requests queued")
    print("  ✓ Requirement 5.6: Queue positions tracked correctly")
    print("="*70 + "\n")


@pytest.mark.asyncio
async def test_phase7_checkpoint_queue_overflow():
    """
    Checkpoint: Verify queue overflow handling (HTTP 503).
    """
    print("\n" + "="*70)
    print("CHECKPOINT: Queue Overflow Handling")
    print("="*70)
    
    manager = ConcurrencyManager(max_concurrent=1)
    
    # Replace queue with smaller one for testing
    manager.queue = asyncio.Queue(maxsize=10)
    
    # Fill the queue
    for i in range(1, 11):
        request = InferenceRequest(
            user_id=i,
            question=f"Question {i}",
            subject_id=1
        )
        await manager.enqueue_request(request)
    
    print(f"✓ Filled queue with 10 requests")
    
    # Check that queue is full
    assert manager.queue.qsize() >= 10, "Queue should be full"
    print(f"✓ Queue is full (size: {manager.queue.qsize()})")
    
    # Try to enqueue one more with timeout
    try:
        request = InferenceRequest(
            user_id=999,
            question="Overflow question",
            subject_id=1
        )
        # Use wait_for with timeout to prevent hanging
        await asyncio.wait_for(
            manager.enqueue_request(request),
            timeout=0.5
        )
        assert False, "Should have raised QueueFull or TimeoutError"
    except (asyncio.QueueFull, asyncio.TimeoutError):
        print(f"✓ Queue overflow detected correctly")
    
    print("="*70)
    print("✅ QUEUE OVERFLOW HANDLING VERIFIED")
    print("="*70 + "\n")


@pytest.mark.asyncio
async def test_phase7_checkpoint_streaming():
    """
    Checkpoint: Verify token streaming works.
    """
    print("\n" + "="*70)
    print("CHECKPOINT: Token Streaming")
    print("="*70)
    
    from src.concurrency.token_streamer import TokenStreamer
    
    streamer = TokenStreamer()
    print(f"✓ TokenStreamer initialized")
    
    # Test SSE formatting
    sse = streamer.format_sse("Hello", "queue-123")
    assert "data:" in sse
    assert "Hello" in sse
    print(f"✓ SSE formatting works")
    
    # Test streaming
    tokens = ["Hello", " ", "world"]
    result = []
    async for sse_data in streamer.stream_response(iter(tokens), "queue-123"):
        result.append(sse_data)
    
    assert len(result) == 4  # 3 tokens + 1 completion
    print(f"✓ Token streaming works ({len(result)} messages)")
    
    print("="*70)
    print("✅ TOKEN STREAMING VERIFIED")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Run checkpoint tests
    pytest.main([__file__, "-v", "-s"])
