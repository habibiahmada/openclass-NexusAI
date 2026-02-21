#!/usr/bin/env python3
"""
Example demonstrating graceful degradation system for OpenClass Nexus AI Phase 3.

This example shows how the graceful degradation manager automatically adjusts
system configuration based on resource constraints and performance metrics.
"""

import time
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import local inference components
from src.edge_runtime.resource_manager import MemoryMonitor, ThreadManager
from src.edge_runtime.performance_monitor import PerformanceTracker, PerformanceMetrics
from src.edge_runtime.graceful_degradation import (
    GracefulDegradationManager,
    DegradationLevel,
    DegradationConfig,
    create_degradation_manager,
    get_degradation_status_summary
)


def simulate_performance_metrics(degradation_manager: GracefulDegradationManager):
    """Simulate various performance scenarios to demonstrate degradation."""
    
    print("\n=== Graceful Degradation System Demo ===\n")
    
    # Scenario 1: Optimal performance
    print("1. Simulating optimal performance...")
    optimal_metrics = PerformanceMetrics(
        response_time_ms=3000,
        memory_usage_mb=1800,
        cpu_usage_percent=45,
        tokens_per_second=12,
        context_tokens=2000,
        response_tokens=150,
        timestamp=datetime.now()
    )
    
    degradation_manager.update_performance_metrics(optimal_metrics)
    print_degradation_status(degradation_manager)
    time.sleep(2)
    
    # Scenario 2: Light degradation (high memory)
    print("\n2. Simulating light degradation (high memory usage)...")
    light_degradation_metrics = PerformanceMetrics(
        response_time_ms=4500,
        memory_usage_mb=2500,
        cpu_usage_percent=60,
        tokens_per_second=8,
        context_tokens=2000,
        response_tokens=150,
        timestamp=datetime.now()
    )
    
    degradation_manager.update_performance_metrics(light_degradation_metrics)
    print_degradation_status(degradation_manager)
    time.sleep(2)
    
    # Scenario 3: Moderate degradation (slow response times)
    print("\n3. Simulating moderate degradation (slow response times)...")
    moderate_degradation_metrics = PerformanceMetrics(
        response_time_ms=12000,
        memory_usage_mb=2750,
        cpu_usage_percent=75,
        tokens_per_second=4,
        context_tokens=2000,
        response_tokens=150,
        timestamp=datetime.now()
    )
    
    degradation_manager.update_performance_metrics(moderate_degradation_metrics)
    print_degradation_status(degradation_manager)
    time.sleep(2)
    
    # Scenario 4: Heavy degradation (critical memory)
    print("\n4. Simulating heavy degradation (critical memory usage)...")
    heavy_degradation_metrics = PerformanceMetrics(
        response_time_ms=18000,
        memory_usage_mb=2950,
        cpu_usage_percent=85,
        tokens_per_second=2,
        context_tokens=2000,
        response_tokens=150,
        timestamp=datetime.now()
    )
    
    degradation_manager.update_performance_metrics(heavy_degradation_metrics)
    print_degradation_status(degradation_manager)
    time.sleep(2)
    
    # Scenario 5: Critical degradation (system under extreme stress)
    print("\n5. Simulating critical degradation (system under extreme stress)...")
    critical_degradation_metrics = PerformanceMetrics(
        response_time_ms=25000,
        memory_usage_mb=3100,
        cpu_usage_percent=95,
        tokens_per_second=0.5,
        context_tokens=2000,
        response_tokens=150,
        timestamp=datetime.now()
    )
    
    degradation_manager.update_performance_metrics(critical_degradation_metrics)
    print_degradation_status(degradation_manager)
    time.sleep(2)
    
    # Scenario 6: Recovery (system performance improves)
    print("\n6. Simulating system recovery...")
    recovery_metrics = PerformanceMetrics(
        response_time_ms=6000,
        memory_usage_mb=2200,
        cpu_usage_percent=50,
        tokens_per_second=7,
        context_tokens=2000,
        response_tokens=150,
        timestamp=datetime.now()
    )
    
    degradation_manager.update_performance_metrics(recovery_metrics)
    print_degradation_status(degradation_manager)


