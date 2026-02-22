"""
TokenStreamer - Handles streaming of LLM tokens to clients.

This module provides async token streaming with Server-Sent Events (SSE) formatting
for real-time response delivery to clients.
"""

import asyncio
import json
import logging
from typing import AsyncIterator, Iterator, Union

logger = logging.getLogger(__name__)


class TokenStreamer:
    """
    Streams LLM tokens to clients using Server-Sent Events (SSE) format.
    
    Handles token streaming with proper SSE formatting and error handling.
    """
    
    def __init__(self):
        """Initialize the token streamer."""
        self.logger = logger
    
    async def stream_response(
        self, 
        llm_output: Union[Iterator[str], AsyncIterator[str]],
        queue_id: str
    ) -> AsyncIterator[str]:
        """
        Stream LLM tokens as Server-Sent Events.
        
        Args:
            llm_output: Iterator or async iterator of token strings from LLM
            queue_id: Unique identifier for this request
            
        Yields:
            SSE-formatted strings containing tokens
            
        Example SSE format:
            data: {"token": "Hello", "queue_id": "abc123"}
            
            data: {"token": " world", "queue_id": "abc123"}
            
            data: {"done": true, "queue_id": "abc123"}
        """
        try:
            self.logger.info(f"Starting token stream for request {queue_id}")
            
            # Check if the output is an async iterator
            if hasattr(llm_output, '__aiter__'):
                async for token in llm_output:
                    yield self.format_sse(token, queue_id)
            else:
                # Synchronous iterator - convert to async
                for token in llm_output:
                    yield self.format_sse(token, queue_id)
                    # Small delay to prevent blocking
                    await asyncio.sleep(0)
            
            # Send completion message
            yield self.format_sse_complete(queue_id)
            self.logger.info(f"Completed token stream for request {queue_id}")
            
        except Exception as e:
            self.logger.error(f"Error streaming tokens for {queue_id}: {e}", exc_info=True)
            yield self.format_sse_error(str(e), queue_id)
    
    def format_sse(self, token: str, queue_id: str) -> str:
        """
        Format a token as a Server-Sent Event.
        
        Args:
            token: The token string to send
            queue_id: Unique identifier for this request
            
        Returns:
            SSE-formatted string
        """
        data = {
            'token': token,
            'queue_id': queue_id
        }
        return f"data: {json.dumps(data)}\n\n"
    
    def format_sse_complete(self, queue_id: str) -> str:
        """
        Format a completion message as SSE.
        
        Args:
            queue_id: Unique identifier for this request
            
        Returns:
            SSE-formatted completion message
        """
        data = {
            'done': True,
            'queue_id': queue_id
        }
        return f"data: {json.dumps(data)}\n\n"
    
    def format_sse_error(self, error_message: str, queue_id: str) -> str:
        """
        Format an error message as SSE.
        
        Args:
            error_message: The error message to send
            queue_id: Unique identifier for this request
            
        Returns:
            SSE-formatted error message
        """
        data = {
            'error': error_message,
            'queue_id': queue_id
        }
        return f"data: {json.dumps(data)}\n\n"
    
    def format_sse_queue_position(self, position: int, queue_id: str) -> str:
        """
        Format a queue position update as SSE.
        
        Args:
            position: Current position in queue
            queue_id: Unique identifier for this request
            
        Returns:
            SSE-formatted queue position message
        """
        data = {
            'queue_position': position,
            'queue_id': queue_id,
            'message': self._get_position_message(position)
        }
        return f"data: {json.dumps(data)}\n\n"
    
    def _get_position_message(self, position: int) -> str:
        """
        Get a user-friendly message for the queue position.
        
        Args:
            position: Current position in queue
            
        Returns:
            User-friendly message
        """
        if position == 0:
            return "Your request is being processed..."
        elif position == -1:
            return "Request completed"
        elif position == -2:
            return "Request not found"
        else:
            return f"You are #{position} in the queue"
    
    async def stream_with_queue_updates(
        self,
        llm_output: Union[Iterator[str], AsyncIterator[str]],
        queue_id: str,
        get_position_func,
        update_interval: float = 2.0
    ) -> AsyncIterator[str]:
        """
        Stream tokens with periodic queue position updates.
        
        This is useful for long-running requests where the user should
        be kept informed of their position in the queue.
        
        Args:
            llm_output: Iterator or async iterator of token strings
            queue_id: Unique identifier for this request
            get_position_func: Function to get current queue position
            update_interval: Seconds between position updates
            
        Yields:
            SSE-formatted strings with tokens and position updates
        """
        try:
            # Send initial position
            position = get_position_func(queue_id)
            yield self.format_sse_queue_position(position, queue_id)
            
            # Stream tokens
            async for sse_data in self.stream_response(llm_output, queue_id):
                yield sse_data
                
        except Exception as e:
            self.logger.error(f"Error in stream_with_queue_updates: {e}", exc_info=True)
            yield self.format_sse_error(str(e), queue_id)
