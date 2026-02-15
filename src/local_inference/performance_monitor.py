"""
Performance monitoring and metrics tracking for OpenClass Nexus AI Phase 3.

This module provides comprehensive performance tracking for the local inference
system, including response time monitoring, memory and CPU usage tracking,
and performance target validation optimized for 4GB RAM systems.
"""

import time
import psutil
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque
from pathlib import Path
import json


logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """
    Comprehensive performance metrics for inference operations.
    
    This class tracks all performance-related data as specified in the
    design document, including response times, resource usage, and
    performance target validation.
    """
    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    tokens_per_second: float
    context_tokens: int
    response_tokens: int
    timestamp: datetime
    
    # Additional metrics for comprehensive tracking
    memory_peak_mb: float = 0.0
    cpu_peak_percent: float = 0.0
    query_length: int = 0
    model_load_time_ms: float = 0.0
    context_processing_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    
    def is_within_targets(self) -> bool:
        """
        Check if metrics meet performance targets for 4GB RAM systems.
        
        Performance targets from requirements:
        - Response time < 10 seconds (10,000ms)
        - Memory usage < 3GB (3072MB)
        - Tokens per second > 5
        
        Returns:
            bool: True if all targets are met
        """
        return (
            self.response_time_ms < 10000 and  # < 10 seconds
            self.memory_usage_mb < 3072 and    # < 3GB
            self.tokens_per_second > 5         # > 5 tokens/sec
        )
    
    def get_performance_grade(self) -> str:
        """
        Get performance grade based on metrics.
        
        Returns:
            str: Performance grade (Excellent, Good, Fair, Poor)
        """
        if (self.response_time_ms < 5000 and 
            self.memory_usage_mb < 2048 and 
            self.tokens_per_second > 10):
            return "Excellent"
        elif (self.response_time_ms < 7500 and 
              self.memory_usage_mb < 2560 and 
              self.tokens_per_second > 7):
            return "Good"
        elif self.is_within_targets():
            return "Fair"
        else:
            return "Poor"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            'response_time_ms': self.response_time_ms,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'tokens_per_second': self.tokens_per_second,
            'context_tokens': self.context_tokens,
            'response_tokens': self.response_tokens,
            'timestamp': self.timestamp.isoformat(),
            'memory_peak_mb': self.memory_peak_mb,
            'cpu_peak_percent': self.cpu_peak_percent,
            'query_length': self.query_length,
            'model_load_time_ms': self.model_load_time_ms,
            'context_processing_time_ms': self.context_processing_time_ms,
            'generation_time_ms': self.generation_time_ms,
            'within_targets': self.is_within_targets(),
            'performance_grade': self.get_performance_grade()
        }


@dataclass
class PerformanceTargets:
    """Performance targets for the inference system."""
    max_response_time_ms: float = 10000  # 10 seconds
    max_memory_usage_mb: float = 3072    # 3GB
    min_tokens_per_second: float = 5     # 5 tokens/sec
    max_cpu_usage_percent: float = 90    # 90% CPU
    max_model_load_time_ms: float = 30000  # 30 seconds


