"""
Integration Test for API Concurrency Management

This test verifies that the concurrency manager is properly integrated
with the API endpoints and works end-to-end.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.concurrency.concurrency_manager import ConcurrencyManager
from src.concurrency.inference_request import InferenceRequest
from src.concurrency.token_streamer import TokenStreamer


class TestAPIConcurrencyIntegration:
    """Integration tests for API concurrency management."""
    
    @pytest.mark.asyncio
    async def test_concurrency_manager_initialization(self):
        """Test that ConcurrencyManager can be initialized for API use."""
        manager = ConcurrencyManager(max_concurrent=5)
        
        assert manager.max_concurrent == 5
        assert manager.queue.maxsize == 1000
        assert len(manager.active_requests) == 0
        assert len(manager.completed_requests) == 0
    
    @pytest.mark.asyncio
    async def test_inference_request_creation_from_api_data(self):
        """Test creating InferenceRequest from API request data."""
        # Simulate API request data
        user_id = 123
        question = "Apa itu algoritma?"
        subject_id = 1
        
        # Create inference request
        request = InferenceRequest(
            user_id=user_id,
            question=question,
            subject_id=subject_id,
            context=[]
        )
        
        assert request.user_id == user_id
        assert request.question == question
        assert request.subject_id == subject_id
        assert request.queue_id is not None
        assert len(request.queue_id) > 0
    
    @pytest.mark.asyncio
    async def test_enqueue_and_process_workflow(self):
        """Test the complete enqueue and process workflow."""
        manager = ConcurrencyManager(max_concurrent=2)
        
        # Create requests
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
        for req in requests:
            queue_id = await manager.enqueue_request(req)
            queue_ids.append(queue_id)
        
        # Verify all enqueued
        assert len(queue_ids) == 3
        assert manager.queue.qsize() == 3
        
        # Start processing
        manager.start_processing()
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Verify some completed
        stats = manager.get_queue_stats()
        assert stats.completed_count > 0
        
        # Stop processing
        await manager.stop_processing()
    
    @pytest.mark.asyncio
    async def test_queue_overflow_scenario(self):
        """Test queue overflow handling."""
        manager = ConcurrencyManager(max_concurrent=1)
        
        # Replace queue with smaller one
        manager.queue = asyncio.Queue(maxsize=5)
        
        # Fill the queue
        for i in range(1, 6):
            request = InferenceRequest(
                user_id=i,
                question=f"Question {i}",
                subject_id=1
            )
            await manager.enqueue_request(request)
        
        # Verify queue is full
        assert manager.is_queue_full()
        
        # Try to enqueue one more - should raise
        with pytest.raises(asyncio.QueueFull):
            request = InferenceRequest(
                user_id=999,
                question="Overflow",
                subject_id=1
            )
            await manager.enqueue_request(request)
    
    @pytest.mark.asyncio
    async def test_queue_position_tracking_workflow(self):
        """Test queue position tracking throughout request lifecycle."""
        manager = ConcurrencyManager(max_concurrent=1)
        
        # Create and enqueue request
        request = InferenceRequest(
            user_id=1,
            question="Test question",
            subject_id=1
        )
        
        queue_id = await manager.enqueue_request(request)
        
        # Initially should be queued (position > 0)
        initial_position = manager.get_queue_position(queue_id)
        assert initial_position > 0
        
        # Start processing
        manager.start_processing()
        
        # Wait for it to become active
        await asyncio.sleep(0.1)
        
        # Should be active (position 0) or completed (position -1)
        active_position = manager.get_queue_position(queue_id)
        assert active_position in [0, -1]
        
        # Wait for completion
        await asyncio.sleep(0.3)
        
        # Should be completed (position -1)
        final_position = manager.get_queue_position(queue_id)
        assert final_position == -1
        
        # Stop processing
        await manager.stop_processing()
    
    @pytest.mark.asyncio
    async def test_token_streamer_sse_formatting(self):
        """Test TokenStreamer SSE formatting for API responses."""
        streamer = TokenStreamer()
        
        # Test token formatting
        token_sse = streamer.format_sse("Hello", "queue-123")
        assert "data:" in token_sse
        assert "Hello" in token_sse
        assert token_sse.endswith("\n\n")
        
        # Test completion formatting
        complete_sse = streamer.format_sse_complete("queue-123")
        assert "data:" in complete_sse
        assert "done" in complete_sse
        
        # Test queue position formatting
        position_sse = streamer.format_sse_queue_position(5, "queue-123")
        assert "data:" in position_sse
        assert "queue_position" in position_sse
        assert "5" in position_sse
    
    @pytest.mark.asyncio
    async def test_concurrent_limit_enforcement(self):
        """Test that concurrent limit is enforced."""
        manager = ConcurrencyManager(max_concurrent=3)
        
        # Create many requests
        requests = [
            InferenceRequest(
                user_id=i,
                question=f"Question {i}",
                subject_id=1
            )
            for i in range(1, 11)
        ]
        
        # Enqueue all
        for req in requests:
            await manager.enqueue_request(req)
        
        # Start processing
        manager.start_processing()
        
        # Wait a bit
        await asyncio.sleep(0.2)
        
        # Check that active count never exceeds max_concurrent
        stats = manager.get_queue_stats()
        assert stats.active_count <= 3
        
        # Stop processing
        await manager.stop_processing()
    
    @pytest.mark.asyncio
    async def test_queue_stats_accuracy(self):
        """Test that queue statistics are accurate."""
        manager = ConcurrencyManager(max_concurrent=2)
        
        # Initial stats
        stats = manager.get_queue_stats()
        assert stats.active_count == 0
        assert stats.queued_count == 0
        assert stats.completed_count == 0
        assert stats.max_concurrent == 2
        
        # Enqueue some requests
        for i in range(1, 6):
            request = InferenceRequest(
                user_id=i,
                question=f"Question {i}",
                subject_id=1
            )
            await manager.enqueue_request(request)
        
        # Check queued count
        stats = manager.get_queue_stats()
        assert stats.queued_count == 5
        
        # Start processing
        manager.start_processing()
        await asyncio.sleep(0.5)
        
        # Check that some completed
        stats = manager.get_queue_stats()
        assert stats.completed_count > 0
        
        # Stop processing
        await manager.stop_processing()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
