"""
InferenceRequest - Data structure for queued inference requests.

This module defines the data structure used to represent inference requests
in the concurrency queue.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class InferenceRequest:
    """
    Represents an inference request in the queue.
    
    Attributes:
        queue_id: Unique identifier for this request
        user_id: ID of the user making the request
        question: The question text to process
        subject_id: ID of the subject/topic
        context: List of context strings for RAG
        timestamp: When the request was created
        priority: Priority level (0 = normal, higher = more priority)
    """
    user_id: int
    question: str
    subject_id: int
    context: List[str] = field(default_factory=list)
    queue_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0
    
    def __post_init__(self):
        """Validate the request after initialization."""
        if not self.question or not self.question.strip():
            raise ValueError("Question cannot be empty")
        
        if self.user_id <= 0:
            raise ValueError("User ID must be positive")
        
        if self.subject_id <= 0:
            raise ValueError("Subject ID must be positive")
        
        if self.priority < 0:
            raise ValueError("Priority cannot be negative")
    
    def to_dict(self) -> dict:
        """
        Convert the request to a dictionary.
        
        Returns:
            Dictionary representation of the request
        """
        return {
            'queue_id': self.queue_id,
            'user_id': self.user_id,
            'question': self.question,
            'subject_id': self.subject_id,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'InferenceRequest':
        """
        Create an InferenceRequest from a dictionary.
        
        Args:
            data: Dictionary containing request data
            
        Returns:
            InferenceRequest instance
        """
        # Parse timestamp if it's a string
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            queue_id=data.get('queue_id', str(uuid.uuid4())),
            user_id=data['user_id'],
            question=data['question'],
            subject_id=data['subject_id'],
            context=data.get('context', []),
            timestamp=timestamp or datetime.now(),
            priority=data.get('priority', 0)
        )