class PerformanceTracker:
    """
    Performance tracking system for monitoring inference operations.
    
    This tracker provides:
    - Real-time performance monitoring
    - Historical performance data
    - Performance target validation
    - Automatic performance reporting
    - Resource usage optimization recommendations
    """
    
    def __init__(self, 
                 targets: Optional[PerformanceTargets] = None,
                 max_history_size: int = 1000,
                 enable_continuous_monitoring: bool = True):
        """
        Initialize performance tracker.
        
        Args:
            targets: Performance targets to validate against
            max_history_size: Maximum number of metrics to keep in history
            enable_continuous_monitoring: Enable background resource monitoring
        """
        self.targets = targets or PerformanceTargets()
        self.max_history_size = max_history_size
        self.enable_continuous_monitoring = enable_continuous_monitoring
        
        # Performance history storage
        self.metrics_history: deque[PerformanceMetrics] = deque(maxlen=max_history_size)
        self.session_start_time = datetime.now()
        
        # Resource monitoring
        self.process = psutil.Process()
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self.resource_samples: deque[Dict[str, float]] = deque(maxlen=100)
        
        # Performance callbacks
        self.performance_callbacks: List[Callable[[PerformanceMetrics], None]] = []
        
        logger.info(f"PerformanceTracker initialized with targets: {self.targets}")
        
        if enable_continuous_monitoring:
            self.start_continuous_monitoring()
    
    def start_continuous_monitoring(self) -> None:
        """Start background resource monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._continuous_monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Started continuous performance monitoring")
    
    def stop_continuous_monitoring(self) -> None:
        """Stop background resource monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        logger.info("Stopped continuous performance monitoring")
    
    def _continuous_monitoring_loop(self) -> None:
        """Background monitoring loop for resource usage."""
        while self.monitoring_active:
            try:
                # Sample current resource usage
                memory_mb = self.process.memory_info().rss / (1024 * 1024)
                cpu_percent = self.process.cpu_percent()
                
                sample = {
                    'timestamp': datetime.now(),
                    'memory_mb': memory_mb,
                    'cpu_percent': cpu_percent
                }
                
                self.resource_samples.append(sample)
                
                # Sleep for 1 second between samples
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                time.sleep(5.0)  # Wait longer on error
    
    def record_metrics(self, metrics: PerformanceMetrics) -> None:
        """
        Record performance metrics.
        
        Args:
            metrics: Performance metrics to record
        """
        # Add to history
        self.metrics_history.append(metrics)
        
        # Log performance information
        grade = metrics.get_performance_grade()
        within_targets = metrics.is_within_targets()
        
        logger.info(f"Performance recorded: {grade} grade, "
                   f"targets met: {within_targets}")
        logger.debug(f"Metrics: {metrics.response_time_ms:.1f}ms, "
                    f"{metrics.memory_usage_mb:.1f}MB, "
                    f"{metrics.tokens_per_second:.1f} tok/s")
        
        # Trigger callbacks
        for callback in self.performance_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Error in performance callback: {e}")
        
        # Check for performance issues
        self._check_performance_issues(metrics)
    
    def _check_performance_issues(self, metrics: PerformanceMetrics) -> None:
        """Check for performance issues and log warnings."""
        issues = []
        
        if metrics.response_time_ms > self.targets.max_response_time_ms:
            issues.append(f"Slow response: {metrics.response_time_ms:.1f}ms > {self.targets.max_response_time_ms}ms")
        
        if metrics.memory_usage_mb > self.targets.max_memory_usage_mb:
            issues.append(f"High memory usage: {metrics.memory_usage_mb:.1f}MB > {self.targets.max_memory_usage_mb}MB")
        
        if metrics.tokens_per_second < self.targets.min_tokens_per_second:
            issues.append(f"Low token rate: {metrics.tokens_per_second:.1f} < {self.targets.min_tokens_per_second}")
        
        if metrics.cpu_usage_percent > self.targets.max_cpu_usage_percent:
            issues.append(f"High CPU usage: {metrics.cpu_usage_percent:.1f}% > {self.targets.max_cpu_usage_percent}%")
        
        if issues:
            logger.warning(f"Performance issues detected: {'; '.join(issues)}")
    
    def get_current_resource_usage(self) -> Dict[str, float]:
        """
        Get current resource usage.
        
        Returns:
            Dict with current memory and CPU usage
        """
        try:
            memory_mb = self.process.memory_info().rss / (1024 * 1024)
            cpu_percent = self.process.cpu_percent()
            
            return {
                'memory_mb': memory_mb,
                'cpu_percent': cpu_percent,
                'timestamp': datetime.now().timestamp()
            }
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {'memory_mb': 0.0, 'cpu_percent': 0.0, 'timestamp': 0.0}
    
    def get_performance_summary(self, 
                              last_n_operations: Optional[int] = None) -> Dict[str, Any]:
        """
        Get performance summary statistics.
        
        Args:
            last_n_operations: Number of recent operations to analyze (None for all)
            
        Returns:
            Dict with performance summary
        """
        if not self.metrics_history:
            return {'error': 'No performance data available'}
        
        # Get metrics to analyze
        if last_n_operations:
            metrics_to_analyze = list(self.metrics_history)[-last_n_operations:]
        else:
            metrics_to_analyze = list(self.metrics_history)
        
        if not metrics_to_analyze:
            return {'error': 'No metrics to analyze'}
        
        # Calculate statistics
        response_times = [m.response_time_ms for m in metrics_to_analyze]
        memory_usage = [m.memory_usage_mb for m in metrics_to_analyze]
        token_rates = [m.tokens_per_second for m in metrics_to_analyze]
        cpu_usage = [m.cpu_usage_percent for m in metrics_to_analyze]
        
        # Count performance grades
        grades = [m.get_performance_grade() for m in metrics_to_analyze]
        grade_counts = {grade: grades.count(grade) for grade in set(grades)}
        
        # Count target compliance
        within_targets = sum(1 for m in metrics_to_analyze if m.is_within_targets())
        target_compliance_rate = within_targets / len(metrics_to_analyze) * 100
        
        return {
            'total_operations': len(metrics_to_analyze),
            'session_duration_minutes': (datetime.now() - self.session_start_time).total_seconds() / 60,
            'response_time': {
                'avg_ms': sum(response_times) / len(response_times),
                'min_ms': min(response_times),
                'max_ms': max(response_times),
                'target_ms': self.targets.max_response_time_ms
            },
            'memory_usage': {
                'avg_mb': sum(memory_usage) / len(memory_usage),
                'min_mb': min(memory_usage),
                'max_mb': max(memory_usage),
                'target_mb': self.targets.max_memory_usage_mb
            },
            'token_rate': {
                'avg_tokens_per_sec': sum(token_rates) / len(token_rates),
                'min_tokens_per_sec': min(token_rates),
                'max_tokens_per_sec': max(token_rates),
                'target_tokens_per_sec': self.targets.min_tokens_per_second
            },
            'cpu_usage': {
                'avg_percent': sum(cpu_usage) / len(cpu_usage),
                'min_percent': min(cpu_usage),
                'max_percent': max(cpu_usage),
                'target_percent': self.targets.max_cpu_usage_percent
            },
            'performance_grades': grade_counts,
            'target_compliance_rate': target_compliance_rate,
            'targets': {
                'max_response_time_ms': self.targets.max_response_time_ms,
                'max_memory_usage_mb': self.targets.max_memory_usage_mb,
                'min_tokens_per_second': self.targets.min_tokens_per_second,
                'max_cpu_usage_percent': self.targets.max_cpu_usage_percent
            }
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """
        Get performance optimization recommendations based on metrics history.
        
        Returns:
            List of optimization recommendations
        """
        if not self.metrics_history:
            return ["No performance data available for recommendations"]
        
        recommendations = []
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 operations
        
        # Analyze response times
        avg_response_time = sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics)
        if avg_response_time > 8000:  # 8 seconds
            recommendations.append("Consider reducing context window size to improve response times")
            recommendations.append("Consider using fewer threads if CPU is not fully utilized")
        
        # Analyze memory usage
        avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
        if avg_memory > 2500:  # 2.5GB
            recommendations.append("High memory usage detected - consider reducing batch size")
            recommendations.append("Consider implementing more aggressive garbage collection")
        
        # Analyze token rates
        avg_token_rate = sum(m.tokens_per_second for m in recent_metrics) / len(recent_metrics)
        if avg_token_rate < 7:
            recommendations.append("Low token generation rate - check CPU utilization")
            recommendations.append("Consider optimizing model quantization settings")
        
        # Analyze CPU usage
        avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)
        if avg_cpu < 50:
            recommendations.append("Low CPU utilization - consider increasing thread count")
        elif avg_cpu > 85:
            recommendations.append("High CPU utilization - consider reducing thread count")
        
        # Check target compliance
        compliance_rate = sum(1 for m in recent_metrics if m.is_within_targets()) / len(recent_metrics)
        if compliance_rate < 0.8:  # Less than 80% compliance
            recommendations.append("Performance targets not consistently met - review system configuration")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable ranges")
        
        return recommendations
    
    def register_performance_callback(self, callback: Callable[[PerformanceMetrics], None]) -> None:
        """
        Register a callback to be called when metrics are recorded.
        
        Args:
            callback: Function to call with performance metrics
        """
        self.performance_callbacks.append(callback)
        logger.debug(f"Registered performance callback: {callback.__name__}")
    
    def export_metrics(self, filepath: Path, format: str = 'json') -> None:
        """
        Export performance metrics to file.
        
        Args:
            filepath: Path to export file
            format: Export format ('json' or 'csv')
        """
        try:
            if format.lower() == 'json':
                data = {
                    'session_info': {
                        'start_time': self.session_start_time.isoformat(),
                        'export_time': datetime.now().isoformat(),
                        'total_operations': len(self.metrics_history)
                    },
                    'targets': {
                        'max_response_time_ms': self.targets.max_response_time_ms,
                        'max_memory_usage_mb': self.targets.max_memory_usage_mb,
                        'min_tokens_per_second': self.targets.min_tokens_per_second,
                        'max_cpu_usage_percent': self.targets.max_cpu_usage_percent
                    },
                    'metrics': [m.to_dict() for m in self.metrics_history]
                }
                
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            
            elif format.lower() == 'csv':
                import csv
                with open(filepath, 'w', newline='') as f:
                    if self.metrics_history:
                        writer = csv.DictWriter(f, fieldnames=self.metrics_history[0].to_dict().keys())
                        writer.writeheader()
                        for metrics in self.metrics_history:
                            writer.writerow(metrics.to_dict())
            
            logger.info(f"Exported {len(self.metrics_history)} metrics to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
    
    def __del__(self):
        """Cleanup when tracker is destroyed."""
        if self.monitoring_active:
            self.stop_continuous_monitoring()


# Context manager for performance tracking
class PerformanceContext:
    """Context manager for tracking performance of operations."""
    
    def __init__(self, 
                 tracker: PerformanceTracker,
                 operation_name: str = "inference",
                 query_length: int = 0):
        """
        Initialize performance context.
        
        Args:
            tracker: PerformanceTracker instance
            operation_name: Name of the operation being tracked
            query_length: Length of the input query
        """
        self.tracker = tracker
        self.operation_name = operation_name
        self.query_length = query_length
        
        self.start_time: Optional[datetime] = None
        self.start_memory: float = 0.0
        self.start_cpu: float = 0.0
        self.peak_memory: float = 0.0
        self.peak_cpu: float = 0.0
        
        self.context_tokens: int = 0
        self.response_tokens: int = 0
        self.model_load_time_ms: float = 0.0
        self.context_processing_time_ms: float = 0.0
    
    def __enter__(self):
        """Start performance tracking."""
        self.start_time = datetime.now()
        
        # Get initial resource usage
        resource_usage = self.tracker.get_current_resource_usage()
        self.start_memory = resource_usage['memory_mb']
        self.start_cpu = resource_usage['cpu_percent']
        self.peak_memory = self.start_memory
        self.peak_cpu = self.start_cpu
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End performance tracking and record metrics."""
        if self.start_time is None:
            return
        
        end_time = datetime.now()
        response_time_ms = (end_time - self.start_time).total_seconds() * 1000
        
        # Get final resource usage
        resource_usage = self.tracker.get_current_resource_usage()
        end_memory = resource_usage['memory_mb']
        end_cpu = resource_usage['cpu_percent']
        
        # Calculate tokens per second
        tokens_per_second = 0.0
        if response_time_ms > 0 and self.response_tokens > 0:
            tokens_per_second = self.response_tokens / (response_time_ms / 1000)
        
        # Create metrics
        metrics = PerformanceMetrics(
            response_time_ms=response_time_ms,
            memory_usage_mb=end_memory,
            cpu_usage_percent=end_cpu,
            tokens_per_second=tokens_per_second,
            context_tokens=self.context_tokens,
            response_tokens=self.response_tokens,
            timestamp=end_time,
            memory_peak_mb=self.peak_memory,
            cpu_peak_percent=self.peak_cpu,
            query_length=self.query_length,
            model_load_time_ms=self.model_load_time_ms,
            context_processing_time_ms=self.context_processing_time_ms,
            generation_time_ms=response_time_ms - self.context_processing_time_ms - self.model_load_time_ms
        )
        
        # Record metrics
        self.tracker.record_metrics(metrics)
    
    def update_token_counts(self, context_tokens: int, response_tokens: int) -> None:
        """Update token counts during operation."""
        self.context_tokens = context_tokens
        self.response_tokens = response_tokens
    
    def update_timing(self, 
                     model_load_time_ms: float = 0.0,
                     context_processing_time_ms: float = 0.0) -> None:
        """Update timing information during operation."""
        self.model_load_time_ms = model_load_time_ms
        self.context_processing_time_ms = context_processing_time_ms
    
    def sample_resources(self) -> None:
        """Sample current resource usage and update peaks."""
        resource_usage = self.tracker.get_current_resource_usage()
        self.peak_memory = max(self.peak_memory, resource_usage['memory_mb'])
        self.peak_cpu = max(self.peak_cpu, resource_usage['cpu_percent'])


# Utility functions
def create_performance_tracker(
    max_response_time_ms: float = 10000,
    max_memory_usage_mb: float = 3072,
    min_tokens_per_second: float = 5,
    max_cpu_usage_percent: float = 90
) -> PerformanceTracker:
    """
    Create a performance tracker with custom targets.
    
    Args:
        max_response_time_ms: Maximum acceptable response time
        max_memory_usage_mb: Maximum acceptable memory usage
        min_tokens_per_second: Minimum acceptable token generation rate
        max_cpu_usage_percent: Maximum acceptable CPU usage
        
    Returns:
        PerformanceTracker instance
    """
    targets = PerformanceTargets(
        max_response_time_ms=max_response_time_ms,
        max_memory_usage_mb=max_memory_usage_mb,
        min_tokens_per_second=min_tokens_per_second,
        max_cpu_usage_percent=max_cpu_usage_percent
    )
    
    return PerformanceTracker(targets=targets)