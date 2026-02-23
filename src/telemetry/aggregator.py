"""
Metrics Aggregator Module

Aggregates collected metrics for batch upload to DynamoDB.
Calculates percentiles, error rates, and storage usage.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
import os
import statistics


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for upload to DynamoDB"""
    school_id: str  # Anonymized hash
    timestamp: int  # Unix timestamp
    
    # Query metrics
    total_queries: int
    successful_queries: int
    failed_queries: int
    average_latency_ms: float
    p50_latency_ms: float
    p90_latency_ms: float
    p99_latency_ms: float
    
    # System metrics
    model_version: str
    embedding_model: str
    chromadb_version: str
    
    # Error metrics
    error_rate: float
    error_types: Dict[str, int]
    
    # Storage metrics
    chromadb_size_mb: float
    postgres_size_mb: float
    disk_usage_percent: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DynamoDB"""
        return {
            'school_id': self.school_id,
            'timestamp': self.timestamp,
            'total_queries': self.total_queries,
            'successful_queries': self.successful_queries,
            'failed_queries': self.failed_queries,
            'average_latency_ms': self.average_latency_ms,
            'p50_latency_ms': self.p50_latency_ms,
            'p90_latency_ms': self.p90_latency_ms,
            'p99_latency_ms': self.p99_latency_ms,
            'model_version': self.model_version,
            'embedding_model': self.embedding_model,
            'chromadb_version': self.chromadb_version,
            'error_rate': self.error_rate,
            'error_types': self.error_types,
            'chromadb_size_mb': self.chromadb_size_mb,
            'postgres_size_mb': self.postgres_size_mb,
            'disk_usage_percent': self.disk_usage_percent
        }


@dataclass
class StorageMetrics:
    """Storage usage metrics"""
    chromadb_size_mb: float
    postgres_size_mb: float
    disk_usage_percent: float


class MetricsAggregator:
    """
    Aggregates telemetry metrics for batch upload.
    
    Calculates percentiles, error rates, and storage usage.
    """
    
    def __init__(self, school_id: str):
        """
        Initialize metrics aggregator.
        
        Args:
            school_id: Anonymized school identifier
        """
        self.school_id = school_id
    
    def aggregate_hourly(self, snapshot: 'MetricsSnapshot') -> AggregatedMetrics:
        """
        Aggregate metrics from snapshot.
        
        Args:
            snapshot: Metrics snapshot from collector
            
        Returns:
            AggregatedMetrics ready for upload
        """
        # Calculate latency percentiles
        latencies = snapshot.latencies
        if latencies:
            avg_latency = statistics.mean(latencies)
            p50 = self._calculate_percentile(latencies, 50)
            p90 = self._calculate_percentile(latencies, 90)
            p99 = self._calculate_percentile(latencies, 99)
        else:
            avg_latency = p50 = p90 = p99 = 0.0
        
        # Calculate error rate
        error_rate = (snapshot.failed_queries / snapshot.total_queries 
                     if snapshot.total_queries > 0 else 0.0)
        
        # Aggregate error types
        error_types = {}
        for error in snapshot.errors:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Get storage metrics
        storage = self.get_storage_usage()
        
        # Get system versions
        model_version = os.getenv('MODEL_VERSION', 'llama-3.2-3b-q4')
        embedding_model = os.getenv('EMBEDDING_MODEL', 'amazon.titan-embed-text-v1')
        chromadb_version = os.getenv('CHROMADB_VERSION', '0.4.0')
        
        return AggregatedMetrics(
            school_id=self.school_id,
            timestamp=int(snapshot.timestamp.timestamp()),
            total_queries=snapshot.total_queries,
            successful_queries=snapshot.successful_queries,
            failed_queries=snapshot.failed_queries,
            average_latency_ms=avg_latency,
            p50_latency_ms=p50,
            p90_latency_ms=p90,
            p99_latency_ms=p99,
            model_version=model_version,
            embedding_model=embedding_model,
            chromadb_version=chromadb_version,
            error_rate=error_rate,
            error_types=error_types,
            chromadb_size_mb=storage.chromadb_size_mb,
            postgres_size_mb=storage.postgres_size_mb,
            disk_usage_percent=storage.disk_usage_percent
        )
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """
        Calculate percentile value.
        
        Args:
            values: List of values
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Percentile value
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100.0) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            fraction = index - int(index)
            return lower + (upper - lower) * fraction
    
    def get_storage_usage(self) -> StorageMetrics:
        """
        Get storage usage metrics.
        
        Returns:
            StorageMetrics with current usage
        """
        # Get ChromaDB size
        chromadb_path = os.getenv('CHROMADB_PATH', 'data/vector_db')
        chromadb_size = self._get_directory_size(chromadb_path)
        
        # Get PostgreSQL size (estimate from data directory)
        postgres_path = os.getenv('POSTGRES_DATA_PATH', 'data/postgres')
        postgres_size = self._get_directory_size(postgres_path)
        
        # Get disk usage
        disk_usage = self._get_disk_usage()
        
        return StorageMetrics(
            chromadb_size_mb=chromadb_size,
            postgres_size_mb=postgres_size,
            disk_usage_percent=disk_usage
        )
    
    def _get_directory_size(self, path: str) -> float:
        """
        Get directory size in MB.
        
        Args:
            path: Directory path
            
        Returns:
            Size in MB
        """
        if not os.path.exists(path):
            return 0.0
        
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except (OSError, PermissionError):
            return 0.0
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def _get_disk_usage(self) -> float:
        """
        Get disk usage percentage.
        
        Returns:
            Disk usage as percentage (0-100)
        """
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            return (used / total) * 100
        except Exception:
            return 0.0
