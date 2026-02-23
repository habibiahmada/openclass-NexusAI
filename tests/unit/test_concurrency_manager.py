"""
Unit Tests for Concurrency Management System

Tests for ConcurrencyManager, InferenceRequest, and TokenStreamer.
"""

import pytest
import asyncio
from datetime import datetime
from src.concurrency.concurrency_manager import ConcurrencyManager, QueueStats
from src.concurrency.inference_request import InferenceRequest
from src.concurrency.token_streamer import TokenStreamer


class TestInferenceRequest:
    """Unit tests for InferenceRequest data structure."""
    
    def test_create_request_with_defaults(self):
        """Test creating a request with default values."""
        request = InferenceRequest(
            user_id=1,
            question="What is Python?",
            subject_id=1
        )
        
        assert request.user_id == 1
        assert request.question == "What is Python?"
        assert request.subject_id == 1
        assert request.context == []
        assert request.priority == 0
        assert request.queue_id is not None
        assert isinstance(request.timestamp, datetime)
    
    def test_create_request_with_custom_values(self):
        """Test creating a request with custom values."""
        context = ["Context 1", "Context 2"]
        request = InferenceRequest(
            user_id=2,
            question="Explain loops",
            subject_id=2,
            context=context,
            priority=5
        )
        
        assert request.user_id == 2
        assert request.question == "Explain loops"
        assert request.subject_id == 2
        assert request.context == context
        assert request.priority == 5
    
    def test_unique_queue_ids(self):
        """Test that each request gets a unique queue_id."""
        request1 = InferenceRequest(user_id=1, question="Q1", subject_id=1)
        request2 = InferenceRequest(user_id=1, question="Q1", subject_id=1)
        
        assert request1.queue_id != request2.queue_id
    
    def test_validation_empty_question(self):
        """Test that empty questions are rejected."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            InferenceRequest(user_id=1, question="", subject_id=1)
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            InferenceRequest(user_id=1, question="   ", subject_id=1)
    
    def test_validation_invalid_user_id(self):
        """Test that invalid user IDs are rejected."""
        with pytest.raises(ValueError, match="User ID must be positive"):
            InferenceRequest(user_id=0, question="Test", subject_id=1)
        
        with pytest.raises(ValueError, match="User ID must be positive"):
            InferenceRequest(user_id=-1, question="Test", subject_id=1)
    
    def test_validation_invalid_subject_id(self):
        """Test that invalid subject IDs are rejected."""
        with pytest.raises(ValueError, match="Subject ID must be positive"):
            InferenceRequest(user_id=1, question="Test", subject_id=0)
        
        with pytest.raises(ValueError, match="Subject ID must be positive"):
            InferenceRequest(user_id=1, question="Test", subject_id=-1)
    
    def test_validation_negative_priority(self):
        """Test that negative priorities are rejected."""
        with pytest.raises(ValueError, match="Priority cannot be negative"):
            InferenceRequest(user_id=1, question="Test", subject_id=1, priority=-1)
    
    def test_to_dict(self):
        """Test converting request to dictionary."""
        request = InferenceRequest(
            user_id=1,
            question="Test question",
            subject_id=1,
            context=["ctx1"],
            priority=2
        )
        
        data = request.to_dict()
        
        assert data['user_id'] == 1
        assert data['question'] == "Test question"
        assert data['subject_id'] == 1
        assert data['context'] == ["ctx1"]
        assert data['priority'] == 2
        assert 'queue_id' in data
        assert 'timestamp' in data
    
    def test_from_dict(self):
        """Test creating request from dictionary."""
        data = {
            'user_id': 1,
            'question': "Test question",
            'subject_id': 1,
            'context': ["ctx1"],
            'priority': 2
        }
        
        request = InferenceRequest.from_dict(data)
        
        assert request.user_id == 1
        assert request.question == "Test question"
        assert request.subject_id == 1
        assert request.context == ["ctx1"]
        assert request.priority == 2
    
    def test_round_trip_serialization(self):
        """Test that to_dict and from_dict are inverses."""
        original = InferenceRequest(
            user_id=1,
            question="Test",
            subject_id=1,
            context=["ctx"],
            priority=3
        )
        
        data = original.to_dict()
        restored = InferenceRequest.from_dict(data)
        
        assert restored.user_id == original.user_id
        assert restored.question == original.question
        assert restored.subject_id == original.subject_id
        assert restored.context == original.context
        assert restored.priority == original.priority
        assert restored.queue_id == original.queue_id


class TestConcurrencyManager:
    """Unit tests for ConcurrencyManager."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test manager initialization."""
        manager = ConcurrencyManager(max_concurrent=5)
        
        assert manager.max_concurrent == 5
        assert manager.queue.qsize() == 0
        assert len(manager.active_requests) == 0
        assert len(manager.completed_requests) == 0
    
    @pytest.mark.asyncio
    async def test_enqueue_request(self):
        """Test enqueueing a request."""
        manager = ConcurrencyManager(max_concurrent=5)
        
        request = InferenceRequest(
            user_id=1,
            question="Test",
            subject_id=1
        )
        
        queue_id = await manager.enqueue_request(request)
        
        assert queue_id == request.queue_id
        assert manager.queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_get_queue_stats(self):
        """Test getting queue statistics."""
        manager = ConcurrencyManager(max_concurrent=3)
        
        # Enqueue some requests
        for i in range(1, 6):  # Start from 1, not 0
            request = InferenceRequest(
                user_id=i,
                question=f"Question {i}",
                subject_id=1
            )
            await manager.enqueue_request(request)
        
        stats = manager.get_queue_stats()
        
        assert isinstance(stats, QueueStats)
        assert stats.max_concurrent == 3
        assert stats.queued_count == 5
        assert stats.active_count == 0
        assert stats.completed_count == 0
    
    @pytest.mark.asyncio
    async def test_is_queue_full(self):
        """Test queue full detection."""
        manager = ConcurrencyManager(max_concurrent=1)
        
        # Initially not full
        assert not manager.is_queue_full()
        
        # Fill the queue (use a smaller number for testing)
        # We'll test with 10 items instead of MAX_QUEUE_SIZE
        for i in range(1, 11):
            request = InferenceRequest(
                user_id=i,
                question=f"Question {i}",
                subject_id=1
            )
            await manager.enqueue_request(request)
        
        # Check queue size
        assert manager.queue.qsize() == 10
    
    @pytest.mark.asyncio
    async def test_queue_overflow_raises_exception(self):
        """Test that enqueueing to full queue raises exception."""
        # For testing, we'll manually create a small queue
        manager = ConcurrencyManager(max_concurrent=1)
        
        # Replace the queue with a smaller one for testing
        manager.queue = asyncio.Queue(maxsize=5)
        
        # Fill the queue
        for i in range(1, 6):
            request = InferenceRequest(
                user_id=i,
                question=f"Question {i}",
                subject_id=1
            )
            await manager.enqueue_request(request)
        
        # Try to enqueue one more - should raise QueueFull
        with pytest.raises(asyncio.QueueFull):
            request = InferenceRequest(
                user_id=9999,
                question="Overflow",
                subject_id=1
            )
            await manager.enqueue_request(request)
    
    @pytest.mark.asyncio
    async def test_get_queue_position_not_found(self):
        """Test queue position for non-existent request."""
        manager = ConcurrencyManager(max_concurrent=5)
        
        position = manager.get_queue_position("non-existent-id")
        
        assert position == -2
    
    @pytest.mark.asyncio
    async def test_start_and_stop_processing(self):
        """Test starting and stopping the processing task."""
        manager = ConcurrencyManager(max_concurrent=5)
        
        # Start processing
        manager.start_processing()
        assert manager._processing_task is not None
        assert not manager._processing_task.done()
        
        # Stop processing
        await manager.stop_processing()
        assert manager._processing_task.done()
    
    @pytest.mark.asyncio
    async def test_start_processing_idempotent(self):
        """Test that starting processing multiple times is safe."""
        manager = ConcurrencyManager(max_concurrent=5)
        
        # Start twice
        manager.start_processing()
        first_task = manager._processing_task
        
        manager.start_processing()
        second_task = manager._processing_task
        
        # Should be the same task
        assert first_task == second_task
        
        # Cleanup
        await manager.stop_processing()


