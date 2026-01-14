"""Property-based tests for cost tracking.

Feature: phase2-backend-knowledge-engineering
"""

import pytest
from hypothesis import given, strategies as st, settings
import tempfile
import shutil
from pathlib import Path

from src.data_processing.cost_tracker import CostTracker


# Feature: phase2-backend-knowledge-engineering, Property 19: Cost Tracking Accuracy
@settings(max_examples=100)
@given(
    tokens_processed=st.integers(min_value=0, max_value=1000000),
    s3_data_mb=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
def test_property_cost_tracking_accuracy(tokens_processed, s3_data_mb):
    """Property 19: For any pipeline execution, the estimated cost should be calculated as:
    (tokens_processed / 1000) × $0.0001 + (s3_data_mb × $0.023 / 1000).
    
    Validates: Requirements 10.4
    """
    # Create temporary directory for cost log
    temp_dir = tempfile.mkdtemp()
    try:
        log_path = Path(temp_dir) / "cost_log.json"
        
        # Create cost tracker
        tracker = CostTracker(log_path=str(log_path), budget_limit=10.0)
        
        # Track costs
        tracker.track_bedrock_tokens(tokens_processed)
        tracker.track_s3_transfer(s3_data_mb)
        
        # Calculate expected costs
        expected_bedrock_cost = (tokens_processed / 1000) * 0.0001
        expected_s3_cost = (s3_data_mb / 1024) * 0.023  # Convert MB to GB, then multiply by cost
        expected_total_cost = expected_bedrock_cost + expected_s3_cost
        
        # Get actual costs
        actual_bedrock_cost = tracker.calculate_bedrock_cost()
        actual_s3_cost = tracker.calculate_s3_cost()
        actual_total_cost = tracker.calculate_total_cost()
        
        # Property: Bedrock cost calculation should be accurate
        assert abs(actual_bedrock_cost - expected_bedrock_cost) < 0.000001, \
            f"Bedrock cost mismatch: expected {expected_bedrock_cost:.6f}, got {actual_bedrock_cost:.6f}"
        
        # Property: S3 cost calculation should be accurate
        assert abs(actual_s3_cost - expected_s3_cost) < 0.000001, \
            f"S3 cost mismatch: expected {expected_s3_cost:.6f}, got {actual_s3_cost:.6f}"
        
        # Property: Total cost should equal sum of individual costs
        assert abs(actual_total_cost - expected_total_cost) < 0.000001, \
            f"Total cost mismatch: expected {expected_total_cost:.6f}, got {actual_total_cost:.6f}"
        
        # Property: Total cost should equal bedrock + s3
        assert abs(actual_total_cost - (actual_bedrock_cost + actual_s3_cost)) < 0.000001, \
            "Total cost should equal sum of Bedrock and S3 costs"
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
