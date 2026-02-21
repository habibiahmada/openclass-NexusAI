"""
Unit tests for API graceful degradation when database is unavailable

Tests that the API returns HTTP 503 with user-friendly messages when PostgreSQL
connection fails, and logs errors with stack traces.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import psycopg2

# Import the app
from api_server import app, state


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db_unavailable():
    """Mock database as unavailable."""
    state.db_initialized = False
    state.db_manager = None
    state.session_repo = None
    state.chat_history_repo = None
    state.user_repo = None
    yield
    # Reset state after test
    state.db_initialized = False


@pytest.fixture
def mock_db_available():
    """Mock database as available with mock repositories."""
    state.db_initialized = True
    state.db_manager = Mock()
    state.session_repo = Mock()
    state.chat_history_repo = Mock()
    state.user_repo = Mock()
    yield
    # Reset state after test
    state.db_initialized = False


class TestLoginGracefulDegradation:
    """Test login endpoint graceful degradation."""
    
    def test_login_database_unavailable(self, client, mock_db_unavailable):
        """Test login returns 503 when database is unavailable."""
        response = client.post("/api/auth/login", json={
            "username": "siswa",
            "password": "siswa123",
            "role": "siswa"
        })
        
        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]
    
    def test_login_database_connection_failure(self, client, mock_db_available):
        """Test login returns 503 when database connection fails during operation."""
        # Mock database operation to raise connection error
        state.user_repo.get_user_by_username.side_effect = psycopg2.OperationalError(
            "connection failed"
        )
        
        response = client.post("/api/auth/login", json={
            "username": "siswa",
            "password": "siswa123",
            "role": "siswa"
        })
        
        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]


class TestTokenVerificationGracefulDegradation:
    """Test token verification graceful degradation."""
    
    def test_verify_token_database_unavailable(self, client, mock_db_unavailable):
        """Test token verification returns 503 when database is unavailable."""
        response = client.post(
            "/api/auth/verify",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]
    
    def test_verify_token_database_connection_failure(self, client, mock_db_available):
        """Test token verification returns 503 when database connection fails."""
        state.session_repo.get_session_by_token.side_effect = psycopg2.OperationalError(
            "connection lost"
        )
        
        response = client.post(
            "/api/auth/verify",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]


class TestLogoutGracefulDegradation:
    """Test logout endpoint graceful degradation."""
    
    def test_logout_database_unavailable(self, client, mock_db_unavailable):
        """Test logout returns 503 when database is unavailable."""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]
    
    def test_logout_database_connection_failure(self, client, mock_db_available):
        """Test logout returns 503 when database connection fails."""
        # Mock successful token verification
        state.session_repo.get_session_by_token.return_value = Mock(user_id=1)
        state.user_repo.get_user_by_id.return_value = Mock(
            id=1, username="siswa", role="siswa", full_name="Test"
        )
        
        # Mock logout operation to fail
        state.session_repo.delete_user_sessions.side_effect = psycopg2.OperationalError(
            "connection failed"
        )
        
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]


class TestTeacherStatsGracefulDegradation:
    """Test teacher stats endpoint graceful degradation."""
    
    def test_teacher_stats_database_unavailable(self, client, mock_db_unavailable):
        """Test teacher stats returns 503 when database is unavailable."""
        response = client.get(
            "/api/teacher/stats",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]
    
    def test_teacher_stats_database_connection_failure(self, client, mock_db_available):
        """Test teacher stats returns 503 when database connection fails."""
        # Mock successful token verification
        state.session_repo.get_session_by_token.return_value = Mock(user_id=1)
        state.user_repo.get_user_by_id.return_value = Mock(
            id=1, username="guru", role="guru", full_name="Test Teacher"
        )
        
        # Mock stats operation to fail
        state.chat_history_repo.get_recent_chats.side_effect = psycopg2.OperationalError(
            "connection timeout"
        )
        
        response = client.get(
            "/api/teacher/stats",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]


class TestExportReportGracefulDegradation:
    """Test export report endpoint graceful degradation."""
    
    def test_export_report_database_unavailable(self, client, mock_db_unavailable):
        """Test export report returns 503 when database is unavailable."""
        response = client.get(
            "/api/teacher/export?format=csv",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]
    
    def test_export_report_database_connection_failure(self, client, mock_db_available):
        """Test export report returns 503 when database connection fails."""
        # Mock successful token verification
        state.session_repo.get_session_by_token.return_value = Mock(user_id=1)
        state.user_repo.get_user_by_id.return_value = Mock(
            id=1, username="guru", role="guru", full_name="Test Teacher"
        )
        
        # Mock export operation to fail
        state.chat_history_repo.get_recent_chats.side_effect = psycopg2.OperationalError(
            "connection failed"
        )
        
        response = client.get(
            "/api/teacher/export?format=csv",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]


class TestChatEndpointDegradation:
    """Test chat endpoint continues to work even if database save fails."""
    
    @patch('api_server.state')
    def test_chat_continues_when_database_save_fails(self, mock_state, client):
        """Test chat endpoint continues even if database save fails."""
        # Mock RAG pipeline as initialized
        mock_state.is_initialized = True
        mock_state.db_initialized = True
        
        # Mock successful token verification
        mock_state.session_repo.get_session_by_token.return_value = Mock(user_id=1)
        mock_state.user_repo.get_user_by_id.return_value = Mock(
            id=1, username="siswa", role="siswa", full_name="Test Student"
        )
        
        # Mock pipeline to return result
        mock_result = Mock()
        mock_result.response = "Test response"
        mock_result.confidence = 0.9
        mock_result.sources = []
        mock_state.pipeline.process_query.return_value = mock_result
        
        # Mock database save to fail
        mock_state.chat_history_repo.save_chat.side_effect = psycopg2.OperationalError(
            "connection failed"
        )
        
        response = client.post(
            "/api/chat",
            json={"message": "Test question", "subject_filter": "all"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Should still return 200 with response, not 503
        assert response.status_code == 200
        assert response.json()["response"] == "Test response"


class TestHealthCheckWithDatabaseStatus:
    """Test health check endpoint reports database status."""
    
    def test_health_check_database_available(self, client, mock_db_available):
        """Test health check shows database as available."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json()["database"] is True
    
    def test_health_check_database_unavailable(self, client, mock_db_unavailable):
        """Test health check shows database as unavailable."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json()["database"] is False


class TestErrorLogging:
    """Test that errors are logged with stack traces."""
    
    @patch('api_server.logger')
    def test_database_error_logged_with_stack_trace(self, mock_logger, client, mock_db_available):
        """Test that database errors are logged with exc_info=True."""
        # Mock database operation to raise error
        state.session_repo.get_session_by_token.side_effect = psycopg2.OperationalError(
            "connection failed"
        )
        
        response = client.post(
            "/api/auth/verify",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify error was logged with stack trace
        assert response.status_code == 503
        # Check that logger.error was called with exc_info=True
        error_calls = [call for call in mock_logger.error.call_args_list 
                      if 'exc_info' in str(call)]
        assert len(error_calls) > 0
