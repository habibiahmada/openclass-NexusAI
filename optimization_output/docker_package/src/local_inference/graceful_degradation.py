"""
Graceful degradation system for OpenClass Nexus AI Phase 3.

This module provides automatic context window reduction and performance-based
configuration adjustment for 4GB RAM systems running Llama-3.2-3B-Instruct model.
Implements Requirements 5.4 and 8.3 for graceful degradation under resource constraints.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .resource_manager import MemoryMonitor, ThreadManager
from .performance_monitor import PerformanceTracker, PerformanceMetrics
from .model_config import InferenceConfig


logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    """Levels of system degradation based on resource constraints."""
    OPTIMAL = 0      # Full performance, no degradation
    LIGHT = 1        # Minor optimizations
    MODERATE = 2     # Noticeable performance reduction
    HEAVY = 3        # Significant performance reduction
    CRITICAL = 4     # Minimal functionality to prevent system failure


@dataclass
class DegradationConfig:
    """Configuration for graceful degradation thresholds and adjustments."""
    
    # Memory thresholds (MB)
    memory_optimal_threshold: float = 2048    # Below this: OPTIMAL
    memory_light_threshold: float = 2400      # Above this: LIGHT degradation
    memory_moderate_threshold: float = 2700   # Above this: MODERATE degradation
    memory_heavy_threshold: float = 2900      # Above this: HEAVY degradation
    memory_critical_threshold: float = 3000   # Above this: CRITICAL degradation
    
    # Response time thresholds (ms)
    response_time_optimal: float = 5000       # Below this: OPTIMAL
    response_time_light: float = 7500         # Above this: LIGHT degradation
    response_time_moderate: float = 10000     # Above this: MODERATE degradation
    response_time_heavy: float = 15000        # Above this: HEAVY degradation
    response_time_critical: float = 20000     # Above this: CRITICAL degradation
    
    # Token rate thresholds (tokens/sec)
    token_rate_optimal: float = 10            # Above this: OPTIMAL
    token_rate_light: float = 7               # Below this: LIGHT degradation
    token_rate_moderate: float = 5            # Below this: MODERATE degradation
    token_rate_heavy: float = 3               # Below this: HEAVY degradation
    token_rate_critical: float = 1            # Below this: CRITICAL degradation
    
    # Context window adjustments by degradation level
    context_window_adjustments: Dict[DegradationLevel, float] = field(default_factory=lambda: {
        DegradationLevel.OPTIMAL: 1.0,     # 100% of max context (3000 tokens)
        DegradationLevel.LIGHT: 0.8,       # 80% of max context (2400 tokens)
        DegradationLevel.MODERATE: 0.6,    # 60% of max context (1800 tokens)
        DegradationLevel.HEAVY: 0.4,       # 40% of max context (1200 tokens)
        DegradationLevel.CRITICAL: 0.2     # 20% of max context (600 tokens)
    })
    
    # Thread count adjustments by degradation level
    thread_adjustments: Dict[DegradationLevel, float] = field(default_factory=lambda: {
        DegradationLevel.OPTIMAL: 1.0,     # 100% of optimal threads
        DegradationLevel.LIGHT: 0.8,       # 80% of optimal threads
        DegradationLevel.MODERATE: 0.6,    # 60% of optimal threads
        DegradationLevel.HEAVY: 0.5,       # 50% of optimal threads
        DegradationLevel.CRITICAL: 0.25    # 25% of optimal threads (minimum 1)
    })
    
    # Batch size adjustments by degradation level
    batch_size_adjustments: Dict[DegradationLevel, float] = field(default_factory=lambda: {
        DegradationLevel.OPTIMAL: 1.0,     # Full batch processing
        DegradationLevel.LIGHT: 0.8,       # Slightly reduced batching
        DegradationLevel.MODERATE: 0.6,    # Moderate batch reduction
        DegradationLevel.HEAVY: 0.4,       # Heavy batch reduction
        DegradationLevel.CRITICAL: 0.2     # Minimal batching
    })


@dataclass
class DegradationState:
    """Current state of system degradation."""
    level: DegradationLevel
    reason: str
    timestamp: datetime
    memory_usage_mb: float
    cpu_usage_percent: float
    response_time_ms: float
    token_rate: float
    context_window_tokens: int
    thread_count: int
    batch_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for logging/serialization."""
        return {
            'level': self.level.name,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat(),
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'response_time_ms': self.response_time_ms,
            'token_rate': self.token_rate,
            'context_window_tokens': self.context_window_tokens,
            'thread_count': self.thread_count,
            'batch_size': self.batch_size
        }


