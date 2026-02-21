"""
Persistence Layer for OpenClass Nexus AI

This module provides database management and repository classes for
persistent storage of user data, sessions, chat history, and metadata.
"""

from .database_manager import DatabaseManager
from .user_repository import UserRepository, User
from .session_repository import SessionRepository, Session
from .chat_history_repository import ChatHistoryRepository, ChatHistory
from .subject_repository import SubjectRepository, Subject
from .book_repository import BookRepository, Book

__all__ = [
    'DatabaseManager',
    'UserRepository',
    'User',
    'SessionRepository',
    'Session',
    'ChatHistoryRepository',
    'ChatHistory',
    'SubjectRepository',
    'Subject',
    'BookRepository',
    'Book'
]
