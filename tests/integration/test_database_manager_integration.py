"""
Integration tests for DatabaseManager

These tests verify DatabaseManager works with a real PostgreSQL database.
Requires PostgreSQL to be running and accessible.
"""

import pytest
import os
from src.persistence.database_manager import DatabaseManager


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


def test_health_check_with_real_database(db_manager):
    """Test health check with real database connection."""
    result = db_manager.health_check()
    assert result is True


def test_execute_query_with_real_database(db_manager):
    """Test query execution with real database."""
    # Simple query that should work on any PostgreSQL database
    result = db_manager.execute_query("SELECT 1 as test_value", fetch_one=True)
    assert result is not None
    assert result['test_value'] == 1


def test_connection_pool_reuse(db_manager):
    """Test that connection pool reuses connections."""
    # Execute multiple queries to verify pool works
    for i in range(15):  # More than POOL_SIZE to test overflow
        result = db_manager.execute_query("SELECT %(num)s as num", {"num": i}, fetch_one=True)
        assert result['num'] == i
