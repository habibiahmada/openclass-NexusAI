"""
Unit tests for ChatHistoryRepository

Tests chat history saving, retrieval, pagination, and deletion operations.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta

from src.persistence.chat_history_repository import ChatHistoryRepository, ChatHistory
from src.persistence.database_manager import DatabaseManager


@pytest.fixture
def mock_db_manager():
    """Create a mock DatabaseManager for testing."""
    return Mock(spec=DatabaseManager)


@pytest.fixture
def chat_history_repository(mock_db_manager):
    """Create a ChatHistoryRepository instance with mock database."""
    return ChatHistoryRepository(mock_db_manager)


@pytest.fixture
def sample_chat_data():
    """Sample chat history data for testing."""
    return {
        'id': 1,
        'user_id': 1,
        'subject_id': 5,
        'question': 'Apa itu teorema Pythagoras?',
        'response': 'Teorema Pythagoras menyatakan bahwa dalam segitiga siku-siku...',
        'confidence': 0.95,
        'created_at': datetime.now()
    }


@pytest.fixture
def sample_chat_no_subject():
    """Sample chat history without subject for testing."""
    return {
        'id': 2,
        'user_id': 1,
        'subject_id': None,
        'question': 'Halo, apa kabar?',
        'response': 'Halo! Saya siap membantu Anda belajar.',
        'confidence': None,
        'created_at': datetime.now()
    }



class TestChatHistory:
    """Tests for ChatHistory data model."""
    
    def test_chat_history_initialization(self, sample_chat_data):
        """Test ChatHistory object initialization."""
        chat = ChatHistory.from_dict(sample_chat_data)
        
        assert chat.id == 1
        assert chat.user_id == 1
        assert chat.subject_id == 5
        assert chat.question == 'Apa itu teorema Pythagoras?'
        assert chat.confidence == 0.95
    
    def test_chat_history_to_dict(self, sample_chat_data):
        """Test ChatHistory to dictionary conversion."""
        chat = ChatHistory.from_dict(sample_chat_data)
        chat_dict = chat.to_dict()
        
        assert chat_dict['id'] == sample_chat_data['id']
        assert chat_dict['user_id'] == sample_chat_data['user_id']
        assert chat_dict['question'] == sample_chat_data['question']
    
    def test_chat_history_no_subject(self, sample_chat_no_subject):
        """Test ChatHistory with no subject_id."""
        chat = ChatHistory.from_dict(sample_chat_no_subject)
        
        assert chat.subject_id is None
        assert chat.confidence is None
    
    def test_chat_history_repr(self, sample_chat_data):
        """Test ChatHistory string representation."""
        chat = ChatHistory.from_dict(sample_chat_data)
        repr_str = repr(chat)
        
        assert 'ChatHistory' in repr_str
        assert 'user_id=1' in repr_str
        assert 'subject_id=5' in repr_str



class TestSaveChat:
    """Tests for saving chat history."""
    
    def test_save_chat_success(self, chat_history_repository, mock_db_manager, sample_chat_data):
        """Test successful chat history save."""
        mock_db_manager.execute_query.return_value = sample_chat_data
        
        chat = chat_history_repository.save_chat(
            user_id=1,
            subject_id=5,
            question='Apa itu teorema Pythagoras?',
            response='Teorema Pythagoras menyatakan bahwa dalam segitiga siku-siku...',
            confidence=0.95
        )
        
        assert chat.user_id == 1
        assert chat.subject_id == 5
        assert chat.confidence == 0.95
        mock_db_manager.execute_query.assert_called_once()
    
    def test_save_chat_no_subject(self, chat_history_repository, mock_db_manager, sample_chat_no_subject):
        """Test saving chat without subject_id."""
        mock_db_manager.execute_query.return_value = sample_chat_no_subject
        
        chat = chat_history_repository.save_chat(
            user_id=1,
            subject_id=None,
            question='Halo, apa kabar?',
            response='Halo! Saya siap membantu Anda belajar.'
        )
        
        assert chat.subject_id is None
        assert chat.confidence is None
    
    def test_save_chat_empty_question(self, chat_history_repository, mock_db_manager):
        """Test save fails with empty question."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            chat_history_repository.save_chat(
                user_id=1,
                subject_id=5,
                question='',
                response='Some response'
            )
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_save_chat_whitespace_question(self, chat_history_repository, mock_db_manager):
        """Test save fails with whitespace-only question."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            chat_history_repository.save_chat(
                user_id=1,
                subject_id=5,
                question='   ',
                response='Some response'
            )
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_save_chat_empty_response(self, chat_history_repository, mock_db_manager):
        """Test save fails with empty response."""
        with pytest.raises(ValueError, match="Response cannot be empty"):
            chat_history_repository.save_chat(
                user_id=1,
                subject_id=5,
                question='Valid question',
                response=''
            )
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_save_chat_invalid_confidence_high(self, chat_history_repository, mock_db_manager):
        """Test save fails with confidence > 1.0."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            chat_history_repository.save_chat(
                user_id=1,
                subject_id=5,
                question='Valid question',
                response='Valid response',
                confidence=1.5
            )
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_save_chat_invalid_confidence_low(self, chat_history_repository, mock_db_manager):
        """Test save fails with confidence < 0.0."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            chat_history_repository.save_chat(
                user_id=1,
                subject_id=5,
                question='Valid question',
                response='Valid response',
                confidence=-0.1
            )
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_save_chat_strips_whitespace(self, chat_history_repository, mock_db_manager, sample_chat_data):
        """Test that question and response are stripped of whitespace."""
        mock_db_manager.execute_query.return_value = sample_chat_data
        
        chat_history_repository.save_chat(
            user_id=1,
            subject_id=5,
            question='  Question with spaces  ',
            response='  Response with spaces  '
        )
        
        call_args = mock_db_manager.execute_query.call_args
        params = call_args[0][1]
        
        assert params['question'] == 'Question with spaces'
        assert params['response'] == 'Response with spaces'



class TestGetUserHistory:
    """Tests for retrieving user chat history."""
    
    def test_get_user_history_success(self, chat_history_repository, mock_db_manager):
        """Test retrieving user history with default pagination."""
        chats_data = [
            {
                'id': 1,
                'user_id': 1,
                'subject_id': 5,
                'question': 'Question 1',
                'response': 'Response 1',
                'confidence': 0.9,
                'created_at': datetime.now()
            },
            {
                'id': 2,
                'user_id': 1,
                'subject_id': 5,
                'question': 'Question 2',
                'response': 'Response 2',
                'confidence': 0.85,
                'created_at': datetime.now()
            }
        ]
        mock_db_manager.execute_query.return_value = chats_data
        
        history = chat_history_repository.get_user_history(user_id=1)
        
        assert len(history) == 2
        assert history[0].question == 'Question 1'
        assert history[1].question == 'Question 2'
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_user_history_with_limit(self, chat_history_repository, mock_db_manager):
        """Test retrieving user history with custom limit."""
        mock_db_manager.execute_query.return_value = []
        
        chat_history_repository.get_user_history(user_id=1, limit=20)
        
        call_args = mock_db_manager.execute_query.call_args
        params = call_args[0][1]
        
        assert params['limit'] == 20
    
    def test_get_user_history_with_offset(self, chat_history_repository, mock_db_manager):
        """Test retrieving user history with pagination offset."""
        mock_db_manager.execute_query.return_value = []
        
        chat_history_repository.get_user_history(user_id=1, limit=20, offset=40)
        
        call_args = mock_db_manager.execute_query.call_args
        params = call_args[0][1]
        
        assert params['limit'] == 20
        assert params['offset'] == 40
    
    def test_get_user_history_empty(self, chat_history_repository, mock_db_manager):
        """Test retrieving history when user has no chats."""
        mock_db_manager.execute_query.return_value = []
        
        history = chat_history_repository.get_user_history(user_id=1)
        
        assert len(history) == 0
        assert history == []
    
    def test_get_user_history_invalid_limit(self, chat_history_repository, mock_db_manager):
        """Test get_user_history fails with invalid limit."""
        with pytest.raises(ValueError, match="Limit must be positive"):
            chat_history_repository.get_user_history(user_id=1, limit=0)
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_get_user_history_negative_offset(self, chat_history_repository, mock_db_manager):
        """Test get_user_history fails with negative offset."""
        with pytest.raises(ValueError, match="Offset cannot be negative"):
            chat_history_repository.get_user_history(user_id=1, offset=-1)
        
        mock_db_manager.execute_query.assert_not_called()



class TestGetSubjectHistory:
    """Tests for retrieving subject chat history."""
    
    def test_get_subject_history_success(self, chat_history_repository, mock_db_manager):
        """Test retrieving subject history."""
        chats_data = [
            {
                'id': 1,
                'user_id': 1,
                'subject_id': 5,
                'question': 'Math question 1',
                'response': 'Math response 1',
                'confidence': 0.9,
                'created_at': datetime.now()
            },
            {
                'id': 2,
                'user_id': 2,
                'subject_id': 5,
                'question': 'Math question 2',
                'response': 'Math response 2',
                'confidence': 0.88,
                'created_at': datetime.now()
            }
        ]
        mock_db_manager.execute_query.return_value = chats_data
        
        history = chat_history_repository.get_subject_history(subject_id=5)
        
        assert len(history) == 2
        assert all(chat.subject_id == 5 for chat in history)
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_subject_history_with_pagination(self, chat_history_repository, mock_db_manager):
        """Test retrieving subject history with pagination."""
        mock_db_manager.execute_query.return_value = []
        
        chat_history_repository.get_subject_history(subject_id=5, limit=30, offset=60)
        
        call_args = mock_db_manager.execute_query.call_args
        params = call_args[0][1]
        
        assert params['subject_id'] == 5
        assert params['limit'] == 30
        assert params['offset'] == 60
    
    def test_get_subject_history_empty(self, chat_history_repository, mock_db_manager):
        """Test retrieving history when subject has no chats."""
        mock_db_manager.execute_query.return_value = []
        
        history = chat_history_repository.get_subject_history(subject_id=5)
        
        assert len(history) == 0
    
    def test_get_subject_history_invalid_limit(self, chat_history_repository, mock_db_manager):
        """Test get_subject_history fails with invalid limit."""
        with pytest.raises(ValueError, match="Limit must be positive"):
            chat_history_repository.get_subject_history(subject_id=5, limit=-5)
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_get_subject_history_negative_offset(self, chat_history_repository, mock_db_manager):
        """Test get_subject_history fails with negative offset."""
        with pytest.raises(ValueError, match="Offset cannot be negative"):
            chat_history_repository.get_subject_history(subject_id=5, offset=-10)
        
        mock_db_manager.execute_query.assert_not_called()



class TestDeleteOldHistory:
    """Tests for deleting old chat history."""
    
    def test_delete_old_history_success(self, chat_history_repository, mock_db_manager):
        """Test deleting old chat history."""
        mock_db_manager.execute_query.return_value = [
            {'id': 1},
            {'id': 2},
            {'id': 3}
        ]
        
        deleted_count = chat_history_repository.delete_old_history(days=90)
        
        assert deleted_count == 3
        mock_db_manager.execute_query.assert_called_once()
    
    def test_delete_old_history_none_deleted(self, chat_history_repository, mock_db_manager):
        """Test delete when no old history exists."""
        mock_db_manager.execute_query.return_value = []
        
        deleted_count = chat_history_repository.delete_old_history(days=90)
        
        assert deleted_count == 0
    
    def test_delete_old_history_invalid_days(self, chat_history_repository, mock_db_manager):
        """Test delete fails with invalid days."""
        with pytest.raises(ValueError, match="Days must be positive"):
            chat_history_repository.delete_old_history(days=0)
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_delete_old_history_negative_days(self, chat_history_repository, mock_db_manager):
        """Test delete fails with negative days."""
        with pytest.raises(ValueError, match="Days must be positive"):
            chat_history_repository.delete_old_history(days=-30)
        
        mock_db_manager.execute_query.assert_not_called()


class TestGetChatCounts:
    """Tests for getting chat counts."""
    
    def test_get_user_chat_count(self, chat_history_repository, mock_db_manager):
        """Test getting total chat count for user."""
        mock_db_manager.execute_query.return_value = {'count': 42}
        
        count = chat_history_repository.get_user_chat_count(user_id=1)
        
        assert count == 42
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_user_chat_count_zero(self, chat_history_repository, mock_db_manager):
        """Test getting count when user has no chats."""
        mock_db_manager.execute_query.return_value = {'count': 0}
        
        count = chat_history_repository.get_user_chat_count(user_id=1)
        
        assert count == 0
    
    def test_get_subject_chat_count(self, chat_history_repository, mock_db_manager):
        """Test getting total chat count for subject."""
        mock_db_manager.execute_query.return_value = {'count': 150}
        
        count = chat_history_repository.get_subject_chat_count(subject_id=5)
        
        assert count == 150
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_subject_chat_count_zero(self, chat_history_repository, mock_db_manager):
        """Test getting count when subject has no chats."""
        mock_db_manager.execute_query.return_value = {'count': 0}
        
        count = chat_history_repository.get_subject_chat_count(subject_id=5)
        
        assert count == 0


class TestGetRecentChats:
    """Tests for getting recent chats across all users."""
    
    def test_get_recent_chats_success(self, chat_history_repository, mock_db_manager):
        """Test getting recent chats."""
        chats_data = [
            {
                'id': 3,
                'user_id': 2,
                'subject_id': 5,
                'question': 'Recent question',
                'response': 'Recent response',
                'confidence': 0.92,
                'created_at': datetime.now()
            },
            {
                'id': 2,
                'user_id': 1,
                'subject_id': 6,
                'question': 'Older question',
                'response': 'Older response',
                'confidence': 0.88,
                'created_at': datetime.now() - timedelta(hours=1)
            }
        ]
        mock_db_manager.execute_query.return_value = chats_data
        
        recent = chat_history_repository.get_recent_chats(limit=10)
        
        assert len(recent) == 2
        assert recent[0].id == 3
        assert recent[1].id == 2
    
    def test_get_recent_chats_custom_limit(self, chat_history_repository, mock_db_manager):
        """Test getting recent chats with custom limit."""
        mock_db_manager.execute_query.return_value = []
        
        chat_history_repository.get_recent_chats(limit=20)
        
        call_args = mock_db_manager.execute_query.call_args
        params = call_args[0][1]
        
        assert params['limit'] == 20
    
    def test_get_recent_chats_empty(self, chat_history_repository, mock_db_manager):
        """Test getting recent chats when none exist."""
        mock_db_manager.execute_query.return_value = []
        
        recent = chat_history_repository.get_recent_chats()
        
        assert len(recent) == 0
    
    def test_get_recent_chats_invalid_limit(self, chat_history_repository, mock_db_manager):
        """Test get_recent_chats fails with invalid limit."""
        with pytest.raises(ValueError, match="Limit must be positive"):
            chat_history_repository.get_recent_chats(limit=0)
        
        mock_db_manager.execute_query.assert_not_called()


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_save_chat_very_long_question(self, chat_history_repository, mock_db_manager, sample_chat_data):
        """Test saving chat with very long question."""
        long_question = 'A' * 10000
        mock_db_manager.execute_query.return_value = sample_chat_data
        
        chat = chat_history_repository.save_chat(
            user_id=1,
            subject_id=5,
            question=long_question,
            response='Response'
        )
        
        assert chat is not None
    
    def test_save_chat_very_long_response(self, chat_history_repository, mock_db_manager, sample_chat_data):
        """Test saving chat with very long response."""
        long_response = 'B' * 50000
        mock_db_manager.execute_query.return_value = sample_chat_data
        
        chat = chat_history_repository.save_chat(
            user_id=1,
            subject_id=5,
            question='Question',
            response=long_response
        )
        
        assert chat is not None
    
    def test_save_chat_confidence_boundaries(self, chat_history_repository, mock_db_manager, sample_chat_data):
        """Test saving chat with confidence at boundaries."""
        mock_db_manager.execute_query.return_value = sample_chat_data
        
        # Test 0.0
        chat = chat_history_repository.save_chat(
            user_id=1,
            subject_id=5,
            question='Question',
            response='Response',
            confidence=0.0
        )
        assert chat is not None
        
        # Test 1.0
        chat = chat_history_repository.save_chat(
            user_id=1,
            subject_id=5,
            question='Question',
            response='Response',
            confidence=1.0
        )
        assert chat is not None
    
    def test_database_error_handling(self, chat_history_repository, mock_db_manager):
        """Test proper error handling for database errors."""
        mock_db_manager.execute_query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            chat_history_repository.get_user_history(user_id=1)
    
    def test_pagination_large_offset(self, chat_history_repository, mock_db_manager):
        """Test pagination with very large offset."""
        mock_db_manager.execute_query.return_value = []
        
        history = chat_history_repository.get_user_history(user_id=1, limit=50, offset=10000)
        
        assert len(history) == 0
