"""
BookRepository - Curriculum book metadata management

This module provides the BookRepository class for managing curriculum books
with VKP version tracking.

Requirements: 3.1
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class Book:
    """
    Book data model representing a curriculum book.
    
    Attributes:
        id: Unique book identifier
        subject_id: Reference to subject
        title: Book title
        filename: Original filename
        vkp_version: Versioned Knowledge Package version (semantic versioning)
        chunk_count: Number of chunks in the book
        created_at: Book creation timestamp
    """
    
    def __init__(
        self,
        id: int,
        subject_id: int,
        title: str,
        filename: Optional[str] = None,
        vkp_version: Optional[str] = None,
        chunk_count: int = 0,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.subject_id = subject_id
        self.title = title
        self.filename = filename
        self.vkp_version = vkp_version
        self.chunk_count = chunk_count
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Book object to dictionary."""
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'title': self.title,
            'filename': self.filename,
            'vkp_version': self.vkp_version,
            'chunk_count': self.chunk_count,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Book':
        """Create Book object from dictionary."""
        return cls(
            id=data['id'],
            subject_id=data['subject_id'],
            title=data['title'],
            filename=data.get('filename'),
            vkp_version=data.get('vkp_version'),
            chunk_count=data.get('chunk_count', 0),
            created_at=data.get('created_at')
        )
    
    def __repr__(self) -> str:
        return f"Book(id={self.id}, title='{self.title}', vkp_version='{self.vkp_version}')"


