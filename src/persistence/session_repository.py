"""
SessionRepository - Session management operations

This module provides the SessionRepository class for managing user sessions,
including creation, retrieval, deletion, and automatic expiration cleanup.

Requirements: 3.1
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class Session:
    """
    Session data model representing an authenticated user session.
    
    Attributes:
        id: Unique session identifier
        user_id: ID of the user who owns this session
        token: Unique authentication token
        expires_at: Session expiration timestamp
        created_at: Session creation timestamp
    """
    
    def __init__(
        self,
        id: int,
        user_id: int,
        token: str,
        expires_at: datetime,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Session object to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'expires_at': self.expires_at,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create Session object from dictionary."""
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            token=data['token'],
            expires_at=data['expires_at'],
            created_at=data.get('created_at')
        )
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now() > self.expires_at
    
    def __repr__(self) -> str:
        return f"Session(id={self.id}, user_id={self.user_id}, token='{self.token[:8]}...', expires_at={self.expires_at})"


class SessionRepository:
    """
    Repository for session management operations.
    
    Provides methods for creating, retrieving, and deleting user sessions
    with automatic 24-hour expiration as specified in requirements.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize SessionRepository with database manager.
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
    
    def create_session(
        self, 
        user_id: int, 
        token: str, 
        expires_hours: int = 24
    ) -> Session:
        """
        Create a new user session.
        
        Args:
            user_id: ID of the user for this session
            token: Unique authentication token
            expires_hours: Number of hours until session expires (default: 24)
        
        Returns:
            Created Session object
        
        Raises:
            ValueError: If validation fails
            psycopg2.IntegrityError: If token already exists
            psycopg2.Error: If database operation fails
        
        Example:
            session = session_repo.create_session(
                user_id=1,
                token="abc123def456",
                expires_hours=24
            )
        """
        # Validate input
        if not token or len(token) < 8:
            raise ValueError("Token must be at least 8 characters long")
        
        if expires_hours <= 0:
            raise ValueError("Expiration hours must be positive")
        
        # Calculate expiration timestamp
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        # Insert session
        query = """
            INSERT INTO sessions (user_id, token, expires_at)
            VALUES (%(user_id)s, %(token)s, %(expires_at)s)
            RETURNING id, user_id, token, expires_at, created_at
        """
        
        params = {
            'user_id': user_id,
            'token': token,
            'expires_at': expires_at
        }
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                session = Session.from_dict(result)
                logger.info(f"Created session for user_id={user_id}, expires at {expires_at}")
                return session
            else:
                raise RuntimeError("Failed to create session: no result returned")
        
        except Exception as e:
            logger.error(f"Failed to create session for user_id={user_id}: {e}")
            raise
    
    def get_session_by_token(self, token: str) -> Optional[Session]:
        """
        Retrieve session by authentication token.
        
        Args:
            token: Authentication token to search for
        
        Returns:
            Session object if found and not expired, None otherwise
        
        Example:
            session = session_repo.get_session_by_token("abc123def456")
            if session:
                print(f"Valid session for user_id={session.user_id}")
            else:
                print("Invalid or expired session")
        """
        query = """
            SELECT id, user_id, token, expires_at, created_at
            FROM sessions
            WHERE token = %(token)s
        """
        
        params = {'token': token}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                session = Session.from_dict(result)
                
                # Check if session is expired
                if session.is_expired():
                    logger.info(f"Session {session.id} is expired, deleting")
                    self.delete_session(token)
                    return None
                
                return session
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get session by token: {e}")
            raise
    
    def delete_session(self, token: str) -> bool:
        """
        Delete a session by token.
        
        Args:
            token: Authentication token of session to delete
        
        Returns:
            True if deletion succeeded, False if session not found
        
        Raises:
            psycopg2.Error: If database operation fails
        
        Example:
            success = session_repo.delete_session("abc123def456")
            if success:
                print("Session deleted (user logged out)")
        """
        query = """
            DELETE FROM sessions
            WHERE token = %(token)s
            RETURNING id
        """
        
        params = {'token': token}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                logger.info(f"Deleted session with token {token[:8]}...")
                return True
            else:
                logger.warning(f"Session with token {token[:8]}... not found for deletion")
                return False
        
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            raise
    
    def cleanup_expired_sessions(self) -> int:
        """
        Delete all expired sessions from the database.
        
        This method should be called periodically (e.g., hourly) to clean up
        expired sessions and free database space.
        
        Returns:
            Number of expired sessions deleted
        
        Raises:
            psycopg2.Error: If database operation fails
        
        Example:
            deleted_count = session_repo.cleanup_expired_sessions()
            print(f"Cleaned up {deleted_count} expired sessions")
        """
        query = """
            DELETE FROM sessions
            WHERE expires_at < CURRENT_TIMESTAMP
            RETURNING id
        """
        
        try:
            results = self.db.execute_query(query)
            
            deleted_count = len(results) if results else 0
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired sessions")
            else:
                logger.debug("No expired sessions to clean up")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            raise
    
    def get_user_sessions(self, user_id: int) -> list:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of active Session objects for the user
        
        Example:
            sessions = session_repo.get_user_sessions(user_id=1)
            print(f"User has {len(sessions)} active sessions")
        """
        query = """
            SELECT id, user_id, token, expires_at, created_at
            FROM sessions
            WHERE user_id = %(user_id)s
            AND expires_at > CURRENT_TIMESTAMP
            ORDER BY created_at DESC
        """
        
        params = {'user_id': user_id}
        
        try:
            results = self.db.execute_query(query, params)
            
            if results:
                return [Session.from_dict(row) for row in results]
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get sessions for user_id={user_id}: {e}")
            raise
    
    def delete_user_sessions(self, user_id: int) -> int:
        """
        Delete all sessions for a specific user.
        
        Useful for logging out a user from all devices.
        
        Args:
            user_id: ID of the user
        
        Returns:
            Number of sessions deleted
        
        Example:
            deleted = session_repo.delete_user_sessions(user_id=1)
            print(f"Logged out user from {deleted} devices")
        """
        query = """
            DELETE FROM sessions
            WHERE user_id = %(user_id)s
            RETURNING id
        """
        
        params = {'user_id': user_id}
        
        try:
            results = self.db.execute_query(query, params)
            
            deleted_count = len(results) if results else 0
            
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} sessions for user_id={user_id}")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"Failed to delete sessions for user_id={user_id}: {e}")
            raise
