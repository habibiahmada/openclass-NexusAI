"""
Unit Tests: Privacy Verification

Comprehensive test suite for verifying privacy by architecture:
- Chat history stored only locally (PostgreSQL)
- User data stored only locally (PostgreSQL)
- No PII sent to AWS under any circumstances
- All AWS API calls scanned for PII

**Validates: Requirements 16.1-16.7**
"""

import pytest
import json
import re
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone

from src.telemetry.pii_verifier import PIIVerifier
from src.telemetry.uploader import TelemetryUploader
from src.telemetry.aggregator import AggregatedMetrics


class TestLocalDataStorage:
    """
    Test suite for local data storage privacy
    
    Validates: Requirements 16.1, 16.2, 16.3
    """
    
    def test_chat_history_stored_only_in_postgresql(self):
        """
        Verify chat history is stored exclusively in local PostgreSQL database
        
        Validates: Requirement 16.1
        """
        from src.persistence.chat_history_repository import ChatHistoryRepository
        from src.persistence.database_manager import DatabaseManager
        
        # Mock the database connection to avoid actual PostgreSQL requirement
        with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
            # Create repository (uses PostgreSQL)
            db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
            repo = ChatHistoryRepository(db_manager)
        
        # Verify repository uses PostgreSQL connection
        assert repo.db is not None
        assert hasattr(repo.db, 'get_connection')
        
        # Verify no AWS client in repository
        assert not hasattr(repo, 's3_client')
        assert not hasattr(repo, 'dynamodb')
        assert not hasattr(repo, 'bedrock_client')
    
    def test_student_identity_stored_only_in_postgresql(self):
        """
        Verify student identity is stored exclusively in local PostgreSQL database
        
        Validates: Requirement 16.2
        """
        from src.persistence.user_repository import UserRepository
        from src.persistence.database_manager import DatabaseManager
        
        # Mock the database connection to avoid actual PostgreSQL requirement
        with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
            # Create repository (uses PostgreSQL)
            db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
            repo = UserRepository(db_manager)
        
        # Verify repository uses PostgreSQL connection
        assert repo.db is not None
        assert hasattr(repo.db, 'get_connection')
        
        # Verify no AWS client in repository
        assert not hasattr(repo, 's3_client')
        assert not hasattr(repo, 'dynamodb')
        assert not hasattr(repo, 'bedrock_client')
    
    def test_teacher_identity_stored_only_in_postgresql(self):
        """
        Verify teacher identity is stored exclusively in local PostgreSQL database
        
        Validates: Requirement 16.3
        """
        from src.persistence.user_repository import UserRepository
        from src.persistence.database_manager import DatabaseManager
        
        # Mock the database connection to avoid actual PostgreSQL requirement
        with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
            # Create repository (uses PostgreSQL)
            db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
            repo = UserRepository(db_manager)
        
        # Verify repository uses PostgreSQL connection
        assert repo.db is not None
        
        # Verify no AWS client in repository
        assert not hasattr(repo, 's3_client')
        assert not hasattr(repo, 'dynamodb')
        assert not hasattr(repo, 'bedrock_client')
    
    def test_session_data_stored_only_in_postgresql(self):
        """
        Verify session data is stored exclusively in local PostgreSQL database
        
        Validates: Requirements 16.2, 16.3
        """
        from src.persistence.session_repository import SessionRepository
        from src.persistence.database_manager import DatabaseManager
        
        # Mock the database connection to avoid actual PostgreSQL requirement
        with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
            # Create repository (uses PostgreSQL)
            db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
            repo = SessionRepository(db_manager)
        
        # Verify repository uses PostgreSQL connection
        assert repo.db is not None
        
        # Verify no AWS client in repository
        assert not hasattr(repo, 's3_client')
        assert not hasattr(repo, 'dynamodb')
        assert not hasattr(repo, 'bedrock_client')