class BookRepository:
    """
    Repository for curriculum book metadata management.
    
    Provides methods for creating, retrieving, updating books with
    VKP version tracking.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize BookRepository with database manager.
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
    
    def validate_book_data(self, title: str, vkp_version: Optional[str] = None) -> None:
        """
        Validate book data before database operations.
        
        Args:
            title: Book title to validate
            vkp_version: Optional VKP version to validate
        
        Raises:
            ValueError: If validation fails
        """
        # Validate title
        if not title or len(title) < 2:
            raise ValueError("Book title must be at least 2 characters long")
        
        if len(title) > 255:
            raise ValueError("Book title must not exceed 255 characters")
        
        # Validate VKP version format (semantic versioning: MAJOR.MINOR.PATCH)
        if vkp_version:
            import re
            version_pattern = r'^\d+\.\d+\.\d+$'
            if not re.match(version_pattern, vkp_version):
                raise ValueError(
                    "VKP version must follow semantic versioning format (e.g., '1.2.0')"
                )
    
    def create_book(
        self,
        subject_id: int,
        title: str,
        filename: Optional[str] = None,
        vkp_version: Optional[str] = None
    ) -> Book:
        """
        Create a new book.
        
        Args:
            subject_id: ID of the subject this book belongs to
            title: Book title
            filename: Original filename (optional)
            vkp_version: VKP version (semantic versioning, optional)
        
        Returns:
            Created Book object
        
        Raises:
            ValueError: If validation fails
            psycopg2.ForeignKeyViolation: If subject_id doesn't exist
            psycopg2.Error: If database operation fails
        
        Example:
            book = book_repo.create_book(
                subject_id=1,
                title="Matematika Kelas 10 Semester 1",
                filename="Matematika_Kelas_10_Semester_1.pdf",
                vkp_version="1.0.0"
            )
        """
        # Validate input
        self.validate_book_data(title, vkp_version)
        
        # Insert book
        query = """
            INSERT INTO books (subject_id, title, filename, vkp_version)
            VALUES (%(subject_id)s, %(title)s, %(filename)s, %(vkp_version)s)
            RETURNING id, subject_id, title, filename, vkp_version, chunk_count, created_at
        """
        
        params = {
            'subject_id': subject_id,
            'title': title,
            'filename': filename,
            'vkp_version': vkp_version
        }
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                book = Book.from_dict(result)
                logger.info(
                    f"Created book: {title} (id={book.id}, version={vkp_version})"
                )
                return book
            else:
                raise RuntimeError("Failed to create book: no result returned")
        
        except Exception as e:
            logger.error(f"Failed to create book '{title}': {e}")
            raise
    
    def get_books_by_subject(self, subject_id: int) -> List[Book]:
        """
        Retrieve all books for a specific subject.
        
        Args:
            subject_id: Subject ID to filter by
        
        Returns:
            List of Book objects for the specified subject
        
        Example:
            books = book_repo.get_books_by_subject(subject_id=1)
            for book in books:
                print(f"{book.title} - v{book.vkp_version}")
        """
        query = """
            SELECT id, subject_id, title, filename, vkp_version, chunk_count, created_at
            FROM books
            WHERE subject_id = %(subject_id)s
            ORDER BY title
        """
        
        params = {'subject_id': subject_id}
        
        try:
            results = self.db.execute_query(query, params)
            
            if results:
                return [Book.from_dict(row) for row in results]
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get books for subject {subject_id}: {e}")
            raise
    
    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """
        Retrieve book by ID.
        
        Args:
            book_id: Book ID to search for
        
        Returns:
            Book object if found, None otherwise
        
        Example:
            book = book_repo.get_book_by_id(1)
            if book:
                print(f"Found book: {book.title}")
        """
        query = """
            SELECT id, subject_id, title, filename, vkp_version, chunk_count, created_at
            FROM books
            WHERE id = %(book_id)s
        """
        
        params = {'book_id': book_id}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                return Book.from_dict(result)
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get book by id {book_id}: {e}")
            raise
    
    def update_book_version(self, book_id: int, vkp_version: str) -> bool:
        """
        Update the VKP version of a book.
        
        This is commonly used when a new version of the curriculum is released
        and the VKP package is updated.
        
        Args:
            book_id: ID of book to update
            vkp_version: New VKP version (semantic versioning)
        
        Returns:
            True if update succeeded, False if book not found
        
        Raises:
            ValueError: If version format is invalid
            psycopg2.Error: If database operation fails
        
        Example:
            success = book_repo.update_book_version(
                book_id=1,
                vkp_version="1.2.0"
            )
        """
        # Validate version format
        self.validate_book_data("dummy", vkp_version)
        
        query = """
            UPDATE books
            SET vkp_version = %(vkp_version)s
            WHERE id = %(book_id)s
            RETURNING id
        """
        
        params = {
            'book_id': book_id,
            'vkp_version': vkp_version
        }
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                logger.info(f"Updated book id={book_id} to version {vkp_version}")
                return True
            else:
                logger.warning(f"Book id={book_id} not found for version update")
                return False
        
        except Exception as e:
            logger.error(f"Failed to update book version for id={book_id}: {e}")
            raise
    
    def update_book_chunk_count(self, book_id: int, chunk_count: int) -> bool:
        """
        Update the chunk count of a book.
        
        This is typically called after processing a VKP package to record
        how many chunks were extracted.
        
        Args:
            book_id: ID of book to update
            chunk_count: Number of chunks in the book
        
        Returns:
            True if update succeeded, False if book not found
        
        Raises:
            ValueError: If chunk_count is negative
            psycopg2.Error: If database operation fails
        
        Example:
            success = book_repo.update_book_chunk_count(
                book_id=1,
                chunk_count=450
            )
        """
        if chunk_count < 0:
            raise ValueError("Chunk count cannot be negative")
        
        query = """
            UPDATE books
            SET chunk_count = %(chunk_count)s
            WHERE id = %(book_id)s
            RETURNING id
        """
        
        params = {
            'book_id': book_id,
            'chunk_count': chunk_count
        }
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                logger.info(f"Updated book id={book_id} chunk count to {chunk_count}")
                return True
            else:
                logger.warning(f"Book id={book_id} not found for chunk count update")
                return False
        
        except Exception as e:
            logger.error(f"Failed to update book chunk count for id={book_id}: {e}")
            raise
    
    def get_book_by_version(self, vkp_version: str) -> Optional[Book]:
        """
        Retrieve book by VKP version.
        
        This is useful for looking up which book corresponds to a specific
        VKP package version.
        
        Args:
            vkp_version: VKP version to search for
        
        Returns:
            Book object if found, None otherwise
        
        Note:
            If multiple books have the same version (unlikely but possible),
            this returns the first match.
        
        Example:
            book = book_repo.get_book_by_version("1.2.0")
            if book:
                print(f"Found book: {book.title}")
        """
        query = """
            SELECT id, subject_id, title, filename, vkp_version, chunk_count, created_at
            FROM books
            WHERE vkp_version = %(vkp_version)s
            LIMIT 1
        """
        
        params = {'vkp_version': vkp_version}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                return Book.from_dict(result)
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get book by version '{vkp_version}': {e}")
            raise
    
    def update_book(self, book_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update book information.
        
        Args:
            book_id: ID of book to update
            updates: Dictionary of fields to update
                Allowed keys: title, filename, vkp_version, chunk_count
        
        Returns:
            True if update succeeded, False if book not found
        
        Raises:
            ValueError: If validation fails or invalid update keys
            psycopg2.Error: If database operation fails
        
        Example:
            success = book_repo.update_book(
                book_id=1,
                updates={
                    'title': 'Matematika Kelas 10 Semester 1 (Revisi)',
                    'vkp_version': '1.3.0'
                }
            )
        """
        if not updates:
            raise ValueError("No updates provided")
        
        # Allowed update fields
        allowed_fields = {'title', 'filename', 'vkp_version', 'chunk_count'}
        invalid_fields = set(updates.keys()) - allowed_fields
        
        if invalid_fields:
            raise ValueError(f"Invalid update fields: {', '.join(invalid_fields)}")
        
        # Validate updates
        if 'title' in updates or 'vkp_version' in updates:
            title = updates.get('title', 'dummy')
            vkp_version = updates.get('vkp_version')
            self.validate_book_data(title, vkp_version)
        
        if 'chunk_count' in updates and updates['chunk_count'] < 0:
            raise ValueError("Chunk count cannot be negative")
        
        # Build update query dynamically
        update_fields = []
        params = {'book_id': book_id}
        
        for key, value in updates.items():
            update_fields.append(f"{key} = %({key})s")
            params[key] = value
        
        query = f"""
            UPDATE books
            SET {', '.join(update_fields)}
            WHERE id = %(book_id)s
            RETURNING id
        """
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                logger.info(f"Updated book id={book_id}: {list(updates.keys())}")
                return True
            else:
                logger.warning(f"Book id={book_id} not found for update")
                return False
        
        except Exception as e:
            logger.error(f"Failed to update book id={book_id}: {e}")
            raise
    
    def delete_book(self, book_id: int) -> bool:
        """
        Delete a book.
        
        Args:
            book_id: ID of book to delete
        
        Returns:
            True if deletion succeeded, False if book not found
        
        Raises:
            psycopg2.Error: If database operation fails
        
        Example:
            success = book_repo.delete_book(book_id=5)
            if success:
                print("Book deleted successfully")
        """
        query = """
            DELETE FROM books
            WHERE id = %(book_id)s
            RETURNING id
        """
        
        params = {'book_id': book_id}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                logger.info(f"Deleted book id={book_id}")
                return True
            else:
                logger.warning(f"Book id={book_id} not found for deletion")
                return False
        
        except Exception as e:
            logger.error(f"Failed to delete book id={book_id}: {e}")
            raise
    
    def get_all_books(self) -> List[Book]:
        """
        Retrieve all books across all subjects.
        
        Returns:
            List of all Book objects
        
        Example:
            books = book_repo.get_all_books()
            for book in books:
                print(f"{book.title} - v{book.vkp_version}")
        """
        query = """
            SELECT id, subject_id, title, filename, vkp_version, chunk_count, created_at
            FROM books
            ORDER BY subject_id, title
        """
        
        try:
            results = self.db.execute_query(query)
            
            if results:
                return [Book.from_dict(row) for row in results]
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get all books: {e}")
            raise
