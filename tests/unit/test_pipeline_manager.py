"""
Unit tests for pipeline manager module.

Tests initialize_pipeline() success and failure cases, get_status() with different
pipeline states, and process_query() error handling.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.ui.pipeline_manager import PipelineManager
from src.ui.models import PipelineStatus


class TestPipelineManagerInitialization:
    """Test PipelineManager initialization."""
    
    def test_init_creates_none_pipeline(self):
        """Test __init__() creates pipeline as None."""
        manager = PipelineManager()
        assert manager.pipeline is None
    
    def test_init_creates_none_error(self):
        """Test __init__() creates initialization_error as None."""
        manager = PipelineManager()
        assert manager.initialization_error is None


class TestInitializePipeline:
    """Test initialize_pipeline() success and failure cases."""
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_initialize_pipeline_success(self, mock_pipeline_class):
        """Test initialize_pipeline() returns True on success."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        result = manager.initialize_pipeline()
        
        assert result is True
        assert manager.pipeline is not None
        assert manager.initialization_error is None
        mock_pipeline.initialize.assert_called_once()
        mock_pipeline.start.assert_called_once()
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_initialize_pipeline_already_initialized(self, mock_pipeline_class):
        """Test initialize_pipeline() returns True if already initialized."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        # Call again
        result = manager.initialize_pipeline()
        
        assert result is True
        # Should only be called once from first initialization
        assert mock_pipeline.initialize.call_count == 1
        assert mock_pipeline.start.call_count == 1
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_initialize_pipeline_initialize_fails(self, mock_pipeline_class):
        """Test initialize_pipeline() returns False when pipeline.initialize() fails."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = False
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        result = manager.initialize_pipeline()
        
        assert result is False
        assert manager.initialization_error == "Pipeline initialization failed"
        mock_pipeline.initialize.assert_called_once()
        mock_pipeline.start.assert_not_called()
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_initialize_pipeline_start_fails(self, mock_pipeline_class):
        """Test initialize_pipeline() returns False when pipeline.start() fails."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = False
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        result = manager.initialize_pipeline()
        
        assert result is False
        assert manager.initialization_error == "Pipeline start failed"
        mock_pipeline.initialize.assert_called_once()
        mock_pipeline.start.assert_called_once()
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    @patch('src.ui.error_handler.get_error_message')
    def test_initialize_pipeline_file_not_found_error(self, mock_get_error, mock_pipeline_class):
        """Test initialize_pipeline() handles FileNotFoundError with model path."""
        # Setup mocks
        mock_get_error.return_value = "Model gagal dimuat. Periksa file model di /path/to/model.gguf."
        mock_pipeline_class.side_effect = FileNotFoundError("Model file not found: /path/to/model.gguf")
        
        manager = PipelineManager()
        result = manager.initialize_pipeline()
        
        assert result is False
        assert "Model gagal dimuat" in manager.initialization_error
        mock_get_error.assert_called_once_with('model_load_failed', path='/path/to/model.gguf')
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    @patch('src.ui.error_handler.get_error_message')
    def test_initialize_pipeline_file_not_found_without_model_prefix(self, mock_get_error, mock_pipeline_class):
        """Test initialize_pipeline() handles FileNotFoundError without 'Model file not found:' prefix."""
        # Setup mocks
        mock_get_error.return_value = "Model gagal dimuat. Periksa file model di some_file.txt."
        mock_pipeline_class.side_effect = FileNotFoundError("some_file.txt")
        
        manager = PipelineManager()
        result = manager.initialize_pipeline()
        
        assert result is False
        mock_get_error.assert_called_once_with('model_load_failed', path='some_file.txt')
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    @patch('src.ui.error_handler.get_error_message')
    def test_initialize_pipeline_generic_exception(self, mock_get_error, mock_pipeline_class):
        """Test initialize_pipeline() handles generic exceptions."""
        # Setup mocks
        mock_get_error.return_value = "Gagal menginisialisasi sistem: Connection timeout"
        mock_pipeline_class.side_effect = Exception("Connection timeout")
        
        manager = PipelineManager()
        result = manager.initialize_pipeline()
        
        assert result is False
        assert "Gagal menginisialisasi sistem" in manager.initialization_error
        mock_get_error.assert_called_once_with('pipeline_init_failed', error='Connection timeout')


class TestGetPipeline:
    """Test get_pipeline() method."""
    
    def test_get_pipeline_returns_none_when_not_initialized(self):
        """Test get_pipeline() returns None when pipeline not initialized."""
        manager = PipelineManager()
        result = manager.get_pipeline()
        assert result is None
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_get_pipeline_returns_pipeline_when_initialized(self, mock_pipeline_class):
        """Test get_pipeline() returns pipeline instance when initialized."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        result = manager.get_pipeline()
        assert result is mock_pipeline


