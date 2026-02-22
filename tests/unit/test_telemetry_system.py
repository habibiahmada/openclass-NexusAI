"""
Unit Tests: Telemetry System

Tests for telemetry collection, aggregation, PII verification,
anonymization, upload, and offline queuing.

Requirements: 9.1-9.5
"""

import pytest
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock

from src.telemetry.collector import TelemetryCollector, MetricsSnapshot, get_collector
from src.telemetry.aggregator import MetricsAggregator, AggregatedMetrics
from src.telemetry.pii_verifier import PIIVerifier, PIIMatch
from src.telemetry.anonymizer import Anonymizer
from src.telemetry.uploader import TelemetryUploader, check_internet_connectivity


class TestTelemetryCollector:
    """Test metrics collection"""
    
    def test_record_query_success(self):
        """Test recording successful query"""
        collector = TelemetryCollector()
        
        collector.record_query(latency=5000.0, success=True)
        
        snapshot = collector.get_metrics_snapshot()
        assert snapshot.total_queries == 1
        assert snapshot.successful_queries == 1
        assert snapshot.failed_queries == 0
        assert 5000.0 in snapshot.latencies
    
    def test_record_query_failure(self):
        """Test recording failed query"""
        collector = TelemetryCollector()
        
        collector.record_query(latency=8000.0, success=False)
        
        snapshot = collector.get_metrics_snapshot()
        assert snapshot.total_queries == 1
        assert snapshot.successful_queries == 0
        assert snapshot.failed_queries == 1
        assert 8000.0 in snapshot.latencies
    
    def test_record_multiple_queries(self):
        """Test recording multiple queries"""
        collector = TelemetryCollector()
        
        collector.record_query(3000.0, True)
        collector.record_query(5000.0, True)
        collector.record_query(7000.0, False)
        
        snapshot = collector.get_metrics_snapshot()
        assert snapshot.total_queries == 3
        assert snapshot.successful_queries == 2
        assert snapshot.failed_queries == 1
        assert len(snapshot.latencies) == 3
    
    def test_record_error(self):
        """Test recording error"""
        collector = TelemetryCollector()
        
        collector.record_error('timeout', 'Request timeout after 30s')
        
        snapshot = collector.get_metrics_snapshot()
        assert len(snapshot.errors) == 1
        assert snapshot.errors[0]['type'] == 'timeout'
        assert 'timeout' in snapshot.errors[0]['message']
    
    def test_reset_metrics(self):
        """Test resetting metrics"""
        collector = TelemetryCollector()
        
        collector.record_query(5000.0, True)
        collector.record_error('oom', 'Out of memory')
        
        collector.reset_metrics()
        
        snapshot = collector.get_metrics_snapshot()
        assert snapshot.total_queries == 0
        assert snapshot.successful_queries == 0
        assert snapshot.failed_queries == 0
        assert len(snapshot.latencies) == 0
        assert len(snapshot.errors) == 0
    
    def test_metrics_snapshot_to_dict(self):
        """Test converting snapshot to dictionary"""
        collector = TelemetryCollector()
        collector.record_query(5000.0, True)
        
        snapshot = collector.get_metrics_snapshot()
        data = snapshot.to_dict()
        
        assert isinstance(data, dict)
        assert 'timestamp' in data
        assert 'total_queries' in data
        assert data['total_queries'] == 1
    
    def test_get_collector_singleton(self):
        """Test global collector singleton"""
        collector1 = get_collector()
        collector2 = get_collector()
        
        assert collector1 is collector2


