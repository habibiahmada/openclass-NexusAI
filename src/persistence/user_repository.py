"""
UserRepository - User CRUD operations

This module provides the UserRepository class for managing user accounts,
including creation, retrieval, updates, and deletion with password hashing.

Requirements: 3.1
"""

import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class User:
    """
    User data model representing a user account.
    
    Attributes:
        id: Unique user identifier
        username: Unique username
        password_hash: SHA256 hashed password
        role: User role (siswa, guru, admin)
        full_name: User's full name
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    
    def __init__(
        self,
        id: int,
        username: str,
        password_hash: str,
        role: str,
        full_name: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.full_name = full_name
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert User object to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'password_hash': self.password_hash,
            'role': self.role,
            'full_name': self.full_name,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User object from dictionary."""
        return cls(
            id=data['id'],
            username=data['username'],
            password_hash=data['password_hash'],
            role=data['role'],
            full_name=data.get('full_name'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def __repr__(self) -> str:
        return f"User(id={self.id}, username='{self.username}', role='{self.role}')"


class UserRepository:
    """
    Repository for user CRUD operations.
    
    Provides methods for creating, retrieving, updating, and deleting users
    with password hashing using SHA256.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize UserRepository with database manager.
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using SHA256.
        
        Args:
            password: Plain text password
        
        Returns:
            SHA256 hashed password as hexadecimal string
        
        Example:
            hashed = UserRepository.hash_password("mypassword123")
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def validate_user_data(
        self, 
        username: str, 
        role: str, 
        password: Optional[str] = None
    ) -> None:
        """
        Validate user data before database operations.
        
        Args:
            username: Username to validate
            role: User role to validate
            password: Optional password to validate
        
        Raises:
            ValueError: If validation fails
        """
        # Validate username
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if len(username) > 50:
            raise ValueError("Username must not exceed 50 characters")
        
        # Validate role
        valid_roles = ['siswa', 'guru', 'admin']
        if role not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        
        # Validate password if provided
        if password is not None:
            if len(password) < 6:
                raise ValueError("Password must be at least 6 characters long")
    
    def create_user(
        self, 
        username: str, 
        password: str, 
        role: str, 
        full_name: Optional[str] = None
    ) -> User:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            role: User role (siswa, guru, admin)
            full_name: Optional full name
        
        Returns:
            Created User object
        
        Raises:
            ValueError: If validation fails
            psycopg2.IntegrityError: If username already exists
            psycopg2.Error: If database operation fails
        
        Example:
            user = user_repo.create_user(
                username="student1",
                password="password123",
                role="siswa",
                full_name="Ahmad Rizki"
            )
        """
        # Validate input
        self.validate_user_data(username, role, password)
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Insert user
        query = """
            INSERT INTO users (username, password_hash, role, full_name)
            VALUES (%(username)s, %(password_hash)s, %(role)s, %(full_name)s)
            RETURNING id, username, password_hash, role, full_name, created_at, updated_at
        """
        
        params = {
            'username': username,
            'password_hash': password_hash,
            'role': role,
            'full_name': full_name
        }
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                user = User.from_dict(result)
                logger.info(f"Created user: {username} (id={user.id})")
                return user
            else:
                raise RuntimeError("Failed to create user: no result returned")
        
        except Exception as e:
            logger.error(f"Failed to create user '{username}': {e}")
            raise
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve user by username.
        
        Args:
            username: Username to search for
        
        Returns:
            User object if found, None otherwise
        
        Example:
            user = user_repo.get_user_by_username("student1")
            if user:
                print(f"Found user: {user.full_name}")
        """
        query = """
            SELECT id, username, password_hash, role, full_name, created_at, updated_at
            FROM users
            WHERE username = %(username)s
        """
        
        params = {'username': username}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                return User.from_dict(result)
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get user by username '{username}': {e}")
            raise
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve user by ID.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            User object if found, None otherwise
        
        Example:
            user = user_repo.get_user_by_id(1)
            if user:
                print(f"Found user: {user.username}")
        """
        query = """
            SELECT id, username, password_hash, role, full_name, created_at, updated_at
            FROM users
            WHERE id = %(user_id)s
        """
        
        params = {'user_id': user_id}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                return User.from_dict(result)
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get user by id {user_id}: {e}")
            raise
    
    def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update user information.
        
        Args:
            user_id: ID of user to update
            updates: Dictionary of fields to update
                Allowed keys: username, password, role, full_name
        
        Returns:
            True if update succeeded, False if user not found
        
        Raises:
            ValueError: If validation fails or invalid update keys
            psycopg2.Error: If database operation fails
        
        Example:
            success = user_repo.update_user(
                user_id=1,
                updates={'full_name': 'Ahmad Rizki Pratama', 'role': 'guru'}
            )
        """
        if not updates:
            raise ValueError("No updates provided")
        
        # Allowed update fields
        allowed_fields = {'username', 'password', 'role', 'full_name'}
        invalid_fields = set(updates.keys()) - allowed_fields
        
        if invalid_fields:
            raise ValueError(f"Invalid update fields: {', '.join(invalid_fields)}")
        
        # Validate updates
        if 'username' in updates:
            self.validate_user_data(updates['username'], 'siswa')  # Role doesn't matter for username validation
        
        if 'role' in updates:
            self.validate_user_data('dummy', updates['role'])  # Username doesn't matter for role validation
        
        if 'password' in updates:
            self.validate_user_data('dummy', 'siswa', updates['password'])
        
        # Build update query dynamically
        update_fields = []
        params = {'user_id': user_id}
        
        for key, value in updates.items():
            if key == 'password':
                # Hash password
                update_fields.append("password_hash = %(password_hash)s")
                params['password_hash'] = self.hash_password(value)
            else:
                update_fields.append(f"{key} = %({key})s")
                params[key] = value
        
        # Always update updated_at timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        query = f"""
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE id = %(user_id)s
            RETURNING id
        """
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                logger.info(f"Updated user id={user_id}: {list(updates.keys())}")
                return True
            else:
                logger.warning(f"User id={user_id} not found for update")
                return False
        
        except Exception as e:
            logger.error(f"Failed to update user id={user_id}: {e}")
            raise
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user account.
        
        Note: This will cascade delete all related records (sessions, chat history, etc.)
        due to ON DELETE CASCADE constraints in the database schema.
        
        Args:
            user_id: ID of user to delete
        
        Returns:
            True if deletion succeeded, False if user not found
        
        Raises:
            psycopg2.Error: If database operation fails
        
        Example:
            success = user_repo.delete_user(user_id=5)
            if success:
                print("User deleted successfully")
        """
        query = """
            DELETE FROM users
            WHERE id = %(user_id)s
            RETURNING id
        """
        
        params = {'user_id': user_id}
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                logger.info(f"Deleted user id={user_id}")
                return True
            else:
                logger.warning(f"User id={user_id} not found for deletion")
                return False
        
        except Exception as e:
            logger.error(f"Failed to delete user id={user_id}: {e}")
            raise
    
    def verify_password(self, username: str, password: str) -> Optional[User]:
        """
        Verify user credentials.
        
        Args:
            username: Username to verify
            password: Plain text password to verify
        
        Returns:
            User object if credentials are valid, None otherwise
        
        Example:
            user = user_repo.verify_password("student1", "password123")
            if user:
                print("Login successful")
            else:
                print("Invalid credentials")
        """
        user = self.get_user_by_username(username)
        
        if not user:
            return None
        
        # Hash provided password and compare
        password_hash = self.hash_password(password)
        
        if password_hash == user.password_hash:
            logger.info(f"Password verified for user: {username}")
            return user
        else:
            logger.warning(f"Password verification failed for user: {username}")
            return None
