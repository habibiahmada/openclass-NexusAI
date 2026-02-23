"""
Property-based tests for data persistence across restarts

This module tests that data persists correctly in the PostgreSQL database
across server restarts, validating Requirements 3.3.

Feature: architecture-alignment-refactoring
Property 3: Data Persistence Across Restarts
"""

import os
import pytest
from hypothesis import given, settings, strategies as st
from datetime import datetime, timedelta

from src.persistence.database_manager import DatabaseManager
from src.persistence.user_repository import UserRepository
from src.persistence.session_repository import SessionRepository
from src.persistence.chat_history_repository import ChatHistoryRepository
from src.persistence.subject_repository import SubjectRepository
from src.persistence.book_repository import BookRepository


# Skip these tests if PostgreSQL is not available
pytestmark = pytest.mark.skipif(
    not os.getenv('TEST_DATABASE_URL'),
    reason="PostgreSQL test database not configured. Set TEST_DATABASE_URL environment variable."
)


def get_db_connection_string():
    """Get database connection string from environment."""
    return os.getenv('TEST_DATABASE_URL')


def simulate_restart(connection_string: str):
    """
    Simulate a server restart by creating a new database manager instance.
    
    This simulates closing and reopening database connections as would happen
    during a real server restart.
    
    Args:
        connection_string: PostgreSQL connection string
    
    Returns:
        New DatabaseManager instance
    """
    # Create a new connection pool (simulates restart)
    return DatabaseManager(connection_string)


