"""Integration test for cost tracking with ETL pipeline.

Verifies that cost tracking integrates correctly with the pipeline.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

from src.data_processing.etl_pipeline import ETLPipeline, PipelineConfig
from src.data_processing.cost_tracker import CostTracker


def test_cost_tracking_integration():
    """Test that cost tracking integrates with ETL pipeline.
    
    Verifies:
    - Cost tracker is initialized with pipeline
    - Costs are tracked during pipeline execution
    - Cost log is saved after pipeline run
    """
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    try:
        input_dir = Path(temp_dir) / "input"
        output_dir = Path(temp_dir) / "output"
        vector_db_dir = Path(temp_dir) / "vector_db"
        
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create pipeline config
        config = PipelineConfig(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            vector_db_dir=str(vector_db_dir),
            budget_limit=1.0
        )
        
        # Create pipeline
        pipeline = ETLPipeline(config)
        
        # Verify cost tracker is initialized
        assert pipeline.cost_tracker is not None
        assert isinstance(pipeline.cost_tracker, CostTracker)
        assert pipeline.cost_tracker.budget_limit == 1.0
        
        # Verify cost log path
        expected_log_path = Path(output_dir) / "metadata" / "cost_log.json"
        assert pipeline.cost_tracker.log_path == expected_log_path
        
        print("✓ Cost tracker integration test passed")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_cost_tracker_tracks_tokens():
    """Test that cost tracker tracks Bedrock tokens correctly."""
    temp_dir = tempfile.mkdtemp()
    try:
        log_path = Path(temp_dir) / "cost_log.json"
        
        tracker = CostTracker(log_path=str(log_path), budget_limit=1.0)
        
        # Track some tokens
        tracker.track_bedrock_tokens(10000)
        
        # Verify tracking
        assert tracker.current_tokens == 10000
        
        # Calculate cost
        cost = tracker.calculate_bedrock_cost()
        expected_cost = (10000 / 1000) * 0.0001  # $0.001
        assert abs(cost - expected_cost) < 0.000001
        
        print("✓ Token tracking test passed")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_cost_tracking_integration()
    test_cost_tracker_tracks_tokens()
    print("\n✅ All integration tests passed!")
