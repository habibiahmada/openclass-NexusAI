"""
Additional unit tests for repository error handling

Tests constraint violations, duplicate keys, and edge cases for all repositories.
This complements the existing unit tests with more comprehensive error scenarios.
"""

import pytest
from unittest.mock import Mock
import psycopg2
from psycopg2 import errors as pg_errors
from datetime import datetime

from src.persistence import (
    DatabaseManager,
    UserRepository,
    SessionRepository,
    ChatHistoryRepository,
    SubjectRepository,
    BookRepository
)


@pytest.fixture
def mock_db_manager():
    """Create a mock DatabaseManager for testing."""
    return Mock(spec=DatabaseManager)


@pytest.fixture
def user_repo(mock_db_manager):
    return UserRepository(mock_db_manager)


@pytest.fixture
def session_repo(mock_db_manager):
    return SessionRepository(mock_db_manager)


@pytest.fixture
def chat_repo(mock_db_manager):
    return ChatHistoryRepository(mock_db_manager)


@pytest.fixture
def subject_repo(mock_db_manager):
    return SubjectRepository(mock_db_manager)


@pytest.fixture
def book_repo(mock_db_manager):
    return BookRepository(mock_db_manager)


class TestUserRepositoryConstraints:
    """Test constraint violations for UserRepository."""
    
    def test_create_user_duplicate_username(self, user_repo, mock_db_manager):
        """Test creating user with duplicate username raises error."""
        # Simulate unique constraint violation
        mock_db_manager.execute_query.side_effect = psycopg2.IntegrityError(
            "duplicate key value violates unique constraint"
        )
        
        with pytest.raises(psycopg2.IntegrityError):
            user_repo.create_user(
                username="existing_user",
                password="password123",
                role="siswa"
            )
    
    def test_update_user_duplicate_username(self, user_repo, mock_db_manager):
        """Test updating user to duplicate username raises error."""
        mock_db_manager.execute_query.side_effect = psycopg2.IntegrityError(
            "duplicate key value violates unique constraint"
        )
        
        with pytest.raises(psycopg2.IntegrityError):
            user_repo.update_user(
                user_id=1,
                updates={'username': 'existing_user'}
            )
    
    def test_create_user_connection_timeout(self, user_repo, mock_db_manager):
        """Test user creation handles connection timeout."""
        mock_db_manager.execute_query.side_effect = psycopg2.OperationalError(
            "connection timeout"
        )
        
        with pytest.raises(psycopg2.OperationalError):
            user_repo.create_user(
                username="testuser",
                password="password123",
                role="siswa"
            )
    
    def test_get_user_connection_lost(self, user_repo, mock_db_manager):
        """Test get_user handles lost connection."""
        mock_db_manager.execute_query.side_effect = psycopg2.OperationalError(
            "server closed the connection unexpectedly"
        )
        
        with pytest.raises(psycopg2.OperationalError):
            user_repo.get_user_by_username("testuser")


class TestSessionRepositoryConstraints:
    """Test constraint violations for SessionRepository."""
    
    def test_create_session_invalid_user_id(self, session_repo, mock_db_manager):
        """Test creating session with non-existent user_id raises foreign key error."""
        mock_db_manager.execute_query.side_effect = psycopg2.IntegrityError(
            "foreign key constraint violation"
        )
        
        with pytest.raises(psycopg2.IntegrityError):
            session_repo.create_session(
                user_id=99999,  # Non-existent user
                token="test_token_123"
            )
    
    def test_create_session_duplicate_token(self, session_repo, mock_db_manager):
        """Test creating session with duplicate token raises error."""
        mock_db_manager.execute_query.side_effect = psycopg2.IntegrityError(
            "duplicate key value violates unique constraint"
        )
        
        with pytest.raises(psycopg2.IntegrityError):
            session_repo.create_session(
                user_id=1,
                token="existing_token"
            )
    
    def test_cleanup_sessions_connection_failure(self, session_repo, mock_db_manager):
        """Test cleanup handles connection failure gracefully."""
        mock_db_manager.execute_query.side_effect = psycopg2.OperationalError(
            "connection failed"
        )
        
        with pytest.raises(psycopg2.OperationalError):
            session_repo.cleanup_expired_sessions()


