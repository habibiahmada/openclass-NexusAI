"""
Performance Benchmarking System for OpenClass Nexus AI Phase 3.

This module provides comprehensive performance testing framework, memory usage
monitoring and reporting, and concurrent processing validation as specified
in requirements 2.2, 2.4, 4.1, 4.2, 4.3.
"""

import logging
import time
import threading
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import psutil
import statistics

from src.edge_runtime.complete_pipeline import CompletePipeline, PipelineConfig
from src.edge_runtime.performance_monitor import PerformanceMetrics, PerformanceTracker
from src.edge_runtime.batch_processor import BatchProcessor, QueryPriority
from src.edge_runtime.resource_manager import MemoryMonitor

logger = logging.getLogger(__name__)


@dataclass
class PerformanceBenchmark:
    """
    Comprehensive performance benchmark results as specified in design document.
    
    This class contains all performance metrics required for system validation
    including response times, memory usage, throughput, and system stability.
    """
    average_response_time_ms: float
    peak_memory_usage_mb: float
    throughput_queries_per_minute: float
    concurrent_query_capacity: int
    curriculum_alignment_accuracy: float
    system_stability_score: float
    hardware_efficiency_score: float
    
    # Detailed metrics
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    response_time_std_dev: float = 0.0
    memory_usage_std_dev: float = 0.0
    cpu_utilization_avg: float = 0.0
    cpu_utilization_peak: float = 0.0
    
    # Test configuration
    test_duration_seconds: float = 0.0
    total_queries_processed: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    benchmark_timestamp: datetime = field(default_factory=datetime.now)
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_queries_processed == 0:
            return 0.0
        return (self.successful_queries / self.total_queries_processed) * 100
    
    def meets_performance_targets(self) -> bool:
        """
        Check if benchmark meets performance targets from requirements.
        
        Targets:
        - Response time < 5 seconds (5000ms)
        - Memory usage < 4GB (4096MB)
        - Concurrent queries >= 3
        - Success rate > 90%
        
        Returns:
            bool: True if all targets are met
        """
        return (
            self.average_response_time_ms < 5000 and
            self.peak_memory_usage_mb < 4096 and
            self.concurrent_query_capacity >= 3 and
            self.get_success_rate() > 90.0
        )
    
    def get_performance_grade(self) -> str:
        """Get overall performance grade."""
        if self.meets_performance_targets() and self.system_stability_score > 0.9:
            return "Excellent"
        elif self.average_response_time_ms < 8000 and self.peak_memory_usage_mb < 3500:
            return "Good"
        elif self.average_response_time_ms < 10000 and self.peak_memory_usage_mb < 4096:
            return "Acceptable"
        else:
            return "Needs Improvement"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert benchmark to dictionary for serialization."""
        return {
            'summary': {
                'average_response_time_ms': self.average_response_time_ms,
                'peak_memory_usage_mb': self.peak_memory_usage_mb,
                'throughput_queries_per_minute': self.throughput_queries_per_minute,
                'concurrent_query_capacity': self.concurrent_query_capacity,
                'curriculum_alignment_accuracy': self.curriculum_alignment_accuracy,
                'system_stability_score': self.system_stability_score,
                'hardware_efficiency_score': self.hardware_efficiency_score,
                'performance_grade': self.get_performance_grade(),
                'meets_targets': self.meets_performance_targets(),
                'success_rate': self.get_success_rate()
            },
            'detailed_metrics': {
                'response_time': {
                    'min_ms': self.min_response_time_ms,
                    'max_ms': self.max_response_time_ms,
                    'avg_ms': self.average_response_time_ms,
                    'std_dev_ms': self.response_time_std_dev
                },
                'memory_usage': {
                    'peak_mb': self.peak_memory_usage_mb,
                    'std_dev_mb': self.memory_usage_std_dev
                },
                'cpu_utilization': {
                    'avg_percent': self.cpu_utilization_avg,
                    'peak_percent': self.cpu_utilization_peak
                }
            },
            'test_info': {
                'duration_seconds': self.test_duration_seconds,
                'total_queries': self.total_queries_processed,
                'successful_queries': self.successful_queries,
                'failed_queries': self.failed_queries,
                'timestamp': self.benchmark_timestamp.isoformat()
            }
        }


@dataclass
class BenchmarkConfig:
    """Configuration for performance benchmarking."""
    # Test duration and load
    test_duration_seconds: float = 300.0  # 5 minutes
    warmup_duration_seconds: float = 30.0  # 30 seconds warmup
    queries_per_minute: int = 12  # 1 query every 5 seconds
    max_concurrent_queries: int = 5
    
    # Memory and resource limits
    memory_limit_mb: int = 4096  # 4GB limit
    cpu_limit_percent: float = 95.0
    
    # Test queries
    use_sample_queries: bool = True
    custom_queries: Optional[List[str]] = None
    
    # Monitoring settings
    resource_sampling_interval_seconds: float = 1.0
    performance_reporting_interval_seconds: float = 30.0
    
    # Validation settings
    enable_educational_validation: bool = True
    minimum_curriculum_alignment: float = 0.7


class PerformanceBenchmarkingEngine:
    """
    Comprehensive performance benchmarking engine for system validation.
    
    This engine provides:
    - Comprehensive performance testing framework
    - Memory usage monitoring and reporting
    - Concurrent processing validation and metrics
    - System stability and reliability testing
    
    Implements requirements 2.2, 2.4, 4.1, 4.2, 4.3 from the specification.
    """
    
    # Sample queries for benchmarking
    BENCHMARK_QUERIES = [
        "Jelaskan konsep algoritma dalam informatika",
        "Apa itu struktur data dan fungsinya?",
        "Bagaimana cara kerja basis data?",
        "Jelaskan perbedaan hardware dan software",
        "Apa yang dimaksud dengan jaringan komputer?",
        "Sebutkan jenis-jenis sistem operasi",
        "Jelaskan konsep pemrograman berorientasi objek",
        "Apa fungsi dari compiler dalam pemrograman?",
        "Bagaimana cara kerja internet?",
        "Jelaskan konsep keamanan siber"
    ]
    
    def __init__(self, 
                 pipeline: Optional[CompletePipeline] = None,
                 config: Optional[BenchmarkConfig] = None):
        """
        Initialize the Performance Benchmarking Engine.
        
        Args:
            pipeline: Complete pipeline instance
            config: Benchmark configuration
        """
        self.pipeline = pipeline
        self.config = config or BenchmarkConfig()
        self.memory_monitor = MemoryMonitor(memory_limit_mb=self.config.memory_limit_mb)
        
        # Benchmark state
        self.is_running = False
        self.benchmark_start_time: Optional[datetime] = None
        self.resource_samples: List[Dict[str, Any]] = []
        self.query_results: List[Dict[str, Any]] = []
        
        # Threading for concurrent testing
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        
        logger.info("PerformanceBenchmarkingEngine initialized")
    
    def run_performance_benchmark(self, 
                                config: Optional[BenchmarkConfig] = None) -> PerformanceBenchmark:
        """
        Run comprehensive performance benchmark.
        
        Args:
            config: Benchmark configuration (uses instance config if None)
            
        Returns:
            PerformanceBenchmark with complete results
        """
        if not self.pipeline or not self.pipeline.is_running:
            raise RuntimeError("Pipeline must be initialized and running")
        
        benchmark_config = config or self.config
        
        logger.info(f"Starting performance benchmark - Duration: {benchmark_config.test_duration_seconds}s")
        
        # Reset state
        self.resource_samples.clear()
        self.query_results.clear()
        self.stop_monitoring.clear()
        self.is_running = True
        self.benchmark_start_time = datetime.now()
        
        try:
            # Start resource monitoring
            self._start_resource_monitoring(benchmark_config)
            
            # Run warmup phase
            logger.info("Running warmup phase...")
            self._run_warmup_phase(benchmark_config)
            
            # Run main benchmark
            logger.info("Running main benchmark...")
            benchmark_results = self._run_main_benchmark(benchmark_config)
            
            # Stop monitoring
            self._stop_resource_monitoring()
            
            logger.info(f"Benchmark completed: {benchmark_results.get_performance_grade()} grade")
            return benchmark_results
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            self._stop_resource_monitoring()
            raise
        finally:
            self.is_running = False
    
    def _start_resource_monitoring(self, config: BenchmarkConfig) -> None:
        """Start background resource monitoring."""
        def monitor_resources():
            while not self.stop_monitoring.is_set():
                try:
                    # Get system resource usage
                    memory_info = psutil.virtual_memory()
                    cpu_percent = psutil.cpu_percent(interval=None)
                    
                    # Get process-specific usage
                    process_memory = self.memory_monitor.get_memory_usage()
                    
                    sample = {
                        'timestamp': datetime.now(),
                        'system_memory_used_mb': memory_info.used / (1024 * 1024),
                        'system_memory_percent': memory_info.percent,
                        'process_memory_mb': process_memory,
                        'cpu_percent': cpu_percent
                    }
                    
                    self.resource_samples.append(sample)
                    
                    # Sleep for sampling interval
                    self.stop_monitoring.wait(config.resource_sampling_interval_seconds)
                    
                except Exception as e:
                    logger.error(f"Error in resource monitoring: {e}")
                    self.stop_monitoring.wait(5.0)
        
        self.monitoring_thread = threading.Thread(target=monitor_resources, daemon=True)
        self.monitoring_thread.start()
        logger.info("Resource monitoring started")
    
    def _stop_resource_monitoring(self) -> None:
        """Stop background resource monitoring."""
        self.stop_monitoring.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        logger.info("Resource monitoring stopped")
    
    def _run_warmup_phase(self, config: BenchmarkConfig) -> None:
        """Run warmup phase to stabilize system performance."""
        warmup_queries = min(5, len(self.BENCHMARK_QUERIES))
        warmup_end_time = time.time() + config.warmup_duration_seconds
        
        query_index = 0
        while time.time() < warmup_end_time:
            try:
                query = self.BENCHMARK_QUERIES[query_index % len(self.BENCHMARK_QUERIES)]
                
                # Process warmup query
                start_time = time.time()
                result = self.pipeline.process_query(query)
                processing_time = (time.time() - start_time) * 1000
                
                logger.debug(f"Warmup query processed in {processing_time:.1f}ms")
                
                query_index += 1
                
                # Wait before next query
                time.sleep(2.0)
                
            except Exception as e:
                logger.warning(f"Warmup query failed: {e}")
                time.sleep(1.0)
        
        logger.info("Warmup phase completed")
    
    def _run_main_benchmark(self, config: BenchmarkConfig) -> PerformanceBenchmark:
        """Run the main benchmark test."""
        test_end_time = time.time() + config.test_duration_seconds
        queries_to_use = config.custom_queries or self.BENCHMARK_QUERIES
        
        # Single-threaded performance test
        single_thread_results = self._run_single_thread_test(
            queries_to_use, 
            test_end_time, 
            config
        )
        
        # Concurrent processing test
        concurrent_results = self._run_concurrent_test(
            queries_to_use,
            config
        )
        
        # Memory stress test
        memory_results = self._run_memory_stress_test(config)
        
        # Calculate comprehensive benchmark
        return self._calculate_benchmark_results(
            single_thread_results,
            concurrent_results, 
            memory_results,
            config
        )
    
    def _run_single_thread_test(self, 
                               queries: List[str], 
                               end_time: float,
                               config: BenchmarkConfig) -> Dict[str, Any]:
        """Run single-threaded performance test."""
        results = {
            'response_times': [],
            'memory_usage': [],
            'successful_queries': 0,
            'failed_queries': 0,
            'curriculum_scores': []
        }
        
        query_index = 0
        query_interval = 60.0 / config.queries_per_minute  # Seconds between queries
        last_query_time = time.time()
        
        while time.time() < end_time:
            try:
                # Wait for next query interval
                current_time = time.time()
                time_since_last = current_time - last_query_time
                if time_since_last < query_interval:
                    time.sleep(query_interval - time_since_last)
                
                query = queries[query_index % len(queries)]
                
                # Process query with timing
                start_time = time.time()
                result = self.pipeline.process_query(query)
                processing_time = (time.time() - start_time) * 1000
                
                # Record results
                results['response_times'].append(processing_time)
                results['memory_usage'].append(self.memory_monitor.get_memory_usage())
                results['successful_queries'] += 1
                
                # Educational validation if enabled
                if config.enable_educational_validation and hasattr(result, 'response'):
                    # Simple curriculum alignment check
                    curriculum_score = self._estimate_curriculum_alignment(result.response)
                    results['curriculum_scores'].append(curriculum_score)
                
                query_index += 1
                last_query_time = time.time()
                
                logger.debug(f"Query {query_index} processed in {processing_time:.1f}ms")
                
            except Exception as e:
                logger.warning(f"Query failed: {e}")
                results['failed_queries'] += 1
                time.sleep(1.0)
        
        logger.info(f"Single-thread test completed: {results['successful_queries']} successful, "
                   f"{results['failed_queries']} failed")
        
        return results
    
    def _run_concurrent_test(self, 
                           queries: List[str],
                           config: BenchmarkConfig) -> Dict[str, Any]:
        """Run concurrent processing test to determine capacity."""
        logger.info("Running concurrent processing test...")
        
        concurrent_results = {
            'max_concurrent': 0,
            'concurrent_response_times': [],
            'concurrent_memory_peak': 0.0,
            'concurrent_success_rate': 0.0
        }
        
        # Test increasing levels of concurrency
        for concurrent_level in range(1, config.max_concurrent_queries + 1):
            try:
                logger.info(f"Testing {concurrent_level} concurrent queries...")
                
                # Run concurrent queries
                test_results = self._test_concurrent_level(
                    queries, 
                    concurrent_level,
                    test_duration=30.0  # 30 second test per level
                )
                
                # Check if this level is successful
                if test_results['success_rate'] > 0.8:  # 80% success rate threshold
                    concurrent_results['max_concurrent'] = concurrent_level
                    concurrent_results['concurrent_response_times'].extend(test_results['response_times'])
                    concurrent_results['concurrent_memory_peak'] = max(
                        concurrent_results['concurrent_memory_peak'],
                        test_results['peak_memory']
                    )
                    concurrent_results['concurrent_success_rate'] = test_results['success_rate']
                else:
                    logger.info(f"Concurrent level {concurrent_level} failed threshold")
                    break
                    
            except Exception as e:
                logger.warning(f"Concurrent test level {concurrent_level} failed: {e}")
                break
        
        logger.info(f"Maximum concurrent capacity: {concurrent_results['max_concurrent']}")
        return concurrent_results
    
    def _test_concurrent_level(self, 
                             queries: List[str], 
                             concurrent_level: int,
                             test_duration: float) -> Dict[str, Any]:
        """Test a specific level of concurrency."""
        results = {
            'response_times': [],
            'peak_memory': 0.0,
            'successful_queries': 0,
            'failed_queries': 0,
            'success_rate': 0.0
        }
        
        def process_query(query: str) -> Tuple[bool, float, float]:
            """Process a single query and return success, time, memory."""
            try:
                start_time = time.time()
                start_memory = self.memory_monitor.get_memory_usage()
                
                result = self.pipeline.process_query(query)
                
                processing_time = (time.time() - start_time) * 1000
                end_memory = self.memory_monitor.get_memory_usage()
                
                return True, processing_time, max(start_memory, end_memory)
                
            except Exception as e:
                logger.debug(f"Concurrent query failed: {e}")
                return False, 0.0, 0.0
        
        # Run concurrent test
        end_time = time.time() + test_duration
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_level) as executor:
            while time.time() < end_time:
                # Submit batch of concurrent queries
                futures = []
                for i in range(concurrent_level):
                    query = queries[i % len(queries)]
                    future = executor.submit(process_query, query)
                    futures.append(future)
                
                # Collect results
                for future in concurrent.futures.as_completed(futures, timeout=30.0):
                    try:
                        success, response_time, memory_usage = future.result()
                        
                        if success:
                            results['successful_queries'] += 1
                            results['response_times'].append(response_time)
                            results['peak_memory'] = max(results['peak_memory'], memory_usage)
                        else:
                            results['failed_queries'] += 1
                            
                    except Exception as e:
                        logger.debug(f"Future result failed: {e}")
                        results['failed_queries'] += 1
                
                # Brief pause between batches
                time.sleep(2.0)
        
        # Calculate success rate
        total_queries = results['successful_queries'] + results['failed_queries']
        if total_queries > 0:
            results['success_rate'] = results['successful_queries'] / total_queries
        
        return results
    
    def _run_memory_stress_test(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """Run memory stress test to validate memory constraints."""
        logger.info("Running memory stress test...")
        
        memory_results = {
            'peak_memory_mb': 0.0,
            'memory_stability': 0.0,
            'memory_efficiency': 0.0
        }
        
        try:
            # Run intensive queries to stress memory
            intensive_queries = [
                "Jelaskan secara detail konsep algoritma sorting dan berikan contoh implementasi",
                "Bagaimana cara kerja basis data relasional dan jelaskan konsep normalisasi",
                "Apa itu jaringan komputer dan jelaskan model OSI layer secara lengkap"
            ]
            
            memory_samples = []
            
            for i in range(10):  # Run 10 intensive queries
                try:
                    query = intensive_queries[i % len(intensive_queries)]
                    
                    start_memory = self.memory_monitor.get_memory_usage()
                    result = self.pipeline.process_query(query)
                    end_memory = self.memory_monitor.get_memory_usage()
                    
                    memory_samples.append(end_memory)
                    memory_results['peak_memory_mb'] = max(memory_results['peak_memory_mb'], end_memory)
                    
                    logger.debug(f"Memory stress query {i+1}: {end_memory:.1f}MB")
                    
                    # Brief pause
                    time.sleep(2.0)
                    
                except Exception as e:
                    logger.warning(f"Memory stress query {i+1} failed: {e}")
            
            # Calculate memory stability (lower std dev = more stable)
            if memory_samples:
                memory_std_dev = statistics.stdev(memory_samples) if len(memory_samples) > 1 else 0.0
                memory_results['memory_stability'] = max(0.0, 1.0 - (memory_std_dev / 1000.0))  # Normalize
                
                # Memory efficiency (lower average usage = more efficient)
                avg_memory = statistics.mean(memory_samples)
                memory_results['memory_efficiency'] = max(0.0, 1.0 - (avg_memory / config.memory_limit_mb))
            
        except Exception as e:
            logger.error(f"Memory stress test failed: {e}")
        
        logger.info(f"Memory stress test completed: Peak {memory_results['peak_memory_mb']:.1f}MB")
        return memory_results
    
    def _calculate_benchmark_results(self,
                                   single_results: Dict[str, Any],
                                   concurrent_results: Dict[str, Any],
                                   memory_results: Dict[str, Any],
                                   config: BenchmarkConfig) -> PerformanceBenchmark:
        """Calculate comprehensive benchmark results."""
        
        # Response time statistics
        all_response_times = (single_results['response_times'] + 
                            concurrent_results['concurrent_response_times'])
        
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            min_response_time = min(all_response_times)
            max_response_time = max(all_response_times)
            response_time_std_dev = statistics.stdev(all_response_times) if len(all_response_times) > 1 else 0.0
        else:
            avg_response_time = min_response_time = max_response_time = response_time_std_dev = 0.0
        
        # Memory statistics
        all_memory_usage = single_results['memory_usage']
        peak_memory = max(max(all_memory_usage) if all_memory_usage else 0.0,
                         concurrent_results['concurrent_memory_peak'],
                         memory_results['peak_memory_mb'])
        
        memory_std_dev = statistics.stdev(all_memory_usage) if len(all_memory_usage) > 1 else 0.0
        
        # CPU statistics from resource samples
        cpu_samples = [sample['cpu_percent'] for sample in self.resource_samples if 'cpu_percent' in sample]
        cpu_avg = statistics.mean(cpu_samples) if cpu_samples else 0.0
        cpu_peak = max(cpu_samples) if cpu_samples else 0.0
        
        # Throughput calculation
        total_successful = single_results['successful_queries']
        test_duration_minutes = config.test_duration_seconds / 60.0
        throughput = total_successful / test_duration_minutes if test_duration_minutes > 0 else 0.0
        
        # Curriculum alignment
        curriculum_scores = single_results.get('curriculum_scores', [])
        curriculum_alignment = statistics.mean(curriculum_scores) if curriculum_scores else 0.8
        
        # System stability score
        total_queries = single_results['successful_queries'] + single_results['failed_queries']
        success_rate = single_results['successful_queries'] / total_queries if total_queries > 0 else 0.0
        stability_score = (success_rate + memory_results.get('memory_stability', 0.8)) / 2.0
        
        # Hardware efficiency score
        memory_efficiency = memory_results.get('memory_efficiency', 0.8)
        cpu_efficiency = max(0.0, 1.0 - (cpu_avg / 100.0)) if cpu_avg > 0 else 0.8
        hardware_efficiency = (memory_efficiency + cpu_efficiency) / 2.0
        
        # Create benchmark result
        benchmark = PerformanceBenchmark(
            average_response_time_ms=avg_response_time,
            peak_memory_usage_mb=peak_memory,
            throughput_queries_per_minute=throughput,
            concurrent_query_capacity=concurrent_results['max_concurrent'],
            curriculum_alignment_accuracy=curriculum_alignment,
            system_stability_score=stability_score,
            hardware_efficiency_score=hardware_efficiency,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            response_time_std_dev=response_time_std_dev,
            memory_usage_std_dev=memory_std_dev,
            cpu_utilization_avg=cpu_avg,
            cpu_utilization_peak=cpu_peak,
            test_duration_seconds=config.test_duration_seconds,
            total_queries_processed=total_queries,
            successful_queries=single_results['successful_queries'],
            failed_queries=single_results['failed_queries']
        )
        
        return benchmark
    
    def _estimate_curriculum_alignment(self, response: str) -> float:
        """Estimate curriculum alignment score for a response."""
        # Simple heuristic-based curriculum alignment estimation
        educational_terms = [
            'algoritma', 'struktur data', 'basis data', 'jaringan', 'pemrograman',
            'komputer', 'software', 'hardware', 'sistem', 'informasi'
        ]
        
        response_lower = response.lower()
        term_count = sum(1 for term in educational_terms if term in response_lower)
        
        # Score based on educational term density
        score = min(1.0, 0.5 + (term_count / len(educational_terms)) * 0.5)
        return score


# Utility functions
def create_performance_benchmarking_engine(
    pipeline: CompletePipeline,
    test_duration_seconds: float = 300.0,
    max_concurrent_queries: int = 5,
    memory_limit_mb: int = 4096
) -> PerformanceBenchmarkingEngine:
    """
    Create a performance benchmarking engine with recommended settings.
    
    Args:
        pipeline: Complete pipeline instance
        test_duration_seconds: Duration of benchmark test
        max_concurrent_queries: Maximum concurrent queries to test
        memory_limit_mb: Memory limit for testing
        
    Returns:
        PerformanceBenchmarkingEngine instance
    """
    config = BenchmarkConfig(
        test_duration_seconds=test_duration_seconds,
        max_concurrent_queries=max_concurrent_queries,
        memory_limit_mb=memory_limit_mb
    )
    
    return PerformanceBenchmarkingEngine(pipeline, config)


# Example usage
def example_benchmarking():
    """Example of how to use the performance benchmarking engine."""
    print("Performance Benchmarking Engine Example")
    print("This example shows how to use the PerformanceBenchmarkingEngine")
    
    # Create benchmark configuration
    config = BenchmarkConfig(
        test_duration_seconds=60.0,  # 1 minute test
        max_concurrent_queries=3,
        memory_limit_mb=4096
    )
    
    print(f"Configuration: {config}")
    print("Benchmarking engine would test:")
    print("1. Single-threaded performance")
    print("2. Concurrent processing capacity")
    print("3. Memory usage and stability")
    print("4. System reliability and throughput")


if __name__ == "__main__":
    example_benchmarking()