#!/usr/bin/env python3
"""
Telemetry System Checkpoint Verification

This script verifies that the telemetry system:
1. Generates test telemetry data
2. Runs PII verification
3. Uploads to DynamoDB (or mocks if AWS not configured)
4. Verifies only anonymized metrics are stored
5. Ensures all tests pass

Requirements: 9.1-9.5, 16.4-16.7
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.telemetry.collector import TelemetryCollector, MetricsSnapshot
from src.telemetry.aggregator import MetricsAggregator, AggregatedMetrics
from src.telemetry.pii_verifier import PIIVerifier
from src.telemetry.anonymizer import Anonymizer
from src.telemetry.uploader import TelemetryUploader


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def generate_test_telemetry():
    """Generate test telemetry data"""
    print_section("Step 1: Generate Test Telemetry Data")
    
    collector = TelemetryCollector()
    
    # Simulate some queries
    print("Simulating 10 queries...")
    for i in range(10):
        latency = 3000.0 + (i * 500)  # 3000-7500ms
        success = i < 8  # 8 successful, 2 failed
        collector.record_query(latency, success)
    
    # Simulate some errors
    print("Recording 2 errors...")
    collector.record_error('timeout', 'Request timeout after 30s')
    collector.record_error('oom', 'Out of memory during inference')
    
    # Get snapshot
    snapshot = collector.get_metrics_snapshot()
    
    print(f"✓ Generated telemetry snapshot:")
    print(f"  - Total queries: {snapshot.total_queries}")
    print(f"  - Successful: {snapshot.successful_queries}")
    print(f"  - Failed: {snapshot.failed_queries}")
    print(f"  - Errors: {len(snapshot.errors)}")
    
    return snapshot


def aggregate_metrics(snapshot):
    """Aggregate metrics"""
    print_section("Step 2: Aggregate Metrics")
    
    # Anonymize school ID
    anonymizer = Anonymizer(salt=os.getenv('TELEMETRY_SALT', 'default-salt-123'))
    school_id = anonymizer.anonymize_school_id('school_test_001')
    
    print(f"✓ Anonymized school ID: {school_id}")
    
    # Aggregate
    aggregator = MetricsAggregator(school_id=school_id)
    aggregated = aggregator.aggregate_hourly(snapshot)
    
    print(f"✓ Aggregated metrics:")
    print(f"  - School ID: {aggregated.school_id}")
    print(f"  - Total queries: {aggregated.total_queries}")
    print(f"  - Average latency: {aggregated.average_latency_ms:.2f}ms")
    print(f"  - P50 latency: {aggregated.p50_latency_ms:.2f}ms")
    print(f"  - P90 latency: {aggregated.p90_latency_ms:.2f}ms")
    print(f"  - Error rate: {aggregated.error_rate:.2%}")
    
    return aggregated


def verify_no_pii(aggregated):
    """Verify no PII in metrics"""
    print_section("Step 3: Run PII Verification")
    
    verifier = PIIVerifier()
    metrics_dict = aggregated.to_dict()
    
    print("Checking for PII patterns...")
    
    # Verify no PII
    has_no_pii = verifier.verify_no_pii(metrics_dict)
    
    if has_no_pii:
        print("✓ PII verification PASSED - No PII detected")
    else:
        print("✗ PII verification FAILED - PII detected!")
        return False
    
    # Validate schema
    is_valid, error_msg = verifier.validate_schema(metrics_dict)
    
    if is_valid:
        print("✓ Schema validation PASSED - Only allowed keys present")
    else:
        print(f"✗ Schema validation FAILED - {error_msg}")
        return False
    
    # Check specific requirements
    print("\nVerifying specific privacy requirements:")
    
    # Requirement 16.4: NO chat content
    chat_keys = ['chat', 'message', 'question', 'response', 'answer']
    has_chat = any(key in metrics_dict for key in chat_keys)
    if not has_chat:
        print("  ✓ Requirement 16.4: NO chat content in metrics")
    else:
        print("  ✗ Requirement 16.4: Chat content detected!")
        return False
    
    # Requirement 16.5: NO user data
    user_keys = ['username', 'user_id', 'email', 'name', 'student_id']
    has_user_data = any(key in metrics_dict for key in user_keys)
    if not has_user_data:
        print("  ✓ Requirement 16.5: NO user data in metrics")
    else:
        print("  ✗ Requirement 16.5: User data detected!")
        return False
    
    # Requirement 16.6: Only anonymized metrics
    school_id = metrics_dict.get('school_id', '')
    is_anonymized = school_id.startswith('school_') and len(school_id) == 23
    if is_anonymized:
        print("  ✓ Requirement 16.6: School ID is anonymized")
    else:
        print("  ✗ Requirement 16.6: School ID not properly anonymized!")
        return False
    
    return True


def simulate_upload(aggregated):
    """Simulate upload to DynamoDB"""
    print_section("Step 4: Simulate Upload to DynamoDB")
    
    # Check if AWS is configured
    aws_configured = os.getenv('AWS_ACCESS_KEY_ID') is not None
    
    if aws_configured:
        print("AWS credentials detected - attempting real upload...")
        uploader = TelemetryUploader(table_name='nexusai-metrics')
        
        try:
            success = uploader.upload_metrics(aggregated)
            if success:
                print("✓ Successfully uploaded to DynamoDB")
                return True
            else:
                print("✗ Upload failed")
                return False
        except Exception as e:
            print(f"✗ Upload error: {e}")
            return False
    else:
        print("AWS not configured - using mock upload...")
        print("✓ Mock upload successful (would upload to DynamoDB in production)")
        
        # Verify what would be uploaded
        metrics_dict = aggregated.to_dict()
        print(f"\nData that would be uploaded:")
        print(f"  - Keys: {list(metrics_dict.keys())}")
        print(f"  - School ID: {metrics_dict['school_id']}")
        print(f"  - Timestamp: {metrics_dict['timestamp']}")
        print(f"  - Total queries: {metrics_dict['total_queries']}")
        
        return True


def run_all_tests():
    """Run all telemetry tests"""
    print_section("Step 5: Run All Tests")
    
    import subprocess
    
    print("Running property tests...")
    result1 = subprocess.run(
        ['python', '-m', 'pytest', 'tests/property/test_telemetry_anonymization.py', '-v'],
        capture_output=True,
        text=True
    )
    
    if result1.returncode == 0:
        print("✓ Property tests PASSED")
    else:
        print("✗ Property tests FAILED")
        print(result1.stdout)
        return False
    
    print("\nRunning AWS transmission privacy tests...")
    result2 = subprocess.run(
        ['python', '-m', 'pytest', 'tests/property/test_aws_transmission_privacy.py', '-v'],
        capture_output=True,
        text=True
    )
    
    if result2.returncode == 0:
        print("✓ AWS transmission privacy tests PASSED")
    else:
        print("✗ AWS transmission privacy tests FAILED")
        print(result2.stdout)
        return False
    
    print("\nRunning unit tests...")
    result3 = subprocess.run(
        ['python', '-m', 'pytest', 'tests/unit/test_telemetry_system.py', '-v'],
        capture_output=True,
        text=True
    )
    
    if result3.returncode == 0:
        print("✓ Unit tests PASSED")
    else:
        print("✗ Unit tests FAILED")
        print(result3.stdout)
        return False
    
    return True


def main():
    """Main checkpoint verification"""
    print("\n" + "="*60)
    print("  TELEMETRY SYSTEM CHECKPOINT VERIFICATION")
    print("  Phase 8: Aggregated Telemetry System")
    print("="*60)
    
    try:
        # Step 1: Generate test telemetry
        snapshot = generate_test_telemetry()
        
        # Step 2: Aggregate metrics
        aggregated = aggregate_metrics(snapshot)
        
        # Step 3: Verify no PII
        if not verify_no_pii(aggregated):
            print("\n✗ CHECKPOINT FAILED: PII verification failed")
            return 1
        
        # Step 4: Simulate upload
        if not simulate_upload(aggregated):
            print("\n✗ CHECKPOINT FAILED: Upload simulation failed")
            return 1
        
        # Step 5: Run all tests
        if not run_all_tests():
            print("\n✗ CHECKPOINT FAILED: Tests failed")
            return 1
        
        # Success!
        print_section("CHECKPOINT VERIFICATION COMPLETE")
        print("✓ All verification steps passed!")
        print("\nSummary:")
        print("  ✓ Test telemetry data generated")
        print("  ✓ Metrics aggregated successfully")
        print("  ✓ PII verification passed")
        print("  ✓ Upload simulation successful")
        print("  ✓ All tests passed")
        print("\nPhase 8 (Aggregated Telemetry System) is COMPLETE!")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ CHECKPOINT FAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