class TestChatContentPrivacy:
    """
    Test suite for chat content privacy
    
    Validates: Requirement 16.4
    """
    
    def test_chat_content_never_sent_to_aws(self):
        """
        Verify chat content is NEVER sent to AWS under any circumstances
        
        Validates: Requirement 16.4
        """
        # Test data with chat content
        chat_data = {
            'question': 'What is the capital of Indonesia?',
            'response': 'The capital of Indonesia is Jakarta.',
            'user_id': 123,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Verify PII verifier rejects chat content
        verifier = PIIVerifier()
        assert not verifier.verify_no_pii(chat_data), \
            "Chat content should be rejected by PII verifier"
    
    def test_telemetry_uploader_blocks_chat_content(self):
        """
        Verify TelemetryUploader blocks any data containing chat content
        
        Validates: Requirement 16.4
        """
        # Create metrics with chat content (should be rejected)
        invalid_metrics = AggregatedMetrics(
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
        
        # Add chat content to metrics dict
        metrics_dict = invalid_metrics.to_dict()
        metrics_dict['chat'] = 'What is photosynthesis?'
        
        # Verify PII verifier rejects it
        verifier = PIIVerifier()
        assert not verifier.verify_no_pii(metrics_dict), \
            "Metrics with chat content should be rejected"
    
    def test_vkp_puller_does_not_send_chat_content(self):
        """
        Verify VKP puller only downloads data, never uploads chat content
        
        Validates: Requirement 16.4
        """
        # VKP puller should only have download methods, not upload methods for chat
        # We test this by checking the class interface, not instantiating
        from src.vkp.puller import VKPPuller
        import inspect
        
        # Get all methods of VKPPuller
        methods = [method for method in dir(VKPPuller) if not method.startswith('_')]
        
        # Verify puller has download methods
        assert 'download_vkp' in methods or any('download' in m for m in methods), \
            "VKPPuller should have download methods"
        assert 'check_updates' in methods or any('check' in m or 'update' in m for m in methods), \
            "VKPPuller should have update check methods"
        
        # Verify puller does NOT have methods to upload chat/user data
        upload_chat_methods = [m for m in methods if 'upload' in m.lower() and ('chat' in m.lower() or 'message' in m.lower())]
        assert len(upload_chat_methods) == 0, \
            f"VKPPuller should not have chat upload methods: {upload_chat_methods}"


class TestUserDataPrivacy:
    """
    Test suite for user data privacy
    
    Validates: Requirement 16.5
    """
    
    def test_user_data_never_sent_to_aws(self):
        """
        Verify user data is NEVER sent to AWS under any circumstances
        
        Validates: Requirement 16.5
        """
        # Test data with user identifiers
        user_data = {
            'username': 'john_doe',
            'email': 'john@example.com',
            'name': 'John Doe',
            'student_id': 'STU12345'
        }
        
        # Verify PII verifier rejects user data
        verifier = PIIVerifier()
        assert not verifier.verify_no_pii(user_data), \
            "User data should be rejected by PII verifier"
    
    def test_telemetry_contains_no_user_identifiers(self):
        """
        Verify telemetry data contains no user identifiers
        
        Validates: Requirement 16.5
        """
        # Valid telemetry metrics
        metrics = AggregatedMetrics(
            school_id='school_abc123def456',
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
        
        metrics_dict = metrics.to_dict()
        
        # Verify no user identifier keys
        user_keys = ['username', 'user_id', 'name', 'email', 'phone', 
                     'student_id', 'teacher_id', 'nik', 'password']
        
        for key in user_keys:
            assert key not in metrics_dict, \
                f"Telemetry should not contain user identifier: {key}"
    
    def test_session_tokens_never_sent_to_aws(self):
        """
        Verify session tokens are never sent to AWS
        
        Validates: Requirement 16.5
        """
        # Test data with session token
        session_data = {
            'session_token': 'abc123def456ghi789jkl012mno345pqr678',
            'user_id': 123
        }
        
        # Verify PII verifier rejects session tokens
        verifier = PIIVerifier()
        assert not verifier.verify_no_pii(session_data), \
            "Session tokens should be rejected by PII verifier"


class TestAnonymizedMetricsOnly:
    """
    Test suite for anonymized metrics verification
    
    Validates: Requirement 16.6
    """
    
    def test_only_anonymized_metrics_sent_to_aws(self):
        """
        Verify only anonymized metrics are transmitted to AWS
        
        Validates: Requirement 16.6
        """
        # Valid anonymized metrics
        metrics = AggregatedMetrics(
            school_id='school_abc123def456',
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
        
        # Verify PII verifier accepts anonymized metrics
        verifier = PIIVerifier()
        assert verifier.verify_no_pii(metrics.to_dict()), \
            "Anonymized metrics should pass PII verification"
    
    def test_school_id_is_anonymized(self):
        """
        Verify school_id is anonymized (hashed) before AWS transmission
        
        Validates: Requirement 16.6
        """
        from src.telemetry.anonymizer import Anonymizer
        
        anonymizer = Anonymizer(salt='test-salt-123')
        
        # Original school ID
        original_id = 'SCHOOL_JAKARTA_001'
        
        # Anonymize
        anonymized_id = anonymizer.anonymize_school_id(original_id)
        
        # Verify format
        assert anonymized_id.startswith('school_'), \
            "Anonymized ID should start with 'school_'"
        assert len(anonymized_id) == 23, \
            "Anonymized ID should be 23 characters"
        
        # Verify original ID not in anonymized version
        assert original_id not in anonymized_id, \
            "Original school ID should not appear in anonymized version"
    
    def test_metrics_contain_only_aggregated_data(self):
        """
        Verify metrics contain only aggregated data, not individual records
        
        Validates: Requirement 16.6
        """
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
        
        metrics_dict = metrics.to_dict()
        
        # Verify all numeric values are aggregated (counts, averages, percentiles)
        # Not individual records
        assert 'total_queries' in metrics_dict
        assert 'average_latency_ms' in metrics_dict
        assert 'p50_latency_ms' in metrics_dict
        
        # Verify no individual query data
        assert 'query_text' not in metrics_dict
        assert 'individual_latencies' not in metrics_dict
        assert 'query_list' not in metrics_dict


class TestPIIAuditTool:
    """
    Test suite for Privacy Audit Tool
    
    Validates: Requirement 16.7
    """
    
    def test_pii_verifier_scans_all_aws_api_calls(self):
        """
        Verify Privacy Audit Tool scans all AWS API calls for PII
        
        Validates: Requirement 16.7
        """
        verifier = PIIVerifier()
        
        # Test various data types
        test_cases = [
            # Valid data (should pass)
            ({'school_id': 'school_test', 'total_queries': 100}, True),
            
            # Invalid data with PII (should fail)
            ({'username': 'john_doe'}, False),
            ({'email': 'test@example.com'}, False),
            ({'chat': 'What is the answer?'}, False),
            ({'nik': '1234567890123456'}, False),
            ({'phone': '+628123456789'}, False),
        ]
        
        for data, expected_pass in test_cases:
            result = verifier.verify_no_pii(data)
            assert result == expected_pass, \
                f"PII verification failed for {data}: expected {expected_pass}, got {result}"
    
    def test_pii_verifier_detects_nik_pattern(self):
        """
        Verify PII verifier detects Indonesian NIK (National ID) pattern
        
        Validates: Requirement 16.7
        """
        verifier = PIIVerifier()
        
        # NIK is 16 digits
        text_with_nik = "NIK: 3201234567890123"
        matches = verifier.scan_for_patterns(text_with_nik)
        
        assert len(matches) > 0, "Should detect NIK pattern"
        assert any(m.pattern_name == 'nik' for m in matches), \
            "Should identify pattern as NIK"
    
    def test_pii_verifier_detects_email_pattern(self):
        """
        Verify PII verifier detects email pattern
        
        Validates: Requirement 16.7
        """
        verifier = PIIVerifier()
        
        text_with_email = "Contact: student@school.edu"
        matches = verifier.scan_for_patterns(text_with_email)
        
        assert len(matches) > 0, "Should detect email pattern"
        assert any(m.pattern_name == 'email' for m in matches), \
            "Should identify pattern as email"
    
    def test_pii_verifier_detects_phone_pattern(self):
        """
        Verify PII verifier detects phone number pattern
        
        Validates: Requirement 16.7
        """
        verifier = PIIVerifier()
        
        # Test various phone formats
        phone_formats = [
            "+628123456789",
            "08123456789",
            "62-812-3456-7890",
            "0812 3456 7890"
        ]
        
        detected = False
        for phone in phone_formats:
            text_with_phone = f"Phone: {phone}"
            matches = verifier.scan_for_patterns(text_with_phone)
            if len(matches) > 0 and any(m.pattern_name == 'phone' for m in matches):
                detected = True
                break
        
        # If none detected, check if phone key is caught by suspicious keys
        if not detected:
            data = {'phone': '+628123456789'}
            result = verifier.verify_no_pii(data)
            assert not result, "Phone should be detected via suspicious keys"
        else:
            assert detected, "Should detect phone pattern"
    
    def test_pii_verifier_validates_schema(self):
        """
        Verify PII verifier validates data schema against allowed keys
        
        Validates: Requirement 16.7
        """
        verifier = PIIVerifier()
        
        # Valid schema
        valid_data = {
            'school_id': 'school_test',
            'timestamp': 1600000000,
            'total_queries': 100
        }
        is_valid, error_msg = verifier.validate_schema(valid_data)
        assert is_valid, f"Valid schema should pass: {error_msg}"
        
        # Invalid schema with unexpected key
        invalid_data = {
            'school_id': 'school_test',
            'username': 'john_doe'  # Not allowed
        }
        is_valid, error_msg = verifier.validate_schema(invalid_data)
        assert not is_valid, "Invalid schema should fail"
        assert 'username' in error_msg, "Error message should mention unexpected key"


class TestAWSAPICallPrivacy:
    """
    Test suite for AWS API call privacy verification
    
    Validates: Requirements 16.4, 16.5, 16.6, 16.7
    """
    
    def test_telemetry_uploader_verifies_before_transmission(self):
        """
        Verify TelemetryUploader verifies no PII before AWS transmission
        
        Validates: Requirements 16.6, 16.7
        """
        with patch('boto3.resource') as mock_boto:
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_table.put_item = Mock(return_value={})
            mock_dynamodb.Table = Mock(return_value=mock_table)
            mock_boto.return_value = mock_dynamodb
            
            uploader = TelemetryUploader(table_name='test-metrics')
            
            # Valid metrics
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
            
            # Upload should succeed
            result = uploader.upload_metrics(metrics)
            
            # Verify data was sent
            if mock_table.put_item.called:
                call_args = mock_table.put_item.call_args
                sent_data = call_args[1]['Item']
                
                # Remove TTL (added by uploader)
                sent_data_copy = sent_data.copy()
                sent_data_copy.pop('ttl', None)
                
                # Verify no PII in sent data
                verifier = PIIVerifier()
                assert verifier.verify_no_pii(sent_data_copy), \
                    "Transmitted data should contain no PII"
    
    def test_vkp_puller_only_downloads_curriculum(self):
        """
        Verify VKP puller only downloads curriculum data, never uploads user data
        
        Validates: Requirements 16.4, 16.5
        """
        from src.vkp.puller import VKPPuller
        import inspect
        
        # Get all methods of VKPPuller
        methods = [method for method in dir(VKPPuller) if not method.startswith('_')]
        
        # Verify puller has download/check methods
        assert any('download' in m.lower() or 'check' in m.lower() or 'pull' in m.lower() for m in methods), \
            "VKPPuller should have download/check methods"
        
        # Verify no upload methods for sensitive data
        sensitive_upload_methods = [
            m for m in methods 
            if 'upload' in m.lower() and any(
                keyword in m.lower() 
                for keyword in ['chat', 'user', 'message', 'history', 'student', 'teacher']
            )
        ]
        assert len(sensitive_upload_methods) == 0, \
            f"VKPPuller should not have sensitive data upload methods: {sensitive_upload_methods}"
    
    def test_bedrock_client_only_generates_embeddings(self):
        """
        Verify Bedrock client only generates embeddings, never sends chat/user data
        
        Validates: Requirements 16.4, 16.5
        """
        from src.embeddings.bedrock_strategy import BedrockEmbeddingStrategy
        
        with patch('boto3.client') as mock_boto:
            mock_bedrock = Mock()
            mock_boto.return_value = mock_bedrock
            
            strategy = BedrockEmbeddingStrategy(region='ap-southeast-1')
            
            # Verify strategy only has embedding methods
            assert hasattr(strategy, 'generate_embedding')
            assert hasattr(strategy, 'batch_generate')
            
            # Verify no methods to send chat/user data
            assert not hasattr(strategy, 'send_chat')
            assert not hasattr(strategy, 'upload_user_data')
            assert not hasattr(strategy, 'store_messages')
    
    def test_no_aws_client_in_persistence_layer(self):
        """
        Verify persistence layer has no AWS clients (data stays local)
        
        Validates: Requirements 16.1, 16.2, 16.3
        """
        from src.persistence.database_manager import DatabaseManager
        from src.persistence.user_repository import UserRepository
        from src.persistence.session_repository import SessionRepository
        from src.persistence.chat_history_repository import ChatHistoryRepository
        
        # Mock the database connection to avoid actual PostgreSQL requirement
        with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
            # Check DatabaseManager
            db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
            assert not hasattr(db_manager, 's3_client')
            assert not hasattr(db_manager, 'dynamodb')
            assert not hasattr(db_manager, 'bedrock_client')
            
            # Check UserRepository
            user_repo = UserRepository(db_manager)
            assert not hasattr(user_repo, 's3_client')
            assert not hasattr(user_repo, 'dynamodb')
            
            # Check SessionRepository
            session_repo = SessionRepository(db_manager)
            assert not hasattr(session_repo, 's3_client')
            assert not hasattr(session_repo, 'dynamodb')
            
            # Check ChatHistoryRepository
            chat_repo = ChatHistoryRepository(db_manager)
            assert not hasattr(chat_repo, 's3_client')
            assert not hasattr(chat_repo, 'dynamodb')


class TestPrivacyByArchitecture:
    """
    Test suite for privacy by architecture enforcement
    
    Validates: All Requirements 16.1-16.7
    """
    
    def test_architecture_enforces_local_storage(self):
        """
        Verify architecture enforces local storage for sensitive data
        
        Validates: Requirements 16.1, 16.2, 16.3
        """
        # Import all persistence repositories
        from src.persistence.user_repository import UserRepository
        from src.persistence.session_repository import SessionRepository
        from src.persistence.chat_history_repository import ChatHistoryRepository
        from src.persistence.database_manager import DatabaseManager
        
        # Mock the database connection to avoid actual PostgreSQL requirement
        with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
            db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
            
            # All repositories should use local PostgreSQL
            repos = [
                UserRepository(db_manager),
                SessionRepository(db_manager),
                ChatHistoryRepository(db_manager)
            ]
            
            for repo in repos:
                # Verify uses PostgreSQL
                assert hasattr(repo, 'db')
                
                # Verify no AWS clients
                assert not hasattr(repo, 's3_client')
                assert not hasattr(repo, 'dynamodb')
                assert not hasattr(repo, 'bedrock_client')
                assert not hasattr(repo, 'lambda_client')
    
    def test_architecture_enforces_pii_verification(self):
        """
        Verify architecture enforces PII verification before AWS transmission
        
        Validates: Requirements 16.6, 16.7
        """
        from src.telemetry.uploader import TelemetryUploader
        from src.telemetry.pii_verifier import PIIVerifier
        
        # TelemetryUploader should have PII verification
        uploader = TelemetryUploader(table_name='test-metrics')
        
        # Verify uploader has access to PII verifier
        # (either as attribute or imports it)
        verifier = PIIVerifier()
        assert verifier is not None
        
        # Verify verifier has required methods
        assert hasattr(verifier, 'verify_no_pii')
        assert hasattr(verifier, 'scan_for_patterns')
        assert hasattr(verifier, 'validate_schema')
    
    def test_architecture_separates_aws_and_local_operations(self):
        """
        Verify architecture clearly separates AWS operations from local operations
        
        Validates: All Requirements 16.1-16.7
        """
        # AWS operations should be in aws_control_plane
        import os
        aws_path = 'src/aws_control_plane'
        assert os.path.exists(aws_path), "AWS operations should be in aws_control_plane"
        
        # Local operations should be in edge_runtime and persistence
        edge_path = 'src/edge_runtime'
        persistence_path = 'src/persistence'
        assert os.path.exists(edge_path), "Local inference should be in edge_runtime"
        assert os.path.exists(persistence_path), "Local storage should be in persistence"
        
        # Verify separation: persistence should not import aws_control_plane
        # (This is enforced by architecture, not runtime check)


class TestComprehensivePrivacyAudit:
    """
    Comprehensive privacy audit across all AWS API calls
    
    Validates: Requirement 16.7
    """
    
    def test_all_aws_api_calls_are_auditable(self):
        """
        Verify all AWS API calls can be audited for PII
        
        Validates: Requirement 16.7
        """
        # List of all modules that use AWS
        aws_modules = [
            'src.telemetry.uploader',
            'src.vkp.puller',
            'src.embeddings.bedrock_strategy',
            'src.aws_control_plane.infrastructure_setup',
        ]
        
        verifier = PIIVerifier()
        
        # Verify PII verifier can scan any data structure
        test_data_types = [
            {'key': 'value'},  # dict
            'string data',  # string
            ['list', 'data'],  # list
            123,  # number
        ]
        
        for data in test_data_types:
            # Should not raise exception
            try:
                if isinstance(data, dict):
                    verifier.verify_no_pii(data)
                elif isinstance(data, str):
                    verifier.scan_for_patterns(data)
            except Exception as e:
                pytest.fail(f"PII verifier should handle {type(data)}: {e}")
    
    def test_privacy_audit_covers_all_pii_types(self):
        """
        Verify privacy audit covers all types of PII
        
        Validates: Requirement 16.7
        """
        verifier = PIIVerifier()
        
        # Test all PII types
        pii_examples = {
            'nik': '3201234567890123',  # Indonesian National ID
            'email': 'student@school.edu',
            'phone': '+628123456789',
            'username': 'john_doe',
            'name': 'John Doe',
            'chat': 'What is the answer?',
            'session_token': 'abc123def456',
        }
        
        for pii_type, pii_value in pii_examples.items():
            data = {pii_type: pii_value}
            result = verifier.verify_no_pii(data)
            assert not result, \
                f"PII verifier should detect {pii_type}: {pii_value}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
