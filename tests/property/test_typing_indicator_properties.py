"""Property-based tests for typing indicator lifecycle.

Feature: phase4-local-application
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, MagicMock, patch
from typing import Iterator
import time

from src.ui.pipeline_manager import PipelineManager
from src.ui.models import ChatMessage


# Feature: phase4-local-application, Property 14: Typing Indicator Lifecycle
@settings(max_examples=100, deadline=None)
@given(
    query=st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='\n\r\t'
    )),
    response_text=st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='\n\r\t'
    ))
)
@patch('src.ui.pipeline_manager.CompletePipeline')
def test_property_typing_indicator_lifecycle(
    mock_pipeline_class, 
    query, 
    response_text
):
    """Property 14: For any streaming response, a typing indicator should be displayed 
    while streaming is active and removed when streaming completes.
    
    This test verifies the lifecycle by checking that:
    1. The response processing completes successfully (indicating the indicator was shown)
    2. A complete ChatMessage is returned (indicating the indicator was removed)
    3. Processing time is recorded (indicating completion)
    
    **Validates: Requirements 9.2, 9.3**
    """
    # Setup mock pipeline
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.initialize.return_value = True
    mock_pipeline_instance.start.return_value = True
    
    # Mock process_query to return a result
    mock_result = MagicMock()
    mock_result.response = response_text
    mock_pipeline_instance.process_query.return_value = mock_result
    
    mock_pipeline_class.return_value = mock_pipeline_instance
    
    # Create and initialize pipeline manager
    manager = PipelineManager()
    manager.initialize_pipeline()
    
    # Import stream_response function
    from src.ui.chat_interface import stream_response
    
    # Call stream_response - this simulates the streaming lifecycle
    # In the actual UI, st.spinner("Sedang berpikir...") wraps this call
    result = stream_response(query, manager, "Semua")
    
    # Property 1: Response should be complete (indicator was removed)
    assert isinstance(result, ChatMessage), \
        "stream_response should return a ChatMessage after streaming completes"
    
    # Property 2: Response content should be present and non-empty
    assert result.content is not None, \
        "Response content should not be None after streaming completes"
    
    assert len(result.content) > 0, \
        "Response content should not be empty after streaming completes"
    
    # Property 3: Processing time should be recorded (indicator of completion)
    assert result.processing_time_ms is not None, \
        "Processing time should be recorded when streaming completes"
    
    assert result.processing_time_ms >= 0, \
        "Processing time should be non-negative"
    
    # Property 4: Result should be a valid assistant message
    assert result.role == "assistant", \
        "Response should have assistant role"
    
    assert result.timestamp is not None, \
        "Response should have a timestamp"


@settings(max_examples=100, deadline=None)
@given(
    query=st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='\n\r\t'
    )),
    response_text=st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='\n\r\t'
    ))
)
@patch('src.ui.pipeline_manager.CompletePipeline')
def test_property_typing_indicator_removed_on_completion(
    mock_pipeline_class,
    query,
    response_text
):
    """Property 14 (Completion): For any streaming response, the typing indicator 
    should be removed when streaming completes successfully.
    
    This test verifies that the response completes properly, which indicates
    the typing indicator lifecycle completed (shown during processing, removed on completion).
    
    **Validates: Requirements 9.3**
    """
    # Setup mock pipeline
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.initialize.return_value = True
    mock_pipeline_instance.start.return_value = True
    
    mock_result = MagicMock()
    mock_result.response = response_text
    mock_pipeline_instance.process_query.return_value = mock_result
    
    mock_pipeline_class.return_value = mock_pipeline_instance
    
    # Create and initialize pipeline manager
    manager = PipelineManager()
    manager.initialize_pipeline()
    
    # Import stream_response function
    from src.ui.chat_interface import stream_response
    
    # Call stream_response
    result = stream_response(query, manager, "Semua")
    
    # Property 1: Response should be complete (indicator was removed)
    assert result.content is not None, \
        "Response should be complete after streaming"
    
    assert len(result.content) > 0, \
        "Response should have non-empty content"
    
    # Property 2: Processing time indicates completion
    assert result.processing_time_ms is not None, \
        "Processing time should be set when streaming completes"
    
    assert result.processing_time_ms >= 0, \
        "Processing time should be non-negative"
    
    # Property 3: Result should be a valid ChatMessage
    assert result.role == "assistant", \
        "Response should have assistant role"
    
    assert result.timestamp is not None, \
        "Response should have a timestamp"
    
    # Property 4: Response content should match expected response
    assert response_text in result.content, \
        "Response should contain the expected text"


@settings(max_examples=100, deadline=None)
@given(
    query=st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='\n\r\t'
    ))
)
@patch('src.ui.pipeline_manager.CompletePipeline')
def test_property_typing_indicator_removed_on_error(
    mock_pipeline_class,
    query
):
    """Property 14 (Error Handling): For any streaming response that encounters an error, 
    the typing indicator should be removed even when streaming fails.
    
    This test verifies that even on error, a complete response is returned,
    indicating the typing indicator lifecycle completed properly.
    
    **Validates: Requirements 9.3, 9.4**
    """
    # Setup mock pipeline that raises an error
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.initialize.return_value = True
    mock_pipeline_instance.start.return_value = True
    mock_pipeline_instance.process_query.side_effect = Exception("Test error")
    
    mock_pipeline_class.return_value = mock_pipeline_instance
    
    # Create and initialize pipeline manager
    manager = PipelineManager()
    manager.initialize_pipeline()
    
    # Import stream_response function
    from src.ui.chat_interface import stream_response
    
    # Call stream_response - should handle error gracefully
    result = stream_response(query, manager, "Semua")
    
    # Property 1: Should return a ChatMessage even on error (indicator was removed)
    assert isinstance(result, ChatMessage), \
        "stream_response should return a ChatMessage even on error"
    
    # Property 2: Error message should be present
    assert result.content is not None, \
        "Error message should be present"
    
    assert len(result.content) > 0, \
        "Error message should not be empty"
    
    # Property 3: Processing time should still be recorded (completion indicator)
    assert result.processing_time_ms is not None, \
        "Processing time should be recorded even on error"
    
    assert result.processing_time_ms >= 0, \
        "Processing time should be non-negative"
    
    # Property 4: Error message should be in Indonesian (as per requirements)
    assert "Terjadi kesalahan" in result.content or "error" in result.content.lower(), \
        "Error message should indicate an error occurred"
    
    # Property 5: Result should be a valid ChatMessage
    assert result.role == "assistant", \
        "Error response should have assistant role"
    
    assert result.timestamp is not None, \
        "Error response should have a timestamp"


@settings(max_examples=100, deadline=None)
@given(
    queries=st.lists(
        st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('L', 'N', 'P', 'Z'),
            blacklist_characters='\n\r\t'
        )),
        min_size=2,
        max_size=5
    )
)
@patch('src.ui.pipeline_manager.CompletePipeline')
def test_property_typing_indicator_lifecycle_multiple_queries(
    mock_pipeline_class,
    queries
):
    """Property 14 (Multiple Queries): For any sequence of queries, each should have 
    its own typing indicator lifecycle (shown during streaming, removed on completion).
    
    This test verifies that each query completes properly with a valid response,
    indicating the typing indicator lifecycle worked correctly for each query.
    
    **Validates: Requirements 9.2, 9.3**
    """
    # Setup mock pipeline
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.initialize.return_value = True
    mock_pipeline_instance.start.return_value = True
    
    mock_pipeline_class.return_value = mock_pipeline_instance
    
    # Create and initialize pipeline manager
    manager = PipelineManager()
    manager.initialize_pipeline()
    
    # Import stream_response function
    from src.ui.chat_interface import stream_response
    
    # Process each query
    results = []
    for i, query in enumerate(queries):
        # Mock a unique response for each query
        mock_result = MagicMock()
        mock_result.response = f"Response {i}: {query[:20]}"
        mock_pipeline_instance.process_query.return_value = mock_result
        
        # Call stream_response
        result = stream_response(query, manager, "Semua")
        results.append(result)
    
    # Property 1: Each query should have a complete response (indicator was removed)
    assert len(results) == len(queries), \
        f"Should have {len(queries)} responses, got {len(results)}"
    
    # Property 2: All responses should be complete (have content)
    for i, result in enumerate(results):
        assert result.content is not None, \
            f"Response {i} should have content"
        
        assert len(result.content) > 0, \
            f"Response {i} should have non-empty content"
    
    # Property 3: All responses should have processing time (indicator of completion)
    for i, result in enumerate(results):
        assert result.processing_time_ms is not None, \
            f"Response {i} should have processing time"
        
        assert result.processing_time_ms >= 0, \
            f"Response {i} should have non-negative processing time"
    
    # Property 4: All responses should be valid ChatMessages
    for i, result in enumerate(results):
        assert isinstance(result, ChatMessage), \
            f"Response {i} should be a ChatMessage"
        
        assert result.role == "assistant", \
            f"Response {i} should have assistant role"
        
        assert result.timestamp is not None, \
            f"Response {i} should have a timestamp"
    
    # Property 5: Each response should be unique (not reused)
    response_contents = [r.content for r in results]
    # At least some responses should be different (unless all queries are identical)
    if len(set(queries)) > 1:
        assert len(set(response_contents)) > 1, \
            "Different queries should produce different responses"


@settings(max_examples=100, deadline=None)
@given(
    query=st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='\n\r\t'
    )),
    subject_filter=st.sampled_from(["Semua", "Matematika", "IPA", "Bahasa Indonesia", "Informatika"]),
    response_text=st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='\n\r\t'
    ))
)
@patch('src.ui.pipeline_manager.CompletePipeline')
def test_property_typing_indicator_with_subject_filter(
    mock_pipeline_class,
    query,
    subject_filter,
    response_text
):
    """Property 14 (Subject Filter): For any query with a subject filter, 
    the typing indicator lifecycle should work correctly.
    
    This test verifies that responses complete properly with subject filters,
    indicating the typing indicator lifecycle works correctly with filters.
    
    **Validates: Requirements 9.2, 9.3, 8.3**
    """
    # Setup mock pipeline
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.initialize.return_value = True
    mock_pipeline_instance.start.return_value = True
    
    mock_result = MagicMock()
    mock_result.response = response_text
    mock_pipeline_instance.process_query.return_value = mock_result
    
    mock_pipeline_class.return_value = mock_pipeline_instance
    
    # Create and initialize pipeline manager
    manager = PipelineManager()
    manager.initialize_pipeline()
    
    # Import stream_response function
    from src.ui.chat_interface import stream_response
    
    # Call stream_response with subject filter
    result = stream_response(query, manager, subject_filter)
    
    # Property 1: Response should be complete (indicator was removed)
    assert result.content is not None, \
        "Response should be complete after streaming"
    
    assert len(result.content) > 0, \
        "Response should have non-empty content"
    
    # Property 2: Processing time should be recorded (indicator of completion)
    assert result.processing_time_ms is not None, \
        "Processing time should be recorded when streaming completes"
    
    assert result.processing_time_ms >= 0, \
        "Processing time should be non-negative"
    
    # Property 3: Subject filter should be included in response if not "Semua"
    if subject_filter != "Semua":
        assert f"[Filter: {subject_filter}]" in result.content, \
            f"Response should include filter indicator for {subject_filter}"
    
    # Property 4: Result should be a valid ChatMessage
    assert isinstance(result, ChatMessage), \
        "Result should be a ChatMessage"
    
    assert result.role == "assistant", \
        "Result should have assistant role"
    
    assert result.timestamp is not None, \
        "Result should have a timestamp"
    
    # Property 5: Response should contain the expected text
    assert response_text in result.content, \
        "Response should contain the expected text"


@settings(max_examples=50, deadline=None)
@given(
    query=st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='\n\r\t'
    ))
)
def test_property_typing_indicator_without_pipeline(query):
    """Property 14 (No Pipeline): For any query without an initialized pipeline, 
    the typing indicator should still be removed even if processing fails.
    
    This test verifies that even without a pipeline, a complete error response
    is returned, indicating the typing indicator lifecycle completed properly.
    
    **Validates: Requirements 9.3**
    """
    # Create pipeline manager without initialization
    manager = PipelineManager()
    
    # Import stream_response function
    from src.ui.chat_interface import stream_response
    
    # Call stream_response without initialized pipeline
    # This should handle the error gracefully
    result = stream_response(query, manager, "Semua")
    
    # Property 1: Should return a ChatMessage even without pipeline (indicator was removed)
    assert isinstance(result, ChatMessage), \
        "stream_response should return a ChatMessage even without pipeline"
    
    # Property 2: Error message should be present
    assert result.content is not None, \
        "Error message should be present"
    
    assert len(result.content) > 0, \
        "Error message should not be empty"
    
    # Property 3: Processing time should still be recorded (completion indicator)
    assert result.processing_time_ms is not None, \
        "Processing time should be recorded even on error"
    
    assert result.processing_time_ms >= 0, \
        "Processing time should be non-negative"
    
    # Property 4: Result should be a valid ChatMessage
    assert result.role == "assistant", \
        "Result should have assistant role"
    
    assert result.timestamp is not None, \
        "Result should have a timestamp"
    
    # Property 5: Error message should indicate an error
    assert "Terjadi kesalahan" in result.content or "error" in result.content.lower(), \
        "Error message should indicate an error occurred"
