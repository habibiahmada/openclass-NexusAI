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
from .lru_cache import LRUCache
from .cache_utils import generate_cache_key, normalize_question
from .cache_integration import CachedRAGPipeline, get_current_vkp_version
from .cache_invalidation import CacheInvalidator, invalidate_cache_on_vkp_update

# Conditional import for RedisCache (requires redis package)
try:
    from .redis_cache import RedisCache
    _redis_available = True
except ImportError:
    RedisCache = None
    _redis_available = False

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
    'LRUCache',
    'generate_cache_key',
    'normalize_question',
    'CachedRAGPipeline',
    'get_current_vkp_version',
    'CacheInvalidator',
    'invalidate_cache_on_vkp_update'
]

# Add RedisCache to __all__ only if available
if _redis_available:
    __all__.append('RedisCache')

