"""
Telemetry Collector Module

Collects local metrics for query performance, errors, and system usage.
Stores metrics in memory for aggregation and batch upload.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List
import threading


@dataclass
class MetricsSnapshot:
    """Snapshot of current metrics"""
    timestamp: datetime
    total_queries: int
    successful_queries: int
    failed_queries: int
    latencies: List[float]
    errors: List[Dict[str, str]]
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_queries': self.total_queries,
            'successful_queries': self.successful_queries,
            'failed_queries': self.failed_queries,
            'latencies': self.latencies,
            'errors': self.errors
        }


class TelemetryCollector:
    """
    Collects anonymized usage metrics locally.
    
    Metrics are stored in memory and periodically aggregated for upload.
    NO PII (chat content, user data, personal information) is collected.
    """
    
    def __init__(self):
        """Initialize telemetry collector"""
        self._lock = threading.Lock()
        self._total_queries = 0
        self._successful_queries = 0
        self._failed_queries = 0
        self._latencies: List[float] = []
        self._errors: List[Dict[str, str]] = []
    
    def record_query(self, latency: float, success: bool) -> None:
        """
        Record a query metric.
        
        Args:
            latency: Query latency in milliseconds
            success: Whether the query succeeded
        """
        with self._lock:
            self._total_queries += 1
            if success:
                self._successful_queries += 1
            else:
                self._failed_queries += 1
            self._latencies.append(latency)
    
    def record_error(self, error_type: str, error_message: str) -> None:
        """
        Record an error metric.
        
        Args:
            error_type: Type of error (e.g., "timeout", "oom", "model_error")
            error_message: Brief error description (NO PII)
        """
        with self._lock:
            self._errors.append({
                'type': error_type,
                'message': error_message,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
    
    def get_metrics_snapshot(self) -> MetricsSnapshot:
        """
        Get current metrics snapshot.
        
        Returns:
            MetricsSnapshot with current metrics
        """
        with self._lock:
            return MetricsSnapshot(
                timestamp=datetime.now(timezone.utc),
                total_queries=self._total_queries,
                successful_queries=self._successful_queries,
                failed_queries=self._failed_queries,
                latencies=self._latencies.copy(),
                errors=self._errors.copy()
            )
    
    def reset_metrics(self) -> None:
        """Reset all metrics to zero (called after successful upload)"""
        with self._lock:
            self._total_queries = 0
            self._successful_queries = 0
            self._failed_queries = 0
            self._latencies.clear()
            self._errors.clear()


# Global singleton instance
_collector_instance = None
_collector_lock = threading.Lock()


def get_collector() -> TelemetryCollector:
    """Get global telemetry collector instance"""
    global _collector_instance
    if _collector_instance is None:
        with _collector_lock:
            if _collector_instance is None:
                _collector_instance = TelemetryCollector()
    return _collector_instance