class TestMetricsAggregator:
    """Test metrics aggregation"""
    
    def test_aggregate_hourly_basic(self):
        """Test basic hourly aggregation"""
        aggregator = MetricsAggregator(school_id='school_test123')
        
        snapshot = MetricsSnapshot(
            timestamp=datetime.now(timezone.utc),
            total_queries=100,
            successful_queries=95,
            failed_queries=5,
            latencies=[3000.0, 5000.0, 7000.0, 4000.0, 6000.0],
            errors=[{'type': 'timeout', 'message': 'Timeout', 'timestamp': datetime.now(timezone.utc).isoformat()}]
        )
        
        aggregated = aggregator.aggregate_hourly(snapshot)
        
        assert aggregated.school_id == 'school_test123'
        assert aggregated.total_queries == 100
        assert aggregated.successful_queries == 95
        assert aggregated.failed_queries == 5
        assert aggregated.error_rate == 0.05
    
    def test_calculate_percentile(self):
        """Test percentile calculation"""
        aggregator = MetricsAggregator(school_id='school_test123')
        
        latencies = [1000.0, 2000.0, 3000.0, 4000.0, 5000.0, 
                     6000.0, 7000.0, 8000.0, 9000.0, 10000.0]
        
        p50 = aggregator._calculate_percentile(latencies, 50)
        p90 = aggregator._calculate_percentile(latencies, 90)
        p99 = aggregator._calculate_percentile(latencies, 99)
        
        assert 5000.0 <= p50 <= 6000.0  # Median
        assert 9000.0 <= p90 <= 10000.0  # 90th percentile
        assert p99 >= 9000.0  # 99th percentile
    
    def test_calculate_percentile_empty(self):
        """Test percentile calculation with empty list"""
        aggregator = MetricsAggregator(school_id='school_test123')
        
        p50 = aggregator._calculate_percentile([], 50)
        
        assert p50 == 0.0
    
    def test_aggregate_error_types(self):
        """Test error type aggregation"""
        aggregator = MetricsAggregator(school_id='school_test123')
        
        snapshot = MetricsSnapshot(
            timestamp=datetime.now(timezone.utc),
            total_queries=100,
            successful_queries=97,
            failed_queries=3,
            latencies=[5000.0],
            errors=[
                {'type': 'timeout', 'message': 'Timeout 1', 'timestamp': datetime.now(timezone.utc).isoformat()},
                {'type': 'timeout', 'message': 'Timeout 2', 'timestamp': datetime.now(timezone.utc).isoformat()},
                {'type': 'oom', 'message': 'Out of memory', 'timestamp': datetime.now(timezone.utc).isoformat()},
            ]
        )
        
        aggregated = aggregator.aggregate_hourly(snapshot)
        
        assert aggregated.error_types['timeout'] == 2
        assert aggregated.error_types['oom'] == 1
    
    def test_aggregated_metrics_to_dict(self):
        """Test converting aggregated metrics to dictionary"""
        metrics = AggregatedMetrics(
            school_id='school_test123',
            timestamp=1600000000,
            total_queries=100,
            successful_queries=95,
            failed_queries=5,
            average_latency_ms=5000.0,
            p50_latency_ms=4500.0,
            p90_latency_ms=7000.0,
            p99_latency_ms=9000.0,
            model_version='llama-3.2-3b-q4',
            embedding_model='amazon.titan-embed-text-v1',
            chromadb_version='0.4.0',
            error_rate=0.05,
            error_types={'timeout': 2, 'oom': 1},
            chromadb_size_mb=1000.0,
            postgres_size_mb=500.0,
            disk_usage_percent=45.0
        )
        
        data = metrics.to_dict()
        
        assert isinstance(data, dict)
        assert data['school_id'] == 'school_test123'
        assert data['total_queries'] == 100
        assert data['error_rate'] == 0.05


