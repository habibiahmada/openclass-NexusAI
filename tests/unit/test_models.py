"""
Unit tests for Phase 4 Local Application data models.

Tests ChatMessage, SourceCitation, and PipelineStatus dataclasses.
"""

import pytest
from datetime import datetime
from src.ui.models import ChatMessage, SourceCitation, PipelineStatus


class TestSourceCitation:
    """Tests for SourceCitation dataclass."""
    
    def test_source_citation_creation(self):
        """Test creating a SourceCitation with all fields."""
        citation = SourceCitation(
            filename="matematika_kelas_7.pdf",
            subject="Matematika",
            relevance_score=0.85,
            chunk_index=5
        )
        
        assert citation.filename == "matematika_kelas_7.pdf"
        assert citation.subject == "Matematika"
        assert citation.relevance_score == 0.85
        assert citation.chunk_index == 5
    
    def test_format_citation_standard(self):
        """Test format_citation() with standard values."""
        citation = SourceCitation(
            filename="ipa_kelas_8.pdf",
            subject="IPA",
            relevance_score=0.92,
            chunk_index=3
        )
        
        result = citation.format_citation()
        expected = "📚 IPA - ipa_kelas_8.pdf (Relevance: 0.92)"
        assert result == expected
    
    def test_format_citation_low_score(self):
        """Test format_citation() with low relevance score."""
        citation = SourceCitation(
            filename="bahasa_indonesia.pdf",
            subject="Bahasa Indonesia",
            relevance_score=0.15,
            chunk_index=0
        )
        
        result = citation.format_citation()
        expected = "📚 Bahasa Indonesia - bahasa_indonesia.pdf (Relevance: 0.15)"
        assert result == expected
    
    def test_format_citation_perfect_score(self):
        """Test format_citation() with perfect relevance score."""
        citation = SourceCitation(
            filename="informatika.pdf",
            subject="Informatika",
            relevance_score=1.0,
            chunk_index=10
        )
        
        result = citation.format_citation()
        expected = "📚 Informatika - informatika.pdf (Relevance: 1.00)"
        assert result == expected
    
    def test_format_citation_zero_score(self):
        """Test format_citation() with zero relevance score."""
        citation = SourceCitation(
            filename="test.pdf",
            subject="Test",
            relevance_score=0.0,
            chunk_index=0
        )
        
        result = citation.format_citation()
        expected = "📚 Test - test.pdf (Relevance: 0.00)"
        assert result == expected
    
    def test_format_citation_rounding(self):
        """Test format_citation() rounds to 2 decimal places."""
        citation = SourceCitation(
            filename="test.pdf",
            subject="Test",
            relevance_score=0.876543,
            chunk_index=0
        )
        
        result = citation.format_citation()
        expected = "📚 Test - test.pdf (Relevance: 0.88)"
        assert result == expected


class TestChatMessage:
    """Tests for ChatMessage dataclass."""
    
    def test_chat_message_user_creation(self):
        """Test creating a user ChatMessage."""
        message = ChatMessage(
            role="user",
            content="Apa itu fotosintesis?"
        )
        
        assert message.role == "user"
        assert message.content == "Apa itu fotosintesis?"
        assert message.sources == []
        assert isinstance(message.timestamp, datetime)
        assert message.processing_time_ms is None
    
    def test_chat_message_assistant_creation(self):
        """Test creating an assistant ChatMessage."""
        message = ChatMessage(
            role="assistant",
            content="Fotosintesis adalah proses..."
        )
        
        assert message.role == "assistant"
        assert message.content == "Fotosintesis adalah proses..."
        assert message.sources == []
        assert isinstance(message.timestamp, datetime)
        assert message.processing_time_ms is None
    
    def test_chat_message_with_sources(self):
        """Test creating a ChatMessage with source citations."""
        sources = [
            SourceCitation(
                filename="ipa_kelas_7.pdf",
                subject="IPA",
                relevance_score=0.9,
                chunk_index=2
            ),
            SourceCitation(
                filename="ipa_kelas_8.pdf",
                subject="IPA",
                relevance_score=0.85,
                chunk_index=5
            )
        ]
        
        message = ChatMessage(
            role="assistant",
            content="Fotosintesis adalah proses...",
            sources=sources
        )
        
        assert message.role == "assistant"
        assert len(message.sources) == 2
        assert message.sources[0].filename == "ipa_kelas_7.pdf"
        assert message.sources[1].filename == "ipa_kelas_8.pdf"
    
    def test_chat_message_with_processing_time(self):
        """Test creating a ChatMessage with processing time."""
        message = ChatMessage(
            role="assistant",
            content="Response text",
            processing_time_ms=1234.56
        )
        
        assert message.processing_time_ms == 1234.56
    
    def test_chat_message_with_custom_timestamp(self):
        """Test creating a ChatMessage with custom timestamp."""
        custom_time = datetime(2024, 1, 15, 10, 30, 0)
        message = ChatMessage(
            role="user",
            content="Test question",
            timestamp=custom_time
        )
        
        assert message.timestamp == custom_time
    
    def test_chat_message_empty_content(self):
        """Test creating a ChatMessage with empty content."""
        message = ChatMessage(
            role="user",
            content=""
        )
        
        assert message.content == ""
        assert message.role == "user"
    
    def test_chat_message_default_factory_sources(self):
        """Test that default sources list is independent for each instance."""
        message1 = ChatMessage(role="user", content="Question 1")
        message2 = ChatMessage(role="user", content="Question 2")
        
        # Add source to message1
        message1.sources.append(
            SourceCitation(
                filename="test.pdf",
                subject="Test",
                relevance_score=0.5,
                chunk_index=0
            )
        )
        
        # message2 should still have empty sources
        assert len(message1.sources) == 1
        assert len(message2.sources) == 0