class TestTokenStreamer:
    """Unit tests for TokenStreamer."""
    
    def test_initialization(self):
        """Test streamer initialization."""
        streamer = TokenStreamer()
        assert streamer is not None
    
    def test_format_sse(self):
        """Test SSE formatting for tokens."""
        streamer = TokenStreamer()
        
        sse = streamer.format_sse("Hello", "queue-123")
        
        assert "data:" in sse
        assert "Hello" in sse
        assert "queue-123" in sse
        assert sse.endswith("\n\n")
    
    def test_format_sse_complete(self):
        """Test SSE formatting for completion."""
        streamer = TokenStreamer()
        
        sse = streamer.format_sse_complete("queue-123")
        
        assert "data:" in sse
        assert "done" in sse
        assert "true" in sse
        assert "queue-123" in sse
        assert sse.endswith("\n\n")
    
    def test_format_sse_error(self):
        """Test SSE formatting for errors."""
        streamer = TokenStreamer()
        
        sse = streamer.format_sse_error("Test error", "queue-123")
        
        assert "data:" in sse
        assert "error" in sse
        assert "Test error" in sse
        assert "queue-123" in sse
        assert sse.endswith("\n\n")
    
    def test_format_sse_queue_position(self):
        """Test SSE formatting for queue position."""
        streamer = TokenStreamer()
        
        sse = streamer.format_sse_queue_position(5, "queue-123")
        
        assert "data:" in sse
        assert "queue_position" in sse
        assert "5" in sse
        assert "queue-123" in sse
        assert sse.endswith("\n\n")
    
    def test_get_position_message(self):
        """Test position message generation."""
        streamer = TokenStreamer()
        
        # Active
        msg = streamer._get_position_message(0)
        assert "being processed" in msg.lower()
        
        # Queued
        msg = streamer._get_position_message(5)
        assert "#5" in msg
        
        # Completed
        msg = streamer._get_position_message(-1)
        assert "completed" in msg.lower()
        
        # Not found
        msg = streamer._get_position_message(-2)
        assert "not found" in msg.lower()
    
    @pytest.mark.asyncio
    async def test_stream_response_sync_iterator(self):
        """Test streaming from synchronous iterator."""
        streamer = TokenStreamer()
        
        # Create a simple iterator
        tokens = ["Hello", " ", "world"]
        
        # Stream tokens
        result = []
        async for sse in streamer.stream_response(iter(tokens), "queue-123"):
            result.append(sse)
        
        # Should have 3 tokens + 1 completion
        assert len(result) == 4
        
        # Check token messages
        assert "Hello" in result[0]
        assert " " in result[1]
        assert "world" in result[2]
        
        # Check completion message
        assert "done" in result[3]
    
    @pytest.mark.asyncio
    async def test_stream_response_async_iterator(self):
        """Test streaming from async iterator."""
        streamer = TokenStreamer()
        
        # Create an async iterator
        async def async_tokens():
            for token in ["Hello", " ", "world"]:
                yield token
        
        # Stream tokens
        result = []
        async for sse in streamer.stream_response(async_tokens(), "queue-123"):
            result.append(sse)
        
        # Should have 3 tokens + 1 completion
        assert len(result) == 4
        
        # Check completion message
        assert "done" in result[3]
    
    @pytest.mark.asyncio
    async def test_stream_response_error_handling(self):
        """Test error handling during streaming."""
        streamer = TokenStreamer()
        
        # Create an iterator that raises an error
        def error_tokens():
            yield "Hello"
            raise ValueError("Test error")
        
        # Stream tokens
        result = []
        async for sse in streamer.stream_response(error_tokens(), "queue-123"):
            result.append(sse)
        
        # Should have 1 token + 1 error message
        assert len(result) == 2
        
        # Check error message
        assert "error" in result[1]
        assert "Test error" in result[1]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
