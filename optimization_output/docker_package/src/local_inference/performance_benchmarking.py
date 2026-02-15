"""
Performance benchmarking system for OpenClass Nexus AI Phase 3.

This module provides comprehensive performance benchmarking capabilities
including Indonesian educational query test suites, performance measurement
and reporting, and automated performance validation for the local inference system.
"""

import time
import json
import logging
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv

from .complete_pipeline import CompletePipeline
from .performance_monitor import PerformanceMetrics, PerformanceTracker


logger = logging.getLogger(__name__)


@dataclass
class BenchmarkQuery:
    """Individual benchmark query with expected characteristics."""
    query_id: str
    query_text: str
    subject: str
    grade_level: str
    difficulty: str  # "easy", "medium", "hard"
    expected_response_time_ms: float
    expected_min_response_length: int
    keywords_to_check: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark query execution."""
    query_id: str
    query_text: str
    response_text: str
    success: bool
    error_message: Optional[str] = None
    
    # Performance metrics
    response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    tokens_per_second: float = 0.0
    context_tokens: int = 0
    response_tokens: int = 0
    
    # Quality metrics
    response_length: int = 0
    contains_expected_keywords: bool = False
    educational_quality_score: float = 0.0
    
    # Timestamps
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime = field(default_factory=datetime.now)
    
    def meets_performance_targets(self, 
                                 max_response_time_ms: float = 10000,
                                 max_memory_mb: float = 3072,
                                 min_tokens_per_second: float = 5) -> bool:
        """Check if result meets performance targets."""
        return (
            self.success and
            self.response_time_ms <= max_response_time_ms and
            self.memory_usage_mb <= max_memory_mb and
            self.tokens_per_second >= min_tokens_per_second
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'query_id': self.query_id,
            'query_text': self.query_text,
            'response_text': self.response_text,
            'success': self.success,
            'error_message': self.error_message,
            'response_time_ms': self.response_time_ms,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'tokens_per_second': self.tokens_per_second,
            'context_tokens': self.context_tokens,
            'response_tokens': self.response_tokens,
            'response_length': self.response_length,
            'contains_expected_keywords': self.contains_expected_keywords,
            'educational_quality_score': self.educational_quality_score,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat()
        }


@dataclass
class BenchmarkSuite:
    """Collection of benchmark queries for comprehensive testing."""
    suite_name: str
    description: str
    queries: List[BenchmarkQuery] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_query(self, query: BenchmarkQuery) -> None:
        """Add a query to the benchmark suite."""
        self.queries.append(query)
    
    def get_queries_by_subject(self, subject: str) -> List[BenchmarkQuery]:
        """Get all queries for a specific subject."""
        return [q for q in self.queries if q.subject.lower() == subject.lower()]
    
    def get_queries_by_difficulty(self, difficulty: str) -> List[BenchmarkQuery]:
        """Get all queries for a specific difficulty level."""
        return [q for q in self.queries if q.difficulty.lower() == difficulty.lower()]


class IndonesianEducationalBenchmarks:
    """
    Indonesian educational benchmark query generator and manager.
    
    This class provides comprehensive benchmark queries covering various
    subjects and difficulty levels from the Indonesian curriculum.
    """
    
    def __init__(self):
        """Initialize the benchmark generator."""
        self.subjects = [
            "informatika", "matematika", "fisika", "kimia", "biologi",
            "bahasa_indonesia", "bahasa_inggris", "sejarah", "geografi",
            "ekonomi", "sosiologi", "pkn"
        ]
        
        self.grade_levels = ["kelas_10", "kelas_11", "kelas_12"]
        self.difficulties = ["easy", "medium", "hard"]
    
    def create_informatika_benchmark_suite(self) -> BenchmarkSuite:
        """Create comprehensive informatika (computer science) benchmark suite."""
        suite = BenchmarkSuite(
            suite_name="informatika_comprehensive",
            description="Comprehensive informatika benchmark covering programming, algorithms, and data structures"
        )
        
        # Easy queries
        easy_queries = [
            BenchmarkQuery(
                query_id="inf_easy_001",
                query_text="Apa itu variabel dalam pemrograman?",
                subject="informatika",
                grade_level="kelas_10",
                difficulty="easy",
                expected_response_time_ms=8000,
                expected_min_response_length=100,
                keywords_to_check=["variabel", "data", "nilai", "menyimpan"]
            ),
            BenchmarkQuery(
                query_id="inf_easy_002", 
                query_text="Jelaskan perbedaan antara algoritma dan program!",
                subject="informatika",
                grade_level="kelas_10",
                difficulty="easy",
                expected_response_time_ms=8000,
                expected_min_response_length=150,
                keywords_to_check=["algoritma", "program", "langkah", "instruksi"]
            ),
            BenchmarkQuery(
                query_id="inf_easy_003",
                query_text="Apa fungsi dari struktur data array?",
                subject="informatika",
                grade_level="kelas_11",
                difficulty="easy",
                expected_response_time_ms=7000,
                expected_min_response_length=120,
                keywords_to_check=["array", "data", "elemen", "indeks"]
            )
        ]
        
        # Medium queries
        medium_queries = [
            BenchmarkQuery(
                query_id="inf_med_001",
                query_text="Bagaimana cara kerja algoritma bubble sort? Berikan contoh implementasinya!",
                subject="informatika",
                grade_level="kelas_11",
                difficulty="medium",
                expected_response_time_ms=9000,
                expected_min_response_length=200,
                keywords_to_check=["bubble sort", "sorting", "perbandingan", "tukar"]
            ),
            BenchmarkQuery(
                query_id="inf_med_002",
                query_text="Jelaskan konsep rekursi dalam pemrograman dan berikan contoh fungsi rekursif!",
                subject="informatika",
                grade_level="kelas_12",
                difficulty="medium",
                expected_response_time_ms=9500,
                expected_min_response_length=250,
                keywords_to_check=["rekursi", "fungsi", "memanggil", "base case"]
            ),
            BenchmarkQuery(
                query_id="inf_med_003",
                query_text="Apa perbedaan antara stack dan queue? Kapan kita menggunakan masing-masing?",
                subject="informatika",
                grade_level="kelas_12",
                difficulty="medium",
                expected_response_time_ms=8500,
                expected_min_response_length=180,
                keywords_to_check=["stack", "queue", "LIFO", "FIFO"]
            )
        ]
        
        # Hard queries
        hard_queries = [
            BenchmarkQuery(
                query_id="inf_hard_001",
                query_text="Analisis kompleksitas waktu dari algoritma merge sort dan jelaskan mengapa lebih efisien dari bubble sort untuk dataset besar!",
                subject="informatika",
                grade_level="kelas_12",
                difficulty="hard",
                expected_response_time_ms=10000,
                expected_min_response_length=300,
                keywords_to_check=["merge sort", "kompleksitas", "O(n log n)", "efisien"]
            ),
            BenchmarkQuery(
                query_id="inf_hard_002",
                query_text="Bagaimana implementasi binary search tree dan operasi insert, delete, search? Jelaskan keuntungan penggunaannya!",
                subject="informatika",
                grade_level="kelas_12",
                difficulty="hard",
                expected_response_time_ms=12000,
                expected_min_response_length=400,
                keywords_to_check=["binary search tree", "BST", "insert", "delete", "search"]
            )
        ]
        
        # Add all queries to suite
        for query in easy_queries + medium_queries + hard_queries:
            suite.add_query(query)
        
        return suite
    
    def create_matematika_benchmark_suite(self) -> BenchmarkSuite:
        """Create comprehensive matematika benchmark suite."""
        suite = BenchmarkSuite(
            suite_name="matematika_comprehensive",
            description="Comprehensive matematika benchmark covering algebra, calculus, and statistics"
        )
        
        queries = [
            BenchmarkQuery(
                query_id="mat_easy_001",
                query_text="Bagaimana cara menyelesaikan persamaan linear satu variabel?",
                subject="matematika",
                grade_level="kelas_10",
                difficulty="easy",
                expected_response_time_ms=7000,
                expected_min_response_length=120,
                keywords_to_check=["persamaan linear", "variabel", "penyelesaian"]
            ),
            BenchmarkQuery(
                query_id="mat_med_001",
                query_text="Jelaskan konsep turunan dalam kalkulus dan berikan contoh aplikasinya!",
                subject="matematika",
                grade_level="kelas_12",
                difficulty="medium",
                expected_response_time_ms=9000,
                expected_min_response_length=200,
                keywords_to_check=["turunan", "kalkulus", "limit", "aplikasi"]
            ),
            BenchmarkQuery(
                query_id="mat_hard_001",
                query_text="Bagaimana cara menghitung integral tentu menggunakan teorema fundamental kalkulus?",
                subject="matematika",
                grade_level="kelas_12",
                difficulty="hard",
                expected_response_time_ms=10000,
                expected_min_response_length=250,
                keywords_to_check=["integral tentu", "teorema fundamental", "kalkulus"]
            )
        ]
        
        for query in queries:
            suite.add_query(query)
        
        return suite
    
    def create_mixed_subjects_benchmark_suite(self) -> BenchmarkSuite:
        """Create benchmark suite with mixed subjects."""
        suite = BenchmarkSuite(
            suite_name="mixed_subjects",
            description="Mixed subjects benchmark for comprehensive testing"
        )
        
        queries = [
            # Fisika
            BenchmarkQuery(
                query_id="fis_001",
                query_text="Jelaskan hukum Newton pertama dan berikan contoh penerapannya!",
                subject="fisika",
                grade_level="kelas_10",
                difficulty="medium",
                expected_response_time_ms=8000,
                expected_min_response_length=150,
                keywords_to_check=["hukum Newton", "inersia", "gaya"]
            ),
            # Kimia
            BenchmarkQuery(
                query_id="kim_001",
                query_text="Apa yang dimaksud dengan ikatan kovalen dan bagaimana terbentuknya?",
                subject="kimia",
                grade_level="kelas_10",
                difficulty="medium",
                expected_response_time_ms=8500,
                expected_min_response_length=140,
                keywords_to_check=["ikatan kovalen", "elektron", "atom"]
            ),
            # Biologi
            BenchmarkQuery(
                query_id="bio_001",
                query_text="Jelaskan proses fotosintesis pada tumbuhan!",
                subject="biologi",
                grade_level="kelas_10",
                difficulty="easy",
                expected_response_time_ms=7500,
                expected_min_response_length=130,
                keywords_to_check=["fotosintesis", "klorofil", "glukosa", "oksigen"]
            )
        ]
        
        for query in queries:
            suite.add_query(query)
        
        return suite
    
    def get_all_benchmark_suites(self) -> List[BenchmarkSuite]:
        """Get all available benchmark suites."""
        return [
            self.create_informatika_benchmark_suite(),
            self.create_matematika_benchmark_suite(),
            self.create_mixed_subjects_benchmark_suite()
        ]

class PerformanceBenchmarkRunner:
    """
    Performance benchmark runner for comprehensive testing.
    
    This class executes benchmark suites against the complete pipeline
    and provides detailed performance analysis and reporting.
    """
    
    def __init__(self, 
                 pipeline: CompletePipeline,
                 performance_tracker: Optional[PerformanceTracker] = None):
        """
        Initialize benchmark runner.
        
        Args:
            pipeline: Complete pipeline to benchmark
            performance_tracker: Optional performance tracker for detailed metrics
        """
        self.pipeline = pipeline
        self.performance_tracker = performance_tracker
        self.benchmark_generator = IndonesianEducationalBenchmarks()
        
        # Results storage
        self.benchmark_results: List[BenchmarkResult] = []
        self.suite_results: Dict[str, List[BenchmarkResult]] = {}
        
        logger.info("PerformanceBenchmarkRunner initialized")
    
    def run_benchmark_suite(self, 
                           suite: BenchmarkSuite,
                           concurrent_queries: int = 1,
                           warmup_queries: int = 2) -> Dict[str, Any]:
        """
        Run a complete benchmark suite.
        
        Args:
            suite: Benchmark suite to execute
            concurrent_queries: Number of concurrent queries (for load testing)
            warmup_queries: Number of warmup queries to run first
            
        Returns:
            Dict with comprehensive benchmark results
        """
        logger.info(f"Starting benchmark suite: {suite.suite_name}")
        logger.info(f"Total queries: {len(suite.queries)}")
        logger.info(f"Concurrent queries: {concurrent_queries}")
        
        start_time = datetime.now()
        suite_results = []
        
        try:
            # Warmup phase
            if warmup_queries > 0:
                logger.info(f"Running {warmup_queries} warmup queries...")
                warmup_suite = BenchmarkSuite(
                    suite_name="warmup",
                    description="Warmup queries"
                )
                # Use first few queries for warmup
                for i in range(min(warmup_queries, len(suite.queries))):
                    warmup_suite.add_query(suite.queries[i])
                
                self._run_queries_sequential(warmup_suite.queries)
                logger.info("Warmup completed")
            
            # Main benchmark execution
            if concurrent_queries == 1:
                # Sequential execution
                suite_results = self._run_queries_sequential(suite.queries)
            else:
                # Concurrent execution
                suite_results = self._run_queries_concurrent(suite.queries, concurrent_queries)
            
            # Store results
            self.suite_results[suite.suite_name] = suite_results
            self.benchmark_results.extend(suite_results)
            
            # Calculate suite statistics
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            suite_stats = self._calculate_suite_statistics(suite_results, total_time)
            suite_stats['suite_name'] = suite.suite_name
            suite_stats['suite_description'] = suite.description
            suite_stats['total_queries'] = len(suite.queries)
            suite_stats['concurrent_queries'] = concurrent_queries
            suite_stats['warmup_queries'] = warmup_queries
            suite_stats['started_at'] = start_time.isoformat()
            suite_stats['completed_at'] = end_time.isoformat()
            
            logger.info(f"Benchmark suite completed in {total_time:.2f} seconds")
            logger.info(f"Success rate: {suite_stats['success_rate']:.1f}%")
            logger.info(f"Average response time: {suite_stats['avg_response_time_ms']:.1f}ms")
            
            return suite_stats
            
        except Exception as e:
            logger.error(f"Benchmark suite failed: {e}")
            return {
                'suite_name': suite.suite_name,
                'error': str(e),
                'success': False,
                'started_at': start_time.isoformat(),
                'failed_at': datetime.now().isoformat()
            }
    
    def run_all_benchmarks(self, concurrent_queries: int = 1) -> Dict[str, Any]:
        """
        Run all available benchmark suites.
        
        Args:
            concurrent_queries: Number of concurrent queries for each suite
            
        Returns:
            Dict with results from all benchmark suites
        """
        logger.info("Starting comprehensive benchmark run")
        
        all_suites = self.benchmark_generator.get_all_benchmark_suites()
        all_results = {}
        overall_start = datetime.now()
        
        for suite in all_suites:
            logger.info(f"Running suite: {suite.suite_name}")
            suite_result = self.run_benchmark_suite(suite, concurrent_queries)
            all_results[suite.suite_name] = suite_result
        
        # Calculate overall statistics
        overall_end = datetime.now()
        overall_time = (overall_end - overall_start).total_seconds()
        
        all_results['overall_summary'] = {
            'total_suites': len(all_suites),
            'total_queries': sum(len(suite.queries) for suite in all_suites),
            'total_time_seconds': overall_time,
            'started_at': overall_start.isoformat(),
            'completed_at': overall_end.isoformat(),
            'concurrent_queries': concurrent_queries
        }
        
        # Add aggregated statistics
        all_suite_results = []
        for suite_results in self.suite_results.values():
            all_suite_results.extend(suite_results)
        
        if all_suite_results:
            overall_stats = self._calculate_suite_statistics(all_suite_results, overall_time)
            all_results['overall_summary'].update(overall_stats)
        
        logger.info(f"All benchmarks completed in {overall_time:.2f} seconds")
        return all_results
    
    def _run_queries_sequential(self, queries: List[BenchmarkQuery]) -> List[BenchmarkResult]:
        """Run queries sequentially."""
        results = []
        
        for i, query in enumerate(queries):
            logger.debug(f"Running query {i+1}/{len(queries)}: {query.query_id}")
            result = self._execute_single_query(query)
            results.append(result)
            
            # Small delay between queries to avoid overwhelming the system
            time.sleep(0.1)
        
        return results
    
    def _run_queries_concurrent(self, 
                               queries: List[BenchmarkQuery], 
                               max_workers: int) -> List[BenchmarkResult]:
        """Run queries concurrently."""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all queries
            future_to_query = {
                executor.submit(self._execute_single_query, query): query 
                for query in queries
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.debug(f"Completed query: {query.query_id}")
                except Exception as e:
                    logger.error(f"Query {query.query_id} failed: {e}")
                    # Create failed result
                    failed_result = BenchmarkResult(
                        query_id=query.query_id,
                        query_text=query.query_text,
                        response_text="",
                        success=False,
                        error_message=str(e)
                    )
                    results.append(failed_result)
        
        # Sort results by query_id to maintain order
        results.sort(key=lambda r: r.query_id)
        return results
    
    def _execute_single_query(self, query: BenchmarkQuery) -> BenchmarkResult:
        """Execute a single benchmark query."""
        start_time = datetime.now()
        
        try:
            # Get initial system state
            initial_memory = 0.0
            if hasattr(self.pipeline, 'memory_monitor') and self.pipeline.memory_monitor:
                initial_memory = self.pipeline.memory_monitor.get_memory_usage()
            
            # Execute query through pipeline
            query_start = time.time()
            
            result = self.pipeline.process_query(
                query=query.query_text,
                subject_filter=query.subject,
                grade_filter=query.grade_level
            )
            
            query_end = time.time()
            response_time_ms = (query_end - query_start) * 1000
            
            # Get final system state
            final_memory = initial_memory
            if hasattr(self.pipeline, 'memory_monitor') and self.pipeline.memory_monitor:
                final_memory = self.pipeline.memory_monitor.get_memory_usage()
            
            # Extract response text
            if hasattr(result, 'response'):
                response_text = result.response
                context_tokens = result.context_stats.get('context_tokens', 0)
            else:
                response_text = str(result)
                context_tokens = 0
            
            # Calculate metrics
            response_tokens = len(response_text.split())
            tokens_per_second = response_tokens / (response_time_ms / 1000) if response_time_ms > 0 else 0
            
            # Check for expected keywords
            contains_keywords = self._check_keywords(response_text, query.keywords_to_check)
            
            # Calculate educational quality score (simple heuristic)
            quality_score = self._calculate_educational_quality_score(
                response_text, query.keywords_to_check, query.expected_min_response_length
            )
            
            # Create successful result
            benchmark_result = BenchmarkResult(
                query_id=query.query_id,
                query_text=query.query_text,
                response_text=response_text,
                success=True,
                response_time_ms=response_time_ms,
                memory_usage_mb=final_memory,
                cpu_usage_percent=0.0,  # Would need additional monitoring
                tokens_per_second=tokens_per_second,
                context_tokens=context_tokens,
                response_tokens=response_tokens,
                response_length=len(response_text),
                contains_expected_keywords=contains_keywords,
                educational_quality_score=quality_score,
                started_at=start_time,
                completed_at=datetime.now()
            )
            
            logger.debug(f"Query {query.query_id} completed successfully in {response_time_ms:.1f}ms")
            return benchmark_result
            
        except Exception as e:
            logger.error(f"Query {query.query_id} failed: {e}")
            
            return BenchmarkResult(
                query_id=query.query_id,
                query_text=query.query_text,
                response_text="",
                success=False,
                error_message=str(e),
                started_at=start_time,
                completed_at=datetime.now()
            )
    
    def _check_keywords(self, response_text: str, keywords: List[str]) -> bool:
        """Check if response contains expected keywords."""
        if not keywords:
            return True
        
        response_lower = response_text.lower()
        found_keywords = sum(1 for keyword in keywords if keyword.lower() in response_lower)
        
        # Consider successful if at least 50% of keywords are found
        return found_keywords >= len(keywords) * 0.5
    
    def _calculate_educational_quality_score(self, 
                                           response_text: str, 
                                           keywords: List[str],
                                           min_length: int) -> float:
        """Calculate educational quality score (0.0 to 1.0)."""
        score = 0.0
        
        # Length score (0.3 weight)
        if len(response_text) >= min_length:
            score += 0.3
        else:
            score += 0.3 * (len(response_text) / min_length)
        
        # Keyword coverage score (0.4 weight)
        if keywords:
            response_lower = response_text.lower()
            found_keywords = sum(1 for keyword in keywords if keyword.lower() in response_lower)
            keyword_score = found_keywords / len(keywords)
            score += 0.4 * keyword_score
        else:
            score += 0.4  # No keywords to check
        
        # Structure score (0.3 weight) - simple heuristics
        sentences = response_text.split('.')
        if len(sentences) >= 3:  # At least 3 sentences
            score += 0.15
        
        if any(word in response_text.lower() for word in ['contoh', 'misalnya', 'yaitu']):
            score += 0.15  # Contains examples
        
        return min(score, 1.0)
    
    def _calculate_suite_statistics(self, 
                                  results: List[BenchmarkResult], 
                                  total_time: float) -> Dict[str, Any]:
        """Calculate comprehensive statistics for a suite of results."""
        if not results:
            return {'error': 'No results to analyze'}
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        stats = {
            'total_queries': len(results),
            'successful_queries': len(successful_results),
            'failed_queries': len(failed_results),
            'success_rate': (len(successful_results) / len(results)) * 100,
            'total_execution_time_seconds': total_time
        }
        
        if successful_results:
            # Response time statistics
            response_times = [r.response_time_ms for r in successful_results]
            stats.update({
                'avg_response_time_ms': statistics.mean(response_times),
                'median_response_time_ms': statistics.median(response_times),
                'min_response_time_ms': min(response_times),
                'max_response_time_ms': max(response_times),
                'response_time_std_dev': statistics.stdev(response_times) if len(response_times) > 1 else 0
            })
            
            # Memory usage statistics
            memory_usage = [r.memory_usage_mb for r in successful_results if r.memory_usage_mb > 0]
            if memory_usage:
                stats.update({
                    'avg_memory_usage_mb': statistics.mean(memory_usage),
                    'max_memory_usage_mb': max(memory_usage),
                    'min_memory_usage_mb': min(memory_usage)
                })
            
            # Token generation statistics
            token_rates = [r.tokens_per_second for r in successful_results if r.tokens_per_second > 0]
            if token_rates:
                stats.update({
                    'avg_tokens_per_second': statistics.mean(token_rates),
                    'min_tokens_per_second': min(token_rates),
                    'max_tokens_per_second': max(token_rates)
                })
            
            # Quality statistics
            quality_scores = [r.educational_quality_score for r in successful_results]
            stats.update({
                'avg_educational_quality_score': statistics.mean(quality_scores),
                'min_educational_quality_score': min(quality_scores),
                'max_educational_quality_score': max(quality_scores)
            })
            
            # Performance target compliance
            target_compliant = [
                r for r in successful_results 
                if r.meets_performance_targets()
            ]
            stats['performance_target_compliance_rate'] = (
                len(target_compliant) / len(successful_results)
            ) * 100
            
            # Throughput calculation
            if total_time > 0:
                stats['queries_per_second'] = len(successful_results) / total_time
                stats['queries_per_minute'] = (len(successful_results) / total_time) * 60
        
        return stats
    
    def generate_performance_report(self, 
                                  output_file: Optional[Path] = None,
                                  format: str = 'json') -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Args:
            output_file: Optional file to save report
            format: Report format ('json', 'html', 'csv')
            
        Returns:
            Dict with complete performance report
        """
        if not self.benchmark_results:
            return {'error': 'No benchmark results available'}
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_benchmark_results': len(self.benchmark_results),
                'total_suites_run': len(self.suite_results),
                'format': format
            },
            'executive_summary': self._generate_executive_summary(),
            'detailed_results': {},
            'performance_analysis': self._generate_performance_analysis(),
            'recommendations': self._generate_recommendations()
        }
        
        # Add detailed results for each suite
        for suite_name, results in self.suite_results.items():
            suite_stats = self._calculate_suite_statistics(results, 0)  # Time not relevant here
            report['detailed_results'][suite_name] = {
                'statistics': suite_stats,
                'individual_results': [r.to_dict() for r in results]
            }
        
        # Save report if requested
        if output_file:
            self._save_report(report, output_file, format)
        
        return report
    
    def _generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary of benchmark results."""
        all_results = self.benchmark_results
        successful_results = [r for r in all_results if r.success]
        
        if not all_results:
            return {'error': 'No results available'}
        
        summary = {
            'overall_success_rate': (len(successful_results) / len(all_results)) * 100,
            'total_queries_tested': len(all_results),
            'successful_queries': len(successful_results),
            'failed_queries': len(all_results) - len(successful_results)
        }
        
        if successful_results:
            response_times = [r.response_time_ms for r in successful_results]
            memory_usage = [r.memory_usage_mb for r in successful_results if r.memory_usage_mb > 0]
            quality_scores = [r.educational_quality_score for r in successful_results]
            
            summary.update({
                'average_response_time_ms': statistics.mean(response_times),
                'response_time_95th_percentile_ms': self._calculate_percentile(response_times, 95),
                'average_memory_usage_mb': statistics.mean(memory_usage) if memory_usage else 0,
                'average_educational_quality_score': statistics.mean(quality_scores),
                'performance_targets_met_rate': sum(
                    1 for r in successful_results if r.meets_performance_targets()
                ) / len(successful_results) * 100
            })
        
        return summary
    
    def _generate_performance_analysis(self) -> Dict[str, Any]:
        """Generate detailed performance analysis."""
        successful_results = [r for r in self.benchmark_results if r.success]
        
        if not successful_results:
            return {'error': 'No successful results for analysis'}
        
        analysis = {}
        
        # Response time analysis
        response_times = [r.response_time_ms for r in successful_results]
        analysis['response_time_analysis'] = {
            'mean_ms': statistics.mean(response_times),
            'median_ms': statistics.median(response_times),
            'std_dev_ms': statistics.stdev(response_times) if len(response_times) > 1 else 0,
            'min_ms': min(response_times),
            'max_ms': max(response_times),
            'percentiles': {
                '50th': self._calculate_percentile(response_times, 50),
                '75th': self._calculate_percentile(response_times, 75),
                '90th': self._calculate_percentile(response_times, 90),
                '95th': self._calculate_percentile(response_times, 95),
                '99th': self._calculate_percentile(response_times, 99)
            }
        }
        
        # Performance by difficulty
        analysis['performance_by_difficulty'] = {}
        for difficulty in ['easy', 'medium', 'hard']:
            difficulty_results = [
                r for r in successful_results 
                if difficulty in r.query_id.lower()
            ]
            if difficulty_results:
                difficulty_times = [r.response_time_ms for r in difficulty_results]
                analysis['performance_by_difficulty'][difficulty] = {
                    'count': len(difficulty_results),
                    'avg_response_time_ms': statistics.mean(difficulty_times),
                    'avg_quality_score': statistics.mean([r.educational_quality_score for r in difficulty_results])
                }
        
        # Performance by subject
        analysis['performance_by_subject'] = {}
        subjects = set()
        for result in successful_results:
            # Extract subject from query_id (assuming format like "inf_easy_001")
            parts = result.query_id.split('_')
            if len(parts) >= 2:
                subjects.add(parts[0])
        
        for subject in subjects:
            subject_results = [
                r for r in successful_results 
                if r.query_id.startswith(subject + '_')
            ]
            if subject_results:
                subject_times = [r.response_time_ms for r in subject_results]
                analysis['performance_by_subject'][subject] = {
                    'count': len(subject_results),
                    'avg_response_time_ms': statistics.mean(subject_times),
                    'avg_quality_score': statistics.mean([r.educational_quality_score for r in subject_results]),
                    'success_rate': 100.0  # These are already successful results
                }
        
        return analysis
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        successful_results = [r for r in self.benchmark_results if r.success]
        
        if not successful_results:
            recommendations.append("No successful results available for analysis")
            return recommendations
        
        # Response time recommendations
        avg_response_time = statistics.mean([r.response_time_ms for r in successful_results])
        if avg_response_time > 8000:  # 8 seconds
            recommendations.append(
                f"Average response time ({avg_response_time:.1f}ms) exceeds 8 seconds. "
                "Consider reducing context window size or optimizing model parameters."
            )
        
        # Memory usage recommendations
        memory_usage = [r.memory_usage_mb for r in successful_results if r.memory_usage_mb > 0]
        if memory_usage:
            avg_memory = statistics.mean(memory_usage)
            if avg_memory > 2800:  # Close to 3GB limit
                recommendations.append(
                    f"High memory usage detected ({avg_memory:.1f}MB). "
                    "Consider implementing more aggressive memory management."
                )
        
        # Quality score recommendations
        avg_quality = statistics.mean([r.educational_quality_score for r in successful_results])
        if avg_quality < 0.7:
            recommendations.append(
                f"Educational quality score ({avg_quality:.2f}) could be improved. "
                "Consider enhancing prompt templates or context retrieval."
            )
        
        # Performance target compliance
        compliant_results = [r for r in successful_results if r.meets_performance_targets()]
        compliance_rate = len(compliant_results) / len(successful_results) * 100
        
        if compliance_rate < 80:
            recommendations.append(
                f"Performance target compliance ({compliance_rate:.1f}%) is below 80%. "
                "Review system configuration and resource allocation."
            )
        
        # Token generation rate
        token_rates = [r.tokens_per_second for r in successful_results if r.tokens_per_second > 0]
        if token_rates:
            avg_token_rate = statistics.mean(token_rates)
            if avg_token_rate < 7:
                recommendations.append(
                    f"Token generation rate ({avg_token_rate:.1f} tokens/sec) is below optimal. "
                    "Consider optimizing inference parameters or hardware utilization."
                )
        
        if not recommendations:
            recommendations.append("Performance is within acceptable ranges. No immediate optimizations needed.")
        
        return recommendations
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value from data."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            
            if upper_index >= len(sorted_data):
                return sorted_data[lower_index]
            
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
    
    def _save_report(self, report: Dict[str, Any], output_file: Path, format: str) -> None:
        """Save report to file in specified format."""
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'csv':
                # Save detailed results as CSV
                csv_data = []
                for suite_name, suite_data in report['detailed_results'].items():
                    for result in suite_data['individual_results']:
                        result['suite_name'] = suite_name
                        csv_data.append(result)
                
                if csv_data:
                    with open(output_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                        writer.writeheader()
                        writer.writerows(csv_data)
            
            elif format.lower() == 'html':
                # Generate simple HTML report
                html_content = self._generate_html_report(report)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            logger.info(f"Report saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
    
    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML report content."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OpenClass Nexus AI Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; }}
                .metric {{ margin: 10px 0; }}
                .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>OpenClass Nexus AI Performance Report</h1>
            <p>Generated: {report['report_metadata']['generated_at']}</p>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <div class="metric">Success Rate: {report['executive_summary'].get('overall_success_rate', 0):.1f}%</div>
                <div class="metric">Total Queries: {report['executive_summary'].get('total_queries_tested', 0)}</div>
                <div class="metric">Average Response Time: {report['executive_summary'].get('average_response_time_ms', 0):.1f}ms</div>
                <div class="metric">Average Quality Score: {report['executive_summary'].get('average_educational_quality_score', 0):.2f}</div>
            </div>
            
            <div class="recommendations">
                <h2>Recommendations</h2>
                <ul>
        """
        
        for rec in report.get('recommendations', []):
            html += f"<li>{rec}</li>"
        
        html += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html