class GracefulDegradationManager:
    """
    Manages graceful degradation of system performance under resource constraints.
    
    This manager provides:
    - Automatic detection of resource constraints
    - Progressive degradation of system capabilities
    - Performance-based configuration adjustment
    - Recovery when resources become available
    - Comprehensive logging and monitoring
    """
    
    def __init__(self,
                 memory_monitor: MemoryMonitor,
                 thread_manager: ThreadManager,
                 performance_tracker: Optional[PerformanceTracker] = None,
                 config: Optional[DegradationConfig] = None,
                 base_context_window: int = 3000,
                 base_thread_count: int = 4,
                 base_batch_size: int = 2):
        """
        Initialize graceful degradation manager.
        
        Args:
            memory_monitor: Memory monitoring system
            thread_manager: Thread management system
            performance_tracker: Performance tracking system
            config: Degradation configuration
            base_context_window: Base context window size in tokens
            base_thread_count: Base thread count
            base_batch_size: Base batch size for concurrent processing
        """
        self.memory_monitor = memory_monitor
        self.thread_manager = thread_manager
        self.performance_tracker = performance_tracker
        self.config = config or DegradationConfig()
        
        # Base configuration values
        self.base_context_window = base_context_window
        self.base_thread_count = base_thread_count
        self.base_batch_size = base_batch_size
        
        # Current state
        self.current_state = DegradationState(
            level=DegradationLevel.OPTIMAL,
            reason="System initialized",
            timestamp=datetime.now(),
            memory_usage_mb=0.0,
            cpu_usage_percent=0.0,
            response_time_ms=0.0,
            token_rate=0.0,
            context_window_tokens=base_context_window,
            thread_count=base_thread_count,
            batch_size=base_batch_size
        )
        
        # State history for trend analysis
        self.state_history: List[DegradationState] = []
        self.max_history_size = 100
        
        # Performance metrics for decision making
        self.recent_metrics: List[PerformanceMetrics] = []
        self.metrics_window_size = 10
        
        # Degradation change tracking
        self.last_degradation_change = datetime.now()
        self.min_change_interval_seconds = 30  # Prevent rapid oscillation
        
        logger.info(f"GracefulDegradationManager initialized with base config: "
                   f"context={base_context_window}, threads={base_thread_count}, "
                   f"batch_size={base_batch_size}")
    
    def update_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """
        Update performance metrics for degradation analysis.
        
        Args:
            metrics: Latest performance metrics
        """
        self.recent_metrics.append(metrics)
        
        # Keep only recent metrics
        if len(self.recent_metrics) > self.metrics_window_size:
            self.recent_metrics.pop(0)
        
        # Trigger degradation assessment
        self._assess_degradation_needs()
    
    def get_current_configuration(self) -> Dict[str, Any]:
        """
        Get current system configuration adjusted for degradation level.
        
        Returns:
            Dict with current configuration values
        """
        return {
            'degradation_level': self.current_state.level.name,
            'context_window_tokens': self.current_state.context_window_tokens,
            'thread_count': self.current_state.thread_count,
            'batch_size': self.current_state.batch_size,
            'memory_usage_mb': self.current_state.memory_usage_mb,
            'reason': self.current_state.reason,
            'timestamp': self.current_state.timestamp.isoformat()
        }
    
    def get_inference_config_adjustments(self) -> Dict[str, Any]:
        """
        Get inference configuration adjustments for current degradation level.
        
        Returns:
            Dict with inference configuration adjustments
        """
        level = self.current_state.level
        
        # Calculate adjusted values
        adjusted_context = int(self.base_context_window * 
                             self.config.context_window_adjustments[level])
        adjusted_threads = max(1, int(self.base_thread_count * 
                                    self.config.thread_adjustments[level]))
        
        return {
            'n_ctx': min(adjusted_context, 4096),  # Cap at model's maximum
            'n_threads': adjusted_threads,
            'max_context_tokens': adjusted_context,
            'degradation_level': level.name,
            'performance_mode': self._get_performance_mode_name(level)
        }
    
    def get_batch_processing_adjustments(self) -> Dict[str, Any]:
        """
        Get batch processing adjustments for current degradation level.
        
        Returns:
            Dict with batch processing adjustments
        """
        level = self.current_state.level
        
        adjusted_batch_size = max(1, int(self.base_batch_size * 
                                       self.config.batch_size_adjustments[level]))
        
        # Adjust queue size and timeouts based on degradation level
        queue_size_multiplier = self.config.batch_size_adjustments[level]
        timeout_multiplier = 2.0 if level in [DegradationLevel.HEAVY, DegradationLevel.CRITICAL] else 1.0
        
        return {
            'max_concurrent_queries': adjusted_batch_size,
            'max_queue_size': max(10, int(50 * queue_size_multiplier)),
            'worker_timeout_seconds': 60.0 * timeout_multiplier,
            'memory_threshold_mb': self._get_memory_threshold_for_level(level),
            'degradation_level': level.name
        }
    
    def force_degradation_level(self, level: DegradationLevel, reason: str = "Manual override") -> None:
        """
        Force a specific degradation level (for testing or emergency situations).
        
        Args:
            level: Degradation level to set
            reason: Reason for the change
        """
        logger.warning(f"Forcing degradation level to {level.name}: {reason}")
        self._apply_degradation_level(level, reason)
    
    def get_degradation_recommendations(self) -> List[str]:
        """
        Get recommendations for improving system performance.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        level = self.current_state.level
        
        if level == DegradationLevel.OPTIMAL:
            recommendations.append("System is operating at optimal performance")
        else:
            # Memory-based recommendations
            if self.current_state.memory_usage_mb > self.config.memory_moderate_threshold:
                recommendations.append("High memory usage detected - consider reducing context window")
                recommendations.append("Consider closing other applications to free memory")
            
            # Performance-based recommendations
            if self.current_state.response_time_ms > self.config.response_time_moderate:
                recommendations.append("Slow response times - consider reducing thread count")
                recommendations.append("Consider using smaller batch sizes")
            
            if self.current_state.token_rate < self.config.token_rate_moderate:
                recommendations.append("Low token generation rate - check CPU utilization")
                recommendations.append("Consider optimizing model quantization settings")
            
            # Level-specific recommendations
            if level == DegradationLevel.CRITICAL:
                recommendations.append("CRITICAL: System is operating at minimal capacity")
                recommendations.append("CRITICAL: Consider restarting the application")
                recommendations.append("CRITICAL: Check for memory leaks or resource issues")
            elif level == DegradationLevel.HEAVY:
                recommendations.append("Heavy degradation active - performance significantly reduced")
                recommendations.append("Consider reducing query complexity or frequency")
            
        return recommendations
    
    def get_state_history(self, last_n_states: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get degradation state history.
        
        Args:
            last_n_states: Number of recent states to return (None for all)
            
        Returns:
            List of state dictionaries
        """
        history = self.state_history
        if last_n_states:
            history = history[-last_n_states:]
        
        return [state.to_dict() for state in history]
    
    def _assess_degradation_needs(self) -> None:
        """Assess whether degradation level needs to be changed."""
        # Prevent rapid oscillation
        time_since_last_change = (datetime.now() - self.last_degradation_change).total_seconds()
        if time_since_last_change < self.min_change_interval_seconds:
            return
        
        # Get current resource usage
        memory_stats = self.memory_monitor.get_system_memory()
        current_memory = memory_stats.process_mb
        
        # Calculate average performance metrics
        avg_response_time = 0.0
        avg_token_rate = 0.0
        
        if self.recent_metrics:
            avg_response_time = sum(m.response_time_ms for m in self.recent_metrics) / len(self.recent_metrics)
            avg_token_rate = sum(m.tokens_per_second for m in self.recent_metrics) / len(self.recent_metrics)
        
        # Determine required degradation level
        required_level = self._calculate_required_degradation_level(
            current_memory, avg_response_time, avg_token_rate
        )
        
        # Apply degradation if level changed
        if required_level != self.current_state.level:
            reason = self._get_degradation_reason(current_memory, avg_response_time, avg_token_rate)
            self._apply_degradation_level(required_level, reason)
    
    def _calculate_required_degradation_level(self, 
                                            memory_mb: float, 
                                            response_time_ms: float, 
                                            token_rate: float) -> DegradationLevel:
        """
        Calculate required degradation level based on current metrics.
        
        Args:
            memory_mb: Current memory usage in MB
            response_time_ms: Average response time in milliseconds
            token_rate: Average token generation rate
            
        Returns:
            Required degradation level
        """
        # Start with optimal and check each constraint
        level = DegradationLevel.OPTIMAL
        
        # Memory-based degradation
        if memory_mb >= self.config.memory_critical_threshold:
            level = max(level, DegradationLevel.CRITICAL)
        elif memory_mb >= self.config.memory_heavy_threshold:
            level = max(level, DegradationLevel.HEAVY)
        elif memory_mb >= self.config.memory_moderate_threshold:
            level = max(level, DegradationLevel.MODERATE)
        elif memory_mb >= self.config.memory_light_threshold:
            level = max(level, DegradationLevel.LIGHT)
        
        # Response time-based degradation
        if response_time_ms >= self.config.response_time_critical:
            level = max(level, DegradationLevel.CRITICAL)
        elif response_time_ms >= self.config.response_time_heavy:
            level = max(level, DegradationLevel.HEAVY)
        elif response_time_ms >= self.config.response_time_moderate:
            level = max(level, DegradationLevel.MODERATE)
        elif response_time_ms >= self.config.response_time_light:
            level = max(level, DegradationLevel.LIGHT)
        
        # Token rate-based degradation (inverse relationship)
        if token_rate <= self.config.token_rate_critical:
            level = max(level, DegradationLevel.CRITICAL)
        elif token_rate <= self.config.token_rate_heavy:
            level = max(level, DegradationLevel.HEAVY)
        elif token_rate <= self.config.token_rate_moderate:
            level = max(level, DegradationLevel.MODERATE)
        elif token_rate <= self.config.token_rate_light:
            level = max(level, DegradationLevel.LIGHT)
        
        return level
    
    def _get_degradation_reason(self, 
                              memory_mb: float, 
                              response_time_ms: float, 
                              token_rate: float) -> str:
        """Get human-readable reason for degradation."""
        reasons = []
        
        if memory_mb >= self.config.memory_light_threshold:
            reasons.append(f"High memory usage ({memory_mb:.0f}MB)")
        
        if response_time_ms >= self.config.response_time_light:
            reasons.append(f"Slow response times ({response_time_ms:.0f}ms)")
        
        if token_rate <= self.config.token_rate_light:
            reasons.append(f"Low token rate ({token_rate:.1f} tok/s)")
        
        if not reasons:
            return "Performance optimization"
        
        return "; ".join(reasons)
    
    def _apply_degradation_level(self, level: DegradationLevel, reason: str) -> None:
        """
        Apply a specific degradation level.
        
        Args:
            level: Degradation level to apply
            reason: Reason for the degradation
        """
        # Calculate adjusted configuration values
        adjusted_context = int(self.base_context_window * 
                             self.config.context_window_adjustments[level])
        adjusted_threads = max(1, int(self.base_thread_count * 
                                    self.config.thread_adjustments[level]))
        adjusted_batch_size = max(1, int(self.base_batch_size * 
                                       self.config.batch_size_adjustments[level]))
        
        # Get current resource usage
        memory_stats = self.memory_monitor.get_system_memory()
        cpu_usage = self.thread_manager.get_cpu_usage()
        
        # Calculate average performance metrics
        avg_response_time = 0.0
        avg_token_rate = 0.0
        if self.recent_metrics:
            avg_response_time = sum(m.response_time_ms for m in self.recent_metrics) / len(self.recent_metrics)
            avg_token_rate = sum(m.tokens_per_second for m in self.recent_metrics) / len(self.recent_metrics)
        
        # Create new state
        new_state = DegradationState(
            level=level,
            reason=reason,
            timestamp=datetime.now(),
            memory_usage_mb=memory_stats.process_mb,
            cpu_usage_percent=cpu_usage,
            response_time_ms=avg_response_time,
            token_rate=avg_token_rate,
            context_window_tokens=adjusted_context,
            thread_count=adjusted_threads,
            batch_size=adjusted_batch_size
        )
        
        # Log the change
        if level != self.current_state.level:
            logger.info(f"Degradation level changed: {self.current_state.level.name} -> {level.name}")
            logger.info(f"Reason: {reason}")
            logger.info(f"New configuration: context={adjusted_context}, "
                       f"threads={adjusted_threads}, batch_size={adjusted_batch_size}")
            
            self.last_degradation_change = datetime.now()
        
        # Update current state
        self.current_state = new_state
        
        # Add to history
        self.state_history.append(new_state)
        if len(self.state_history) > self.max_history_size:
            self.state_history.pop(0)
    
    def _get_performance_mode_name(self, level: DegradationLevel) -> str:
        """Get human-readable performance mode name."""
        mode_names = {
            DegradationLevel.OPTIMAL: "High Performance",
            DegradationLevel.LIGHT: "Balanced Performance",
            DegradationLevel.MODERATE: "Power Saving",
            DegradationLevel.HEAVY: "Low Resource",
            DegradationLevel.CRITICAL: "Emergency Mode"
        }
        return mode_names.get(level, "Unknown")
    
    def _get_memory_threshold_for_level(self, level: DegradationLevel) -> float:
        """Get memory threshold for batch processing based on degradation level."""
        thresholds = {
            DegradationLevel.OPTIMAL: 2800,
            DegradationLevel.LIGHT: 2600,
            DegradationLevel.MODERATE: 2400,
            DegradationLevel.HEAVY: 2200,
            DegradationLevel.CRITICAL: 2000
        }
        return thresholds.get(level, 2800)


