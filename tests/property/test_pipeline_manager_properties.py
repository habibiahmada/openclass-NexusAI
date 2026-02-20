"""
Property-based tests for PipelineManager lazy initialization.

Feature: phase4-local-application
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, MagicMock
from src.ui.pipeline_manager import PipelineManager
from src.local_inference.complete_pipeline import CompletePipeline


class TestLazyInitializationProperty:
    """
    Property 10: Lazy Initialization
    
    **Validates: Requirements 5.1, 5.2**
    
    For any application startup, the Inference_Engine and Vector_DB should not be 
    loaded until the first query is submitted.
    """
    
    @given(
        # Generate random initialization attempts
        num_manager_creations=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_pipeline_not_loaded_on_manager_creation(self, num_manager_creations):
        """
        Property: Creating PipelineManager instances should not load the pipeline.
        
        For any number of PipelineManager creations, the pipeline should remain None
        until initialize_pipeline() is explicitly called.
        """
        for _ in range(num_manager_creations):
            manager = PipelineManager()
            
            # Assert pipeline is not loaded
            assert manager.pipeline is None, \
                "Pipeline should be None immediately after PipelineManager creation"
            
            # Assert no initialization error
            assert manager.initialization_error is None, \
                "No initialization error should exist before initialization attempt"
    
    @given(
        # Generate random sequences of get_pipeline calls before initialization
        num_get_calls=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_get_pipeline_returns_none_before_initialization(self, num_get_calls):
        """
        Property: get_pipeline() should return None before initialization.
        
        For any number of get_pipeline() calls before initialize_pipeline(),
        the result should always be None.
        """
        manager = PipelineManager()
        
        for _ in range(num_get_calls):
            pipeline = manager.get_pipeline()
            assert pipeline is None, \
                "get_pipeline() should return None before initialize_pipeline() is called"
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_inference_engine_not_loaded_until_initialization(self, mock_pipeline_class):
        """
        Property: Inference_Engine should not be loaded until initialize_pipeline() is called.
        
        This test verifies that the CompletePipeline (which loads the Inference_Engine)
        is not instantiated until initialize_pipeline() is explicitly called.
        """
        # Create manager - should not instantiate CompletePipeline
        manager = PipelineManager()
        
        # Verify CompletePipeline was not instantiated
        mock_pipeline_class.assert_not_called()
        
        # Verify pipeline is None
        assert manager.pipeline is None
        
        # Now initialize - this should instantiate CompletePipeline
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.initialize.return_value = True
        mock_pipeline_instance.start.return_value = True
        mock_pipeline_class.return_value = mock_pipeline_instance
        
        result = manager.initialize_pipeline()
        
        # Verify CompletePipeline was instantiated only after initialize_pipeline()
        mock_pipeline_class.assert_called_once()
        assert result is True
        assert manager.pipeline is not None
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_vector_db_not_loaded_until_initialization(self, mock_pipeline_class):
        """
        Property: Vector_DB should not be loaded until initialize_pipeline() is called.
        
        This test verifies that the Vector_DB (part of CompletePipeline) is not
        accessed or loaded until initialize_pipeline() is explicitly called.
        """
        # Create manager
        manager = PipelineManager()
        
        # Get status before initialization - should not access vector_db
        status = manager.get_status()
        
        # Verify status shows database not loaded
        assert status.database_loaded is False
        assert status.database_document_count == 0
        
        # Verify CompletePipeline was not instantiated
        mock_pipeline_class.assert_not_called()
    
    @given(
        # Generate random query strings
        query=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=50, deadline=None)
    def test_process_query_fails_before_initialization(self, query):
        """
        Property: process_query() should fail before initialization.
        
        For any query string, calling process_query() before initialize_pipeline()
        should raise a RuntimeError.
        """
        manager = PipelineManager()
        
        # Attempt to process query without initialization
        with pytest.raises(RuntimeError, match="Pipeline not initialized"):
            list(manager.process_query(query, subject_filter=None))
    
    @given(
        # Generate random initialization sequences
        initialize_twice=st.booleans()
    )
    @settings(max_examples=50, deadline=None)
    def test_lazy_initialization_happens_once(self, initialize_twice):
        """
        Property: Lazy initialization should only happen once.
        
        For any sequence of initialize_pipeline() calls, the CompletePipeline
        should only be instantiated once (subsequent calls should be no-ops).
        """
        with patch('src.ui.pipeline_manager.CompletePipeline') as mock_pipeline_class:
            # Setup mock
            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.initialize.return_value = True
            mock_pipeline_instance.start.return_value = True
            mock_pipeline_class.return_value = mock_pipeline_instance
            
            manager = PipelineManager()
            
            # First initialization
            result1 = manager.initialize_pipeline()
            assert result1 is True
            
            # Verify CompletePipeline was instantiated once
            assert mock_pipeline_class.call_count == 1
            
            if initialize_twice:
                # Second initialization should not create new pipeline
                result2 = manager.initialize_pipeline()
                assert result2 is True
                
                # Verify CompletePipeline was still only instantiated once
                assert mock_pipeline_class.call_count == 1
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_status_reflects_lazy_initialization_state(self, mock_pipeline_class):
        """
        Property: Status should accurately reflect lazy initialization state.
        
        Before initialization: model_loaded=False, database_loaded=False
        After initialization: model_loaded=True, database_loaded=True
        """
        # Setup mock
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.initialize.return_value = True
        mock_pipeline_instance.start.return_value = True
        mock_pipeline_instance.vector_db = MagicMock()
        mock_pipeline_instance.vector_db.count_documents.return_value = 100
        mock_pipeline_instance.get_pipeline_status.return_value = {
            'components': {
                'vector_db': True,
                'inference_engine': True
            },
            'memory': {
                'usage_mb': 1500.0
            }
        }
        mock_pipeline_class.return_value = mock_pipeline_instance
        
        manager = PipelineManager()
        
        # Status before initialization
        status_before = manager.get_status()
        assert status_before.model_loaded is False
        assert status_before.database_loaded is False
        
        # Initialize
        manager.initialize_pipeline()
        
        # Status after initialization
        status_after = manager.get_status()
        assert status_after.model_loaded is True
        assert status_after.database_loaded is True
        assert status_after.database_document_count == 100


class TestPipelineInstanceReuseProperty:
    """
    Property 11: Pipeline Instance Reuse
    
    **Validates: Requirements 5.5**
    
    For any session, all queries should use the same Complete_Pipeline instance 
    (verified by object identity).
    """
    
    @given(
        # Generate random sequences of queries
        num_queries=st.integers(min_value=1, max_value=20),
        queries=st.lists(
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_same_pipeline_instance_across_queries(self, mock_pipeline_class, num_queries, queries):
        """
        Property: All queries in a session should use the same pipeline instance.
        
        For any sequence of queries, the PipelineManager should reuse the same
        CompletePipeline instance (verified by object identity).
        """
        # Setup mock
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.initialize.return_value = True
        mock_pipeline_instance.start.return_value = True
        mock_pipeline_instance.process_query.return_value = MagicMock(response="Test response")
        mock_pipeline_class.return_value = mock_pipeline_instance
        
        manager = PipelineManager()
        
        # Initialize pipeline
        result = manager.initialize_pipeline()
        assert result is True
        
        # Get the pipeline instance after initialization
        first_pipeline = manager.get_pipeline()
        assert first_pipeline is not None
        
        # Process multiple queries and verify same instance is used
        for i in range(min(num_queries, len(queries))):
            query = queries[i]
            
            # Process query
            try:
                list(manager.process_query(query, subject_filter=None))
            except Exception:
                # Ignore query processing errors, we're testing instance reuse
                pass
            
            # Verify pipeline instance hasn't changed
            current_pipeline = manager.get_pipeline()
            assert current_pipeline is first_pipeline, \
                f"Pipeline instance changed after query {i+1}. Expected same instance across all queries."
        
        # Verify CompletePipeline was only instantiated once
        assert mock_pipeline_class.call_count == 1, \
            "CompletePipeline should only be instantiated once per session"
    
    @given(
        # Generate random subject filters
        subject_filters=st.lists(
            st.sampled_from([None, "matematika", "ipa", "bahasa indonesia", "informatika"]),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=None)
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_pipeline_instance_reused_across_different_filters(self, mock_pipeline_class, subject_filters):
        """
        Property: Pipeline instance should be reused regardless of subject filter.
        
        For any sequence of queries with different subject filters, the same
        CompletePipeline instance should be used.
        """
        # Setup mock
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.initialize.return_value = True
        mock_pipeline_instance.start.return_value = True
        mock_pipeline_instance.process_query.return_value = MagicMock(response="Test response")
        mock_pipeline_class.return_value = mock_pipeline_instance
        
        manager = PipelineManager()
        
        # Initialize pipeline
        manager.initialize_pipeline()
        
        # Get initial pipeline instance
        initial_pipeline = manager.get_pipeline()
        initial_pipeline_id = id(initial_pipeline)
        
        # Process queries with different filters
        for subject_filter in subject_filters:
            try:
                list(manager.process_query("Test query", subject_filter=subject_filter))
            except Exception:
                # Ignore query processing errors
                pass
            
            # Verify same pipeline instance
            current_pipeline = manager.get_pipeline()
            assert id(current_pipeline) == initial_pipeline_id, \
                f"Pipeline instance changed with filter '{subject_filter}'. Should reuse same instance."
        
        # Verify only one pipeline was created
        assert mock_pipeline_class.call_count == 1
    
    @given(
        # Generate random sequences of get_pipeline calls
        num_get_calls=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=100, deadline=None)
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_get_pipeline_returns_same_instance(self, mock_pipeline_class, num_get_calls):
        """
        Property: get_pipeline() should always return the same instance after initialization.
        
        For any number of get_pipeline() calls after initialization, the returned
        instance should be identical (same object identity).
        """
        # Setup mock
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.initialize.return_value = True
        mock_pipeline_instance.start.return_value = True
        mock_pipeline_class.return_value = mock_pipeline_instance
        
        manager = PipelineManager()
        
        # Initialize pipeline
        manager.initialize_pipeline()
        
        # Get first instance
        first_instance = manager.get_pipeline()
        first_instance_id = id(first_instance)
        
        # Call get_pipeline multiple times
        for _ in range(num_get_calls):
            current_instance = manager.get_pipeline()
            assert id(current_instance) == first_instance_id, \
                "get_pipeline() should return the same instance every time"
            assert current_instance is first_instance, \
                "get_pipeline() should return identical object (same identity)"
    
    @given(
        # Generate random sequences of status checks
        num_status_checks=st.integers(min_value=1, max_value=30)
    )
    @settings(max_examples=100, deadline=None)
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_pipeline_instance_unchanged_by_status_checks(self, mock_pipeline_class, num_status_checks):
        """
        Property: get_status() should not affect pipeline instance.
        
        For any number of get_status() calls, the pipeline instance should remain
        the same (status checks should not recreate the pipeline).
        """
        # Setup mock
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.initialize.return_value = True
        mock_pipeline_instance.start.return_value = True
        mock_pipeline_instance.vector_db = MagicMock()
        mock_pipeline_instance.vector_db.count_documents.return_value = 100
        mock_pipeline_instance.get_pipeline_status.return_value = {
            'components': {
                'vector_db': True,
                'inference_engine': True
            },
            'memory': {
                'usage_mb': 1500.0
            }
        }
        mock_pipeline_class.return_value = mock_pipeline_instance
        
        manager = PipelineManager()
        
        # Initialize pipeline
        manager.initialize_pipeline()
        
        # Get initial pipeline instance
        initial_pipeline = manager.get_pipeline()
        initial_pipeline_id = id(initial_pipeline)
        
        # Call get_status multiple times
        for _ in range(num_status_checks):
            manager.get_status()
            
            # Verify pipeline instance hasn't changed
            current_pipeline = manager.get_pipeline()
            assert id(current_pipeline) == initial_pipeline_id, \
                "get_status() should not change the pipeline instance"
        
        # Verify only one pipeline was created
        assert mock_pipeline_class.call_count == 1
    
    @given(
        # Generate random mixed operations
        operations=st.lists(
            st.sampled_from(['query', 'status', 'get_pipeline']),
            min_size=5,
            max_size=30
        )
    )
    @settings(max_examples=100, deadline=None)
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_pipeline_instance_reused_across_mixed_operations(self, mock_pipeline_class, operations):
        """
        Property: Pipeline instance should be reused across all operations.
        
        For any sequence of mixed operations (queries, status checks, get_pipeline calls),
        the same CompletePipeline instance should be used throughout.
        """
        # Setup mock
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.initialize.return_value = True
        mock_pipeline_instance.start.return_value = True
        mock_pipeline_instance.process_query.return_value = MagicMock(response="Test response")
        mock_pipeline_instance.vector_db = MagicMock()
        mock_pipeline_instance.vector_db.count_documents.return_value = 100
        mock_pipeline_instance.get_pipeline_status.return_value = {
            'components': {
                'vector_db': True,
                'inference_engine': True
            },
            'memory': {
                'usage_mb': 1500.0
            }
        }
        mock_pipeline_class.return_value = mock_pipeline_instance
        
        manager = PipelineManager()
        
        # Initialize pipeline
        manager.initialize_pipeline()
        
        # Get initial pipeline instance
        initial_pipeline = manager.get_pipeline()
        initial_pipeline_id = id(initial_pipeline)
        
        # Perform mixed operations
        for operation in operations:
            if operation == 'query':
                try:
                    list(manager.process_query("Test query", subject_filter=None))
                except Exception:
                    pass
            elif operation == 'status':
                manager.get_status()
            elif operation == 'get_pipeline':
                manager.get_pipeline()
            
            # Verify pipeline instance hasn't changed
            current_pipeline = manager.get_pipeline()
            assert id(current_pipeline) == initial_pipeline_id, \
                f"Pipeline instance changed after '{operation}' operation. Should reuse same instance."
        
        # Verify only one pipeline was created
        assert mock_pipeline_class.call_count == 1
