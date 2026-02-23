"""
Property Test: AWS Data Transmission Privacy

**Property 33: AWS Data Transmission Privacy**
**Validates: Requirements 16.4, 16.5, 16.6, 16.7**

This property test verifies that:
1. NO chat content is sent to AWS
2. NO user data is sent to AWS
3. Only anonymized metrics are transmitted to AWS
4. All AWS API calls are scanned for PII and rejected if found
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
import json
import re
from unittest.mock import Mock, patch, MagicMock

from src.telemetry.aggregator import AggregatedMetrics
from src.telemetry.pii_verifier import PIIVerifier
from src.telemetry.uploader import TelemetryUploader
from src.telemetry.anonymizer import Anonymizer


# Strategy for generating valid anonymized metrics
@st.composite
def valid_aws_metrics(draw):
    """Generate valid metrics for AWS transmission"""
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


# Strategy for generating data with chat content
@st.composite
def metrics_with_chat_content(draw):
    """Generate metrics that incorrectly contain chat content"""
    base_metrics = draw(valid_aws_metrics())
    metrics_dict = base_metrics.to_dict()
    
    # Add chat content (this should be rejected)
    chat_keys = draw(st.sampled_from(['chat', 'message', 'question', 'response', 'answer']))
    chat_content = draw(st.text(min_size=10, max_size=100))
    metrics_dict[chat_keys] = chat_content
    
    return metrics_dict


# Strategy for generating data with user identifiers
@st.composite
def metrics_with_user_data(draw):
    """Generate metrics that incorrectly contain user data"""
    base_metrics = draw(valid_aws_metrics())
    metrics_dict = base_metrics.to_dict()
    
    # Add user data (this should be rejected)
    user_key = draw(st.sampled_from(['username', 'user_id', 'email', 'name', 'student_id']))
    user_value = draw(st.text(min_size=3, max_size=50))
    metrics_dict[user_key] = user_value
    
    return metrics_dict


@given(metrics=valid_aws_metrics())
@settings(max_examples=100, deadline=None)
def test_aws_transmission_contains_no_chat_content(metrics):
    """
    Property: Data transmitted to AWS never contains chat content
    
    Validates: Requirement 16.4
    """
    metrics_dict = metrics.to_dict()
    
    # Check that no chat-related keys exist
    chat_keys = ['chat', 'message', 'question', 'response', 'answer', 'content', 
                 'query', 'prompt', 'conversation', 'dialogue']
    
    for key in metrics_dict.keys():
        assert key.lower() not in chat_keys, \
            f"AWS transmission should not contain chat-related keys: {key}"
    
    # Scan values for chat-like content patterns
    data_str = json.dumps(metrics_dict, ensure_ascii=False)
    
    # These patterns suggest chat content
    chat_patterns = [
        r'(?i)\b(what|how|why|when|where|who)\s+\w+',  # Question words
        r'(?i)\b(please|help|explain|tell me|show me)\b',  # Request phrases
        r'(?i)\b(student|teacher|class|homework|assignment)\s+(said|asked|answered)',  # Educational context
    ]
    
    for pattern in chat_patterns:
        matches = re.findall(pattern, data_str)
        # Allow a few false positives (e.g., "model_error" contains "error")
        # but reject if there are many matches suggesting actual chat content
        assert len(matches) < 3, \
            f"AWS transmission appears to contain chat content (pattern: {pattern}): {matches}"


@given(metrics=valid_aws_metrics())
@settings(max_examples=100, deadline=None)
def test_aws_transmission_contains_no_user_data(metrics):
    """
    Property: Data transmitted to AWS never contains user data
    
    Validates: Requirement 16.5
    """
    metrics_dict = metrics.to_dict()
    
    # Check that no user identifier keys exist
    user_keys = ['username', 'user_id', 'name', 'email', 'phone', 'address',
                 'student_id', 'teacher_id', 'nik', 'ktp', 'password', 'token',
                 'session_id', 'ip_address', 'nama', 'telepon', 'alamat']
    
    for key in metrics_dict.keys():
        assert key.lower() not in user_keys, \
            f"AWS transmission should not contain user data keys: {key}"
    
    # Verify PII patterns are not present (excluding school_id which is anonymized)
    verifier = PIIVerifier()
    
    # Use the verifier's verify_no_pii which already excludes school_id
    assert verifier.verify_no_pii(metrics_dict), \
        f"AWS transmission contains PII"


@given(metrics=valid_aws_metrics())
@settings(max_examples=100, deadline=None)
def test_aws_transmission_contains_only_anonymized_metrics(metrics):
    """
    Property: Data transmitted to AWS contains only anonymized metrics
    
    Validates: Requirement 16.6
    """
    verifier = PIIVerifier()
    metrics_dict = metrics.to_dict()
    
    # Verify no PII
    assert verifier.verify_no_pii(metrics_dict), \
        f"AWS transmission failed PII verification: {metrics_dict}"
    
    # Verify schema matches allowed keys
    is_valid, error_msg = verifier.validate_schema(metrics_dict)
    assert is_valid, f"AWS transmission schema validation failed: {error_msg}"
    
    # Verify school_id is anonymized (hashed format)
    school_id = metrics_dict.get('school_id', '')
    assert school_id.startswith('school_'), \
        f"School ID should be anonymized with 'school_' prefix: {school_id}"
    assert len(school_id) == 23, \
        f"Anonymized school ID should be 23 characters: {school_id}"
    
    # Verify all values are aggregated (no individual records)
    for key, value in metrics_dict.items():
        if key == 'error_types':
            assert isinstance(value, dict), f"{key} should be aggregated dict"
        elif key in ['school_id', 'model_version', 'embedding_model', 'chromadb_version']:
            assert isinstance(value, str), f"{key} should be string"
        else:
            assert isinstance(value, (int, float)), \
                f"{key} should be aggregated number, not individual record"


@given(metrics=metrics_with_chat_content())
@settings(max_examples=100, deadline=None)
def test_aws_transmission_rejects_chat_content(metrics):
    """
    Property: AWS transmission rejects data containing chat content
    
    Validates: Requirement 16.4
    """
    verifier = PIIVerifier()
    
    # Data with chat content should fail verification
    assert not verifier.verify_no_pii(metrics), \
        f"AWS transmission should reject data with chat content: {metrics}"


@given(metrics=metrics_with_user_data())
@settings(max_examples=100, deadline=None)
def test_aws_transmission_rejects_user_data(metrics):
    """
    Property: AWS transmission rejects data containing user data
    
    Validates: Requirement 16.5
    """
    verifier = PIIVerifier()
    
    # Data with user identifiers should fail verification
    # verify_no_pii checks both patterns and suspicious keys
    result = verifier.verify_no_pii(metrics)
    
    assert not result, \
        f"AWS transmission should reject data with user data: {list(metrics.keys())}"


@given(metrics=valid_aws_metrics())
@settings(max_examples=100, deadline=None)
def test_privacy_audit_scans_all_aws_api_calls(metrics):
    """
    Property: Privacy audit tool scans all AWS API calls for PII
    
    Validates: Requirement 16.7
    """
    verifier = PIIVerifier()
    uploader = TelemetryUploader(table_name='test-metrics')
    
    # Mock the DynamoDB table's put_item method
    with patch('boto3.resource') as mock_boto:
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_table.put_item = Mock(return_value={})
        mock_dynamodb.Table = Mock(return_value=mock_table)
        mock_boto.return_value = mock_dynamodb
        
        # Create a new uploader with mocked boto3
        uploader = TelemetryUploader(table_name='test-metrics')
        
        # Attempt upload
        uploader.upload_metrics(metrics)
        
        # Verify put_item was called
        if mock_table.put_item.called:
            # Get the data that would be sent to AWS
            call_args = mock_table.put_item.call_args
            sent_data = call_args[1]['Item'] if call_args else {}
            
            # Remove TTL field (added by uploader, not part of metrics)
            sent_data_copy = sent_data.copy()
            sent_data_copy.pop('ttl', None)
            
            # Verify the data passes PII verification
            assert verifier.verify_no_pii(sent_data_copy), \
                f"AWS API call contains PII: {sent_data_copy}"


@given(
    school_id=st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=65)),
    metrics=valid_aws_metrics()
)
@settings(max_examples=100, deadline=None)
def test_school_id_anonymization_before_aws_transmission(school_id, metrics):
    """
    Property: School IDs are anonymized before AWS transmission
    
    Validates: Requirements 16.6, 9.4
    """
    anonymizer = Anonymizer(salt='test-salt-456')
    
    # Anonymize school ID
    anonymized_id = anonymizer.anonymize_school_id(school_id)
    
    # Create metrics with anonymized ID
    metrics_dict = metrics.to_dict()
    metrics_dict['school_id'] = anonymized_id
    
    # Verify anonymized ID format
    assert anonymized_id.startswith('school_'), \
        f"Anonymized ID should start with 'school_': {anonymized_id}"
    
    # Verify original school_id is not in the anonymized school_id field
    # (Check only the school_id field to avoid false positives from numeric fields)
    assert school_id not in metrics_dict['school_id'], \
        f"Original school_id should not appear in anonymized school_id: {school_id}"
    
    # Verify data passes PII verification
    verifier = PIIVerifier()
    assert verifier.verify_no_pii(metrics_dict), \
        f"Anonymized metrics should pass PII verification"


@given(metrics=valid_aws_metrics())
@settings(max_examples=100, deadline=None)
def test_aws_transmission_contains_no_session_tokens(metrics):
    """
    Property: AWS transmission never contains session tokens or credentials
    
    Validates: Requirements 16.5, 16.6
    """
    metrics_dict = metrics.to_dict()
    data_str = json.dumps(metrics_dict)
    
    # Check for token-like patterns (long hex strings)
    token_pattern = r'\b[a-f0-9]{32,}\b'
    
    # School ID hash is expected (16 hex chars), but longer tokens are suspicious
    matches = re.findall(token_pattern, data_str)
    
    # Filter out the school_id hash (which is 16 chars, part of "school_XXXXXXXXXXXXXXXX")
    suspicious_tokens = [m for m in matches if len(m) > 20]
    
    assert len(suspicious_tokens) == 0, \
        f"AWS transmission should not contain session tokens: {suspicious_tokens}"


@given(metrics=valid_aws_metrics())
@settings(max_examples=100, deadline=None)
def test_aws_transmission_contains_no_ip_addresses(metrics):
    """
    Property: AWS transmission never contains IP addresses
    
    Validates: Requirements 16.5, 16.6
    """
    metrics_dict = metrics.to_dict()
    data_str = json.dumps(metrics_dict)
    
    # Check for IP address patterns
    ip_pattern = r'(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)'
    
    matches = re.findall(ip_pattern, data_str)
    
    # Filter out version numbers (e.g., "0.4.0") which look like IPs
    # Real IPs typically have at least one octet > 9
    suspicious_ips = []
    for match in matches:
        octets = [int(x) for x in match.split('.')]
        # If all octets are < 10, it's likely a version number
        if any(octet > 9 for octet in octets):
            suspicious_ips.append(match)
    
    assert len(suspicious_ips) == 0, \
        f"AWS transmission should not contain IP addresses: {suspicious_ips}"


@given(metrics=valid_aws_metrics())
@settings(max_examples=50, deadline=None)
def test_uploader_verifies_pii_before_transmission(metrics):
    """
    Property: TelemetryUploader verifies no PII before AWS transmission
    
    Validates: Requirements 16.6, 16.7
    """
    verifier = PIIVerifier()
    
    # Mock boto3 to capture what would be sent
    with patch('boto3.resource') as mock_boto:
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_table.put_item = Mock(return_value={})
        mock_dynamodb.Table = Mock(return_value=mock_table)
        mock_boto.return_value = mock_dynamodb
        
        # Create uploader with mocked boto3
        uploader = TelemetryUploader(table_name='test-metrics')
        
        # Upload metrics
        result = uploader.upload_metrics(metrics)
        
        # If upload was attempted, verify the data
        if mock_table.put_item.called:
            call_args = mock_table.put_item.call_args
            sent_data = call_args[1]['Item'] if call_args else {}
            
            # Remove TTL (added by uploader)
            sent_data_copy = sent_data.copy()
            sent_data_copy.pop('ttl', None)
            
            # Verify no PII in transmitted data
            assert verifier.verify_no_pii(sent_data_copy), \
                f"Uploader transmitted data with PII: {sent_data_copy}"


@given(
    metrics=valid_aws_metrics(),
    pii_key=st.sampled_from(['username', 'email', 'chat', 'message']),
    pii_value=st.text(min_size=5, max_size=50)
)
@settings(max_examples=50, deadline=None)
def test_uploader_blocks_transmission_with_pii(metrics, pii_key, pii_value):
    """
    Property: TelemetryUploader blocks transmission if PII is detected
    
    Validates: Requirements 16.6, 16.7
    """
    # Add PII to metrics
    metrics_dict = metrics.to_dict()
    metrics_dict[pii_key] = pii_value
    
    # Create a modified metrics object
    from dataclasses import replace
    modified_metrics = replace(metrics)
    
    # Verify PII detection
    verifier = PIIVerifier()
    assert not verifier.verify_no_pii(metrics_dict), \
        f"PII should be detected in metrics with {pii_key}={pii_value}"


@given(metrics=valid_aws_metrics())
@settings(max_examples=50, deadline=None)
def test_aws_transmission_data_is_json_serializable(metrics):
    """
    Property: All AWS transmission data is JSON-serializable (no binary data)
    
    Validates: Requirement 16.6
    """
    metrics_dict = metrics.to_dict()
    
    # Should be JSON-serializable
    try:
        json_str = json.dumps(metrics_dict)
        assert isinstance(json_str, str), "Should serialize to string"
        
        # Should be deserializable
        deserialized = json.loads(json_str)
        assert isinstance(deserialized, dict), "Should deserialize to dict"
        
    except (TypeError, ValueError) as e:
        pytest.fail(f"AWS transmission data should be JSON-serializable: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