# Utility functions for graceful degradation
def create_degradation_manager(
    memory_monitor: MemoryMonitor,
    thread_manager: ThreadManager,
    performance_tracker: Optional[PerformanceTracker] = None,
    base_context_window: int = 3000,
    base_thread_count: int = 4,
    base_batch_size: int = 2
) -> GracefulDegradationManager:
    """
    Create a graceful degradation manager with recommended settings.
    
    Args:
        memory_monitor: Memory monitoring system
        thread_manager: Thread management system
        performance_tracker: Performance tracking system
        base_context_window: Base context window size
        base_thread_count: Base thread count
        base_batch_size: Base batch size
        
    Returns:
        GracefulDegradationManager instance
    """
    return GracefulDegradationManager(
        memory_monitor=memory_monitor,
        thread_manager=thread_manager,
        performance_tracker=performance_tracker,
        base_context_window=base_context_window,
        base_thread_count=base_thread_count,
        base_batch_size=base_batch_size
    )


def get_degradation_status_summary(manager: GracefulDegradationManager) -> Dict[str, Any]:
    """
    Get a comprehensive summary of degradation status.
    
    Args:
        manager: GracefulDegradationManager instance
        
    Returns:
        Dict with degradation status summary
    """
    current_config = manager.get_current_configuration()
    recommendations = manager.get_degradation_recommendations()
    
    return {
        'current_level': current_config['degradation_level'],
        'performance_impact': _get_performance_impact_description(manager.current_state.level),
        'configuration': current_config,
        'recommendations': recommendations,
        'last_change': current_config['timestamp'],
        'reason': current_config['reason']
    }


def _get_performance_impact_description(level: DegradationLevel) -> str:
    """Get description of performance impact for degradation level."""
    descriptions = {
        DegradationLevel.OPTIMAL: "No performance impact - system running at full capacity",
        DegradationLevel.LIGHT: "Minimal performance impact - slight reduction in context window and threading",
        DegradationLevel.MODERATE: "Moderate performance impact - noticeable reduction in response quality and speed",
        DegradationLevel.HEAVY: "Significant performance impact - substantial reduction in capabilities",
        DegradationLevel.CRITICAL: "Critical performance impact - system running at minimal capacity to prevent failure"
    }
    return descriptions.get(level, "Unknown performance impact")