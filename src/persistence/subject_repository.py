"""
SubjectRepository - Dynamic subject management

This module provides the SubjectRepository class for managing curriculum subjects,
including creation, retrieval, updates, and deletion.

Requirements: 3.1
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class Subject:
    """
    Subject data model representing a curriculum subject.
    
    Attributes:
        id: Unique subject identifier
        grade: Grade level (10-12)
        name: Subject name (e.g., "Matematika", "Informatika")
        code: Unique subject code (e.g., "MAT_10", "INF_11")
        created_at: Subject creation timestamp
    """
    
    def __init__(
        self,
        id: int,
        grade: int,
        name: str,
        code: str,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.grade = grade
        self.name = name
        self.code = code
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Subject object to dictionary."""
        return {
            'id': self.id,
            'grade': self.grade,
            'name': self.name,
            'code': self.code,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subject':
        """Create Subject object from dictionary."""
        return cls(
            id=data['id'],
            grade=data['grade'],
            name=data['name'],
            code=data['code'],
            created_at=data.get('created_at')
        )
    
    def __repr__(self) -> str:
        return f"Subject(id={self.id}, code='{self.code}', name='{self.name}', grade={self.grade})"


class SubjectRepository:
    """
    Repository for dynamic subject management.
    
    Provides methods for creating, retrieving, updating, and deleting subjects
    for grades 10-12.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize SubjectRepository with database manager.
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
    
    def validate_subject_data(self, grade: int, name: str, code: str) -> None:
        """
        Validate subject data before database operations.
        
        Args:
            grade: Grade level to validate
            name: Subject name to validate
            code: Subject code to validate
        
        Raises:
            ValueError: If validation fails
        """
        # Validate grade
        if grade not in [10, 11, 12]:
            raise ValueError("Grade must be 10, 11, or 12")
        
        # Validate name
        if not name or len(name) < 2:
            raise ValueError("Subject name must be at least 2 characters long")
        
        if len(name) > 100:
            raise ValueError("Subject name must not exceed 100 characters")
        
        # Validate code
        if not code or len(code) < 2:
            raise ValueError("Subject code must be at least 2 characters long")
        
        if len(code) > 50:
            raise ValueError("Subject code must not exceed 50 characters")
    
    def create_subject(self, grade: int, name: str, code: str) -> Subject:
        """
        Create a new subject.
        
        Args:
            grade: Grade level (10-12)
            name: Subject name (e.g., "Matematika")
            code: Unique subject code (e.g., "MAT_10")
        
        Returns:
            Created Subject object
        
        Raises:
            ValueError: If validation fails
            psycopg2.IntegrityError: If subject code already exists
            psycopg2.Error: If database operation fails
        
        Example:
            subject = subject_repo.create_subject(
                grade=10,
                name="Matematika",
                code="MAT_10"
            )
        """
        # Validate input
        self.validate_subject_data(grade, name, code)
        
        # Insert subject
        query = """
            INSERT INTO subjects (grade, name, code)
            VALUES (%(grade)s, %(name)s, %(code)s)
            RETURNING id, grade, name, code, created_at
        """
        
        params = {
            'grade': grade,
            'name': name,
            'code': code
        }
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                subject = Subject.from_dict(result)
                logger.info(f"Created subject: {code} - {name} (id={subject.id})")
                return subject
            else:
                raise RuntimeError("Failed to create subject: no result returned")
        
        except Exception as e:
            logger.error(f"Failed to create subject '{code}': {e}")
            raise
    
    def get_all_subjects(self) -> List[Subject]:
        """
        Retrieve all subjects.
        
        Returns:
            List of Subject objects
        
        Example:
            subjects = subject_repo.get_all_subjects()
            for subject in subjects:
                print(f"{subject.code}: {subject.name}")
        """
        query = """
            SELECT id, grade, name, code, created_at
            FROM subjects
            ORDER BY grade, name
        """
        
        try:
            results = self.db.execute_query(query)
            
            if results:
                return [Subject.from_dict(row) for row in results]
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get all subjects: {e}")
            raise
    
    def get_subjects_by_grade(self, grade: int) -> List[Subject]:
        """
        Retrieve subjects for a specific grade.
        
        Args:
            grade: Grade level (10-12)
        
        Returns:
            List of Subject objects for the specified grade
        
        Raises:
            ValueError: If grade is invalid
        
        Example:
            subjects = subject_repo.get_subjects_by_grade(10)
            for subject in subjects:
                print(f"{subject.name}")
        """
        if grade not in [10, 11, 12]:
            raise ValueError("Grade must be 10, 11, or 12")
        
        query = """
            SELECT id, grade, name, code, created_at
            FROM subjects
            WHERE grade = %(grade)s
            ORDER BY name
        """
        
        params = {'grade': grade}
        
        try:
            results = self.db.execute_query(query, params)
            
            if results:
                return [Subject.from_dict(row) for row in results]
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get subjects for grade {grade}: {e}")
            raise
    
    def get_subject_by_id(self, subject_id: int) -> Optional[Subject]:
        """
        Retrieve subject by ID.
        
        Args:
            subject_id: Subject ID to search for
        
        Returns:
            Subject object if found, None otherwise
        
        Example:
            subject = subject_repo.get_subject_by_id(1)
            if subject:
                print(f"Found subject: {subject.name}")
        """
        query = """
            SELECT id, grade, name, code, created_at
            FROM subjects
            WHERE id = %(subject_id)s
        """
        
        params = {'subject_id': subject_id}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                return Subject.from_dict(result)
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get subject by id {subject_id}: {e}")
            raise
    
    def get_subject_by_code(self, code: str) -> Optional[Subject]:
        """
        Retrieve subject by code.
        
        Args:
            code: Subject code to search for
        
        Returns:
            Subject object if found, None otherwise
        
        Example:
            subject = subject_repo.get_subject_by_code("MAT_10")
            if subject:
                print(f"Found subject: {subject.name}")
        """
        query = """
            SELECT id, grade, name, code, created_at
            FROM subjects
            WHERE code = %(code)s
        """
        
        params = {'code': code}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                return Subject.from_dict(result)
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get subject by code '{code}': {e}")
            raise
    
    def update_subject(self, subject_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update subject information.
        
        Args:
            subject_id: ID of subject to update
            updates: Dictionary of fields to update
                Allowed keys: grade, name, code
        
        Returns:
            True if update succeeded, False if subject not found
        
        Raises:
            ValueError: If validation fails or invalid update keys
            psycopg2.Error: If database operation fails
        
        Example:
            success = subject_repo.update_subject(
                subject_id=1,
                updates={'name': 'Matematika Lanjutan'}
            )
        """
        if not updates:
            raise ValueError("No updates provided")
        
        # Allowed update fields
        allowed_fields = {'grade', 'name', 'code'}
        invalid_fields = set(updates.keys()) - allowed_fields
        
        if invalid_fields:
            raise ValueError(f"Invalid update fields: {', '.join(invalid_fields)}")
        
        # Validate updates
        if 'grade' in updates or 'name' in updates or 'code' in updates:
            # Get current subject data for validation
            current = self.get_subject_by_id(subject_id)
            if not current:
                return False
            
            grade = updates.get('grade', current.grade)
            name = updates.get('name', current.name)
            code = updates.get('code', current.code)
            
            self.validate_subject_data(grade, name, code)
        
        # Build update query dynamically
        update_fields = []
        params = {'subject_id': subject_id}
        
        for key, value in updates.items():
            update_fields.append(f"{key} = %({key})s")
            params[key] = value
        
        query = f"""
            UPDATE subjects
            SET {', '.join(update_fields)}
            WHERE id = %(subject_id)s
            RETURNING id
        """
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                logger.info(f"Updated subject id={subject_id}: {list(updates.keys())}")
                return True
            else:
                logger.warning(f"Subject id={subject_id} not found for update")
                return False
        
        except Exception as e:
            logger.error(f"Failed to update subject id={subject_id}: {e}")
            raise
    
    def delete_subject(self, subject_id: int) -> bool:
        """
        Delete a subject.
        
        Note: This will cascade delete all related records (books, chat history, etc.)
        due to ON DELETE CASCADE constraints in the database schema.
        
        Args:
            subject_id: ID of subject to delete
        
        Returns:
            True if deletion succeeded, False if subject not found
        
        Raises:
            psycopg2.Error: If database operation fails
        
        Example:
            success = subject_repo.delete_subject(subject_id=5)
            if success:
                print("Subject deleted successfully")
        """
        query = """
            DELETE FROM subjects
            WHERE id = %(subject_id)s
            RETURNING id
        """
        
        params = {'subject_id': subject_id}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                logger.info(f"Deleted subject id={subject_id}")
                return True
            else:
                logger.warning(f"Subject id={subject_id} not found for deletion")
                return False
        
        except Exception as e:
            logger.error(f"Failed to delete subject id={subject_id}: {e}")
            raise
