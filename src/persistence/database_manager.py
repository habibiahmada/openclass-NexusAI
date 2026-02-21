"""
DatabaseManager - Core database operations and connection management

This module provides the DatabaseManager class for PostgreSQL connection pooling,
query execution, transaction management, and health checks.

Requirements: 3.1, 3.4, 3.5
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor

# Connection pool configuration
POOL_SIZE = 10
MAX_OVERFLOW = 20
POOL_TIMEOUT = 30
POOL_RECYCLE = 3600

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Core database operations and connection management.
    
    Provides connection pooling, query execution, transaction support,
    and health check capabilities for PostgreSQL database.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize DatabaseManager with connection pooling.
        
        Args:
            connection_string: PostgreSQL connection string
                Format: "postgresql://user:password@host:port/database"
        
        Raises:
            psycopg2.Error: If connection pool creation fails
        """
        self.connection_string = connection_string
        self._pool: Optional[pool.ThreadedConnectionPool] = None
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """
        Initialize the connection pool with configured settings.
        
        Creates a ThreadedConnectionPool with POOL_SIZE minimum connections
        and POOL_SIZE + MAX_OVERFLOW maximum connections.
        """
        try:
            self._pool = pool.ThreadedConnectionPool(
                minconn=POOL_SIZE,
                maxconn=POOL_SIZE + MAX_OVERFLOW,
                dsn=self.connection_string,
                connect_timeout=POOL_TIMEOUT
            )
            logger.info(
                f"Database connection pool initialized: "
                f"min={POOL_SIZE}, max={POOL_SIZE + MAX_OVERFLOW}"
            )
        except psycopg2.Error as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool using context manager.
        
        Yields:
            psycopg2.connection: Database connection from pool
        
        Raises:
            psycopg2.Error: If connection cannot be obtained
        
        Example:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
        """
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")
        
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._pool.putconn(conn)
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None,
        fetch_one: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL query string (use %(name)s for parameters)
            params: Dictionary of query parameters
            fetch_one: If True, return only first result
        
        Returns:
            List of dictionaries (rows) or single dictionary if fetch_one=True
            None if no results
        
        Raises:
            psycopg2.Error: If query execution fails
        
        Example:
            results = db_manager.execute_query(
                "SELECT * FROM users WHERE username = %(username)s",
                {"username": "student1"}
            )
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                try:
                    cursor.execute(query, params or {})
                    
                    # Check if this is a write operation (INSERT, UPDATE, DELETE)
                    query_upper = query.strip().upper()
                    if query_upper.startswith(('INSERT', 'UPDATE', 'DELETE')):
                        conn.commit()
                    
                    if fetch_one:
                        result = cursor.fetchone()
                        return dict(result) if result else None
                    
                    results = cursor.fetchall()
                    return [dict(row) for row in results] if results else []
                
                except psycopg2.Error as e:
                    logger.error(f"Query execution failed: {e}")
                    logger.error(f"Query: {query}")
                    logger.error(f"Params: {params}")
                    raise
    
    def execute_transaction(
        self, 
        queries: List[Tuple[str, Optional[Dict[str, Any]]]]
    ) -> bool:
        """
        Execute multiple queries in a single transaction.
        
        All queries are executed atomically - if any query fails,
        all changes are rolled back.
        
        Args:
            queries: List of (query, params) tuples
        
        Returns:
            True if transaction succeeded, False otherwise
        
        Raises:
            psycopg2.Error: If transaction fails
        
        Example:
            success = db_manager.execute_transaction([
                ("INSERT INTO users (username) VALUES (%(username)s)", 
                 {"username": "student1"}),
                ("INSERT INTO sessions (user_id, token) VALUES (%(user_id)s, %(token)s)",
                 {"user_id": 1, "token": "abc123"})
            ])
        """
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    for query, params in queries:
                        cursor.execute(query, params or {})
                
                conn.commit()
                logger.debug(f"Transaction completed: {len(queries)} queries")
                return True
            
            except psycopg2.Error as e:
                conn.rollback()
                logger.error(f"Transaction failed, rolled back: {e}")
                raise
    
    def health_check(self) -> bool:
        """
        Check database connectivity and health.
        
        Performs a simple query to verify the database is accessible
        and responding.
        
        Returns:
            True if database is healthy, False otherwise
        
        Example:
            if db_manager.health_check():
                print("Database is healthy")
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    
                    if result and result[0] == 1:
                        logger.debug("Database health check passed")
                        return True
                    
                    logger.warning("Database health check returned unexpected result")
                    return False
        
        except psycopg2.Error as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def close(self) -> None:
        """
        Close all connections in the pool.
        
        Should be called when shutting down the application.
        """
        if self._pool:
            self._pool.closeall()
            logger.info("Database connection pool closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close pool."""
        self.close()
