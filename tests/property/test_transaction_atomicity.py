"""
Property-based tests for database transaction atomicity

This module tests that database transactions are atomic - either all operations
succeed and are committed, or all fail and are rolled back, maintaining data integrity.

Feature: architecture-alignment-refactoring
Property 4: Database Transaction Atomicity
**Validates: Requirements 3.4**
"""

import os
import pytest
from hypothesis import given, settings, strategies as st
from datetime import datetime

from src.persistence.database_manager import DatabaseManager
from src.persistence.user_repository import UserRepository
from src.persistence.session_repository import SessionRepository
from src.persistence.chat_history_repository import ChatHistoryRepository


# Skip these tests if PostgreSQL is not available
pytestmark = pytest.mark.skipif(
    not os.getenv('TEST_DATABASE_URL'),
    reason="PostgreSQL test database not configured. Set TEST_DATABASE_URL environment variable."
)


def get_db_connection_string():
    """Get database connection string from environment."""
    return os.getenv('TEST_DATABASE_URL')


# Property 4: Database Transaction Atomicity
# **Validates: Requirements 3.4**
@settings(max_examples=100)
@given(
    username1=st.text(
        min_size=3, 
        max_size=50, 
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            blacklist_characters=' '
        )
    ),
    username2=st.text(
        min_size=3, 
        max_size=50, 
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            blacklist_characters=' '
        )
    ),
    password=st.text(min_size=6, max_size=50),
    full_name=st.text(min_size=3, max_size=100)
)
def test_transaction_all_or_nothing(username1, username2, password, full_name):
    """
    Property: For any set of database operations in a transaction, either all operations
    succeed and are committed, or all fail and are rolled back.
    
    This test verifies that when a transaction contains multiple INSERT operations
    and one fails (e.g., due to constraint violation), none of the operations are
    committed to the database.
    
    **Validates: Requirements 3.4**
    """
    connection_string = get_db_connection_string()
    db_manager = DatabaseManager(connection_string)
    
    try:
        # First, create a user to cause a duplicate key violation later
        user_repo = UserRepository(db_manager)
        existing_user = user_repo.create_user(
            username=username1,
            password=password,
            role="siswa",
            full_name=full_name
        )
        existing_user_id = existing_user.id
        
        # Count users before transaction
        initial_count_result = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM users"
        )
        initial_count = initial_count_result[0]['count']
        
        # Attempt a transaction that should fail
        # First query succeeds, second query fails due to duplicate username
        try:
            db_manager.execute_transaction([
                # This should succeed (new username)
                (
                    "INSERT INTO users (username, password_hash, role, full_name) "
                    "VALUES (%(username)s, %(password)s, %(role)s, %(full_name)s)",
                    {
                        "username": username2,
                        "password": password,
                        "role": "siswa",
                        "full_name": full_name
                    }
                ),
                # This should fail (duplicate username)
                (
                    "INSERT INTO users (username, password_hash, role, full_name) "
                    "VALUES (%(username)s, %(password)s, %(role)s, %(full_name)s)",
                    {
                        "username": username1,  # Duplicate!
                        "password": password,
                        "role": "siswa",
                        "full_name": full_name
                    }
                )
            ])
            # If we reach here, the transaction unexpectedly succeeded
            transaction_succeeded = True
        except Exception:
            # Transaction failed as expected
            transaction_succeeded = False
        
        # Verify atomicity: count should be unchanged
        final_count_result = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM users"
        )
        final_count = final_count_result[0]['count']
        
        # The transaction should have failed, so count should be unchanged
        assert final_count == initial_count, \
            f"Transaction should be atomic: count was {initial_count}, now {final_count}. " \
            f"Transaction succeeded: {transaction_succeeded}"
        
        # Verify username2 was NOT inserted (rollback worked)
        user2 = user_repo.get_user_by_username(username2)
        assert user2 is None, \
            "Second user should not exist after transaction rollback"
        
    finally:
        # Cleanup
        try:
            user_repo.delete_user(existing_user_id)
        except Exception as e:
            print(f"Cleanup error: {e}")
        finally:
            db_manager.close()


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
    token=st.text(min_size=8, max_size=64),
    question=st.text(min_size=10, max_size=500),
    response=st.text(min_size=10, max_size=1000)
)
def test_transaction_rollback_on_foreign_key_violation(
    username, password, full_name, token, question, response
):
    """
    Property: When a transaction fails due to foreign key constraint violation,
    all operations in the transaction should be rolled back.
    
    This test verifies that if we try to insert a session and chat history
    for a non-existent user in a transaction, neither record is created.
    
    **Validates: Requirements 3.4**
    """
    connection_string = get_db_connection_string()
    db_manager = DatabaseManager(connection_string)
    
    try:
        # Use a non-existent user_id
        non_existent_user_id = 999999999
        
        # Count sessions and chats before transaction
        session_count_before = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM sessions"
        )[0]['count']
        
        chat_count_before = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM chat_history"
        )[0]['count']
        
        # Attempt transaction that should fail due to foreign key violation
        try:
            db_manager.execute_transaction([
                # This should fail - user_id doesn't exist
                (
                    "INSERT INTO sessions (user_id, token, expires_at) "
                    "VALUES (%(user_id)s, %(token)s, NOW() + INTERVAL '24 hours')",
                    {
                        "user_id": non_existent_user_id,
                        "token": token
                    }
                ),
                # This should also fail
                (
                    "INSERT INTO chat_history (user_id, subject_id, question, response, confidence) "
                    "VALUES (%(user_id)s, NULL, %(question)s, %(response)s, 0.9)",
                    {
                        "user_id": non_existent_user_id,
                        "question": question,
                        "response": response
                    }
                )
            ])
            transaction_succeeded = True
        except Exception:
            # Transaction failed as expected
            transaction_succeeded = False
        
        # Verify atomicity: counts should be unchanged
        session_count_after = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM sessions"
        )[0]['count']
        
        chat_count_after = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM chat_history"
        )[0]['count']
        
        assert session_count_after == session_count_before, \
            f"Session count should be unchanged after failed transaction. " \
            f"Before: {session_count_before}, After: {session_count_after}"
        
        assert chat_count_after == chat_count_before, \
            f"Chat count should be unchanged after failed transaction. " \
            f"Before: {chat_count_before}, After: {chat_count_after}"
        
        assert not transaction_succeeded, \
            "Transaction should have failed due to foreign key constraint"
        
    finally:
        db_manager.close()


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
    num_operations=st.integers(min_value=2, max_value=5)
)
def test_transaction_success_commits_all_operations(
    username, password, full_name, num_operations
):
    """
    Property: When all operations in a transaction succeed, all changes should be
    committed to the database.
    
    This test verifies that successful transactions commit all operations atomically.
    
    **Validates: Requirements 3.4**
    """
    connection_string = get_db_connection_string()
    db_manager = DatabaseManager(connection_string)
    user_repo = UserRepository(db_manager)
    created_user_ids = []
    
    try:
        # Count users before transaction
        initial_count = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM users"
        )[0]['count']
        
        # Build transaction with multiple successful inserts
        queries = []
        for i in range(num_operations):
            queries.append((
                "INSERT INTO users (username, password_hash, role, full_name) "
                "VALUES (%(username)s, %(password)s, %(role)s, %(full_name)s)",
                {
                    "username": f"{username}_{i}_{datetime.now().timestamp()}",
                    "password": password,
                    "role": "siswa",
                    "full_name": f"{full_name} {i}"
                }
            ))
        
        # Execute transaction - should succeed
        success = db_manager.execute_transaction(queries)
        
        assert success, "Transaction should succeed when all operations are valid"
        
        # Verify all operations were committed
        final_count = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM users"
        )[0]['count']
        
        assert final_count == initial_count + num_operations, \
            f"All {num_operations} users should be inserted. " \
            f"Expected {initial_count + num_operations}, got {final_count}"
        
        # Verify each user exists
        for i in range(num_operations):
            username_to_check = f"{username}_{i}_{datetime.now().timestamp()}"
            # Note: timestamp might differ slightly, so we check by pattern
            users = db_manager.execute_query(
                "SELECT * FROM users WHERE username LIKE %(pattern)s",
                {"pattern": f"{username}_{i}_%"}
            )
            assert len(users) > 0, f"User {i} should exist after successful transaction"
            if users:
                created_user_ids.append(users[0]['id'])
        
    finally:
        # Cleanup
        try:
            for user_id in created_user_ids:
                user_repo.delete_user(user_id)
        except Exception as e:
            print(f"Cleanup error: {e}")
        finally:
            db_manager.close()


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
    password=st.text(min_size=6, max_size=50),
    full_name=st.text(min_size=3, max_size=100),
    token=st.text(min_size=8, max_size=64)
)
def test_transaction_rollback_preserves_existing_data(
    username, password, full_name, token
):
    """
    Property: When a transaction is rolled back, existing data should remain unchanged.
    
    This test verifies that a failed transaction doesn't corrupt or modify existing
    database records.
    
    **Validates: Requirements 3.4**
    """
    connection_string = get_db_connection_string()
    db_manager = DatabaseManager(connection_string)
    user_repo = UserRepository(db_manager)
    session_repo = SessionRepository(db_manager)
    
    try:
        # Create initial user and session
        user = user_repo.create_user(
            username=username,
            password=password,
            role="siswa",
            full_name=full_name
        )
        user_id = user.id
        
        session = session_repo.create_session(
            user_id=user_id,
            token=token,
            expires_hours=24
        )
        
        # Store original data
        original_user = user_repo.get_user_by_id(user_id)
        original_session = session_repo.get_session_by_token(token)
        
        assert original_user is not None
        assert original_session is not None
        
        # Attempt a failing transaction (duplicate username)
        try:
            db_manager.execute_transaction([
                (
                    "UPDATE users SET full_name = %(new_name)s WHERE id = %(user_id)s",
                    {"new_name": "Modified Name", "user_id": user_id}
                ),
                (
                    "INSERT INTO users (username, password_hash, role, full_name) "
                    "VALUES (%(username)s, %(password)s, %(role)s, %(full_name)s)",
                    {
                        "username": username,  # Duplicate!
                        "password": password,
                        "role": "siswa",
                        "full_name": full_name
                    }
                )
            ])
        except Exception:
            # Transaction failed as expected
            pass
        
        # Verify original data is unchanged
        current_user = user_repo.get_user_by_id(user_id)
        current_session = session_repo.get_session_by_token(token)
        
        assert current_user is not None, "User should still exist"
        assert current_user.full_name == original_user.full_name, \
            "User full_name should be unchanged after rollback"
        assert current_user.username == original_user.username, \
            "Username should be unchanged after rollback"
        
        assert current_session is not None, "Session should still exist"
        assert current_session.token == original_session.token, \
            "Session token should be unchanged after rollback"
        
    finally:
        # Cleanup
        try:
            session_repo.delete_session(token)
            user_repo.delete_user(user_id)
        except Exception as e:
            print(f"Cleanup error: {e}")
        finally:
            db_manager.close()


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
    password=st.text(min_size=6, max_size=50),
    full_name=st.text(min_size=3, max_size=100)
)
def test_transaction_isolation_between_connections(username, password, full_name):
    """
    Property: Transactions should be isolated - uncommitted changes in one transaction
    should not be visible to other connections.
    
    This test verifies transaction isolation by checking that changes are not visible
    until committed.
    
    **Validates: Requirements 3.4**
    """
    connection_string = get_db_connection_string()
    db_manager1 = DatabaseManager(connection_string)
    db_manager2 = DatabaseManager(connection_string)
    
    try:
        # Connection 1: Start a transaction but don't commit yet
        with db_manager1.get_connection() as conn1:
            with conn1.cursor() as cursor1:
                # Insert user but don't commit
                cursor1.execute(
                    "INSERT INTO users (username, password_hash, role, full_name) "
                    "VALUES (%(username)s, %(password)s, %(role)s, %(full_name)s) "
                    "RETURNING id",
                    {
                        "username": username,
                        "password": password,
                        "role": "siswa",
                        "full_name": full_name
                    }
                )
                result = cursor1.fetchone()
                user_id = result[0] if result else None
                
                # Connection 2: Try to read the uncommitted user
                user_from_conn2 = db_manager2.execute_query(
                    "SELECT * FROM users WHERE username = %(username)s",
                    {"username": username},
                    fetch_one=True
                )
                
                # Uncommitted data should NOT be visible to other connections
                assert user_from_conn2 is None, \
                    "Uncommitted transaction data should not be visible to other connections"
                
                # Now commit the transaction
                conn1.commit()
        
        # After commit, data should be visible
        user_after_commit = db_manager2.execute_query(
            "SELECT * FROM users WHERE username = %(username)s",
            {"username": username},
            fetch_one=True
        )
        
        assert user_after_commit is not None, \
            "Committed transaction data should be visible to other connections"
        assert user_after_commit['username'] == username
        
        # Cleanup
        if user_id:
            db_manager1.execute_query(
                "DELETE FROM users WHERE id = %(id)s",
                {"id": user_id}
            )
        
    finally:
        db_manager1.close()
        db_manager2.close()
