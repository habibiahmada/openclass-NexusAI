"""
Unit tests for DatabaseManager class

Tests connection pooling, query execution, transaction management,
and health check functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import psycopg2
from psycopg2 import pool

from src.persistence.database_manager import DatabaseManager, POOL_SIZE, MAX_OVERFLOW


class TestDatabaseManager:
    """Test suite for DatabaseManager class."""
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_init_creates_connection_pool(self, mock_pool_class):
        """Test that __init__ creates a connection pool with correct parameters."""
        connection_string = "postgresql://user:pass@localhost:5432/testdb"
        
        db_manager = DatabaseManager(connection_string)
        
        mock_pool_class.assert_called_once_with(
            minconn=POOL_SIZE,
            maxconn=POOL_SIZE + MAX_OVERFLOW,
            dsn=connection_string,
            connect_timeout=30
        )
        assert db_manager._pool is not None
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_init_raises_on_pool_creation_failure(self, mock_pool_class):
        """Test that __init__ raises exception if pool creation fails."""
        mock_pool_class.side_effect = psycopg2.Error("Connection failed")
        
        with pytest.raises(psycopg2.Error):
            DatabaseManager("postgresql://invalid")
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_get_connection_returns_connection(self, mock_pool_class):
        """Test that get_connection returns a connection from pool."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool
        
        db_manager = DatabaseManager("postgresql://test")
        
        with db_manager.get_connection() as conn:
            assert conn == mock_conn
        
        mock_pool.getconn.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_get_connection_returns_connection_on_error(self, mock_pool_class):
        """Test that get_connection returns connection to pool even on error."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool
        
        db_manager = DatabaseManager("postgresql://test")
        
        try:
            with db_manager.get_connection() as conn:
                raise psycopg2.Error("Test error")
        except psycopg2.Error:
            pass
        
        mock_pool.putconn.assert_called_once_with(mock_conn)
        mock_conn.rollback.assert_called_once()
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_execute_query_returns_results(self, mock_pool_class):
        """Test that execute_query returns query results as list of dicts."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock query results
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'username': 'student1'},
            {'id': 2, 'username': 'student2'}
        ]
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool
        
        db_manager = DatabaseManager("postgresql://test")
        
        results = db_manager.execute_query(
            "SELECT * FROM users WHERE role = %(role)s",
            {"role": "siswa"}
        )
        
        assert len(results) == 2
        assert results[0]['username'] == 'student1'
        mock_cursor.execute.assert_called_once()
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_execute_query_fetch_one(self, mock_pool_class):
        """Test that execute_query with fetch_one returns single result."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_cursor.fetchone.return_value = {'id': 1, 'username': 'student1'}
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool
        
        db_manager = DatabaseManager("postgresql://test")
        
        result = db_manager.execute_query(
            "SELECT * FROM users WHERE id = %(id)s",
            {"id": 1},
            fetch_one=True
        )
        
        assert result['username'] == 'student1'
        mock_cursor.fetchone.assert_called_once()
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_execute_query_returns_empty_list_on_no_results(self, mock_pool_class):
        """Test that execute_query returns empty list when no results."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_cursor.fetchall.return_value = []
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool
        
        db_manager = DatabaseManager("postgresql://test")
        
        results = db_manager.execute_query("SELECT * FROM users WHERE id = -1")
        
        assert results == []
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_execute_query_raises_on_error(self, mock_pool_class):
        """Test that execute_query raises exception on query error."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_cursor.execute.side_effect = psycopg2.Error("Query failed")
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool
        
        db_manager = DatabaseManager("postgresql://test")
        
        with pytest.raises(psycopg2.Error):
            db_manager.execute_query("INVALID SQL")
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_execute_transaction_commits_all_queries(self, mock_pool_class):
        """Test that execute_transaction commits all queries atomically."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool
        
        db_manager = DatabaseManager("postgresql://test")
        
        queries = [
            ("INSERT INTO users (username) VALUES (%(username)s)", {"username": "test1"}),
            ("INSERT INTO users (username) VALUES (%(username)s)", {"username": "test2"})
        ]
        
        result = db_manager.execute_transaction(queries)
        
        assert result is True
        assert mock_cursor.execute.call_count == 2
        mock_conn.commit.assert_called_once()
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_execute_transaction_rolls_back_on_error(self, mock_pool_class):
        """Test that execute_transaction rolls back on error."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # First query succeeds, second fails
        mock_cursor.execute.side_effect = [None, psycopg2.Error("Query failed")]
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool
        
        db_manager = DatabaseManager("postgresql://test")
        
        queries = [
            ("INSERT INTO users (username) VALUES ('test1')", None),
            ("INVALID SQL", None)
        ]
        
        with pytest.raises(psycopg2.Error):
            db_manager.execute_transaction(queries)
        
        # Rollback is called twice: once in execute_transaction, once in get_connection
        assert mock_conn.rollback.call_count >= 1
        mock_conn.commit.assert_not_called()
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_health_check_returns_true_on_success(self, mock_pool_class):
        """Test that health_check returns True when database is healthy."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_cursor.fetchone.return_value = (1,)
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool
        
        db_manager = DatabaseManager("postgresql://test")
        
        result = db_manager.health_check()
        
        assert result is True
        mock_cursor.execute.assert_called_once_with("SELECT 1")
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_health_check_returns_false_on_error(self, mock_pool_class):
        """Test that health_check returns False on database error."""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        
        mock_conn.cursor.side_effect = psycopg2.Error("Connection failed")
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool
        
        db_manager = DatabaseManager("postgresql://test")
        
        result = db_manager.health_check()
        
        assert result is False
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_close_closes_pool(self, mock_pool_class):
        """Test that close() closes all connections in pool."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        db_manager = DatabaseManager("postgresql://test")
        db_manager.close()
        
        mock_pool.closeall.assert_called_once()
    
    @patch('src.persistence.database_manager.pool.ThreadedConnectionPool')
    def test_context_manager_closes_pool(self, mock_pool_class):
        """Test that context manager closes pool on exit."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        with DatabaseManager("postgresql://test") as db_manager:
            pass
        
        mock_pool.closeall.assert_called_once()
