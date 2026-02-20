"""
Unit tests for Phase 4 Local Application chat interface.

Tests display_sources(), display_message(), and stream_response() functions.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from src.ui.chat_interface import display_sources, display_message, stream_response
from src.ui.models import ChatMessage, SourceCitation
from src.ui.pipeline_manager import PipelineManager


class TestDisplaySources:
    """Tests for display_sources() function."""
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', True)
    @patch('src.ui.chat_interface.st')
    def test_display_sources_formats_single_citation(self, mock_st):
        """Test display_sources() formats a single citation correctly."""
        sources = [
            SourceCitation(
                filename="matematika_kelas_7.pdf",
                subject="Matematika",
                relevance_score=0.85,
                chunk_index=5
            )
        ]
        
        display_sources(sources)
        
        # Verify markdown header was called
        mock_st.markdown.assert_called_once_with("**Sumber:**")
        
        # Verify caption was called with formatted citation
        mock_st.caption.assert_called_once_with(
            "📚 Matematika - matematika_kelas_7.pdf (Relevance: 0.85)"
        )
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', True)
    @patch('src.ui.chat_interface.st')
    def test_display_sources_formats_multiple_citations(self, mock_st):
        """Test display_sources() formats multiple citations correctly."""
        sources = [
            SourceCitation(
                filename="ipa_kelas_7.pdf",
                subject="IPA",
                relevance_score=0.92,
                chunk_index=3
            ),
            SourceCitation(
                filename="ipa_kelas_8.pdf",
                subject="IPA",
                relevance_score=0.88,
                chunk_index=7
            ),
            SourceCitation(
                filename="matematika_kelas_7.pdf",
                subject="Matematika",
                relevance_score=0.75,
                chunk_index=2
            )
        ]
        
        display_sources(sources)
        
        # Verify markdown header was called
        mock_st.markdown.assert_called_once_with("**Sumber:**")
        
        # Verify caption was called for each source
        assert mock_st.caption.call_count == 3
        
        # Verify each citation was formatted correctly
        calls = mock_st.caption.call_args_list
        assert calls[0][0][0] == "📚 IPA - ipa_kelas_7.pdf (Relevance: 0.92)"
        assert calls[1][0][0] == "📚 IPA - ipa_kelas_8.pdf (Relevance: 0.88)"
        assert calls[2][0][0] == "📚 Matematika - matematika_kelas_7.pdf (Relevance: 0.75)"
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', True)
    @patch('src.ui.chat_interface.st')
    def test_display_sources_empty_list(self, mock_st):
        """Test display_sources() handles empty source list."""
        sources = []
        
        display_sources(sources)
        
        # Should not call any streamlit functions
        mock_st.markdown.assert_not_called()
        mock_st.caption.assert_not_called()
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', False)
    def test_display_sources_streamlit_not_available(self):
        """Test display_sources() handles Streamlit not available."""
        sources = [
            SourceCitation(
                filename="test.pdf",
                subject="Test",
                relevance_score=0.5,
                chunk_index=0
            )
        ]
        
        # Should not raise an error
        display_sources(sources)
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', True)
    @patch('src.ui.chat_interface.st')
    def test_display_sources_formats_with_different_scores(self, mock_st):
        """Test display_sources() formats citations with various relevance scores."""
        sources = [
            SourceCitation(
                filename="high_score.pdf",
                subject="Test",
                relevance_score=0.99,
                chunk_index=0
            ),
            SourceCitation(
                filename="low_score.pdf",
                subject="Test",
                relevance_score=0.12,
                chunk_index=1
            ),
            SourceCitation(
                filename="perfect_score.pdf",
                subject="Test",
                relevance_score=1.0,
                chunk_index=2
            )
        ]
        
        display_sources(sources)
        
        # Verify all citations were formatted with correct scores
        calls = mock_st.caption.call_args_list
        assert calls[0][0][0] == "📚 Test - high_score.pdf (Relevance: 0.99)"
        assert calls[1][0][0] == "📚 Test - low_score.pdf (Relevance: 0.12)"
        assert calls[2][0][0] == "📚 Test - perfect_score.pdf (Relevance: 1.00)"


class TestDisplayMessage:
    """Tests for display_message() function."""
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', True)
    @patch('src.ui.chat_interface.st')
    def test_display_message_user_role(self, mock_st):
        """Test display_message() handles user role correctly."""
        message = ChatMessage(
            role="user",
            content="Apa itu fotosintesis?",
            timestamp=datetime.now()
        )
        
        # Create mock context manager
        mock_chat_message = MagicMock()
        mock_st.chat_message.return_value.__enter__ = Mock(return_value=mock_chat_message)
        mock_st.chat_message.return_value.__exit__ = Mock(return_value=False)
        
        display_message(message)
        
        # Verify chat_message was called with "user"
        mock_st.chat_message.assert_called_once_with("user")
        
        # Verify markdown was called with message content
        mock_st.markdown.assert_called_once_with("Apa itu fotosintesis?")
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', True)
    @patch('src.ui.chat_interface.st')
    def test_display_message_assistant_role(self, mock_st):
        """Test display_message() handles assistant role correctly."""
        message = ChatMessage(
            role="assistant",
            content="Fotosintesis adalah proses...",
            timestamp=datetime.now()
        )
        
        # Create mock context manager
        mock_chat_message = MagicMock()
        mock_st.chat_message.return_value.__enter__ = Mock(return_value=mock_chat_message)
        mock_st.chat_message.return_value.__exit__ = Mock(return_value=False)
        
        display_message(message)
        
        # Verify chat_message was called with "assistant"
        mock_st.chat_message.assert_called_once_with("assistant")
        
        # Verify markdown was called with message content
        mock_st.markdown.assert_called_once_with("Fotosintesis adalah proses...")
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', True)
    @patch('src.ui.chat_interface.st')
    @patch('src.ui.chat_interface.display_sources')
    def test_display_message_with_sources(self, mock_display_sources, mock_st):
        """Test display_message() displays sources for assistant messages."""
        sources = [
            SourceCitation(
                filename="ipa_kelas_7.pdf",
                subject="IPA",
                relevance_score=0.9,
                chunk_index=2
            )
        ]
        
        message = ChatMessage(
            role="assistant",
            content="Response with sources",
            sources=sources,
            timestamp=datetime.now()
        )
        
        # Create mock context manager
        mock_chat_message = MagicMock()
        mock_st.chat_message.return_value.__enter__ = Mock(return_value=mock_chat_message)
        mock_st.chat_message.return_value.__exit__ = Mock(return_value=False)
        
        display_message(message)
        
        # Verify display_sources was called with sources
        mock_display_sources.assert_called_once_with(sources)
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', True)
    @patch('src.ui.chat_interface.st')
    def test_display_message_with_processing_time(self, mock_st):
        """Test display_message() displays processing time."""
        message = ChatMessage(
            role="assistant",
            content="Response text",
            processing_time_ms=1234.56,
            timestamp=datetime.now()
        )
        
        # Create mock context manager
        mock_chat_message = MagicMock()
        mock_st.chat_message.return_value.__enter__ = Mock(return_value=mock_chat_message)
        mock_st.chat_message.return_value.__exit__ = Mock(return_value=False)
        
        display_message(message)
        
        # Verify caption was called with processing time
        mock_st.caption.assert_called_once_with("⏱️ Waktu proses: 1235ms")
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', True)
    @patch('src.ui.chat_interface.st')
    @patch('src.ui.chat_interface.display_sources')
    def test_display_message_assistant_without_sources(self, mock_display_sources, mock_st):
        """Test display_message() handles assistant message without sources."""
        message = ChatMessage(
            role="assistant",
            content="Response without sources",
            sources=[],
            timestamp=datetime.now()
        )
        
        # Create mock context manager
        mock_chat_message = MagicMock()
        mock_st.chat_message.return_value.__enter__ = Mock(return_value=mock_chat_message)
        mock_st.chat_message.return_value.__exit__ = Mock(return_value=False)
        
        display_message(message)
        
        # Verify display_sources was not called
        mock_display_sources.assert_not_called()
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', False)
    def test_display_message_streamlit_not_available(self):
        """Test display_message() handles Streamlit not available."""
        message = ChatMessage(
            role="user",
            content="Test message",
            timestamp=datetime.now()
        )
        
        # Should not raise an error
        display_message(message)
    
    @patch('src.ui.chat_interface.STREAMLIT_AVAILABLE', True)
    @patch('src.ui.chat_interface.st')
    def test_display_message_user_without_processing_time(self, mock_st):
        """Test display_message() handles user message without processing time."""
        message = ChatMessage(
            role="user",
            content="User question",
            timestamp=datetime.now()
        )
        
        # Create mock context manager
        mock_chat_message = MagicMock()
        mock_st.chat_message.return_value.__enter__ = Mock(return_value=mock_chat_message)
        mock_st.chat_message.return_value.__exit__ = Mock(return_value=False)
        
        display_message(message)
        
        # Verify caption was not called (no processing time for user messages)
        mock_st.caption.assert_not_called()


class TestStreamResponse:
    """Tests for stream_response() function."""
    
    @patch('src.ui.subject_filter.map_subject_to_filter')
    def test_stream_response_success(self, mock_map_filter):
        """Test stream_response() successfully processes a query."""
        # Setup mocks
        mock_map_filter.return_value = None
        
        mock_pipeline_manager = Mock(spec=PipelineManager)
        mock_pipeline_manager.process_query.return_value = iter(["Hello", " ", "world", "!"])
        
        # Call function
        result = stream_response("Test query", mock_pipeline_manager, "Semua")
        
        # Verify result
        assert isinstance(result, ChatMessage)
        assert result.role == "assistant"
        assert result.content == "Hello world!"
        assert result.sources == []
        assert result.processing_time_ms is not None
        assert result.processing_time_ms > 0
        
        # Verify pipeline was called correctly
        mock_pipeline_manager.process_query.assert_called_once_with("Test query", None)
        mock_map_filter.assert_called_once_with("Semua")
    
    @patch('src.ui.subject_filter.map_subject_to_filter')
    def test_stream_response_with_subject_filter(self, mock_map_filter):
        """Test stream_response() applies subject filter correctly."""
        # Setup mocks
        mock_map_filter.return_value = "matematika"
        
        mock_pipeline_manager = Mock(spec=PipelineManager)
        mock_pipeline_manager.process_query.return_value = iter(["Response", " ", "text"])
        
        # Call function
        result = stream_response("Math question", mock_pipeline_manager, "Matematika")
        
        # Verify filter was applied
        assert result.content.startswith("*[Filter: Matematika]*\n\n")
        assert "Response text" in result.content
        
        # Verify pipeline was called with filter
        mock_pipeline_manager.process_query.assert_called_once_with("Math question", "matematika")
        mock_map_filter.assert_called_once_with("Matematika")
    
    @patch('src.ui.subject_filter.map_subject_to_filter')
    def test_stream_response_no_filter_for_semua(self, mock_map_filter):
        """Test stream_response() doesn't add filter text for 'Semua'."""
        # Setup mocks
        mock_map_filter.return_value = None
        
        mock_pipeline_manager = Mock(spec=PipelineManager)
        mock_pipeline_manager.process_query.return_value = iter(["Response"])
        
        # Call function
        result = stream_response("Question", mock_pipeline_manager, "Semua")
        
        # Verify no filter text was added
        assert result.content == "Response"
        assert "*[Filter:" not in result.content
    
    @patch('src.ui.subject_filter.map_subject_to_filter')
    @patch('src.ui.chat_interface.get_error_message')
    def test_stream_response_error_handling(self, mock_get_error, mock_map_filter):
        """Test stream_response() handles errors gracefully."""
        # Setup mocks
        mock_map_filter.return_value = None
        mock_get_error.return_value = "Terjadi kesalahan. Silakan coba lagi."
        
        mock_pipeline_manager = Mock(spec=PipelineManager)
        mock_pipeline_manager.process_query.side_effect = RuntimeError("Pipeline error")
        
        # Call function
        result = stream_response("Test query", mock_pipeline_manager, "Semua")
        
        # Verify error message was returned
        assert isinstance(result, ChatMessage)
        assert result.role == "assistant"
        assert result.content == "Terjadi kesalahan. Silakan coba lagi."
        assert result.sources == []
        assert result.processing_time_ms is not None
        
        # Verify error message was retrieved
        mock_get_error.assert_called_once_with('query_failed')
    
    @patch('src.ui.subject_filter.map_subject_to_filter')
    @patch('src.ui.chat_interface.get_error_message')
    def test_stream_response_handles_different_exceptions(self, mock_get_error, mock_map_filter):
        """Test stream_response() handles various exception types."""
        # Setup mocks
        mock_map_filter.return_value = None
        mock_get_error.return_value = "Terjadi kesalahan. Silakan coba lagi."
        
        mock_pipeline_manager = Mock(spec=PipelineManager)
        
        # Test with different exception types
        exceptions = [
            ValueError("Invalid input"),
            KeyError("Missing key"),
            AttributeError("Missing attribute"),
            Exception("Generic error")
        ]
        
        for exc in exceptions:
            mock_pipeline_manager.process_query.side_effect = exc
            
            result = stream_response("Test query", mock_pipeline_manager, "Semua")
            
            # All should return error message
            assert result.role == "assistant"
            assert result.content == "Terjadi kesalahan. Silakan coba lagi."
    
    @patch('src.ui.subject_filter.map_subject_to_filter')
    def test_stream_response_empty_response(self, mock_map_filter):
        """Test stream_response() handles empty response from pipeline."""
        # Setup mocks
        mock_map_filter.return_value = None
        
        mock_pipeline_manager = Mock(spec=PipelineManager)
        mock_pipeline_manager.process_query.return_value = iter([])
        
        # Call function
        result = stream_response("Test query", mock_pipeline_manager, "Semua")
        
        # Verify empty content
        assert result.content == ""
        assert result.role == "assistant"
    
    @patch('src.ui.subject_filter.map_subject_to_filter')
    def test_stream_response_processing_time_calculated(self, mock_map_filter):
        """Test stream_response() calculates processing time."""
        # Setup mocks
        mock_map_filter.return_value = None
        
        mock_pipeline_manager = Mock(spec=PipelineManager)
        mock_pipeline_manager.process_query.return_value = iter(["Response"])
        
        # Call function
        result = stream_response("Test query", mock_pipeline_manager, "Semua")
        
        # Verify processing time is present and reasonable
        assert result.processing_time_ms is not None
        assert result.processing_time_ms >= 0
        assert result.processing_time_ms < 10000  # Should be less than 10 seconds
    
    @patch('src.ui.subject_filter.map_subject_to_filter')
    def test_stream_response_timestamp_set(self, mock_map_filter):
        """Test stream_response() sets timestamp on message."""
        # Setup mocks
        mock_map_filter.return_value = None
        
        mock_pipeline_manager = Mock(spec=PipelineManager)
        mock_pipeline_manager.process_query.return_value = iter(["Response"])
        
        before = datetime.now()
        result = stream_response("Test query", mock_pipeline_manager, "Semua")
        after = datetime.now()
        
        # Verify timestamp is within reasonable range
        assert result.timestamp >= before
        assert result.timestamp <= after
