"""
Telemetry Module

Provides anonymized usage metrics collection and upload to AWS DynamoDB.
Enforces privacy by architecture - NO PII can ever be transmitted.
"""

from src.telemetry.collector import TelemetryCollector, get_collector, MetricsSnapshot
from src.telemetry.aggregator import MetricsAggregator, AggregatedMetrics, StorageMetrics
from src.telemetry.pii_verifier import PIIVerifier, PIIMatch
from src.telemetry.anonymizer import Anonymizer, get_anonymizer
from src.telemetry.uploader import TelemetryUploader, check_internet_connectivity

__all__ = [
    'TelemetryCollector',
    'get_collector',
    'MetricsSnapshot',
    'MetricsAggregator',
    'AggregatedMetrics',
    'StorageMetrics',
    'PIIVerifier',
    'PIIMatch',
    'Anonymizer',
    'get_anonymizer',
    'TelemetryUploader',
    'check_internet_connectivity',
]
