"""
Resource management utilities for OpenClass Nexus AI Phase 3.

This module provides memory monitoring and thread management optimized
for 4GB RAM systems running Llama-3.2-3B-Instruct model.
"""

import gc
import os
import psutil
import logging
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total_mb: float
    available_mb: float
    used_mb: float
    percent_used: float
    process_mb: float
    timestamp: datetime
    
    def is_critical(self, threshold_percent: float = 85.0) -> bool:
        """Check if memory usage is at critical level."""
        return self.percent_used >= threshold_percent
    
    def has_available(self, required_mb: float) -> bool:
        """Check if required memory is available."""
        return self.available_mb >= required_mb


class MemoryMonitor:
    """
    Memory usage tracking and management for 4GB RAM constraints.
    
    This monitor provides:
    - Real-time memory usage tracking
    - Automatic cleanup triggers
    - Memory pressure detection
    - Resource optimization recommendations
    """
    
    def __init__(self, memory_limit_mb: int = 3072):
        """
        Initialize memory monitor.
        
        Args:
            memory_limit_mb: Maximum memory limit in MB (default 3GB for 4GB systems)
        """
        self.memory_limit_mb = memory_limit_mb
        self.process = psutil.Process()
        self.cleanup_callbacks: list[Callable] = []
        self.monitoring_active = False
        self.stats_history: list[MemoryStats] = []
        self.max_history_size = 100
        
        logger.info(f"MemoryMonitor initialized with {memory_limit_mb}MB limit")
    
    def get_memory_usage(self) -> float:
        """
        Get current process memory usage in MB.
        
        Returns:
            float: Memory usage in MB
        """
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert bytes to MB
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return 0.0
    
    def get_system_memory(self) -> MemoryStats:
        """
        Get comprehensive system memory statistics.
        
        Returns:
            MemoryStats: Current memory statistics
        """
        try:
            system_memory = psutil.virtual_memory()
            process_memory = self.get_memory_usage()
            
            stats = MemoryStats(
                total_mb=system_memory.total / (1024 * 1024),
                available_mb=system_memory.available / (1024 * 1024),
                used_mb=system_memory.used / (1024 * 1024),
                percent_used=system_memory.percent,
                process_mb=process_memory,
                timestamp=datetime.now()
            )
            
            # Store in history
            self.stats_history.append(stats)
            if len(self.stats_history) > self.max_history_size:
                self.stats_history.pop(0)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system memory stats: {e}")
            return MemoryStats(0, 0, 0, 0, 0, datetime.now())
    
    def check_memory_available(self, required_mb: int) -> bool:
        """
        Check if enough memory is available for an operation.
        
        Args:
            required_mb: Required memory in MB
            
        Returns:
            bool: True if enough memory is available
        """
        stats = self.get_system_memory()
        return stats.has_available(required_mb)
    
    def is_memory_critical(self, threshold_percent: float = 85.0) -> bool:
        """
        Check if memory usage is at critical level.
        
        Args:
            threshold_percent: Critical threshold percentage
            
        Returns:
            bool: True if memory usage is critical
        """
        stats = self.get_system_memory()
        return stats.is_critical(threshold_percent)
    
    def trigger_cleanup(self) -> None:
        """
        Trigger memory cleanup operations.
        
        This method:
        1. Runs registered cleanup callbacks
        2. Forces garbage collection
        3. Logs memory recovery results
        """
        logger.info("Triggering memory cleanup")
        
        # Get memory usage before cleanup
        before_stats = self.get_system_memory()
        
        # Run cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in cleanup callback: {e}")
        
        # Force garbage collection
        gc.collect()
        
        # Get memory usage after cleanup
        after_stats = self.get_system_memory()
        
        # Log results
        memory_freed = before_stats.process_mb - after_stats.process_mb
        logger.info(f"Memory cleanup completed. Freed: {memory_freed:.1f}MB")
        logger.info(f"Memory usage: {after_stats.process_mb:.1f}MB "
                   f"({after_stats.percent_used:.1f}% system)")
    
    def register_cleanup_callback(self, callback: Callable) -> None:
        """
        Register a callback to be called during memory cleanup.
        
        Args:
            callback: Function to call during cleanup
        """
        self.cleanup_callbacks.append(callback)
        logger.debug(f"Registered cleanup callback: {callback.__name__}")
    
    def get_memory_recommendations(self) -> Dict[str, Any]:
        """
        Get memory optimization recommendations based on current usage.
        
        Returns:
            Dict with recommendations and current status
        """
        stats = self.get_system_memory()
        recommendations = []
        
        if stats.percent_used > 90:
            recommendations.append("Critical: Consider reducing context window size")
            recommendations.append("Critical: Unload unused models immediately")
        elif stats.percent_used > 80:
            recommendations.append("Warning: Monitor memory usage closely")
            recommendations.append("Warning: Consider batch size reduction")
        elif stats.percent_used > 70:
            recommendations.append("Info: Memory usage is elevated but manageable")
        
        if stats.process_mb > self.memory_limit_mb:
            recommendations.append(f"Critical: Process exceeds limit ({stats.process_mb:.1f}MB > {self.memory_limit_mb}MB)")
        
        return {
            'current_stats': stats,
            'recommendations': recommendations,
            'within_limits': stats.process_mb <= self.memory_limit_mb,
            'critical_level': stats.is_critical()
        }


