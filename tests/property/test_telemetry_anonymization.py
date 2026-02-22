"""
Property Test: Telemetry Data Anonymization

**Property 23: Telemetry Data Anonymization**
**Validates: Requirements 9.1, 9.2, 9.4, 9.5**

This property test verifies that:
1. Telemetry data contains ONLY anonymized metrics (no PII)
2. School IDs are properly anonymized using one-way hashing
3. NO chat content, user data, or personal information is included
4. PII verification correctly rejects data containing PII patterns
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timezone
import re

from src.telemetry.aggregator import AggregatedMetrics, MetricsAggregator
from src.telemetry.pii_verifier import PIIVerifier
from src.telemetry.anonymizer import Anonymizer


# Strategy for generating valid anonymized metrics
@st.composite
def valid_metrics(draw):
    """Generate valid anonymized metrics"""
    return AggregatedMetrics(
        school_id=f"school_{draw(st.text(alphabet='0123456789abcdef', min_size=16, max_size=16))}",
        timestamp=draw(st.integers(min_value=1600000000, max_value=2000000000)),
        total_queries=draw(st.integers(min_value=0, max_value=10000)),
        successful_queries=draw(st.integers(min_value=0, max_value=10000)),
        failed_queries=draw(st.integers(min_value=0, max_value=1000)),
        average_latency_ms=draw(st.floats(min_value=0, max_value=30000)),
        p50_latency_ms=draw(st.floats(min_value=0, max_value=30000)),
        p90_latency_ms=draw(st.floats(min_value=0, max_value=30000)),
        p99_latency_ms=draw(st.floats(min_value=0, max_value=30000)),
        model_version=draw(st.sampled_from(['llama-3.2-3b-q4', 'llama-3.1-8b-q4'])),
        embedding_model=draw(st.sampled_from(['amazon.titan-embed-text-v1', 'local-minilm'])),
        chromadb_version=draw(st.sampled_from(['0.4.0', '0.4.1', '0.4.2'])),
        error_rate=draw(st.floats(min_value=0.0, max_value=1.0)),
        error_types=draw(st.dictionaries(
            keys=st.sampled_from(['timeout', 'oom', 'model_error', 'network_error']),
            values=st.integers(min_value=0, max_value=100),
            max_size=4
        )),
        chromadb_size_mb=draw(st.floats(min_value=0, max_value=100000)),
        postgres_size_mb=draw(st.floats(min_value=0, max_value=100000)),
        disk_usage_percent=draw(st.floats(min_value=0, max_value=100))
    )


# Strategy for generating PII-containing data
@st.composite
def pii_data(draw):
    """Generate data containing PII"""
    pii_type = draw(st.sampled_from(['nik', 'email', 'phone', 'name', 'username', 'chat']))
    
    if pii_type == 'nik':
        # Indonesian National ID (16 digits)
        return {'nik': draw(st.text(alphabet='0123456789', min_size=16, max_size=16))}
    elif pii_type == 'email':
        # Email address
        username = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=10))
        domain = draw(st.sampled_from(['gmail.com', 'yahoo.com', 'example.com']))
        return {'email': f"{username}@{domain}"}
    elif pii_type == 'phone':
        # Indonesian phone number
        phone = draw(st.text(alphabet='0123456789', min_size=10, max_size=12))
        return {'phone': f"+62{phone}"}
    elif pii_type == 'name':
        # Name pattern
        return {'name': 'Nama: John Doe'}
    elif pii_type == 'username':
        # Username
        return {'username': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=10))}
    else:
        # Chat content
        return {'chat': 'This is a student question about math'}


@given(metrics=valid_metrics())
@settings(max_examples=100, deadline=None)
def test_valid_metrics_pass_pii_verification(metrics):
    """
    Property: Valid anonymized metrics should always pass PII verification
    
    Validates: Requirements 9.1, 9.2, 9.5
    """
    verifier = PIIVerifier()
    metrics_dict = metrics.to_dict()
    
    # Valid metrics should pass verification
    assert verifier.verify_no_pii(metrics_dict), \
        f"Valid metrics failed PII verification: {metrics_dict}"


@given(school_id=st.text(min_size=1, max_size=50))
@settings(max_examples=100, deadline=None)
def test_school_id_anonymization_is_one_way(school_id):
    """
    Property: School ID anonymization is one-way (cannot be reversed)
    
    Validates: Requirement 9.4
    """
    anonymizer = Anonymizer(salt='test-salt-123')
    
    # Anonymize school ID
    anonymized = anonymizer.anonymize_school_id(school_id)
    
    # Check format
    assert anonymized.startswith('school_'), \
        f"Anonymized ID should start with 'school_': {anonymized}"
    
    # 'school_' (7 chars) + 16 hex chars = 23 total
    assert len(anonymized) == 23, \
        f"Anonymized ID should be 23 characters: {anonymized}"
    
    # Check that original school_id is not in anonymized version
    # (except for very short school_ids like "_" which might appear in "school_" prefix)
    if len(school_id) > 2:
        assert school_id not in anonymized, \
            f"Original school_id should not appear in anonymized version"
    
    # Verify anonymization is consistent
    anonymized2 = anonymizer.anonymize_school_id(school_id)
    assert anonymized == anonymized2, \
        "Anonymization should be deterministic"


@given(school_id1=st.text(min_size=1, max_size=50), 
       school_id2=st.text(min_size=1, max_size=50))
@settings(max_examples=100, deadline=None)
def test_different_school_ids_produce_different_hashes(school_id1, school_id2):
    """
    Property: Different school IDs produce different anonymized hashes
    
    Validates: Requirement 9.4
    """
    assume(school_id1 != school_id2)
    
    anonymizer = Anonymizer(salt='test-salt-123')
    
    anonymized1 = anonymizer.anonymize_school_id(school_id1)
    anonymized2 = anonymizer.anonymize_school_id(school_id2)
    
    # Different inputs should produce different outputs
    assert anonymized1 != anonymized2, \
        f"Different school IDs should produce different hashes: {school_id1} vs {school_id2}"


@given(pii=pii_data())
@settings(max_examples=100, deadline=None)
def test_pii_data_fails_verification(pii):
    """
    Property: Data containing PII should always fail verification
    
    Validates: Requirements 9.2, 9.5
    """
    verifier = PIIVerifier()
    
    # PII data should fail verification
    assert not verifier.verify_no_pii(pii), \
        f"PII data should fail verification: {pii}"


@given(metrics=valid_metrics())
@settings(max_examples=100, deadline=None)
def test_metrics_contain_no_chat_content(metrics):
    """
    Property: Telemetry metrics never contain chat content
    
    Validates: Requirement 9.2
    """
    metrics_dict = metrics.to_dict()
    
    # Check that no suspicious keys exist
    suspicious_keys = ['chat', 'message', 'question', 'response', 'answer', 'content']
    
    for key in metrics_dict.keys():
        assert key.lower() not in suspicious_keys, \
            f"Metrics should not contain chat-related keys: {key}"


@given(metrics=valid_metrics())
@settings(max_examples=100, deadline=None)
def test_metrics_contain_no_user_identifiers(metrics):
    """
    Property: Telemetry metrics never contain user identifiers
    
    Validates: Requirement 9.2
    """
    metrics_dict = metrics.to_dict()
    
    # Check that no user identifier keys exist
    user_keys = ['username', 'user_id', 'name', 'email', 'student_id', 'teacher_id']
    
    for key in metrics_dict.keys():
        assert key.lower() not in user_keys, \
            f"Metrics should not contain user identifier keys: {key}"


@given(metrics=valid_metrics())
@settings(max_examples=100, deadline=None)
def test_metrics_schema_matches_allowed_keys(metrics):
    """
    Property: Telemetry metrics only contain allowed keys
    
    Validates: Requirements 9.1, 9.2
    """
    verifier = PIIVerifier()
    metrics_dict = metrics.to_dict()
    
    # Validate schema
    is_valid, error_msg = verifier.validate_schema(metrics_dict)
    
    assert is_valid, f"Metrics schema validation failed: {error_msg}"


@given(
    total=st.integers(min_value=0, max_value=10000),
    successful=st.integers(min_value=0, max_value=10000),
    failed=st.integers(min_value=0, max_value=10000)
)
@settings(max_examples=100, deadline=None)
def test_aggregated_metrics_are_counts_not_details(total, successful, failed):
    """
    Property: Aggregated metrics contain only counts, not individual details
    
    Validates: Requirement 9.1
    """
    # Create metrics with counts
    metrics = AggregatedMetrics(
        school_id='school_test123456789',
        timestamp=int(datetime.now(timezone.utc).timestamp()),
        total_queries=total,
        successful_queries=successful,
        failed_queries=failed,
        average_latency_ms=5000.0,
        p50_latency_ms=4500.0,
        p90_latency_ms=7000.0,
        p99_latency_ms=9000.0,
        model_version='llama-3.2-3b-q4',
        embedding_model='amazon.titan-embed-text-v1',
        chromadb_version='0.4.0',
        error_rate=0.01,
        error_types={'timeout': 5},
        chromadb_size_mb=1000.0,
        postgres_size_mb=500.0,
        disk_usage_percent=45.0
    )
    
    metrics_dict = metrics.to_dict()
    
    # Check that all values are aggregated (numbers), not individual records
    for key, value in metrics_dict.items():
        if key == 'error_types':
            # error_types is a dict of counts
            assert isinstance(value, dict), f"{key} should be a dict"
            for error_type, count in value.items():
                assert isinstance(count, int), f"Error count should be integer: {error_type}={count}"
        elif key in ['school_id', 'model_version', 'embedding_model', 'chromadb_version']:
            # These are strings
            assert isinstance(value, str), f"{key} should be a string"
        else:
            # All other values should be numbers (int or float)
            assert isinstance(value, (int, float)), \
                f"{key} should be a number, got {type(value)}"


@given(
    latencies=st.lists(st.floats(min_value=0, max_value=30000), min_size=1, max_size=1000)
)
@settings(max_examples=50, deadline=None)
def test_percentile_calculations_preserve_anonymity(latencies):
    """
    Property: Percentile calculations aggregate data without exposing individual queries
    
    Validates: Requirement 9.1
    """
    # Percentiles should be single numbers, not lists of individual latencies
    aggregator = MetricsAggregator(school_id='school_test123456789')
    
    p50 = aggregator._calculate_percentile(latencies, 50)
    p90 = aggregator._calculate_percentile(latencies, 90)
    p99 = aggregator._calculate_percentile(latencies, 99)
    
    # Percentiles should be single float values
    assert isinstance(p50, float), "p50 should be a single float"
    assert isinstance(p90, float), "p90 should be a single float"
    assert isinstance(p99, float), "p99 should be a single float"
    
    # Percentiles should be within the range of input data
    assert min(latencies) <= p50 <= max(latencies), "p50 should be within data range"
    assert min(latencies) <= p90 <= max(latencies), "p90 should be within data range"
    assert min(latencies) <= p99 <= max(latencies), "p99 should be within data range"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