class TestPipelineStatus:
    """Tests for PipelineStatus dataclass."""
    
    def test_pipeline_status_creation(self):
        """Test creating a PipelineStatus with all fields."""
        now = datetime.now()
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=150,
            model_loaded=True,
            memory_usage_mb=2000.0,
            last_update=now
        )
        
        assert status.database_loaded is True
        assert status.database_document_count == 150
        assert status.model_loaded is True
        assert status.memory_usage_mb == 2000.0
        assert status.last_update == now
        assert status.error_message is None
    
    def test_pipeline_status_with_error(self):
        """Test creating a PipelineStatus with error message."""
        status = PipelineStatus(
            database_loaded=False,
            database_document_count=0,
            model_loaded=False,
            memory_usage_mb=500.0,
            last_update=datetime.now(),
            error_message="Model file not found"
        )
        
        assert status.error_message == "Model file not found"
    
    def test_get_database_status_text_loaded(self):
        """Test get_database_status_text() when database is loaded."""
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=250,
            model_loaded=True,
            memory_usage_mb=2000.0,
            last_update=datetime.now()
        )
        
        result = status.get_database_status_text()
        assert result == "Database: Loaded (250 documents)"
    
    def test_get_database_status_text_not_loaded(self):
        """Test get_database_status_text() when database is not loaded."""
        status = PipelineStatus(
            database_loaded=False,
            database_document_count=0,
            model_loaded=False,
            memory_usage_mb=500.0,
            last_update=datetime.now()
        )
        
        result = status.get_database_status_text()
        assert result == "Database: Not Loaded"
    
    def test_get_database_status_text_zero_documents(self):
        """Test get_database_status_text() with zero documents."""
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=0,
            model_loaded=True,
            memory_usage_mb=1000.0,
            last_update=datetime.now()
        )
        
        result = status.get_database_status_text()
        assert result == "Database: Loaded (0 documents)"
    
    def test_get_model_status_text_ready(self):
        """Test get_model_status_text() when model is ready."""
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=100,
            model_loaded=True,
            memory_usage_mb=2000.0,
            last_update=datetime.now()
        )
        
        result = status.get_model_status_text()
        assert result == "Model: Ready"
    
    def test_get_model_status_text_loading(self):
        """Test get_model_status_text() when model is loading."""
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=100,
            model_loaded=False,
            memory_usage_mb=1000.0,
            last_update=datetime.now()
        )
        
        result = status.get_model_status_text()
        assert result == "Model: Loading"
    
    def test_get_model_status_text_error(self):
        """Test get_model_status_text() when there's an error."""
        status = PipelineStatus(
            database_loaded=False,
            database_document_count=0,
            model_loaded=False,
            memory_usage_mb=500.0,
            last_update=datetime.now(),
            error_message="Failed to load model"
        )
        
        result = status.get_model_status_text()
        assert result == "Model: Error"
    
    def test_get_model_status_text_error_priority(self):
        """Test get_model_status_text() prioritizes error over loaded state."""
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=100,
            model_loaded=True,
            memory_usage_mb=2000.0,
            last_update=datetime.now(),
            error_message="Some error occurred"
        )
        
        result = status.get_model_status_text()
        assert result == "Model: Error"
    
    def test_has_memory_warning_below_threshold(self):
        """Test has_memory_warning() returns False below 2.5GB."""
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=100,
            model_loaded=True,
            memory_usage_mb=2000.0,
            last_update=datetime.now()
        )
        
        assert status.has_memory_warning() is False
    
    def test_has_memory_warning_at_threshold(self):
        """Test has_memory_warning() returns False at exactly 2.5GB."""
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=100,
            model_loaded=True,
            memory_usage_mb=2500.0,
            last_update=datetime.now()
        )
        
        assert status.has_memory_warning() is False
    
    def test_has_memory_warning_above_threshold(self):
        """Test has_memory_warning() returns True above 2.5GB."""
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=100,
            model_loaded=True,
            memory_usage_mb=2501.0,
            last_update=datetime.now()
        )
        
        assert status.has_memory_warning() is True
    
    def test_has_memory_warning_high_usage(self):
        """Test has_memory_warning() returns True with high memory usage."""
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=100,
            model_loaded=True,
            memory_usage_mb=3500.0,
            last_update=datetime.now()
        )
        
        assert status.has_memory_warning() is True
    
    def test_has_memory_warning_zero_usage(self):
        """Test has_memory_warning() returns False with zero memory usage."""
        status = PipelineStatus(
            database_loaded=False,
            database_document_count=0,
            model_loaded=False,
            memory_usage_mb=0.0,
            last_update=datetime.now()
        )
        
        assert status.has_memory_warning() is False