class ThreadManager:
    """
    Optimal thread count detection and management for CPU inference.
    
    This manager provides:
    - Hardware-aware thread optimization
    - Dynamic thread adjustment
    - Performance monitoring
    - Resource-based recommendations
    """
    
    def __init__(self):
        """Initialize thread manager with hardware detection."""
        self.cpu_count = os.cpu_count() or 4
        self.optimal_threads = self._calculate_optimal_threads()
        self.performance_history: list[Dict[str, Any]] = []
        
        logger.info(f"ThreadManager initialized: {self.cpu_count} CPUs, "
                   f"{self.optimal_threads} optimal threads")
    
    def _calculate_optimal_threads(self) -> int:
        """
        Calculate optimal thread count for current hardware.
        
        Returns:
            int: Optimal number of threads
        """
        # For CPU inference, optimal threads is typically:
        # - Physical cores for high-end systems
        # - Physical cores - 1 for mid-range systems
        # - Cap at 6 threads to avoid context switching overhead
        
        if self.cpu_count >= 8:
            # High-end system: use most cores but leave some for OS
            optimal = min(self.cpu_count - 2, 8)
        elif self.cpu_count >= 4:
            # Mid-range system: use most cores
            optimal = min(self.cpu_count, 6)
        else:
            # Low-end system: use all available cores
            optimal = self.cpu_count
        
        # Ensure at least 1 thread
        return max(optimal, 1)
    
    def get_thread_config(self, available_memory_mb: int) -> int:
        """
        Get thread configuration based on available resources.
        
        Args:
            available_memory_mb: Available memory in MB
            
        Returns:
            int: Recommended number of threads
        """
        base_threads = self.optimal_threads
        
        # Reduce threads if memory is constrained
        if available_memory_mb < 2000:  # Less than 2GB available
            base_threads = max(base_threads // 2, 1)
            logger.warning(f"Reducing threads to {base_threads} due to memory constraints")
        elif available_memory_mb < 3000:  # Less than 3GB available
            base_threads = max(base_threads - 1, 1)
            logger.info(f"Reducing threads to {base_threads} due to moderate memory pressure")
        
        return base_threads
    
    def get_cpu_usage(self) -> float:
        """
        Get current CPU usage percentage.
        
        Returns:
            float: CPU usage percentage
        """
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return 0.0
    
    def monitor_performance(self, thread_count: int, operation_time: float) -> None:
        """
        Monitor performance for a given thread configuration.
        
        Args:
            thread_count: Number of threads used
            operation_time: Time taken for operation in seconds
        """
        cpu_usage = self.get_cpu_usage()
        
        performance_data = {
            'thread_count': thread_count,
            'operation_time': operation_time,
            'cpu_usage': cpu_usage,
            'timestamp': datetime.now()
        }
        
        self.performance_history.append(performance_data)
        
        # Keep only recent history
        if len(self.performance_history) > 50:
            self.performance_history.pop(0)
        
        logger.debug(f"Performance recorded: {thread_count} threads, "
                    f"{operation_time:.2f}s, {cpu_usage:.1f}% CPU")
    
    def get_performance_recommendations(self) -> Dict[str, Any]:
        """
        Get performance recommendations based on monitoring history.
        
        Returns:
            Dict with recommendations and performance analysis
        """
        if not self.performance_history:
            return {
                'recommendations': ['No performance data available yet'],
                'optimal_threads': self.optimal_threads,
                'current_config': self.optimal_threads
            }
        
        # Analyze recent performance
        recent_data = self.performance_history[-10:]  # Last 10 operations
        avg_time = sum(d['operation_time'] for d in recent_data) / len(recent_data)
        avg_cpu = sum(d['cpu_usage'] for d in recent_data) / len(recent_data)
        
        recommendations = []
        
        if avg_cpu < 50:
            recommendations.append("CPU utilization is low - consider increasing thread count")
        elif avg_cpu > 90:
            recommendations.append("CPU utilization is high - consider reducing thread count")
        else:
            recommendations.append("CPU utilization is optimal")
        
        if avg_time > 5.0:  # More than 5 seconds average
            recommendations.append("Response times are slow - check memory and thread configuration")
        
        return {
            'recommendations': recommendations,
            'optimal_threads': self.optimal_threads,
            'avg_operation_time': avg_time,
            'avg_cpu_usage': avg_cpu,
            'performance_history_size': len(self.performance_history)
        }
    
    def auto_adjust_threads(self, memory_monitor: MemoryMonitor) -> int:
        """
        Automatically adjust thread count based on system resources.
        
        Args:
            memory_monitor: MemoryMonitor instance for resource checking
            
        Returns:
            int: Recommended thread count
        """
        memory_stats = memory_monitor.get_system_memory()
        recommended_threads = self.get_thread_config(memory_stats.available_mb)
        
        logger.info(f"Auto-adjusted threads: {recommended_threads} "
                   f"(memory: {memory_stats.available_mb:.0f}MB available)")
        
        return recommended_threads


# Utility functions for resource management
def setup_resource_monitoring(memory_limit_mb: int = 3072) -> tuple[MemoryMonitor, ThreadManager]:
    """
    Setup resource monitoring for the inference system.
    
    Args:
        memory_limit_mb: Memory limit in MB
        
    Returns:
        Tuple of (MemoryMonitor, ThreadManager)
    """
    memory_monitor = MemoryMonitor(memory_limit_mb)
    thread_manager = ThreadManager()
    
    logger.info("Resource monitoring setup completed")
    return memory_monitor, thread_manager


def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information for diagnostics.
    
    Returns:
        Dict with system information
    """
    try:
        memory = psutil.virtual_memory()
        cpu_info = {
            'cpu_count': os.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=1)
        }
        
        return {
            'memory': {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'percent_used': memory.percent
            },
            'cpu': cpu_info,
            'platform': {
                'system': os.name,
                'python_version': os.sys.version
            }
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {'error': str(e)}