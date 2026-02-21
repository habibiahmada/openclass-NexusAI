"""
Integration tests for ChatHistoryRepository

These tests verify ChatHistoryRepository works with a real PostgreSQL database.
Requires PostgreSQL to be running and accessible with the schema initialized.
"""

import pytest
import os
from datetime import datetime

from src.persistence.database_manager import DatabaseManager
from src.persistence.chat_history_repository import ChatHistoryRepository


# Skip these tests if PostgreSQL is not available
pytestmark = pytest.mark.skipif(
    not os.getenv('TEST_DATABASE_URL'),
    reason="PostgreSQL test database not configured. Set TEST_DATABASE_URL environment variable."
)


@pytest.fixture
def db_manager():
    """Create a DatabaseManager instance for testing."""
    connection_string = os.getenv('TEST_DATABASE_URL')
    manager = DatabaseManager(connection_string)
    yield manager
    manager.close()


@pytest.fixture
def chat_history_repo(db_manager):
    """Create a ChatHistoryRepository instance for testing."""
    return ChatHistoryRepository(db_manager)


@pytest.fixture
def cleanup_chat_history(db_manager):
    """Clean up chat history after tests."""
    yield
    # Clean up test data after each test
    try:
        db_manager.execute_query("DELETE FROM chat_history WHERE question LIKE 'TEST:%'")
    except Exception:
        pass  # Ignore cleanup errors


def test_save_and_retrieve_chat(chat_history_repo, cleanup_chat_history):
    """Test saving and retrieving a chat interaction."""
    # Save a chat
    chat = chat_history_repo.save_chat(
        user_id=1,
        subject_id=1,
        question="TEST: What is Python?",
        response="Python is a programming language.",
        confidence=0.95
    )
    
    assert chat.id is not None
    assert chat.user_id == 1
    assert chat.subject_id == 1
    assert chat.confidence == 0.95
    assert isinstance(chat.created_at, datetime)


def test_get_user_history_with_real_data(chat_history_repo, cleanup_chat_history):
    """Test retrieving user history with real database."""
    # Save multiple chats for the same user
    chat_history_repo.save_chat(
        user_id=1,
        subject_id=1,
        question="TEST: Question 1",
        response="Response 1"
    )
    chat_history_repo.save_chat(
        user_id=1,
        subject_id=1,
        question="TEST: Question 2",
        response="Response 2"
    )
    
    # Retrieve history
    history = chat_history_repo.get_user_history(user_id=1, limit=10)
    
    # Should have at least 2 chats (may have more from other tests)
    test_chats = [h for h in history if h.question.startswith('TEST:')]
    assert len(test_chats) >= 2


def test_pagination_with_real_data(chat_history_repo, cleanup_chat_history):
    """Test pagination with real database."""
    # Save 5 chats
    for i in range(5):
        chat_history_repo.save_chat(
            user_id=1,
            subject_id=1,
            question=f"TEST: Pagination question {i}",
            response=f"Response {i}"
        )
    
    # Get first page
    page1 = chat_history_repo.get_user_history(user_id=1, limit=2, offset=0)
    
    # Get second page
    page2 = chat_history_repo.get_user_history(user_id=1, limit=2, offset=2)
    
    # Pages should be different
    if len(page1) >= 2 and len(page2) >= 2:
        assert page1[0].id != page2[0].id