# Property 3: Data Persistence Across Restarts
# **Validates: Requirements 3.3**
@settings(max_examples=100)
@given(
    username=st.text(
        min_size=3, 
        max_size=50, 
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            blacklist_characters=' '
        )
    ),
    password=st.text(min_size=6, max_size=50),
    full_name=st.text(min_size=3, max_size=100),
    question=st.text(min_size=10, max_size=500),
    response=st.text(min_size=10, max_size=1000),
    token=st.text(min_size=8, max_size=64),
    subject_name=st.text(min_size=3, max_size=100),
    book_title=st.text(min_size=3, max_size=200)
)
def test_data_persists_across_restarts(
    username, 
    password, 
    full_name, 
    question, 
    response, 
    token,
    subject_name,
    book_title
):
    """
    Property: For any user session, chat history entry, or metadata stored in the system,
    restarting the server should preserve that data, and querying the database after 
    restart should return the same data.
    
    This test verifies that:
    1. User data persists across restarts
    2. Session data persists across restarts
    3. Chat history persists across restarts
    4. Subject and book metadata persists across restarts
    
    **Validates: Requirements 3.3**
    """
    connection_string = get_db_connection_string()
    
    # Phase 1: Create data with initial connection
    db_manager1 = DatabaseManager(connection_string)
    
    try:
        user_repo1 = UserRepository(db_manager1)
        session_repo1 = SessionRepository(db_manager1)
        chat_repo1 = ChatHistoryRepository(db_manager1)
        subject_repo1 = SubjectRepository(db_manager1)
        book_repo1 = BookRepository(db_manager1)
        
        # Create user
        user = user_repo1.create_user(
            username=username,
            password=password,
            role="siswa",
            full_name=full_name
        )
        user_id = user.id
        
        # Create session
        session = session_repo1.create_session(
            user_id=user_id,
            token=token,
            expires_hours=24
        )
        session_id = session.id
        
        # Create subject
        subject = subject_repo1.create_subject(
            grade=10,
            name=subject_name,
            code=f"subj_{username[:10]}"  # Use username prefix for uniqueness
        )
        subject_id = subject.id
        
        # Create book
        book = book_repo1.create_book(
            subject_id=subject_id,
            title=book_title,
            filename=f"{username}_book.pdf",
            vkp_version="1.0.0"
        )
        book_id = book.id
        
        # Create chat history
        chat = chat_repo1.save_chat(
            user_id=user_id,
            subject_id=subject_id,
            question=question,
            response=response,
            confidence=0.95
        )
        chat_id = chat.id
        
        # Store original data for comparison
        original_user = user.to_dict()
        original_session = session.to_dict()
        original_chat = chat.to_dict()
        original_subject = subject.to_dict()
        original_book = book.to_dict()
        
    finally:
        # Close the first connection (simulate shutdown)
        db_manager1.close()
    
    # Phase 2: Simulate restart by creating new connection
    db_manager2 = simulate_restart(connection_string)
    
    try:
        user_repo2 = UserRepository(db_manager2)
        session_repo2 = SessionRepository(db_manager2)
        chat_repo2 = ChatHistoryRepository(db_manager2)
        subject_repo2 = SubjectRepository(db_manager2)
        book_repo2 = BookRepository(db_manager2)
        
        # Verify user persists
        retrieved_user = user_repo2.get_user_by_id(user_id)
        assert retrieved_user is not None, "User should persist after restart"
        assert retrieved_user.username == original_user['username']
        assert retrieved_user.password_hash == original_user['password_hash']
        assert retrieved_user.role == original_user['role']
        assert retrieved_user.full_name == original_user['full_name']
        
        # Verify user can also be retrieved by username
        retrieved_user_by_name = user_repo2.get_user_by_username(username)
        assert retrieved_user_by_name is not None
        assert retrieved_user_by_name.id == user_id
        
        # Verify session persists
        retrieved_session = session_repo2.get_session_by_token(token)
        assert retrieved_session is not None, "Session should persist after restart"
        assert retrieved_session.user_id == original_session['user_id']
        assert retrieved_session.token == original_session['token']
        # Note: expires_at comparison should be close but may have microsecond differences
        
        # Verify chat history persists
        user_history = chat_repo2.get_user_history(user_id, limit=10)
        assert len(user_history) > 0, "Chat history should persist after restart"
        
        # Find our specific chat
        retrieved_chat = None
        for chat_entry in user_history:
            if chat_entry.id == chat_id:
                retrieved_chat = chat_entry
                break
        
        assert retrieved_chat is not None, "Specific chat should be found"
        assert retrieved_chat.question == original_chat['question']
        assert retrieved_chat.response == original_chat['response']
        assert retrieved_chat.user_id == original_chat['user_id']
        assert retrieved_chat.subject_id == original_chat['subject_id']
        assert retrieved_chat.confidence == original_chat['confidence']
        
        # Verify subject persists
        retrieved_subject = subject_repo2.get_subject_by_id(subject_id)
        assert retrieved_subject is not None, "Subject should persist after restart"
        assert retrieved_subject.name == original_subject['name']
        assert retrieved_subject.code == original_subject['code']
        assert retrieved_subject.grade == original_subject['grade']
        
        # Verify book persists
        retrieved_book = book_repo2.get_book_by_id(book_id)
        assert retrieved_book is not None, "Book should persist after restart"
        assert retrieved_book.title == original_book['title']
        assert retrieved_book.filename == original_book['filename']
        assert retrieved_book.vkp_version == original_book['vkp_version']
        assert retrieved_book.subject_id == original_book['subject_id']
        
    finally:
        # Cleanup: Delete test data
        try:
            # Delete in reverse order of dependencies
            chat_repo2.db.execute_query(
                "DELETE FROM chat_history WHERE id = %(id)s",
                {'id': chat_id}
            )
            book_repo2.delete_book(book_id)
            subject_repo2.delete_subject(subject_id)
            session_repo2.delete_session(token)
            user_repo2.delete_user(user_id)
        except Exception as e:
            # Log cleanup errors but don't fail the test
            print(f"Cleanup error: {e}")
        finally:
            db_manager2.close()


