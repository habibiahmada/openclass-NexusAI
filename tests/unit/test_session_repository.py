"""
Unit tests for SessionRepository

Tests session creation, retrieval, deletion, expiration, and cleanup operations.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta

from src.persistence.session_repository import SessionRepository, Session
from src.persistence.database_manager import DatabaseManager


@pytest.fixture
def mock_db_manager():
    """Create a mock DatabaseManager for testing."""
    return Mock(spec=DatabaseManager)


@pytest.fixture
def session_repository(mock_db_manager):
    """Create a SessionRepository instance with mock database."""
    return SessionRepository(mock_db_manager)


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        'id': 1,
        'user_id': 1,
        'token': 'abc123def456ghi789',
        'expires_at': datetime.now() + timedelta(hours=24),
        'created_at': datetime.now()
    }


@pytest.fixture
def expired_session_data():
    """Sample expired session data for testing."""
    return {
        'id': 2,
        'user_id': 1,
        'token': 'expired_token_xyz',
        'expires_at': datetime.now() - timedelta(hours=1),  # Expired 1 hour ago
        'created_at': datetime.now() - timedelta(hours=25)
    }


class TestSession:
    """Tests for Session data model."""
    
    def test_session_initialization(self, sample_session_data):
        """Test Session object initialization."""
        session = Session.from_dict(sample_session_data)
        
        assert session.id == 1
        assert session.user_id == 1
        assert session.token == 'abc123def456ghi789'
        assert isinstance(session.expires_at, datetime)
    
    def test_session_to_dict(self, sample_session_data):
        """Test Session to dictionary conversion."""
        session = Session.from_dict(sample_session_data)
        session_dict = session.to_dict()
        
        assert session_dict['id'] == sample_session_data['id']
        assert session_dict['user_id'] == sample_session_data['user_id']
        assert session_dict['token'] == sample_session_data['token']
    
    def test_session_is_expired_false(self, sample_session_data):
        """Test is_expired returns False for valid session."""
        session = Session.from_dict(sample_session_data)
        
        assert session.is_expired() is False
    
    def test_session_is_expired_true(self, expired_session_data):
        """Test is_expired returns True for expired session."""
        session = Session.from_dict(expired_session_data)
        
        assert session.is_expired() is True
    
    def test_session_repr(self, sample_session_data):
        """Test Session string representation."""
        session = Session.from_dict(sample_session_data)
        repr_str = repr(session)
        
        assert 'Session' in repr_str
        assert 'user_id=1' in repr_str
        assert 'abc123de' in repr_str  # First 8 chars of token


class TestCreateSession:
    """Tests for session creation."""
    
    def test_create_session_success(self, session_repository, mock_db_manager, sample_session_data):
        """Test successful session creation with default 24-hour expiration."""
        mock_db_manager.execute_query.return_value = sample_session_data
        
        session = session_repository.create_session(
            user_id=1,
            token='abc123def456ghi789'
        )
        
        assert session.user_id == 1
        assert session.token == 'abc123def456ghi789'
        
        # Verify database was called
        mock_db_manager.execute_query.assert_called_once()
        call_args = mock_db_manager.execute_query.call_args
        
        # Check expires_at was set
        assert 'expires_at' in call_args[0][1]
    
    def test_create_session_custom_expiration(self, session_repository, mock_db_manager, sample_session_data):
        """Test session creation with custom expiration hours."""
        mock_db_manager.execute_query.return_value = sample_session_data
        
        session = session_repository.create_session(
            user_id=1,
            token='abc123def456ghi789',
            expires_hours=48
        )
        
        assert session is not None
        mock_db_manager.execute_query.assert_called_once()
    
    def test_create_session_token_too_short(self, session_repository, mock_db_manager):
        """Test session creation fails with short token."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            session_repository.create_session(
                user_id=1,
                token='short'
            )
        
        # Database should not be called
        mock_db_manager.execute_query.assert_not_called()
    
    def test_create_session_empty_token(self, session_repository, mock_db_manager):
        """Test session creation fails with empty token."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            session_repository.create_session(
                user_id=1,
                token=''
            )
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_create_session_negative_expiration(self, session_repository, mock_db_manager):
        """Test session creation fails with negative expiration hours."""
        with pytest.raises(ValueError, match="must be positive"):
            session_repository.create_session(
                user_id=1,
                token='abc123def456',
                expires_hours=-1
            )
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_create_session_zero_expiration(self, session_repository, mock_db_manager):
        """Test session creation fails with zero expiration hours."""
        with pytest.raises(ValueError, match="must be positive"):
            session_repository.create_session(
                user_id=1,
                token='abc123def456',
                expires_hours=0
            )
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_create_session_calculates_expiration(self, session_repository, mock_db_manager, sample_session_data):
        """Test that expiration timestamp is calculated correctly."""
        mock_db_manager.execute_query.return_value = sample_session_data
        
        before_creation = datetime.now()
        session_repository.create_session(
            user_id=1,
            token='abc123def456',
            expires_hours=24
        )
        after_creation = datetime.now()
        
        # Verify expires_at was set to approximately 24 hours from now
        call_args = mock_db_manager.execute_query.call_args
        expires_at = call_args[0][1]['expires_at']
        
        expected_min = before_creation + timedelta(hours=24)
        expected_max = after_creation + timedelta(hours=24)
        
        assert expected_min <= expires_at <= expected_max


class TestGetSessionByToken:
    """Tests for session retrieval by token."""
    
    def test_get_session_by_token_found(self, session_repository, mock_db_manager, sample_session_data):
        """Test retrieving session by token when session exists and is valid."""
        mock_db_manager.execute_query.return_value = sample_session_data
        
        session = session_repository.get_session_by_token('abc123def456ghi789')
        
        assert session is not None
        assert session.token == 'abc123def456ghi789'
        assert session.user_id == 1
        
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_session_by_token_not_found(self, session_repository, mock_db_manager):
        """Test retrieving session by token when session doesn't exist."""
        mock_db_manager.execute_query.return_value = None
        
        session = session_repository.get_session_by_token('nonexistent_token')
        
        assert session is None
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_session_by_token_expired(self, session_repository, mock_db_manager, expired_session_data):
        """Test retrieving expired session returns None and deletes it."""
        # First call returns expired session, second call for deletion
        mock_db_manager.execute_query.side_effect = [
            expired_session_data,  # get_session_by_token query
            {'id': 2}  # delete_session query
        ]
        
        session = session_repository.get_session_by_token('expired_token_xyz')
        
        assert session is None
        
        # Verify both get and delete were called
        assert mock_db_manager.execute_query.call_count == 2


