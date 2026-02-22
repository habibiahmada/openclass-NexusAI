"""
Persistence Layer for OpenClass Nexus AI

This module provides database management and repository classes for
persistent storage of user data, sessions, chat history, and metadata.
Also includes caching layer for performance optimization.
"""

from .database_manager import DatabaseManager
from .user_repository import UserRepository, User
from .session_repository import SessionRepository, Session
from .chat_history_repository import ChatHistoryRepository, ChatHistory
from .subject_repository import SubjectRepository, Subject
from .book_repository import BookRepository, Book
from .cache_manager import CacheManager, CacheStats
from .redis_cache import RedisCache
from .lru_cache import LRUCache
from .cache_utils import generate_cache_key, normalize_question
from .cache_integration import CachedRAGPipeline, get_current_vkp_version
from .cache_invalidation import CacheInvalidator, invalidate_cache_on_vkp_update

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
    'Book',
    'CacheManager',
    'CacheStats',
    'RedisCache',
    'LRUCache',
    'generate_cache_key',
    'normalize_question',
    'CachedRAGPipeline',
    'get_current_vkp_version',
    'CacheInvalidator',
    'invalidate_cache_on_vkp_update'
]