@settings(max_examples=100)
@given(
    num_users=st.integers(min_value=1, max_value=10),
    num_chats_per_user=st.integers(min_value=1, max_value=5)
)
def test_multiple_records_persist_across_restarts(num_users, num_chats_per_user):
    """
    Property: Multiple users and their associated data should all persist across restarts.
    
    This test verifies that the database correctly handles multiple records and
    maintains referential integrity across restarts.
    
    **Validates: Requirements 3.3**
    """
    connection_string = get_db_connection_string()
    
    # Phase 1: Create multiple users and chats
    db_manager1 = DatabaseManager(connection_string)
    created_user_ids = []
    created_chat_ids = []
    
    try:
        user_repo1 = UserRepository(db_manager1)
        chat_repo1 = ChatHistoryRepository(db_manager1)
        
        # Create multiple users
        for i in range(num_users):
            user = user_repo1.create_user(
                username=f"testuser_{i}_{datetime.now().timestamp()}",
                password="password123",
                role="siswa",
                full_name=f"Test User {i}"
            )
            created_user_ids.append(user.id)
            
            # Create multiple chats for each user
            for j in range(num_chats_per_user):
                chat = chat_repo1.save_chat(
                    user_id=user.id,
                    subject_id=None,
                    question=f"Question {j} from user {i}",
                    response=f"Response {j} for user {i}",
                    confidence=0.9
                )
                created_chat_ids.append(chat.id)
        
        # Store expected counts
        expected_user_count = len(created_user_ids)
        expected_chat_count = len(created_chat_ids)
        
    finally:
        db_manager1.close()
    
    # Phase 2: Simulate restart and verify all data persists
    db_manager2 = simulate_restart(connection_string)
    
    try:
        user_repo2 = UserRepository(db_manager2)
        chat_repo2 = ChatHistoryRepository(db_manager2)
        
        # Verify all users persist
        persisted_users = 0
        for user_id in created_user_ids:
            user = user_repo2.get_user_by_id(user_id)
            if user is not None:
                persisted_users += 1
        
        assert persisted_users == expected_user_count, \
            f"All {expected_user_count} users should persist, but only {persisted_users} found"
        
        # Verify all chats persist
        persisted_chats = 0
        for user_id in created_user_ids:
            user_chats = chat_repo2.get_user_history(user_id, limit=100)
            persisted_chats += len(user_chats)
        
        assert persisted_chats == expected_chat_count, \
            f"All {expected_chat_count} chats should persist, but only {persisted_chats} found"
        
    finally:
        # Cleanup
        try:
            for user_id in created_user_ids:
                user_repo2.delete_user(user_id)  # Cascade deletes chats
        except Exception as e:
            print(f"Cleanup error: {e}")
        finally:
            db_manager2.close()


@settings(max_examples=50)
@given(
    username=st.text(
        min_size=3, 
        max_size=50, 
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            blacklist_characters=' '
        )
    ),
    num_restarts=st.integers(min_value=2, max_value=5)
)
def test_data_persists_across_multiple_restarts(username, num_restarts):
    """
    Property: Data should persist across multiple consecutive restarts.
    
    This test verifies that data remains intact even after multiple restart cycles,
    ensuring long-term persistence reliability.
    
    **Validates: Requirements 3.3**
    """
    connection_string = get_db_connection_string()
    
    # Create initial data
    db_manager = DatabaseManager(connection_string)
    
    try:
        user_repo = UserRepository(db_manager)
        user = user_repo.create_user(
            username=username,
            password="password123",
            role="siswa",
            full_name="Test User"
        )
        user_id = user.id
        original_username = user.username
    finally:
        db_manager.close()
    
    # Simulate multiple restarts
    try:
        for restart_num in range(num_restarts):
            db_manager = simulate_restart(connection_string)
            
            try:
                user_repo = UserRepository(db_manager)
                
                # Verify user still exists
                retrieved_user = user_repo.get_user_by_id(user_id)
                assert retrieved_user is not None, \
                    f"User should persist after restart {restart_num + 1}"
                assert retrieved_user.username == original_username, \
                    f"Username should remain unchanged after restart {restart_num + 1}"
            finally:
                db_manager.close()
    finally:
        # Cleanup
        db_manager = DatabaseManager(connection_string)
        try:
            user_repo = UserRepository(db_manager)
            user_repo.delete_user(user_id)
        except Exception as e:
            print(f"Cleanup error: {e}")
        finally:
            db_manager.close()