class TestChatHistoryRepositoryConstraints:
    """Test constraint violations for ChatHistoryRepository."""
    
    def test_save_chat_invalid_user_id(self, chat_repo, mock_db_manager):
        """Test saving chat with non-existent user_id raises foreign key error."""
        mock_db_manager.execute_query.side_effect = psycopg2.IntegrityError(
            "foreign key constraint violation"
        )
        
        with pytest.raises(psycopg2.IntegrityError):
            chat_repo.save_chat(
                user_id=99999,  # Non-existent user
                subject_id=1,
                question="Test question",
                response="Test response"
            )
    
    def test_save_chat_invalid_subject_id(self, chat_repo, mock_db_manager):
        """Test saving chat with non-existent subject_id raises foreign key error."""
        mock_db_manager.execute_query.side_effect = psycopg2.IntegrityError(
            "foreign key constraint violation"
        )
        
        with pytest.raises(psycopg2.IntegrityError):
            chat_repo.save_chat(
                user_id=1,
                subject_id=99999,  # Non-existent subject
                question="Test question",
                response="Test response"
            )
    
    def test_get_history_connection_timeout(self, chat_repo, mock_db_manager):
        """Test get_user_history handles connection timeout."""
        mock_db_manager.execute_query.side_effect = psycopg2.OperationalError(
            "connection timeout"
        )
        
        with pytest.raises(psycopg2.OperationalError):
            chat_repo.get_user_history(user_id=1)
    
    def test_delete_old_history_deadlock(self, chat_repo, mock_db_manager):
        """Test delete_old_history handles deadlock."""
        mock_db_manager.execute_query.side_effect = psycopg2.extensions.TransactionRollbackError(
            "deadlock detected"
        )
        
        with pytest.raises(psycopg2.extensions.TransactionRollbackError):
            chat_repo.delete_old_history(days=90)


class TestSubjectRepositoryConstraints:
    """Test constraint violations for SubjectRepository."""
    
    def test_create_subject_duplicate_code(self, subject_repo, mock_db_manager):
        """Test creating subject with duplicate code raises error."""
        mock_db_manager.execute_query.side_effect = psycopg2.IntegrityError(
            "duplicate key value violates unique constraint"
        )
        
        with pytest.raises(psycopg2.IntegrityError):
            subject_repo.create_subject(
                grade=10,
                name="Matematika",
                code="MAT_10"  # Duplicate code
            )
    
    def test_delete_subject_with_books(self, subject_repo, mock_db_manager):
        """Test deleting subject with associated books raises foreign key error."""
        mock_db_manager.execute_query.side_effect = psycopg2.IntegrityError(
            "foreign key constraint violation"
        )
        
        with pytest.raises(psycopg2.IntegrityError):
            subject_repo.delete_subject(subject_id=1)
    
    def test_update_subject_connection_lost(self, subject_repo, mock_db_manager):
        """Test update_subject handles lost connection."""
        # First call for get_subject_by_id succeeds
        mock_db_manager.execute_query.side_effect = [
            {'id': 1, 'grade': 10, 'name': 'Math', 'code': 'MAT_10', 'created_at': datetime.now()},
            psycopg2.OperationalError("connection lost")
        ]
        
        with pytest.raises(psycopg2.OperationalError):
            subject_repo.update_subject(1, {'name': 'Mathematics'})


