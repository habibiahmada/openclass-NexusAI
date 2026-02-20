"""
Unit tests for status dashboard module.

Tests get_status_indicator(), format_memory_usage(), and render_status_dashboard()
with different pipeline states.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.ui.status_dashboard import get_status_indicator, format_memory_usage, render_status_dashboard
from src.ui.models import PipelineStatus


class TestGetStatusIndicator:
    """Test get_status_indicator() returns correct emojis."""
    
    def test_ready_status_returns_green_circle(self):
        """Test 'ready' status returns green circle emoji."""
        result = get_status_indicator('ready')
        assert result == '🟢'
    
    def test_loading_status_returns_yellow_circle(self):
        """Test 'loading' status returns yellow circle emoji."""
        result = get_status_indicator('loading')
        assert result == '🟡'
    
    def test_error_status_returns_red_circle(self):
        """Test 'error' status returns red circle emoji."""
        result = get_status_indicator('error')
        assert result == '🔴'
    
    def test_ready_uppercase_returns_green_circle(self):
        """Test 'READY' (uppercase) status returns green circle emoji."""
        result = get_status_indicator('READY')
        assert result == '🟢'
    
    def test_loading_mixed_case_returns_yellow_circle(self):
        """Test 'Loading' (mixed case) status returns yellow circle emoji."""
        result = get_status_indicator('Loading')
        assert result == '🟡'
    
    def test_error_uppercase_returns_red_circle(self):
        """Test 'ERROR' (uppercase) status returns red circle emoji."""
        result = get_status_indicator('ERROR')
        assert result == '🔴'
    
    def test_unknown_status_returns_white_circle(self):
        """Test unknown status returns white circle emoji as default."""
        result = get_status_indicator('unknown')
        assert result == '⚪'
    
    def test_empty_status_returns_white_circle(self):
        """Test empty status returns white circle emoji as default."""
        result = get_status_indicator('')
        assert result == '⚪'
    
    def test_invalid_status_returns_white_circle(self):
        """Test invalid status returns white circle emoji as default."""
        result = get_status_indicator('invalid_status')
        assert result == '⚪'


class TestFormatMemoryUsage:
    """Test format_memory_usage() shows warning at threshold."""
    
    def test_memory_below_threshold_no_warning(self):
        """Test memory usage below 2.5GB shows no warning."""
        result = format_memory_usage(2000.0)
        assert result == "2000 MB"
        assert "⚠️" not in result
        assert "Tinggi" not in result
    
    def test_memory_at_threshold_no_warning(self):
        """Test memory usage at exactly 2.5GB shows no warning."""
        result = format_memory_usage(2500.0)
        assert result == "2500 MB"
        assert "⚠️" not in result
        assert "Tinggi" not in result
    
    def test_memory_above_threshold_shows_warning(self):
        """Test memory usage above 2.5GB shows warning."""
        result = format_memory_usage(2501.0)
        assert result == "⚠️ 2501 MB (Tinggi)"
        assert "⚠️" in result
        assert "Tinggi" in result
    
    def test_memory_high_usage_shows_warning(self):
        """Test high memory usage (3GB) shows warning."""
        result = format_memory_usage(3000.0)
        assert result == "⚠️ 3000 MB (Tinggi)"
        assert "⚠️" in result
        assert "Tinggi" in result
    
    def test_memory_very_high_usage_shows_warning(self):
        """Test very high memory usage (3.5GB) shows warning."""
        result = format_memory_usage(3500.0)
        assert result == "⚠️ 3500 MB (Tinggi)"
        assert "⚠️" in result
        assert "Tinggi" in result
    
    def test_memory_low_usage_no_warning(self):
        """Test low memory usage (500MB) shows no warning."""
        result = format_memory_usage(500.0)
        assert result == "500 MB"
        assert "⚠️" not in result
        assert "Tinggi" not in result
    
    def test_memory_zero_usage_no_warning(self):
        """Test zero memory usage shows no warning."""
        result = format_memory_usage(0.0)
        assert result == "0 MB"
        assert "⚠️" not in result
        assert "Tinggi" not in result
    
    def test_memory_formatting_rounds_to_integer(self):
        """Test memory usage is formatted as integer (no decimals)."""
        result = format_memory_usage(2345.67)
        assert result == "2346 MB"
    
    def test_memory_formatting_with_decimals_below_threshold(self):
        """Test memory formatting with decimals below threshold."""
        result = format_memory_usage(1999.99)
        assert result == "2000 MB"
    
    def test_memory_formatting_with_decimals_above_threshold(self):
        """Test memory formatting with decimals above threshold."""
        result = format_memory_usage(2600.45)
        assert result == "⚠️ 2600 MB (Tinggi)"


class TestRenderStatusDashboard:
    """Test render_status_dashboard() with different pipeline states."""
    
    def test_render_with_database_loaded_and_model_ready(self):
        """Test rendering dashboard when database is loaded and model is ready."""
        # Create mock streamlit module
        mock_st = MagicMock()
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.status_dashboard
        importlib.reload(src.ui.status_dashboard)
        
        try:
            # Create mock pipeline manager
            mock_pipeline_manager = MagicMock()
            now = datetime.now()
            status = PipelineStatus(
                database_loaded=True,
                database_document_count=150,
                model_loaded=True,
                memory_usage_mb=2000.0,
                last_update=now
            )
            mock_pipeline_manager.get_status.return_value = status
            
            # Call render function
            src.ui.status_dashboard.render_status_dashboard(mock_pipeline_manager)
            
            # Verify sidebar header was called
            mock_st.sidebar.header.assert_called_once_with("Status Sistem")
            
            # Verify markdown calls for status indicators
            assert mock_st.sidebar.markdown.call_count >= 3  # DB, Model, Memory
            
            # Verify caption for last update
            mock_st.sidebar.caption.assert_called_once()
            
            # Verify divider was added
            mock_st.sidebar.divider.assert_called_once()
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.status_dashboard)
    
    def test_render_with_database_not_loaded(self):
        """Test rendering dashboard when database is not loaded."""
        # Create mock streamlit module
        mock_st = MagicMock()
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.status_dashboard
        importlib.reload(src.ui.status_dashboard)
        
        try:
            # Create mock pipeline manager
            mock_pipeline_manager = MagicMock()
            status = PipelineStatus(
                database_loaded=False,
                database_document_count=0,
                model_loaded=False,
                memory_usage_mb=500.0,
                last_update=datetime.now()
            )
            mock_pipeline_manager.get_status.return_value = status
            
            # Call render function
            src.ui.status_dashboard.render_status_dashboard(mock_pipeline_manager)
            
            # Verify sidebar header was called
            mock_st.sidebar.header.assert_called_once_with("Status Sistem")
            
            # Check that "Tidak Dimuat" (Not Loaded) message is displayed
            markdown_calls = [str(call) for call in mock_st.sidebar.markdown.call_args_list]
            assert any("Tidak Dimuat" in call for call in markdown_calls)
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.status_dashboard)
    
    def test_render_with_model_loading(self):
        """Test rendering dashboard when model is loading."""
        # Create mock streamlit module
        mock_st = MagicMock()
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.status_dashboard
        importlib.reload(src.ui.status_dashboard)
        
        try:
            # Create mock pipeline manager
            mock_pipeline_manager = MagicMock()
            status = PipelineStatus(
                database_loaded=True,
                database_document_count=100,
                model_loaded=False,
                memory_usage_mb=1500.0,
                last_update=datetime.now()
            )
            mock_pipeline_manager.get_status.return_value = status
            
            # Call render function
            src.ui.status_dashboard.render_status_dashboard(mock_pipeline_manager)
            
            # Check that "Memuat..." (Loading) message is displayed
            markdown_calls = [str(call) for call in mock_st.sidebar.markdown.call_args_list]
            assert any("Memuat" in call for call in markdown_calls)
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.status_dashboard)
    
    def test_render_with_model_error(self):
        """Test rendering dashboard when model has error."""
        # Create mock streamlit module
        mock_st = MagicMock()
        mock_expander = MagicMock()
        mock_st.sidebar.expander.return_value.__enter__ = MagicMock(return_value=mock_expander)
        mock_st.sidebar.expander.return_value.__exit__ = MagicMock(return_value=False)
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.status_dashboard
        importlib.reload(src.ui.status_dashboard)
        
        try:
            # Create mock pipeline manager
            mock_pipeline_manager = MagicMock()
            status = PipelineStatus(
                database_loaded=False,
                database_document_count=0,
                model_loaded=False,
                memory_usage_mb=500.0,
                last_update=datetime.now(),
                error_message="Model file not found"
            )
            mock_pipeline_manager.get_status.return_value = status
            
            # Call render function
            src.ui.status_dashboard.render_status_dashboard(mock_pipeline_manager)
            
            # Check that "Error" message is displayed
            markdown_calls = [str(call) for call in mock_st.sidebar.markdown.call_args_list]
            assert any("Error" in call for call in markdown_calls)
            
            # Verify expander was created for error details
            mock_st.sidebar.expander.assert_called_once_with("Detail Error")
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.status_dashboard)
    
    def test_render_with_high_memory_usage(self):
        """Test rendering dashboard with high memory usage (>2.5GB)."""
        # Create mock streamlit module
        mock_st = MagicMock()
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.status_dashboard
        importlib.reload(src.ui.status_dashboard)
        
        try:
            # Create mock pipeline manager
            mock_pipeline_manager = MagicMock()
            status = PipelineStatus(
                database_loaded=True,
                database_document_count=200,
                model_loaded=True,
                memory_usage_mb=3000.0,
                last_update=datetime.now()
            )
            mock_pipeline_manager.get_status.return_value = status
            
            # Call render function
            src.ui.status_dashboard.render_status_dashboard(mock_pipeline_manager)
            
            # Check that memory warning is displayed
            markdown_calls = [str(call) for call in mock_st.sidebar.markdown.call_args_list]
            assert any("⚠️" in call and "Tinggi" in call for call in markdown_calls)
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.status_dashboard)
    
    def test_render_displays_document_count(self):
        """Test rendering dashboard displays document count."""
        # Create mock streamlit module
        mock_st = MagicMock()
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.status_dashboard
        importlib.reload(src.ui.status_dashboard)
        
        try:
            # Create mock pipeline manager
            mock_pipeline_manager = MagicMock()
            status = PipelineStatus(
                database_loaded=True,
                database_document_count=250,
                model_loaded=True,
                memory_usage_mb=2000.0,
                last_update=datetime.now()
            )
            mock_pipeline_manager.get_status.return_value = status
            
            # Call render function
            src.ui.status_dashboard.render_status_dashboard(mock_pipeline_manager)
            
            # Check that document count is displayed
            markdown_calls = [str(call) for call in mock_st.sidebar.markdown.call_args_list]
            # The get_database_status_text() should include document count
            assert any("250" in call for call in markdown_calls)
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.status_dashboard)
    
    def test_render_displays_timestamp(self):
        """Test rendering dashboard displays last update timestamp."""
        # Create mock streamlit module
        mock_st = MagicMock()
        sys.modules['streamlit'] = mock_st
        
        # Reload the module to pick up the mocked streamlit
        import importlib
        import src.ui.status_dashboard
        importlib.reload(src.ui.status_dashboard)
        
        try:
            # Create mock pipeline manager
            mock_pipeline_manager = MagicMock()
            now = datetime(2024, 1, 15, 14, 30, 45)
            status = PipelineStatus(
                database_loaded=True,
                database_document_count=100,
                model_loaded=True,
                memory_usage_mb=2000.0,
                last_update=now
            )
            mock_pipeline_manager.get_status.return_value = status
            
            # Call render function
            src.ui.status_dashboard.render_status_dashboard(mock_pipeline_manager)
            
            # Verify caption was called with timestamp
            mock_st.sidebar.caption.assert_called_once()
            caption_call = str(mock_st.sidebar.caption.call_args)
            assert "14:30:45" in caption_call
        finally:
            # Clean up
            if 'streamlit' in sys.modules:
                del sys.modules['streamlit']
            importlib.reload(src.ui.status_dashboard)
    
    @patch('src.ui.status_dashboard.STREAMLIT_AVAILABLE', False)
    @patch('src.ui.status_dashboard.logger')
    def test_render_without_streamlit_logs_warning(self, mock_logger):
        """Test rendering dashboard without Streamlit logs warning."""
        from src.ui.status_dashboard import render_status_dashboard
        
        # Create mock pipeline manager
        mock_pipeline_manager = MagicMock()
        status = PipelineStatus(
            database_loaded=True,
            database_document_count=100,
            model_loaded=True,
            memory_usage_mb=2000.0,
            last_update=datetime.now()
        )
        mock_pipeline_manager.get_status.return_value = status
        
        # Call render function
        render_status_dashboard(mock_pipeline_manager)
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        warning_call = str(mock_logger.warning.call_args)
        assert "Streamlit not available" in warning_call