class TestPIIVerifier:
    """Test PII verification"""
    
    def test_verify_no_pii_valid_metrics(self):
        """Test verification passes for valid metrics"""
        verifier = PIIVerifier()
        
        data = {
            'school_id': 'school_abc123def456',
            'timestamp': 1600000000,
            'total_queries': 100,
            'average_latency_ms': 5000.0
        }
        
        assert verifier.verify_no_pii(data) is True
    
    def test_verify_no_pii_detects_nik(self):
        """Test verification detects NIK (Indonesian National ID)"""
        verifier = PIIVerifier()
        
        data = {
            'school_id': 'school_test',
            'nik': '1234567890123456'  # 16 digits
        }
        
        assert verifier.verify_no_pii(data) is False
    
    def test_verify_no_pii_detects_email(self):
        """Test verification detects email"""
        verifier = PIIVerifier()
        
        data = {
            'school_id': 'school_test',
            'email': 'student@example.com'
        }
        
        assert verifier.verify_no_pii(data) is False
    
    def test_verify_no_pii_detects_phone(self):
        """Test verification detects phone number"""
        verifier = PIIVerifier()
        
        data = {
            'school_id': 'school_test',
            'contact': '+628123456789'
        }
        
        assert verifier.verify_no_pii(data) is False
    
    def test_verify_no_pii_detects_suspicious_keys(self):
        """Test verification detects suspicious keys"""
        verifier = PIIVerifier()
        
        data = {
            'school_id': 'school_test',
            'username': 'john_doe'
        }
        
        assert verifier.verify_no_pii(data) is False
    
    def test_verify_no_pii_detects_chat_keys(self):
        """Test verification detects chat-related keys"""
        verifier = PIIVerifier()
        
        data = {
            'school_id': 'school_test',
            'chat': 'What is the capital of Indonesia?'
        }
        
        assert verifier.verify_no_pii(data) is False
    
    def test_scan_for_patterns_nik(self):
        """Test pattern scanning for NIK"""
        verifier = PIIVerifier()
        
        text = "NIK: 1234567890123456"
        matches = verifier.scan_for_patterns(text)
        
        assert len(matches) > 0
        assert any(m.pattern_name == 'nik' for m in matches)
    
    def test_scan_for_patterns_email(self):
        """Test pattern scanning for email"""
        verifier = PIIVerifier()
        
        text = "Contact: student@example.com"
        matches = verifier.scan_for_patterns(text)
        
        assert len(matches) > 0
        assert any(m.pattern_name == 'email' for m in matches)
    
    def test_validate_schema_allowed_keys(self):
        """Test schema validation with allowed keys"""
        verifier = PIIVerifier()
        
        data = {
            'school_id': 'school_test',
            'timestamp': 1600000000,
            'total_queries': 100
        }
        
        is_valid, error_msg = verifier.validate_schema(data)
        assert is_valid is True
        assert error_msg == ""
    
    def test_validate_schema_unexpected_keys(self):
        """Test schema validation detects unexpected keys"""
        verifier = PIIVerifier()
        
        data = {
            'school_id': 'school_test',
            'unexpected_key': 'value'
        }
        
        is_valid, error_msg = verifier.validate_schema(data)
        assert is_valid is False
        assert 'unexpected_key' in error_msg
    
    def test_get_allowed_keys(self):
        """Test getting allowed keys list"""
        verifier = PIIVerifier()
        
        allowed_keys = verifier.get_allowed_keys()
        
        assert 'school_id' in allowed_keys
        assert 'timestamp' in allowed_keys
        assert 'total_queries' in allowed_keys
        assert 'username' not in allowed_keys
        assert 'chat' not in allowed_keys


class TestAnonymizer:
    """Test anonymization"""
    
    def test_anonymize_school_id_format(self):
        """Test school ID anonymization format"""
        anonymizer = Anonymizer(salt='test-salt-123')
        
        anonymized = anonymizer.anonymize_school_id('school_001')
        
        assert anonymized.startswith('school_')
        assert len(anonymized) == 23  # 'school_' (7) + 16 hex chars
    
    def test_anonymize_school_id_deterministic(self):
        """Test anonymization is deterministic"""
        anonymizer = Anonymizer(salt='test-salt-123')
        
        anonymized1 = anonymizer.anonymize_school_id('school_001')
        anonymized2 = anonymizer.anonymize_school_id('school_001')
        
        assert anonymized1 == anonymized2
    
    def test_anonymize_school_id_different_inputs(self):
        """Test different inputs produce different hashes"""
        anonymizer = Anonymizer(salt='test-salt-123')
        
        anonymized1 = anonymizer.anonymize_school_id('school_001')
        anonymized2 = anonymizer.anonymize_school_id('school_002')
        
        assert anonymized1 != anonymized2
    
    def test_anonymize_school_id_one_way(self):
        """Test anonymization is one-way (cannot reverse)"""
        anonymizer = Anonymizer(salt='test-salt-123')
        
        original = 'school_secret_id_12345'
        anonymized = anonymizer.anonymize_school_id(original)
        
        # Original should not appear in anonymized version
        assert original not in anonymized
        assert 'secret' not in anonymized
    
    def test_anonymize_school_id_different_salts(self):
        """Test different salts produce different hashes"""
        anonymizer1 = Anonymizer(salt='salt1')
        anonymizer2 = Anonymizer(salt='salt2')
        
        anonymized1 = anonymizer1.anonymize_school_id('school_001')
        anonymized2 = anonymizer2.anonymize_school_id('school_001')
        
        assert anonymized1 != anonymized2