class TestBookRepositoryConstraints:
    """Test constraint violations for BookRepository."""
    
    def test_create_book_invalid_subject_id(self, book_repo, mock_db_manager):
        """Test creating book with non-existent subject_id raises foreign key error."""
        mock_db_manager.execute_query.side_effect = psycopg2.IntegrityError(
            "foreign key constraint violation"
        )
        
        with pytest.raises(psycopg2.IntegrityError):
            book_repo.create_book(
                subject_id=99999,  # Non-existent subject
                title="Test Book",
                filename="test.pdf",
                vkp_version="1.0.0"
            )
    
    def test_create_book_duplicate_filename(self, book_repo, mock_db_manager):
        """Test creating book with duplicate filename raises error."""
        mock_db_manager.execute_query.side_effect = psycopg2.IntegrityError(
            "duplicate key value violates unique constraint"
        )
        
        with pytest.raises(psycopg2.IntegrityError):
            book_repo.create_book(
                subject_id=1,
                title="Test Book",
                filename="existing.pdf",  # Duplicate filename
                vkp_version="1.0.0"
            )
    
    def test_update_book_version_connection_failure(self, book_repo, mock_db_manager):
        """Test update_book_version handles connection failure."""
        mock_db_manager.execute_query.side_effect = psycopg2.OperationalError(
            "connection failed"
        )
        
        with pytest.raises(psycopg2.OperationalError):
            book_repo.update_book_version(book_id=1, vkp_version="1.1.0")


class TestEdgeCasesEmptyResults:
    """Test edge cases with empty results for all repositories."""
    
    def test_user_repo_get_nonexistent_user(self, user_repo, mock_db_manager):
        """Test getting non-existent user returns None."""
        mock_db_manager.execute_query.return_value = None
        
        user = user_repo.get_user_by_id(99999)
        assert user is None
    
    def test_session_repo_get_nonexistent_session(self, session_repo, mock_db_manager):
        """Test getting non-existent session returns None."""
        mock_db_manager.execute_query.return_value = None
        
        session = session_repo.get_session_by_token("nonexistent_token")
        assert session is None
    
    def test_chat_repo_empty_history(self, chat_repo, mock_db_manager):
        """Test getting history for user with no chats returns empty list."""
        mock_db_manager.execute_query.return_value = []
        
        history = chat_repo.get_user_history(user_id=1)
        assert history == []
        assert len(history) == 0
    
    def test_subject_repo_no_subjects_for_grade(self, subject_repo, mock_db_manager):
        """Test getting subjects for grade with none returns empty list."""
        mock_db_manager.execute_query.return_value = []
        
        subjects = subject_repo.get_subjects_by_grade(grade=12)
        assert subjects == []
    
    def test_book_repo_no_books_for_subject(self, book_repo, mock_db_manager):
        """Test getting books for subject with none returns empty list."""
        mock_db_manager.execute_query.return_value = []
        
        books = book_repo.get_books_by_subject(subject_id=1)
        assert books == []


