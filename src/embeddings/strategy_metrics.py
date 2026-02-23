"""
Performance metrics tracking for embedding strategies.
Tracks calls, timing, and errors for monitoring and optimization.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import time


@dataclass
class StrategyMetrics:
    """Performance metrics for an embedding strategy"""
    
    total_calls: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    def record_call(self, duration_ms: float):
        """Record a successful call.
        
        Args:
            duration_ms: Duration of the call in milliseconds
        """
        self.total_calls += 1
        self.total_time_ms += duration_ms
        self.avg_time_ms = self.total_time_ms / self.total_calls
    
    def record_error(self, error_message: str):
        """Record an error.
        
        Args:
            error_message: Error message to record
        """
        self.error_count += 1
        self.last_error = error_message
        self.last_error_time = datetime.now()
    
    def reset(self):
        """Reset all metrics to zero"""
        self.total_calls = 0
        self.total_time_ms = 0.0
        self.avg_time_ms = 0.0
        self.error_count = 0
        self.last_error = None
        self.last_error_time = None
    
    def to_dict(self) -> dict:
        """Convert metrics to dictionary.
        
        Returns:
            Dictionary representation of metrics
        """
        return {
            'total_calls': self.total_calls,
            'total_time_ms': self.total_time_ms,
            'avg_time_ms': self.avg_time_ms,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None
        }


class MetricsTracker:
    """Context manager for tracking metrics of operations"""
    
    def __init__(self, metrics: StrategyMetrics):
        """Initialize metrics tracker.
        
        Args:
            metrics: StrategyMetrics instance to update
        """
        self.metrics = metrics
        self.start_time = None
    
    def __enter__(self):
        """Start timing"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Record timing and errors"""
        duration_ms = (time.time() - self.start_time) * 1000
        
        if exc_type is None:
            # Success
            self.metrics.record_call(duration_ms)
        else:
            # Error
            self.metrics.record_error(str(exc_val))
        
        # Don't suppress exceptions
        return False