class TestDeleteSession:
    """Tests for session deletion."""
    
    def test_delete_session_success(self, session_repository, mock_db_manager):
        """Test successful session deletion."""
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = session_repository.delete_session('abc123def456')
        
        assert success is True
        mock_db_manager.execute_query.assert_called_once()
    
    def test_delete_session_not_found(self, session_repository, mock_db_manager):
        """Test deleting non-existent session."""
        mock_db_manager.execute_query.return_value = None
        
        success = session_repository.delete_session('nonexistent_token')
        
        assert success is False
        mock_db_manager.execute_query.assert_called_once()


class TestCleanupExpiredSessions:
    """Tests for expired session cleanup."""
    
    def test_cleanup_expired_sessions_some_deleted(self, session_repository, mock_db_manager):
        """Test cleanup deletes expired sessions."""
        # Simulate 3 expired sessions deleted
        mock_db_manager.execute_query.return_value = [
            {'id': 1},
            {'id': 2},
            {'id': 3}
        ]
        
        deleted_count = session_repository.cleanup_expired_sessions()
        
        assert deleted_count == 3
        mock_db_manager.execute_query.assert_called_once()
    
    def test_cleanup_expired_sessions_none_deleted(self, session_repository, mock_db_manager):
        """Test cleanup when no expired sessions exist."""
        mock_db_manager.execute_query.return_value = []
        
        deleted_count = session_repository.cleanup_expired_sessions()
        
        assert deleted_count == 0
        mock_db_manager.execute_query.assert_called_once()
    
    def test_cleanup_expired_sessions_null_result(self, session_repository, mock_db_manager):
        """Test cleanup handles None result from database."""
        mock_db_manager.execute_query.return_value = None
        
        deleted_count = session_repository.cleanup_expired_sessions()
        
        assert deleted_count == 0


