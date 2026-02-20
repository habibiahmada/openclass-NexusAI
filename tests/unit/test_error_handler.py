"""
Unit tests for error handler module.

Tests error message constants, get_error_message() function, and display_error() function.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from src.ui.error_handler import ErrorMessages, get_error_message, display_error


class TestErrorMessages:
    """Test error message constants."""
    
    def test_empty_database_message(self):
        """Test EMPTY_DATABASE constant contains correct Indonesian text."""
        assert ErrorMessages.EMPTY_DATABASE == "Database kosong. Silakan jalankan pipeline ETL terlebih dahulu."
    
    def test_model_load_failed_message(self):
        """Test MODEL_LOAD_FAILED constant contains correct Indonesian text with placeholder."""
        assert ErrorMessages.MODEL_LOAD_FAILED == "Model gagal dimuat. Periksa file model di {path}."
    
    def test_query_failed_message(self):
        """Test QUERY_FAILED constant contains correct Indonesian text."""
        assert ErrorMessages.QUERY_FAILED == "Terjadi kesalahan. Silakan coba lagi."
    
    def test_insufficient_memory_message(self):
        """Test INSUFFICIENT_MEMORY constant contains correct Indonesian text."""
        assert ErrorMessages.INSUFFICIENT_MEMORY == "Memori tidak cukup. Tutup aplikasi lain dan coba lagi."
    
    def test_pipeline_init_failed_message(self):
        """Test PIPELINE_INIT_FAILED constant contains correct Indonesian text with placeholder."""
        assert ErrorMessages.PIPELINE_INIT_FAILED == "Gagal menginisialisasi sistem: {error}"


class TestGetErrorMessage:
    """Test get_error_message() function with different error types."""
    
    def test_empty_database_error_type(self):
        """Test get_error_message() with 'empty_database' error type."""
        result = get_error_message('empty_database')
        assert result == "Database kosong. Silakan jalankan pipeline ETL terlebih dahulu."
    
    def test_model_load_failed_with_path(self):
        """Test get_error_message() with 'model_load_failed' and path parameter."""
        result = get_error_message('model_load_failed', path='/path/to/model.gguf')
        assert result == "Model gagal dimuat. Periksa file model di /path/to/model.gguf."
    
    def test_model_load_failed_without_path(self):
        """Test get_error_message() with 'model_load_failed' but missing path parameter."""
        result = get_error_message('model_load_failed')
        # Should return template with placeholder when parameter is missing
        assert result == "Model gagal dimuat. Periksa file model di {path}."
    
    def test_query_failed_error_type(self):
        """Test get_error_message() with 'query_failed' error type."""
        result = get_error_message('query_failed')
        assert result == "Terjadi kesalahan. Silakan coba lagi."
    
    def test_insufficient_memory_error_type(self):
        """Test get_error_message() with 'insufficient_memory' error type."""
        result = get_error_message('insufficient_memory')
        assert result == "Memori tidak cukup. Tutup aplikasi lain dan coba lagi."
    
    def test_pipeline_init_failed_with_error(self):
        """Test get_error_message() with 'pipeline_init_failed' and error parameter."""
        result = get_error_message('pipeline_init_failed', error='Connection timeout')
        assert result == "Gagal menginisialisasi sistem: Connection timeout"
    
    def test_pipeline_init_failed_without_error(self):
        """Test get_error_message() with 'pipeline_init_failed' but missing error parameter."""
        result = get_error_message('pipeline_init_failed')
        # Should return template with placeholder when parameter is missing
        assert result == "Gagal menginisialisasi sistem: {error}"
    
    def test_unknown_error_type_returns_default(self):
        """Test get_error_message() with unknown error type returns default message."""
        result = get_error_message('unknown_error_type')
        assert result == "Terjadi kesalahan. Silakan coba lagi."
    
    def test_multiple_format_parameters(self):
        """Test get_error_message() handles multiple format parameters correctly."""
        # Using model_load_failed with path parameter
        result = get_error_message('model_load_failed', path='/models/llama.gguf', extra='ignored')
        assert result == "Model gagal dimuat. Periksa file model di /models/llama.gguf."


class TestDisplayError:
    """Test display_error() output format."""
    
    def test_display_error_calls_streamlit_error(self):
        """Test display_error() calls st.error() when Streamlit is available."""
        # Create a mock streamlit module
        mock_st = MagicMock()
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.error_handler
        importlib.reload(src.ui.error_handler)
        
        try:
            error_message = "Test error message"
            src.ui.error_handler.display_error(error_message)
            
            mock_st.error.assert_called_once_with(error_message)
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.error_handler)
    
    def test_display_error_without_details(self):
        """Test display_error() without show_details flag."""
        # Create a mock streamlit module
        mock_st = MagicMock()
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.error_handler
        importlib.reload(src.ui.error_handler)
        
        try:
            error_message = "Test error"
            src.ui.error_handler.display_error(error_message, show_details=False)
            
            mock_st.error.assert_called_once_with(error_message)
            mock_st.expander.assert_not_called()
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.error_handler)
    
    def test_display_error_with_details(self):
        """Test display_error() with show_details=True shows expander."""
        # Create a mock streamlit module
        mock_st = MagicMock()
        mock_expander = MagicMock()
        mock_st.expander.return_value.__enter__ = MagicMock(return_value=mock_expander)
        mock_st.expander.return_value.__exit__ = MagicMock(return_value=False)
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.error_handler
        importlib.reload(src.ui.error_handler)
        
        try:
            error_message = "Detailed error message"
            src.ui.error_handler.display_error(error_message, show_details=True)
            
            mock_st.error.assert_called_once_with(error_message)
            mock_st.expander.assert_called_once_with("Detail Kesalahan")
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.error_handler)
    
    @patch('src.ui.error_handler.STREAMLIT_AVAILABLE', False)
    @patch('src.ui.error_handler.logger')
    def test_display_error_without_streamlit_logs_error(self, mock_logger):
        """Test display_error() logs error when Streamlit is not available."""
        error_message = "Error without Streamlit"
        display_error(error_message)
        
        mock_logger.error.assert_called()
    
    def test_display_error_logs_to_console(self):
        """Test display_error() logs error details to console for debugging."""
        # Create a mock streamlit module
        mock_st = MagicMock()
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.error_handler
        importlib.reload(src.ui.error_handler)
        
        try:
            with patch('src.ui.error_handler.logger') as mock_logger:
                error_message = "Test error for logging"
                src.ui.error_handler.display_error(error_message)
                
                # Should log the error
                mock_logger.error.assert_called()
                call_args = str(mock_logger.error.call_args)
                assert "Test error for logging" in call_args
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.error_handler)
    
    def test_display_error_with_indonesian_message(self):
        """Test display_error() correctly displays Indonesian error messages."""
        # Create a mock streamlit module
        mock_st = MagicMock()
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.error_handler
        importlib.reload(src.ui.error_handler)
        
        try:
            indonesian_message = "Database kosong. Silakan jalankan pipeline ETL terlebih dahulu."
            src.ui.error_handler.display_error(indonesian_message)
            
            mock_st.error.assert_called_once_with(indonesian_message)
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.error_handler)