# Utility functions
def create_benchmark_runner(pipeline: CompletePipeline) -> PerformanceBenchmarkRunner:
    """
    Create a benchmark runner with recommended settings.
    
    Args:
        pipeline: Complete pipeline to benchmark
        
    Returns:
        PerformanceBenchmarkRunner instance
    """
    performance_tracker = None
    if hasattr(pipeline, 'performance_tracker') and pipeline.performance_tracker:
        performance_tracker = pipeline.performance_tracker
    
    return PerformanceBenchmarkRunner(
        pipeline=pipeline,
        performance_tracker=performance_tracker
    )


def run_quick_benchmark(pipeline: CompletePipeline) -> Dict[str, Any]:
    """
    Run a quick benchmark with a small set of queries.
    
    Args:
        pipeline: Complete pipeline to benchmark
        
    Returns:
        Dict with benchmark results
    """
    runner = create_benchmark_runner(pipeline)
    generator = IndonesianEducationalBenchmarks()
    
    # Create a small test suite
    quick_suite = BenchmarkSuite(
        suite_name="quick_test",
        description="Quick performance test"
    )
    
    # Add a few representative queries
    informatika_suite = generator.create_informatika_benchmark_suite()
    quick_suite.queries = informatika_suite.queries[:3]  # First 3 queries
    
    return runner.run_benchmark_suite(quick_suite)


# Example usage
def example_benchmarking():
    """Example of how to use the performance benchmarking system."""
    print("Performance Benchmarking Example")
    print("This example shows how to use the benchmarking system")
    print("In practice, you would initialize with a real CompletePipeline")
    
    # Example benchmark suite creation
    generator = IndonesianEducationalBenchmarks()
    informatika_suite = generator.create_informatika_benchmark_suite()
    
    print(f"Created informatika benchmark suite with {len(informatika_suite.queries)} queries")
    print("Benchmark runner would execute these queries and measure performance")
    print("Results would include response times, memory usage, and educational quality scores")


if __name__ == "__main__":
    example_benchmarking()