class TestTelemetryUploader:
    """Test telemetry upload"""
    
    def test_upload_metrics_success(self):
        """Test successful metrics upload"""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_file = os.path.join(tmpdir, 'queue.json')
            uploader = TelemetryUploader(
                table_name='test-metrics',
                queue_file=queue_file
            )
            
            metrics = AggregatedMetrics(
                school_id='school_test123',
                timestamp=1600000000,
                total_queries=100,
                successful_queries=95,
                failed_queries=5,
                average_latency_ms=5000.0,
                p50_latency_ms=4500.0,
                p90_latency_ms=7000.0,
                p99_latency_ms=9000.0,
                model_version='llama-3.2-3b-q4',
                embedding_model='amazon.titan-embed-text-v1',
                chromadb_version='0.4.0',
                error_rate=0.05,
                error_types={'timeout': 2},
                chromadb_size_mb=1000.0,
                postgres_size_mb=500.0,
                disk_usage_percent=45.0
            )
            
            # Mock DynamoDB
            with patch('boto3.resource') as mock_boto:
                mock_dynamodb = Mock()
                mock_table = Mock()
                mock_table.put_item = Mock(return_value={})
                mock_dynamodb.Table = Mock(return_value=mock_table)
                mock_boto.return_value = mock_dynamodb
                
                # Create uploader with mocked boto3
                uploader = TelemetryUploader(
                    table_name='test-metrics',
                    queue_file=queue_file
                )
                
                result = uploader.upload_metrics(metrics)
                
                assert result is True
                assert mock_table.put_item.called
    
    def test_upload_metrics_adds_ttl(self):
        """Test upload adds TTL field"""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_file = os.path.join(tmpdir, 'queue.json')
            
            metrics = AggregatedMetrics(
                school_id='school_test123',
                timestamp=1600000000,
                total_queries=100,
                successful_queries=95,
                failed_queries=5,
                average_latency_ms=5000.0,
                p50_latency_ms=4500.0,
                p90_latency_ms=7000.0,
                p99_latency_ms=9000.0,
                model_version='llama-3.2-3b-q4',
                embedding_model='amazon.titan-embed-text-v1',
                chromadb_version='0.4.0',
                error_rate=0.05,
                error_types={'timeout': 2},
                chromadb_size_mb=1000.0,
                postgres_size_mb=500.0,
                disk_usage_percent=45.0
            )
            
            # Mock DynamoDB
            with patch('boto3.resource') as mock_boto:
                mock_dynamodb = Mock()
                mock_table = Mock()
                mock_table.put_item = Mock(return_value={})
                mock_dynamodb.Table = Mock(return_value=mock_table)
                mock_boto.return_value = mock_dynamodb
                
                uploader = TelemetryUploader(
                    table_name='test-metrics',
                    queue_file=queue_file
                )
                
                uploader.upload_metrics(metrics)
                
                # Check that TTL was added
                call_args = mock_table.put_item.call_args
                sent_data = call_args[1]['Item']
                
                assert 'ttl' in sent_data
                assert isinstance(sent_data['ttl'], int)
    
    def test_queue_offline_metrics(self):
        """Test queuing metrics when offline"""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_file = os.path.join(tmpdir, 'queue.json')
            uploader = TelemetryUploader(
                table_name='test-metrics',
                queue_file=queue_file
            )
            
            metrics = AggregatedMetrics(
                school_id='school_test123',
                timestamp=1600000000,
                total_queries=100,
                successful_queries=95,
                failed_queries=5,
                average_latency_ms=5000.0,
                p50_latency_ms=4500.0,
                p90_latency_ms=7000.0,
                p99_latency_ms=9000.0,
                model_version='llama-3.2-3b-q4',
                embedding_model='amazon.titan-embed-text-v1',
                chromadb_version='0.4.0',
                error_rate=0.05,
                error_types={'timeout': 2},
                chromadb_size_mb=1000.0,
                postgres_size_mb=500.0,
                disk_usage_percent=45.0
            )
            
            uploader.queue_offline_metrics(metrics)
            
            assert uploader.get_queue_size() == 1
            assert os.path.exists(queue_file)
    
    def test_retry_failed_uploads(self):
        """Test retrying failed uploads with exponential backoff"""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_file = os.path.join(tmpdir, 'queue.json')
            uploader = TelemetryUploader(
                table_name='test-metrics',
                queue_file=queue_file
            )
            
            metrics = AggregatedMetrics(
                school_id='school_test123',
                timestamp=1600000000,
                total_queries=100,
                successful_queries=95,
                failed_queries=5,
                average_latency_ms=5000.0,
                p50_latency_ms=4500.0,
                p90_latency_ms=7000.0,
                p99_latency_ms=9000.0,
                model_version='llama-3.2-3b-q4',
                embedding_model='amazon.titan-embed-text-v1',
                chromadb_version='0.4.0',
                error_rate=0.05,
                error_types={'timeout': 2},
                chromadb_size_mb=1000.0,
                postgres_size_mb=500.0,
                disk_usage_percent=45.0
            )
            
            # Queue metrics
            uploader.queue_offline_metrics(metrics)
            
            # Mock successful upload
            with patch('boto3.resource') as mock_boto:
                mock_dynamodb = Mock()
                mock_table = Mock()
                mock_table.put_item = Mock(return_value={})
                mock_dynamodb.Table = Mock(return_value=mock_table)
                mock_boto.return_value = mock_dynamodb
                
                uploader = TelemetryUploader(
                    table_name='test-metrics',
                    queue_file=queue_file
                )
                
                successful = uploader.retry_failed_uploads(max_retries=1)
                
                assert successful == 1
                assert uploader.get_queue_size() == 0
    
    def test_get_queue_size(self):
        """Test getting queue size"""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_file = os.path.join(tmpdir, 'queue.json')
            uploader = TelemetryUploader(
                table_name='test-metrics',
                queue_file=queue_file
            )
            
            assert uploader.get_queue_size() == 0
    
    def test_clear_queue(self):
        """Test clearing queue"""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_file = os.path.join(tmpdir, 'queue.json')
            uploader = TelemetryUploader(
                table_name='test-metrics',
                queue_file=queue_file
            )
            
            metrics = AggregatedMetrics(
                school_id='school_test123',
                timestamp=1600000000,
                total_queries=100,
                successful_queries=95,
                failed_queries=5,
                average_latency_ms=5000.0,
                p50_latency_ms=4500.0,
                p90_latency_ms=7000.0,
                p99_latency_ms=9000.0,
                model_version='llama-3.2-3b-q4',
                embedding_model='amazon.titan-embed-text-v1',
                chromadb_version='0.4.0',
                error_rate=0.05,
                error_types={'timeout': 2},
                chromadb_size_mb=1000.0,
                postgres_size_mb=500.0,
                disk_usage_percent=45.0
            )
            
            uploader.queue_offline_metrics(metrics)
            assert uploader.get_queue_size() == 1
            
            uploader.clear_queue()
            assert uploader.get_queue_size() == 0


class TestInternetConnectivity:
    """Test internet connectivity check"""
    
    def test_check_internet_connectivity_mock_success(self):
        """Test internet connectivity check (mocked success)"""
        with patch('socket.create_connection') as mock_socket:
            mock_socket.return_value = Mock()
            
            result = check_internet_connectivity()
            
            assert result is True
    
    def test_check_internet_connectivity_mock_failure(self):
        """Test internet connectivity check (mocked failure)"""
        with patch('socket.create_connection') as mock_socket:
            mock_socket.side_effect = OSError('Network unreachable')
            
            result = check_internet_connectivity()
            
            assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
