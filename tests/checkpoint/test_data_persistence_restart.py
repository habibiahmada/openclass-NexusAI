"""
Checkpoint Test: Verify Data Persists Across Server Restarts

This test verifies that data stored in PostgreSQL survives server restarts.
It creates test data, simulates a restart, and verifies the data is still present.

Requirements tested: 3.3 - Data must survive server restarts
"""

import pytest
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.persistence.database_manager import DatabaseManager
from src.persistence.user_repository import UserRepository
from src.persistence.session_repository import SessionRepository
from src.persistence.chat_history_repository import ChatHistoryRepository
from src.persistence.subject_repository import SubjectRepository
from src.persistence.book_repository import BookRepository


# Load environment variables
load_dotenv()


@pytest.fixture(scope="module")
def database_url():
    """Get database URL from environment."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        pytest.skip("DATABASE_URL not set - skipping persistence test")
    return db_url


@pytest.fixture(scope="module")
def test_data_ids():
    """Store IDs of created test data for verification."""
    return {}


class TestDataPersistenceAcrossRestarts:
    """Test that data persists across database connection restarts."""
    
    def test_01_create_test_data(self, database_url, test_data_ids):
        """
        Step 1: Create test data in database.
        
        This simulates the first server session where data is created.
        """
        # Create database manager and repositories
        db_manager = DatabaseManager(database_url)
        
        # Verify database is healthy
        assert db_manager.health_check(), "Database health check failed"
        
        user_repo = UserRepository(db_manager)
        session_repo = SessionRepository(db_manager)
        chat_repo = ChatHistoryRepository(db_manager)
        subject_repo = SubjectRepository(db_manager)
        book_repo = BookRepository(db_manager)
        
        # Create test user
        test_username = f"test_persist_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        user = user_repo.create_user(
            username=test_username,
            password="test_password_123",
            role="siswa",
            full_name="Test Persistence User"
        )
        assert user is not None
        test_data_ids['user_id'] = user.id
        test_data_ids['username'] = user.username
        print(f"✓ Created user: {user.username} (ID: {user.id})")
        
        # Create test session
        test_token = f"test_token_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        session = session_repo.create_session(
            user_id=user.id,
            token=test_token,
            expires_hours=24
        )
        assert session is not None
        test_data_ids['session_id'] = session.id
        test_data_ids['token'] = session.token
        print(f"✓ Created session: {session.token[:20]}... (ID: {session.id})")
        
        # Create test subject
        test_subject_code = f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        subject = subject_repo.create_subject(
            grade=10,
            name="Test Subject for Persistence",
            code=test_subject_code
        )
        assert subject is not None
        test_data_ids['subject_id'] = subject.id
        test_data_ids['subject_code'] = subject.code
        print(f"✓ Created subject: {subject.name} (ID: {subject.id})")
        
        # Create test book
        book = book_repo.create_book(
            subject_id=subject.id,
            title="Test Book for Persistence",
            filename=f"test_book_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf",
            vkp_version="1.0.0"
        )
        assert book is not None
        test_data_ids['book_id'] = book.id
        print(f"✓ Created book: {book.title} (ID: {book.id})")
        
        # Create test chat history
        chat = chat_repo.save_chat(
            user_id=user.id,
            subject_id=subject.id,
            question="Test question for persistence verification",
            response="Test response for persistence verification",
            confidence=0.95
        )
        assert chat is not None
        test_data_ids['chat_id'] = chat.id
        print(f"✓ Created chat history (ID: {chat.id})")
        
        # Close database connection (simulating server shutdown)
        db_manager.close()
        print("\n✓ Database connection closed (simulating server shutdown)")
        
        # Verify all IDs were stored
        assert 'user_id' in test_data_ids
        assert 'session_id' in test_data_ids
        assert 'subject_id' in test_data_ids
        assert 'book_id' in test_data_ids
        assert 'chat_id' in test_data_ids
        
        print(f"\n✓ Test data created successfully:")
        print(f"  - User ID: {test_data_ids['user_id']}")
        print(f"  - Session ID: {test_data_ids['session_id']}")
        print(f"  - Subject ID: {test_data_ids['subject_id']}")
        print(f"  - Book ID: {test_data_ids['book_id']}")
        print(f"  - Chat ID: {test_data_ids['chat_id']}")
    
    def test_02_verify_data_after_restart(self, database_url, test_data_ids):
        """
        Step 2: Verify data still exists after restart.
        
        This simulates a new server session after restart, creating new
        database connections and verifying the data persists.
        """
        # Verify test data was created in previous test
        assert 'user_id' in test_data_ids, "Test data not created in previous test"
        
        print("\n" + "="*60)
        print("SIMULATING SERVER RESTART")
        print("="*60)
        
        # Create NEW database manager and repositories (simulating restart)
        db_manager = DatabaseManager(database_url)
        
        # Verify database is healthy
        assert db_manager.health_check(), "Database health check failed after restart"
        print("✓ Database connection re-established")
        
        user_repo = UserRepository(db_manager)
        session_repo = SessionRepository(db_manager)
        chat_repo = ChatHistoryRepository(db_manager)
        subject_repo = SubjectRepository(db_manager)
        book_repo = BookRepository(db_manager)
        
        # Verify user persists
        user = user_repo.get_user_by_id(test_data_ids['user_id'])
        assert user is not None, "User not found after restart"
        assert user.username == test_data_ids['username']
        assert user.role == "siswa"
        assert user.full_name == "Test Persistence User"
        print(f"✓ User persisted: {user.username} (ID: {user.id})")
        
        # Verify session persists
        session = session_repo.get_session_by_token(test_data_ids['token'])
        assert session is not None, "Session not found after restart"
        assert session.user_id == test_data_ids['user_id']
        assert not session.is_expired()
        print(f"✓ Session persisted: {session.token[:20]}... (ID: {session.id})")
        
        # Verify subject persists
        subject = subject_repo.get_subject_by_id(test_data_ids['subject_id'])
        assert subject is not None, "Subject not found after restart"
        assert subject.code == test_data_ids['subject_code']
        assert subject.name == "Test Subject for Persistence"
        assert subject.grade == 10
        print(f"✓ Subject persisted: {subject.name} (ID: {subject.id})")
        
        # Verify book persists
        book = book_repo.get_book_by_id(test_data_ids['book_id'])
        assert book is not None, "Book not found after restart"
        assert book.subject_id == test_data_ids['subject_id']
        assert book.title == "Test Book for Persistence"
        assert book.vkp_version == "1.0.0"
        print(f"✓ Book persisted: {book.title} (ID: {book.id})")
        
        # Verify chat history persists
        user_history = chat_repo.get_user_history(user_id=test_data_ids['user_id'])
        assert len(user_history) > 0, "Chat history not found after restart"
        
        # Find our specific chat
        chat = next((c for c in user_history if c.id == test_data_ids['chat_id']), None)
        assert chat is not None, "Specific chat not found after restart"
        assert chat.question == "Test question for persistence verification"
        assert chat.response == "Test response for persistence verification"
        assert chat.confidence == 0.95
        assert chat.subject_id == test_data_ids['subject_id']
        print(f"✓ Chat history persisted (ID: {chat.id})")
        
        # Close database connection
        db_manager.close()
        print("\n✓ Database connection closed")
        
        print("\n" + "="*60)
        print("✓ ALL DATA PERSISTED SUCCESSFULLY ACROSS RESTART")
        print("="*60)
    
    def test_03_cleanup_test_data(self, database_url, test_data_ids):
        """
        Step 3: Clean up test data.
        
        Remove test data created during this test to keep database clean.
        """
        if not test_data_ids:
            pytest.skip("No test data to clean up")
        
        print("\n" + "="*60)
        print("CLEANING UP TEST DATA")
        print("="*60)
        
        # Create database manager and repositories
        db_manager = DatabaseManager(database_url)
        
        user_repo = UserRepository(db_manager)
        session_repo = SessionRepository(db_manager)
        subject_repo = SubjectRepository(db_manager)
        book_repo = BookRepository(db_manager)
        
        # Delete in reverse order (respecting foreign keys)
        # Chat history will be deleted by CASCADE when user is deleted
        
        if 'book_id' in test_data_ids:
            success = book_repo.delete_book(test_data_ids['book_id'])
            if success:
                print(f"✓ Deleted book (ID: {test_data_ids['book_id']})")
        
        if 'subject_id' in test_data_ids:
            success = subject_repo.delete_subject(test_data_ids['subject_id'])
            if success:
                print(f"✓ Deleted subject (ID: {test_data_ids['subject_id']})")
        
        if 'session_id' in test_data_ids:
            success = session_repo.delete_session(test_data_ids['token'])
            if success:
                print(f"✓ Deleted session (ID: {test_data_ids['session_id']})")
        
        if 'user_id' in test_data_ids:
            success = user_repo.delete_user(test_data_ids['user_id'])
            if success:
                print(f"✓ Deleted user (ID: {test_data_ids['user_id']})")
        
        db_manager.close()
        print("\n✓ Test data cleanup complete")


class TestMultipleRestartCycles:
    """Test data persists across multiple restart cycles."""
    
    def test_data_survives_multiple_restarts(self, database_url):
        """
        Test that data survives multiple connection open/close cycles.
        
        This simulates multiple server restarts in succession.
        """
        test_username = f"test_multi_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        user_id = None
        
        try:
            # Cycle 1: Create data
            db_manager = DatabaseManager(database_url)
            user_repo = UserRepository(db_manager)
            
            user = user_repo.create_user(
                username=test_username,
                password="test123",
                role="siswa"
            )
            user_id = user.id
            db_manager.close()
            print(f"✓ Cycle 1: Created user (ID: {user_id})")
            
            # Cycle 2: Verify and update
            db_manager = DatabaseManager(database_url)
            user_repo = UserRepository(db_manager)
            
            user = user_repo.get_user_by_id(user_id)
            assert user is not None
            success = user_repo.update_user(user_id, {'full_name': 'Updated Name'})
            assert success
            db_manager.close()
            print(f"✓ Cycle 2: Verified and updated user")
            
            # Cycle 3: Verify update persisted
            db_manager = DatabaseManager(database_url)
            user_repo = UserRepository(db_manager)
            
            user = user_repo.get_user_by_id(user_id)
            assert user is not None
            assert user.full_name == 'Updated Name'
            db_manager.close()
            print(f"✓ Cycle 3: Verified update persisted")
            
            # Cycle 4: Final verification
            db_manager = DatabaseManager(database_url)
            user_repo = UserRepository(db_manager)
            
            user = user_repo.get_user_by_id(user_id)
            assert user is not None
            assert user.username == test_username
            assert user.full_name == 'Updated Name'
            db_manager.close()
            print(f"✓ Cycle 4: Final verification successful")
            
            print("\n✓ Data survived 4 restart cycles")
            
        finally:
            # Cleanup
            if user_id:
                db_manager = DatabaseManager(database_url)
                user_repo = UserRepository(db_manager)
                user_repo.delete_user(user_id)
                db_manager.close()
                print(f"✓ Cleanup: Deleted test user (ID: {user_id})")


class TestConcurrentConnectionHandling:
    """Test that multiple connections can access persisted data."""
    
    def test_multiple_connections_see_same_data(self, database_url):
        """
        Test that multiple database connections see the same persisted data.
        
        This simulates multiple server instances or concurrent requests.
        """
        test_username = f"test_concurrent_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        user_id = None
        
        try:
            # Connection 1: Create data
            db1 = DatabaseManager(database_url)
            user_repo1 = UserRepository(db1)
            
            user = user_repo1.create_user(
                username=test_username,
                password="test123",
                role="siswa",
                full_name="Concurrent Test"
            )
            user_id = user.id
            print(f"✓ Connection 1: Created user (ID: {user_id})")
            
            # Connection 2: Read same data (while connection 1 is still open)
            db2 = DatabaseManager(database_url)
            user_repo2 = UserRepository(db2)
            
            user2 = user_repo2.get_user_by_id(user_id)
            assert user2 is not None
            assert user2.username == test_username
            assert user2.full_name == "Concurrent Test"
            print(f"✓ Connection 2: Read same user data")
            
            # Connection 3: Another concurrent read
            db3 = DatabaseManager(database_url)
            user_repo3 = UserRepository(db3)
            
            user3 = user_repo3.get_user_by_id(user_id)
            assert user3 is not None
            assert user3.username == test_username
            print(f"✓ Connection 3: Read same user data")
            
            # Close all connections
            db1.close()
            db2.close()
            db3.close()
            print("✓ All connections closed")
            
            # New connection: Verify data still exists
            db4 = DatabaseManager(database_url)
            user_repo4 = UserRepository(db4)
            
            user4 = user_repo4.get_user_by_id(user_id)
            assert user4 is not None
            assert user4.username == test_username
            db4.close()
            print("✓ Data persisted after all connections closed")
            
        finally:
            # Cleanup
            if user_id:
                db_cleanup = DatabaseManager(database_url)
                user_repo_cleanup = UserRepository(db_cleanup)
                user_repo_cleanup.delete_user(user_id)
                db_cleanup.close()
                print(f"✓ Cleanup: Deleted test user (ID: {user_id})")


if __name__ == "__main__":
    """
    Run this test standalone to verify data persistence.
    
    Usage:
        python tests/checkpoint/test_data_persistence_restart.py
    """
    pytest.main([__file__, "-v", "-s"])