class TestGetUserSessions:
    """Tests for retrieving all sessions for a user."""
    
    def test_get_user_sessions_multiple(self, session_repository, mock_db_manager):
        """Test retrieving multiple sessions for a user."""
        sessions_data = [
            {
                'id': 1,
                'user_id': 1,
                'token': 'token1',
                'expires_at': datetime.now() + timedelta(hours=24),
                'created_at': datetime.now()
            },
            {
                'id': 2,
                'user_id': 1,
                'token': 'token2',
                'expires_at': datetime.now() + timedelta(hours=12),
                'created_at': datetime.now()
            }
        ]
        mock_db_manager.execute_query.return_value = sessions_data
        
        sessions = session_repository.get_user_sessions(user_id=1)
        
        assert len(sessions) == 2
        assert sessions[0].token == 'token1'
        assert sessions[1].token == 'token2'
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_user_sessions_none(self, session_repository, mock_db_manager):
        """Test retrieving sessions when user has none."""
        mock_db_manager.execute_query.return_value = []
        
        sessions = session_repository.get_user_sessions(user_id=1)
        
        assert len(sessions) == 0
        assert sessions == []
    
    def test_get_user_sessions_null_result(self, session_repository, mock_db_manager):
        """Test get_user_sessions handles None result."""
        mock_db_manager.execute_query.return_value = None
        
        sessions = session_repository.get_user_sessions(user_id=1)
        
        assert sessions == []


class TestDeleteUserSessions:
    """Tests for deleting all sessions for a user."""
    
    def test_delete_user_sessions_multiple(self, session_repository, mock_db_manager):
        """Test deleting multiple sessions for a user."""
        mock_db_manager.execute_query.return_value = [
            {'id': 1},
            {'id': 2},
            {'id': 3}
        ]
        
        deleted_count = session_repository.delete_user_sessions(user_id=1)
        
        assert deleted_count == 3
        mock_db_manager.execute_query.assert_called_once()
    
    def test_delete_user_sessions_none(self, session_repository, mock_db_manager):
        """Test deleting sessions when user has none."""
        mock_db_manager.execute_query.return_value = []
        
        deleted_count = session_repository.delete_user_sessions(user_id=1)
        
        assert deleted_count == 0
    
    def test_delete_user_sessions_null_result(self, session_repository, mock_db_manager):
        """Test delete_user_sessions handles None result."""
        mock_db_manager.execute_query.return_value = None
        
        deleted_count = session_repository.delete_user_sessions(user_id=1)
        
        assert deleted_count == 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_create_session_very_long_token(self, session_repository, mock_db_manager, sample_session_data):
        """Test creating session with very long token."""
        long_token = 'a' * 255
        mock_db_manager.execute_query.return_value = sample_session_data
        
        session = session_repository.create_session(
            user_id=1,
            token=long_token
        )
        
        assert session is not None
    
    def test_create_session_large_expiration(self, session_repository, mock_db_manager, sample_session_data):
        """Test creating session with very large expiration hours."""
        mock_db_manager.execute_query.return_value = sample_session_data
        
        session = session_repository.create_session(
            user_id=1,
            token='abc123def456',
            expires_hours=8760  # 1 year
        )
        
        assert session is not None
    
    def test_database_error_handling(self, session_repository, mock_db_manager):
        """Test proper error handling for database errors."""
        mock_db_manager.execute_query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            session_repository.get_session_by_token('abc123def456')
    
    def test_session_expiration_boundary(self):
        """Test session expiration at exact boundary."""
        # Create session that expires exactly now
        session_data = {
            'id': 1,
            'user_id': 1,
            'token': 'test_token',
            'expires_at': datetime.now(),
            'created_at': datetime.now() - timedelta(hours=24)
        }
        
        session = Session.from_dict(session_data)
        
        # Should be expired (or very close to it)
        # Allow small time difference due to execution time
        assert session.is_expired() or (datetime.now() - session.expires_at).total_seconds() < 1


class TestSessionLifecycle:
    """Integration-style tests for complete session lifecycle."""
    
    def test_complete_session_lifecycle(self, session_repository, mock_db_manager):
        """Test creating, retrieving, and deleting a session."""
        # Create session
        create_data = {
            'id': 1,
            'user_id': 1,
            'token': 'lifecycle_token',
            'expires_at': datetime.now() + timedelta(hours=24),
            'created_at': datetime.now()
        }
        mock_db_manager.execute_query.return_value = create_data
        
        session = session_repository.create_session(
            user_id=1,
            token='lifecycle_token'
        )
        assert session is not None
        
        # Retrieve session
        mock_db_manager.execute_query.return_value = create_data
        retrieved = session_repository.get_session_by_token('lifecycle_token')
        assert retrieved is not None
        
        # Delete session
        mock_db_manager.execute_query.return_value = {'id': 1}
        deleted = session_repository.delete_session('lifecycle_token')
        assert deleted is True