def print_degradation_status(degradation_manager: GracefulDegradationManager):
    """Print current degradation status and configuration."""
    
    # Get current configuration
    config = degradation_manager.get_current_configuration()
    
    # Get inference adjustments
    inference_adjustments = degradation_manager.get_inference_config_adjustments()
    
    # Get batch processing adjustments
    batch_adjustments = degradation_manager.get_batch_processing_adjustments()
    
    # Get recommendations
    recommendations = degradation_manager.get_degradation_recommendations()
    
    print(f"Current Degradation Level: {config['degradation_level']}")
    print(f"Reason: {config['reason']}")
    print(f"Memory Usage: {config['memory_usage_mb']:.1f} MB")
    
    print(f"\nConfiguration Adjustments:")
    print(f"  Context Window: {config['context_window_tokens']} tokens")
    print(f"  Thread Count: {config['thread_count']}")
    print(f"  Batch Size: {config['batch_size']}")
    print(f"  Performance Mode: {inference_adjustments.get('performance_mode', 'Unknown')}")
    
    print(f"\nInference Engine Settings:")
    print(f"  n_ctx: {inference_adjustments.get('n_ctx', 'N/A')}")
    print(f"  n_threads: {inference_adjustments.get('n_threads', 'N/A')}")
    
    print(f"\nBatch Processing Settings:")
    print(f"  Max Concurrent Queries: {batch_adjustments.get('max_concurrent_queries', 'N/A')}")
    print(f"  Memory Threshold: {batch_adjustments.get('memory_threshold_mb', 'N/A')} MB")
    
    print(f"\nRecommendations:")
    for i, rec in enumerate(recommendations[:3], 1):  # Show top 3 recommendations
        print(f"  {i}. {rec}")
    
    print("-" * 60)


def demonstrate_manual_degradation(degradation_manager: GracefulDegradationManager):
    """Demonstrate manual degradation level setting."""
    
    print("\n=== Manual Degradation Control Demo ===\n")
    
    # Force different degradation levels
    levels_to_test = [
        (DegradationLevel.CRITICAL, "Emergency testing"),
        (DegradationLevel.HEAVY, "Load testing"),
        (DegradationLevel.MODERATE, "Performance testing"),
        (DegradationLevel.LIGHT, "Optimization testing"),
        (DegradationLevel.OPTIMAL, "Normal operation restored")
    ]
    
    for level, reason in levels_to_test:
        print(f"Setting degradation level to {level.name}: {reason}")
        degradation_manager.force_degradation_level(level, reason)
        print_degradation_status(degradation_manager)
        time.sleep(1)


def demonstrate_state_history(degradation_manager: GracefulDegradationManager):
    """Demonstrate degradation state history tracking."""
    
    print("\n=== Degradation State History ===\n")
    
    history = degradation_manager.get_state_history(last_n_states=5)
    
    print("Recent degradation state changes:")
    for i, state in enumerate(history, 1):
        print(f"{i}. {state['timestamp'][:19]} - {state['level']} ({state['reason']})")
        print(f"   Memory: {state['memory_usage_mb']:.1f}MB, "
              f"Response: {state['response_time_ms']:.0f}ms, "
              f"Tokens/s: {state['token_rate']:.1f}")


def main():
    """Main demonstration function."""
    
    print("OpenClass Nexus AI - Graceful Degradation System Demo")
    print("=" * 60)
    
    try:
        # Initialize resource monitoring components
        print("Initializing resource monitoring...")
        memory_monitor = MemoryMonitor(memory_limit_mb=3072)
        thread_manager = ThreadManager()
        performance_tracker = PerformanceTracker()
        
        # Create degradation manager
        print("Creating graceful degradation manager...")
        degradation_manager = create_degradation_manager(
            memory_monitor=memory_monitor,
            thread_manager=thread_manager,
            performance_tracker=performance_tracker,
            base_context_window=3000,
            base_thread_count=4,
            base_batch_size=2
        )
        
        # Run performance simulation
        simulate_performance_metrics(degradation_manager)
        
        # Demonstrate manual control
        demonstrate_manual_degradation(degradation_manager)
        
        # Show state history
        demonstrate_state_history(degradation_manager)
        
        # Final status summary
        print("\n=== Final Status Summary ===\n")
        summary = get_degradation_status_summary(degradation_manager)
        
        print(f"Current Level: {summary['current_level']}")
        print(f"Performance Impact: {summary['performance_impact']}")
        print(f"Last Change: {summary['last_change'][:19]}")
        print(f"Reason: {summary['reason']}")
        
        print("\nDemo completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in demonstration: {e}")
        print(f"Demo failed with error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())