class TestEdgeCasesBoundaryValues:
    """Test edge cases with boundary values."""
    
    def test_user_repo_minimum_username_length(self, user_repo, mock_db_manager):
        """Test creating user with minimum valid username length (3 chars)."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'username': 'abc',
            'password_hash': 'hash',
            'role': 'siswa',
            'full_name': None,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        user = user_repo.create_user(
            username="abc",
            password="password123",
            role="siswa"
        )
        
        assert user.username == "abc"
    
    def test_user_repo_maximum_username_length(self, user_repo, mock_db_manager):
        """Test creating user with maximum valid username length (50 chars)."""
        long_username = "a" * 50
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'username': long_username,
            'password_hash': 'hash',
            'role': 'siswa',
            'full_name': None,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        user = user_repo.create_user(
            username=long_username,
            password="password123",
            role="siswa"
        )
        
        assert user.username == long_username
    
    def test_session_repo_minimum_token_length(self, session_repo, mock_db_manager):
        """Test creating session with minimum valid token length (8 chars)."""
        from datetime import timedelta
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'user_id': 1,
            'token': 'abcd1234',
            'expires_at': datetime.now() + timedelta(hours=24),
            'created_at': datetime.now()
        }
        
        session = session_repo.create_session(
            user_id=1,
            token="abcd1234"
        )
        
        assert session.token == "abcd1234"
    
    def test_chat_repo_confidence_zero(self, chat_repo, mock_db_manager):
        """Test saving chat with confidence = 0.0."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'user_id': 1,
            'subject_id': 1,
            'question': 'Test',
            'response': 'Response',
            'confidence': 0.0,
            'created_at': datetime.now()
        }
        
        chat = chat_repo.save_chat(
            user_id=1,
            subject_id=1,
            question="Test",
            response="Response",
            confidence=0.0
        )
        
        assert chat.confidence == 0.0
    
    def test_chat_repo_confidence_one(self, chat_repo, mock_db_manager):
        """Test saving chat with confidence = 1.0."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'user_id': 1,
            'subject_id': 1,
            'question': 'Test',
            'response': 'Response',
            'confidence': 1.0,
            'created_at': datetime.now()
        }
        
        chat = chat_repo.save_chat(
            user_id=1,
            subject_id=1,
            question="Test",
            response="Response",
            confidence=1.0
        )
        
        assert chat.confidence == 1.0
    
    def test_chat_repo_pagination_first_page(self, chat_repo, mock_db_manager):
        """Test pagination with offset=0 (first page)."""
        mock_db_manager.execute_query.return_value = []
        
        history = chat_repo.get_user_history(user_id=1, limit=50, offset=0)
        
        call_args = mock_db_manager.execute_query.call_args
        params = call_args[0][1]
        assert params['offset'] == 0
    
    def test_chat_repo_pagination_large_offset(self, chat_repo, mock_db_manager):
        """Test pagination with very large offset."""
        mock_db_manager.execute_query.return_value = []
        
        history = chat_repo.get_user_history(user_id=1, limit=50, offset=100000)
        
        call_args = mock_db_manager.execute_query.call_args
        params = call_args[0][1]
        assert params['offset'] == 100000


class TestConcurrentOperations:
    """Test handling of concurrent operations and race conditions."""
    
    def test_session_cleanup_during_creation(self, session_repo, mock_db_manager):
        """Test session creation while cleanup is running."""
        from datetime import timedelta
        # Simulate successful creation even during cleanup
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'user_id': 1,
            'token': 'test_token',
            'expires_at': datetime.now() + timedelta(hours=24),
            'created_at': datetime.now()
        }
        
        session = session_repo.create_session(user_id=1, token="test_token")
        assert session is not None
    
    def test_user_update_race_condition(self, user_repo, mock_db_manager):
        """Test user update with potential race condition."""
        # Simulate successful update
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = user_repo.update_user(
            user_id=1,
            updates={'full_name': 'Updated Name'}
        )
        
        assert success is True


class TestNullAndNoneHandling:
    """Test handling of NULL and None values."""
    
    def test_user_repo_none_full_name(self, user_repo, mock_db_manager):
        """Test creating user with None full_name."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'username': 'testuser',
            'password_hash': 'hash',
            'role': 'siswa',
            'full_name': None,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        user = user_repo.create_user(
            username="testuser",
            password="password123",
            role="siswa",
            full_name=None
        )
        
        assert user.full_name is None
    
    def test_chat_repo_none_subject_id(self, chat_repo, mock_db_manager):
        """Test saving chat with None subject_id."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'user_id': 1,
            'subject_id': None,
            'question': 'Test',
            'response': 'Response',
            'confidence': None,
            'created_at': datetime.now()
        }
        
        chat = chat_repo.save_chat(
            user_id=1,
            subject_id=None,
            question="Test",
            response="Response"
        )
        
        assert chat.subject_id is None
        assert chat.confidence is None
    
    def test_chat_repo_none_confidence(self, chat_repo, mock_db_manager):
        """Test saving chat with None confidence."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'user_id': 1,
            'subject_id': 1,
            'question': 'Test',
            'response': 'Response',
            'confidence': None,
            'created_at': datetime.now()
        }
        
        chat = chat_repo.save_chat(
            user_id=1,
            subject_id=1,
            question="Test",
            response="Response",
            confidence=None
        )
        
        assert chat.confidence is None
