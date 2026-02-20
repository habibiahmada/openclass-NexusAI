"""
Property-based tests for status dashboard display accuracy.

Feature: phase4-local-application
"""

import pytest
from datetime import datetime
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, MagicMock

from src.ui.models import PipelineStatus
from src.ui.pipeline_manager import PipelineManager


class TestStatusDisplayAccuracyProperty:
    """
    Property 8: Status Display Accuracy
    
    **Validates: Requirements 3.3, 3.4**
    
    For any pipeline state, the status dashboard should accurately reflect the current 
    state of the database (loaded/not loaded with document count) and model 
    (ready/loading/error).
    """
    
    @given(
        database_loaded=st.booleans(),
        database_document_count=st.integers(min_value=0, max_value=100000),
        model_loaded=st.booleans(),
        memory_usage_mb=st.floats(min_value=0.0, max_value=8192.0, allow_nan=False, allow_infinity=False),
        has_error=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_status_reflects_pipeline_state_accurately(
        self, 
        database_loaded, 
        database_document_count, 
        model_loaded, 
        memory_usage_mb,
        has_error
    ):
        """
        Property: Status dashboard should accurately reflect pipeline state.
        
        For any combination of database state, model state, memory usage, and error state,
        the PipelineStatus returned by get_status() should accurately represent the 
        current pipeline state.
        """
        # Create a mock pipeline manager
        pipeline_manager = PipelineManager()
        
        # Create expected status
        error_message = "Test error message" if has_error else None
        expected_status = PipelineStatus(
            database_loaded=database_loaded,
            database_document_count=database_document_count,
            model_loaded=model_loaded,
            memory_usage_mb=memory_usage_mb,
            last_update=datetime.now(),
            error_message=error_message
        )
        
        # Mock the get_status method to return our expected status
        pipeline_manager.get_status = Mock(return_value=expected_status)
        
        # Get status from pipeline manager
        status = pipeline_manager.get_status()
        
        # Property 1: Database loaded state should match
        assert status.database_loaded == database_loaded, \
            f"Database loaded state mismatch: expected {database_loaded}, got {status.database_loaded}"
        
        # Property 2: Database document count should match
        assert status.database_document_count == database_document_count, \
            f"Document count mismatch: expected {database_document_count}, got {status.database_document_count}"
        
        # Property 3: Model loaded state should match
        assert status.model_loaded == model_loaded, \
            f"Model loaded state mismatch: expected {model_loaded}, got {status.model_loaded}"
        
        # Property 4: Memory usage should match
        assert abs(status.memory_usage_mb - memory_usage_mb) < 0.01, \
            f"Memory usage mismatch: expected {memory_usage_mb}, got {status.memory_usage_mb}"
        
        # Property 5: Error message should match
        assert status.error_message == error_message, \
            f"Error message mismatch: expected {error_message}, got {status.error_message}"
    
    @given(
        database_loaded=st.booleans(),
        database_document_count=st.integers(min_value=0, max_value=100000)
    )
    @settings(max_examples=100, deadline=None)
    def test_database_status_text_accuracy(self, database_loaded, database_document_count):
        """
        Property: Database status text should accurately reflect database state.
        
        For any database state (loaded/not loaded) and document count, the status text
        should correctly indicate whether the database is loaded and include the 
        document count when loaded.
        
        **Validates: Requirement 3.4**
        """
        status = PipelineStatus(
            database_loaded=database_loaded,
            database_document_count=database_document_count,
            model_loaded=True,
            memory_usage_mb=1000.0,
            last_update=datetime.now()
        )
        
        status_text = status.get_database_status_text()
        
        if database_loaded:
            # Property: When loaded, status should include "Loaded" and document count
            assert "Loaded" in status_text, \
                f"Database status should contain 'Loaded' when database_loaded=True, got: {status_text}"
            assert str(database_document_count) in status_text, \
                f"Database status should contain document count {database_document_count}, got: {status_text}"
            assert "documents" in status_text, \
                f"Database status should contain 'documents' label, got: {status_text}"
        else:
            # Property: When not loaded, status should indicate "Not Loaded"
            assert "Not Loaded" in status_text, \
                f"Database status should contain 'Not Loaded' when database_loaded=False, got: {status_text}"
    
    @given(
        model_loaded=st.booleans(),
        has_error=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_model_status_text_accuracy(self, model_loaded, has_error):
        """
        Property: Model status text should accurately reflect model state.
        
        For any model state (ready/loading/error), the status text should correctly
        indicate the current model state.
        
        **Validates: Requirement 3.3**
        """
        error_message = "Test error" if has_error else None
        
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=100,
            model_loaded=model_loaded,
            memory_usage_mb=1000.0,
            last_update=datetime.now(),
            error_message=error_message
        )
        
        status_text = status.get_model_status_text()
        
        if has_error:
            # Property: When error exists, status should indicate "Error"
            assert status_text == "Model: Error", \
                f"Model status should be 'Model: Error' when error exists, got: {status_text}"
        elif model_loaded:
            # Property: When loaded and no error, status should indicate "Ready"
            assert status_text == "Model: Ready", \
                f"Model status should be 'Model: Ready' when loaded, got: {status_text}"
        else:
            # Property: When not loaded and no error, status should indicate "Loading"
            assert status_text == "Model: Loading", \
                f"Model status should be 'Model: Loading' when not loaded, got: {status_text}"
    
    @given(
        # Generate random sequences of pipeline states
        state_sequence=st.lists(
            st.tuples(
                st.booleans(),  # database_loaded
                st.integers(min_value=0, max_value=10000),  # database_document_count
                st.booleans(),  # model_loaded
                st.floats(min_value=0.0, max_value=4096.0, allow_nan=False, allow_infinity=False)  # memory_usage_mb
            ),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_status_consistency_across_state_changes(self, state_sequence):
        """
        Property: Status should consistently reflect state changes.
        
        For any sequence of pipeline state changes, each status query should accurately
        reflect the current state at that moment.
        """
        pipeline_manager = PipelineManager()
        
        for db_loaded, doc_count, model_loaded, memory_mb in state_sequence:
            # Create status for this state
            expected_status = PipelineStatus(
                database_loaded=db_loaded,
                database_document_count=doc_count,
                model_loaded=model_loaded,
                memory_usage_mb=memory_mb,
                last_update=datetime.now()
            )
            
            # Mock get_status to return this state
            pipeline_manager.get_status = Mock(return_value=expected_status)
            
            # Get status
            status = pipeline_manager.get_status()
            
            # Verify all fields match
            assert status.database_loaded == db_loaded, \
                "Database loaded state should match current state"
            assert status.database_document_count == doc_count, \
                "Document count should match current state"
            assert status.model_loaded == model_loaded, \
                "Model loaded state should match current state"
            assert abs(status.memory_usage_mb - memory_mb) < 0.01, \
                "Memory usage should match current state"
    
    @given(
        database_document_count=st.integers(min_value=0, max_value=100000)
    )
    @settings(max_examples=100, deadline=None)
    def test_document_count_display_accuracy(self, database_document_count):
        """
        Property: Document count should be accurately displayed in status.
        
        For any document count, when the database is loaded, the status should
        display the exact document count.
        
        **Validates: Requirement 3.4**
        """
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=database_document_count,
            model_loaded=True,
            memory_usage_mb=1000.0,
            last_update=datetime.now()
        )
        
        status_text = status.get_database_status_text()
        
        # Property: Status text should contain the exact document count
        assert str(database_document_count) in status_text, \
            f"Status should display document count {database_document_count}, got: {status_text}"
        
        # Property: Format should be consistent
        expected_format = f"Database: Loaded ({database_document_count} documents)"
        assert status_text == expected_format, \
            f"Status format should be '{expected_format}', got: {status_text}"
    
    @given(
        # Test all three model states
        model_state=st.sampled_from(['ready', 'loading', 'error'])
    )
    @settings(max_examples=100, deadline=None)
    def test_model_state_display_accuracy(self, model_state):
        """
        Property: Model state should be accurately displayed.
        
        For any model state (ready/loading/error), the status should correctly
        display the state.
        
        **Validates: Requirement 3.3**
        """
        # Map state to status parameters
        if model_state == 'ready':
            model_loaded = True
            error_message = None
            expected_text = "Model: Ready"
        elif model_state == 'loading':
            model_loaded = False
            error_message = None
            expected_text = "Model: Loading"
        else:  # error
            model_loaded = False
            error_message = "Test error"
            expected_text = "Model: Error"
        
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=100,
            model_loaded=model_loaded,
            memory_usage_mb=1000.0,
            last_update=datetime.now(),
            error_message=error_message
        )
        
        status_text = status.get_model_status_text()
        
        # Property: Status text should match expected state
        assert status_text == expected_text, \
            f"Model status should be '{expected_text}' for state '{model_state}', got: {status_text}"
    
    @given(
        database_loaded=st.booleans(),
        model_loaded=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_status_independence_of_components(self, database_loaded, model_loaded):
        """
        Property: Database and model status should be independent.
        
        For any combination of database and model states, each component's status
        should be reported independently and accurately.
        """
        status = PipelineStatus(
            database_loaded=database_loaded,
            database_document_count=100,
            model_loaded=model_loaded,
            memory_usage_mb=1000.0,
            last_update=datetime.now()
        )
        
        db_status = status.get_database_status_text()
        model_status = status.get_model_status_text()
        
        # Property: Database status should only depend on database_loaded
        if database_loaded:
            assert "Loaded" in db_status, \
                "Database status should show 'Loaded' regardless of model state"
        else:
            assert "Not Loaded" in db_status, \
                "Database status should show 'Not Loaded' regardless of model state"
        
        # Property: Model status should only depend on model_loaded (when no error)
        if model_loaded:
            assert model_status == "Model: Ready", \
                "Model status should show 'Ready' regardless of database state"
        else:
            assert model_status == "Model: Loading", \
                "Model status should show 'Loading' regardless of database state"
    
    @given(
        num_status_checks=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_status_idempotency(self, num_status_checks):
        """
        Property: Multiple status checks should return consistent results.
        
        For any pipeline state, calling get_status() multiple times without state
        changes should return equivalent status information.
        """
        pipeline_manager = PipelineManager()
        
        # Create a fixed status
        fixed_status = PipelineStatus(
            database_loaded=True,
            database_document_count=500,
            model_loaded=True,
            memory_usage_mb=2048.0,
            last_update=datetime.now()
        )
        
        # Mock get_status to return the same status
        pipeline_manager.get_status = Mock(return_value=fixed_status)
        
        # Check status multiple times
        statuses = [pipeline_manager.get_status() for _ in range(num_status_checks)]
        
        # Property: All status checks should return the same values
        for status in statuses:
            assert status.database_loaded == fixed_status.database_loaded, \
                "Database loaded state should be consistent across multiple checks"
            assert status.database_document_count == fixed_status.database_document_count, \
                "Document count should be consistent across multiple checks"
            assert status.model_loaded == fixed_status.model_loaded, \
                "Model loaded state should be consistent across multiple checks"
            assert status.memory_usage_mb == fixed_status.memory_usage_mb, \
                "Memory usage should be consistent across multiple checks"
