"""Unit tests for cost tracking module.

Tests Bedrock cost calculation, S3 cost calculation, and budget alert triggering.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data_processing.cost_tracker import CostTracker, CostLog, CostEntry


class TestCostTracker:
    """Unit tests for CostTracker class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = Path(self.temp_dir) / "cost_log.json"
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_bedrock_cost_calculation(self):
        """Test Bedrock cost calculation with known values.
        
        Requirements: 10.1, 10.4
        """
        tracker = CostTracker(log_path=str(self.log_path), budget_limit=1.0)
        
        # Test case 1: 1000 tokens = $0.0001
        tracker.track_bedrock_tokens(1000)
        cost = tracker.calculate_bedrock_cost()
        assert abs(cost - 0.0001) < 0.000001, f"Expected $0.0001, got ${cost}"
        
        # Test case 2: 600,000 tokens = $0.06
        tracker.current_tokens = 0  # Reset
        tracker.track_bedrock_tokens(600000)
        cost = tracker.calculate_bedrock_cost()
        assert abs(cost - 0.06) < 0.000001, f"Expected $0.06, got ${cost}"
        
        # Test case 3: 0 tokens = $0.00
        cost = tracker.calculate_bedrock_cost(tokens=0)
        assert cost == 0.0, f"Expected $0.00, got ${cost}"
    
    def test_s3_cost_calculation(self):
        """Test S3 cost calculation with known values.
        
        Requirements: 10.2, 10.4
        """
        tracker = CostTracker(log_path=str(self.log_path), budget_limit=1.0)
        
        # Test case 1: 1024 MB (1 GB) = $0.023
        tracker.track_s3_transfer(1024.0)
        cost = tracker.calculate_s3_cost()
        assert abs(cost - 0.023) < 0.000001, f"Expected $0.023, got ${cost}"
        
        # Test case 2: 512 MB (0.5 GB) = $0.0115
        tracker.current_s3_mb = 0.0  # Reset
        tracker.track_s3_transfer(512.0)
        cost = tracker.calculate_s3_cost()
        expected = 0.5 * 0.023
        assert abs(cost - expected) < 0.000001, f"Expected ${expected}, got ${cost}"
        
        # Test case 3: 0 MB = $0.00
        cost = tracker.calculate_s3_cost(size_mb=0.0)
        assert cost == 0.0, f"Expected $0.00, got ${cost}"
    
    def test_budget_alert_triggering(self):
        """Test budget alert is triggered at 80% threshold.
        
        Requirements: 10.5
        """
        tracker = CostTracker(log_path=str(self.log_path), budget_limit=1.0)
        
        # Mock logger to capture warnings
        with patch('src.data_processing.cost_tracker.logger') as mock_logger:
            # Test case 1: 70% of budget - no alert
            tracker.cost_log.total_cost_to_date = 0.70
            tracker.cost_log.budget_remaining = 0.30
            tracker._check_budget_alert()
            mock_logger.warning.assert_not_called()
            
            # Test case 2: 80% of budget - alert triggered
            mock_logger.reset_mock()
            tracker.cost_log.total_cost_to_date = 0.80
            tracker.cost_log.budget_remaining = 0.20
            tracker._check_budget_alert()
            mock_logger.warning.assert_called_once()
            
            # Verify alert message contains budget info
            alert_message = mock_logger.warning.call_args[0][0]
            assert "BUDGET ALERT" in alert_message
            assert "80.0%" in alert_message
            
            # Test case 3: 95% of budget - alert triggered
            mock_logger.reset_mock()
            tracker.cost_log.total_cost_to_date = 0.95
            tracker.cost_log.budget_remaining = 0.05
            tracker._check_budget_alert()
            mock_logger.warning.assert_called_once()
            
            alert_message = mock_logger.warning.call_args[0][0]
            assert "95.0%" in alert_message
    
    def test_cost_log_persistence(self):
        """Test cost log is saved and loaded correctly.
        
        Requirements: 10.4
        """
        # Create tracker and record a run
        tracker1 = CostTracker(log_path=str(self.log_path), budget_limit=1.0)
        tracker1.track_bedrock_tokens(10000)
        tracker1.track_s3_transfer(100.0)
        tracker1.record_pipeline_run(files_processed=5, chunks_processed=50)
        
        # Verify log file was created
        assert self.log_path.exists(), "Cost log file should be created"
        
        # Load log in new tracker
        tracker2 = CostTracker(log_path=str(self.log_path), budget_limit=1.0)
        
        # Verify data was persisted
        assert len(tracker2.cost_log.pipeline_runs) == 1, "Should have 1 pipeline run"
        assert tracker2.cost_log.total_cost_to_date > 0, "Should have non-zero cost"
        assert tracker2.cost_log.budget_remaining < 1.0, "Budget remaining should be less than limit"
        
        # Verify specific values
        run = tracker2.cost_log.pipeline_runs[0]
        assert run.tokens_processed == 10000
        assert run.files_processed == 5
        assert run.chunks_processed == 50
    
    def test_multiple_pipeline_runs(self):
        """Test tracking multiple pipeline runs accumulates costs.
        
        Requirements: 10.4
        """
        tracker = CostTracker(log_path=str(self.log_path), budget_limit=1.0)
        
        # Run 1
        tracker.track_bedrock_tokens(5000)
        tracker.track_s3_transfer(50.0)
        entry1 = tracker.record_pipeline_run(files_processed=3, chunks_processed=30)
        
        # Run 2
        tracker.track_bedrock_tokens(8000)
        tracker.track_s3_transfer(80.0)
        entry2 = tracker.record_pipeline_run(files_processed=5, chunks_processed=50)
        
        # Verify both runs are recorded
        assert len(tracker.cost_log.pipeline_runs) == 2
        
        # Verify costs accumulate
        total_cost = entry1.total_cost + entry2.total_cost
        assert abs(tracker.cost_log.total_cost_to_date - total_cost) < 0.000001
        
        # Verify budget remaining is updated
        expected_remaining = 1.0 - total_cost
        assert abs(tracker.cost_log.budget_remaining - expected_remaining) < 0.000001
    
    def test_cost_summary(self):
        """Test cost summary generation.
        
        Requirements: 10.4
        """
        tracker = CostTracker(log_path=str(self.log_path), budget_limit=1.0)
        
        # Track some costs
        tracker.track_bedrock_tokens(10000)
        tracker.track_s3_transfer(100.0)
        
        # Get summary
        summary = tracker.get_cost_summary()
        
        # Verify summary structure
        assert 'current_run' in summary
        assert 'total_to_date' in summary
        assert 'budget_limit' in summary
        assert 'budget_remaining' in summary
        assert 'budget_used_percentage' in summary
        assert 'total_runs' in summary
        
        # Verify current run values
        assert summary['current_run']['tokens'] == 10000
        assert summary['current_run']['s3_mb'] == 100.0
        assert summary['current_run']['bedrock_cost'] > 0
        assert summary['current_run']['s3_cost'] > 0
        assert summary['current_run']['total_cost'] > 0
        
        # Verify budget values
        assert summary['budget_limit'] == 1.0
        assert summary['total_runs'] == 0  # No runs recorded yet
    
    def test_reset_after_recording(self):
        """Test that current run tracking resets after recording.
        
        Requirements: 10.4
        """
        tracker = CostTracker(log_path=str(self.log_path), budget_limit=1.0)
        
        # Track costs
        tracker.track_bedrock_tokens(10000)
        tracker.track_s3_transfer(100.0)
        
        # Verify costs are tracked
        assert tracker.current_tokens == 10000
        assert tracker.current_s3_mb == 100.0
        
        # Record run
        tracker.record_pipeline_run(files_processed=5, chunks_processed=50)
        
        # Verify tracking is reset
        assert tracker.current_tokens == 0
        assert tracker.current_s3_mb == 0.0
    
    def test_empty_cost_log_creation(self):
        """Test creating new cost log when none exists.
        
        Requirements: 10.4
        """
        tracker = CostTracker(log_path=str(self.log_path), budget_limit=1.0)
        
        # Verify initial state
        assert len(tracker.cost_log.pipeline_runs) == 0
        assert tracker.cost_log.total_cost_to_date == 0.0
        assert tracker.cost_log.budget_limit == 1.0
        assert tracker.cost_log.budget_remaining == 1.0
    
    def test_budget_limit_update(self):
        """Test that budget limit can be updated.
        
        Requirements: 10.5
        """
        # Create tracker with $1 budget
        tracker1 = CostTracker(log_path=str(self.log_path), budget_limit=1.0)
        tracker1.track_bedrock_tokens(5000)
        tracker1.record_pipeline_run(files_processed=3, chunks_processed=30)
        
        # Load with new budget limit
        tracker2 = CostTracker(log_path=str(self.log_path), budget_limit=2.0)
        
        # Verify budget limit is updated
        assert tracker2.cost_log.budget_limit == 2.0
        
        # Verify budget remaining is recalculated
        expected_remaining = 2.0 - tracker2.cost_log.total_cost_to_date
        assert abs(tracker2.cost_log.budget_remaining - expected_remaining) < 0.000001
    
    def test_cost_calculation_with_zero_values(self):
        """Test cost calculation handles zero values correctly.
        
        Requirements: 10.4
        """
        tracker = CostTracker(log_path=str(self.log_path), budget_limit=1.0)
        
        # Test with zero tokens
        cost = tracker.calculate_bedrock_cost(tokens=0)
        assert cost == 0.0
        
        # Test with zero S3 data
        cost = tracker.calculate_s3_cost(size_mb=0.0)
        assert cost == 0.0
        
        # Test total cost with zeros
        total = tracker.calculate_total_cost()
        assert total == 0.0