class TestGetStatus:
    """Test get_status() with different pipeline states."""
    
    def test_get_status_when_pipeline_not_initialized(self):
        """Test get_status() returns correct status when pipeline is None."""
        manager = PipelineManager()
        status = manager.get_status()
        
        assert isinstance(status, PipelineStatus)
        assert status.database_loaded is False
        assert status.database_document_count == 0
        assert status.model_loaded is False
        assert status.memory_usage_mb == 0.0
        assert status.error_message is None
        assert isinstance(status.last_update, datetime)
    
    def test_get_status_with_initialization_error(self):
        """Test get_status() includes initialization error when present."""
        manager = PipelineManager()
        manager.initialization_error = "Test error message"
        
        status = manager.get_status()
        
        assert status.error_message == "Test error message"
        assert status.database_loaded is False
        assert status.model_loaded is False
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_get_status_when_pipeline_initialized(self, mock_pipeline_class):
        """Test get_status() returns correct status when pipeline is initialized."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_pipeline.get_pipeline_status.return_value = {
            'components': {
                'vector_db': True,
                'inference_engine': True
            },
            'memory': {
                'usage_mb': 1500.0
            }
        }
        mock_pipeline.vector_db = Mock()
        mock_pipeline.vector_db.count_documents.return_value = 100
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        status = manager.get_status()
        
        assert status.database_loaded is True
        assert status.database_document_count == 100
        assert status.model_loaded is True
        assert status.memory_usage_mb == 1500.0
        assert status.error_message is None
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    @patch('src.ui.error_handler.get_error_message')
    def test_get_status_with_empty_database(self, mock_get_error, mock_pipeline_class):
        """Test get_status() detects empty database and sets error message."""
        # Setup mocks
        mock_get_error.return_value = "Database kosong. Silakan jalankan pipeline ETL terlebih dahulu."
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_pipeline.get_pipeline_status.return_value = {
            'components': {
                'vector_db': True,
                'inference_engine': True
            },
            'memory': {
                'usage_mb': 1000.0
            }
        }
        mock_pipeline.vector_db = Mock()
        mock_pipeline.vector_db.count_documents.return_value = 0
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        status = manager.get_status()
        
        assert status.database_loaded is True
        assert status.database_document_count == 0
        assert "Database kosong" in status.error_message
        mock_get_error.assert_called_once_with('empty_database')
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_get_status_handles_missing_components(self, mock_pipeline_class):
        """Test get_status() handles missing components in status dict."""
        # Setup mock with incomplete status
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_pipeline.get_pipeline_status.return_value = {
            'components': {},
            'memory': {}
        }
        mock_pipeline.vector_db = None
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        status = manager.get_status()
        
        assert status.database_loaded is False
        assert status.model_loaded is False
        assert status.memory_usage_mb == 0.0
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_get_status_handles_document_count_error(self, mock_pipeline_class):
        """Test get_status() handles error when getting document count."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_pipeline.get_pipeline_status.return_value = {
            'components': {
                'vector_db': True,
                'inference_engine': True
            },
            'memory': {
                'usage_mb': 1200.0
            }
        }
        mock_pipeline.vector_db = Mock()
        mock_pipeline.vector_db.count_documents.side_effect = Exception("Database error")
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        status = manager.get_status()
        
        # Should default to 0 when count fails
        assert status.database_document_count == 0
        assert status.database_loaded is True
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_get_status_handles_exception_in_get_pipeline_status(self, mock_pipeline_class):
        """Test get_status() handles exception when calling get_pipeline_status()."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_pipeline.get_pipeline_status.side_effect = Exception("Status error")
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        status = manager.get_status()
        
        assert status.database_loaded is False
        assert status.model_loaded is False
        assert status.error_message == "Status error"


class TestProcessQuery:
    """Test process_query() error handling."""
    
    def test_process_query_raises_error_when_not_initialized(self):
        """Test process_query() raises RuntimeError when pipeline not initialized."""
        manager = PipelineManager()
        
        with pytest.raises(RuntimeError, match="Pipeline not initialized"):
            list(manager.process_query("test query", None))
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_process_query_success(self, mock_pipeline_class):
        """Test process_query() yields response on success."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_result = Mock()
        mock_result.response = "Test response"
        mock_pipeline.process_query.return_value = mock_result
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        result = list(manager.process_query("test query", None))
        
        assert result == ["Test response"]
        mock_pipeline.process_query.assert_called_once_with(
            query="test query",
            subject_filter=None,
            use_batch_processing=False
        )
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_process_query_with_subject_filter(self, mock_pipeline_class):
        """Test process_query() passes subject filter to pipeline."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_result = Mock()
        mock_result.response = "Filtered response"
        mock_pipeline.process_query.return_value = mock_result
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        result = list(manager.process_query("test query", "matematika"))
        
        assert result == ["Filtered response"]
        mock_pipeline.process_query.assert_called_once_with(
            query="test query",
            subject_filter="matematika",
            use_batch_processing=False
        )
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    @patch('src.ui.error_handler.get_error_message')
    def test_process_query_handles_memory_error(self, mock_get_error, mock_pipeline_class):
        """Test process_query() handles MemoryError and yields error message."""
        # Setup mocks
        mock_get_error.return_value = "Memori tidak cukup. Tutup aplikasi lain dan coba lagi."
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_pipeline.process_query.side_effect = MemoryError("Out of memory")
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        result = list(manager.process_query("test query", None))
        
        assert len(result) == 1
        assert "Memori tidak cukup" in result[0]
        mock_get_error.assert_called_once_with('insufficient_memory')
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    @patch('src.ui.error_handler.get_error_message')
    def test_process_query_handles_generic_exception(self, mock_get_error, mock_pipeline_class):
        """Test process_query() handles generic exceptions and yields error message."""
        # Setup mocks
        mock_get_error.return_value = "Terjadi kesalahan. Silakan coba lagi."
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_pipeline.process_query.side_effect = Exception("Query processing failed")
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        result = list(manager.process_query("test query", None))
        
        assert len(result) == 1
        assert "Terjadi kesalahan" in result[0]
        mock_get_error.assert_called_once_with('query_failed')
    
    @patch('src.ui.pipeline_manager.CompletePipeline')
    def test_process_query_yields_complete_response(self, mock_pipeline_class):
        """Test process_query() yields complete response as single chunk."""
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.initialize.return_value = True
        mock_pipeline.start.return_value = True
        mock_result = Mock()
        mock_result.response = "This is a complete response with multiple words"
        mock_pipeline.process_query.return_value = mock_result
        mock_pipeline_class.return_value = mock_pipeline
        
        manager = PipelineManager()
        manager.initialize_pipeline()
        
        result = list(manager.process_query("test query", None))
        
        # Should yield complete response as single chunk
        assert len(result) == 1
        assert result[0] == "This is a complete response with multiple words"
