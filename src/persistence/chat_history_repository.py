"""
ChatHistoryRepository - Chat history persistence operations

This module provides the ChatHistoryRepository class for managing chat history,
including saving conversations, retrieving user/subject history, and pagination support.

Requirements: 3.1, 3.2
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ChatHistory:
    """
    ChatHistory data model representing a student-AI interaction.
    
    Attributes:
        id: Unique chat history identifier
        user_id: ID of the user who asked the question
        subject_id: ID of the subject (optional)
        question: The question asked by the user
        response: The AI-generated response
        confidence: LLM confidence score (0.0 to 1.0)
        created_at: Timestamp of the interaction
    """
    
    def __init__(
        self,
        id: int,
        user_id: int,
        subject_id: Optional[int],
        question: str,
        response: str,
        confidence: Optional[float] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.subject_id = subject_id
        self.question = question
        self.response = response
        self.confidence = confidence
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ChatHistory object to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject_id': self.subject_id,
            'question': self.question,
            'response': self.response,
            'confidence': self.confidence,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatHistory':
        """Create ChatHistory object from dictionary."""
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            subject_id=data.get('subject_id'),
            question=data['question'],
            response=data['response'],
            confidence=data.get('confidence'),
            created_at=data.get('created_at')
        )
    
    def __repr__(self) -> str:
        return f"ChatHistory(id={self.id}, user_id={self.user_id}, subject_id={self.subject_id}, created_at={self.created_at})"


class ChatHistoryRepository:
    """
    Repository for chat history persistence operations.
    
    Provides methods for saving chat interactions, retrieving user/subject history,
    and managing chat history with pagination support.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize ChatHistoryRepository with database manager.
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
    
    def save_chat(
        self,
        user_id: int,
        subject_id: Optional[int],
        question: str,
        response: str,
        confidence: Optional[float] = None
    ) -> ChatHistory:
        """
        Save a chat interaction to the database.
        
        Args:
            user_id: ID of the user who asked the question
            subject_id: ID of the subject (optional, can be None)
            question: The question asked by the user
            response: The AI-generated response
            confidence: LLM confidence score (0.0 to 1.0, optional)
        
        Returns:
            Created ChatHistory object
        
        Raises:
            ValueError: If validation fails
            psycopg2.Error: If database operation fails
        
        Example:
            chat = chat_repo.save_chat(
                user_id=1,
                subject_id=5,
                question="Apa itu teorema Pythagoras?",
                response="Teorema Pythagoras menyatakan bahwa...",
                confidence=0.95
            )
        """
        # Validate input
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        if not response or not response.strip():
            raise ValueError("Response cannot be empty")
        
        if confidence is not None:
            if not (0.0 <= confidence <= 1.0):
                raise ValueError("Confidence must be between 0.0 and 1.0")
        
        # Insert chat history
        query = """
            INSERT INTO chat_history (user_id, subject_id, question, response, confidence)
            VALUES (%(user_id)s, %(subject_id)s, %(question)s, %(response)s, %(confidence)s)
            RETURNING id, user_id, subject_id, question, response, confidence, created_at
        """
        
        params = {
            'user_id': user_id,
            'subject_id': subject_id,
            'question': question.strip(),
            'response': response.strip(),
            'confidence': confidence
        }
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                chat = ChatHistory.from_dict(result)
                logger.info(f"Saved chat history for user_id={user_id}, subject_id={subject_id}")
                return chat
            else:
                raise RuntimeError("Failed to save chat: no result returned")
        
        except Exception as e:
            logger.error(f"Failed to save chat for user_id={user_id}: {e}")
            raise
    
    def get_user_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatHistory]:
        """
        Retrieve chat history for a specific user with pagination.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of records to return (default: 50)
            offset: Number of records to skip for pagination (default: 0)
        
        Returns:
            List of ChatHistory objects ordered by most recent first
        
        Raises:
            ValueError: If limit or offset are invalid
            psycopg2.Error: If database operation fails
        
        Example:
            # Get first 20 chats
            history = chat_repo.get_user_history(user_id=1, limit=20)
            
            # Get next 20 chats (pagination)
            history_page2 = chat_repo.get_user_history(user_id=1, limit=20, offset=20)
        """
        # Validate pagination parameters
        if limit <= 0:
            raise ValueError("Limit must be positive")
        
        if offset < 0:
            raise ValueError("Offset cannot be negative")
        
        query = """
            SELECT id, user_id, subject_id, question, response, confidence, created_at
            FROM chat_history
            WHERE user_id = %(user_id)s
            ORDER BY created_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        
        params = {
            'user_id': user_id,
            'limit': limit,
            'offset': offset
        }
        
        try:
            results = self.db.execute_query(query, params)
            
            if results:
                history = [ChatHistory.from_dict(row) for row in results]
                logger.debug(f"Retrieved {len(history)} chat records for user_id={user_id}")
                return history
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get user history for user_id={user_id}: {e}")
            raise
    
    def get_subject_history(
        self,
        subject_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatHistory]:
        """
        Retrieve chat history for a specific subject with pagination.
        
        Args:
            subject_id: ID of the subject
            limit: Maximum number of records to return (default: 50)
            offset: Number of records to skip for pagination (default: 0)
        
        Returns:
            List of ChatHistory objects ordered by most recent first
        
        Raises:
            ValueError: If limit or offset are invalid
            psycopg2.Error: If database operation fails
        
        Example:
            # Get recent questions for Mathematics subject
            history = chat_repo.get_subject_history(subject_id=5, limit=100)
        """
        # Validate pagination parameters
        if limit <= 0:
            raise ValueError("Limit must be positive")
        
        if offset < 0:
            raise ValueError("Offset cannot be negative")
        
        query = """
            SELECT id, user_id, subject_id, question, response, confidence, created_at
            FROM chat_history
            WHERE subject_id = %(subject_id)s
            ORDER BY created_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        
        params = {
            'subject_id': subject_id,
            'limit': limit,
            'offset': offset
        }
        
        try:
            results = self.db.execute_query(query, params)
            
            if results:
                history = [ChatHistory.from_dict(row) for row in results]
                logger.debug(f"Retrieved {len(history)} chat records for subject_id={subject_id}")
                return history
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get subject history for subject_id={subject_id}: {e}")
            raise
    
    def delete_old_history(self, days: int) -> int:
        """
        Delete chat history older than specified number of days.
        
        This method is useful for data retention policies and database cleanup.
        
        Args:
            days: Delete records older than this many days
        
        Returns:
            Number of records deleted
        
        Raises:
            ValueError: If days is not positive
            psycopg2.Error: If database operation fails
        
        Example:
            # Delete chat history older than 90 days
            deleted_count = chat_repo.delete_old_history(days=90)
            print(f"Deleted {deleted_count} old chat records")
        """
        if days <= 0:
            raise ValueError("Days must be positive")
        
        query = """
            DELETE FROM chat_history
            WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%(days)s days'
            RETURNING id
        """
        
        params = {'days': days}
        
        try:
            results = self.db.execute_query(query, params)
            
            deleted_count = len(results) if results else 0
            
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} chat records older than {days} days")
            else:
                logger.debug(f"No chat records older than {days} days to delete")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"Failed to delete old history (days={days}): {e}")
            raise
    
    def get_user_chat_count(self, user_id: int) -> int:
        """
        Get total number of chat interactions for a user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            Total count of chat records for the user
        
        Example:
            count = chat_repo.get_user_chat_count(user_id=1)
            print(f"User has {count} total interactions")
        """
        query = """
            SELECT COUNT(*) as count
            FROM chat_history
            WHERE user_id = %(user_id)s
        """
        
        params = {'user_id': user_id}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                return result['count']
            
            return 0
        
        except Exception as e:
            logger.error(f"Failed to get chat count for user_id={user_id}: {e}")
            raise
    
    def get_subject_chat_count(self, subject_id: int) -> int:
        """
        Get total number of chat interactions for a subject.
        
        Args:
            subject_id: ID of the subject
        
        Returns:
            Total count of chat records for the subject
        
        Example:
            count = chat_repo.get_subject_chat_count(subject_id=5)
            print(f"Subject has {count} total questions")
        """
        query = """
            SELECT COUNT(*) as count
            FROM chat_history
            WHERE subject_id = %(subject_id)s
        """
        
        params = {'subject_id': subject_id}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                return result['count']
            
            return 0
        
        except Exception as e:
            logger.error(f"Failed to get chat count for subject_id={subject_id}: {e}")
            raise
    
    def get_recent_chats(
        self,
        limit: int = 10
    ) -> List[ChatHistory]:
        """
        Get most recent chat interactions across all users and subjects.
        
        Useful for monitoring and analytics.
        
        Args:
            limit: Maximum number of records to return (default: 10)
        
        Returns:
            List of ChatHistory objects ordered by most recent first
        
        Example:
            recent = chat_repo.get_recent_chats(limit=20)
            for chat in recent:
                print(f"User {chat.user_id}: {chat.question[:50]}...")
        """
        if limit <= 0:
            raise ValueError("Limit must be positive")
        
        query = """
            SELECT id, user_id, subject_id, question, response, confidence, created_at
            FROM chat_history
            ORDER BY created_at DESC
            LIMIT %(limit)s
        """
        
        params = {'limit': limit}
        
        try:
            results = self.db.execute_query(query, params)
            
            if results:
                return [ChatHistory.from_dict(row) for row in results]
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get recent chats: {e}")
            raise
