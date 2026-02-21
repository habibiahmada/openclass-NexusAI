"""
Unit tests for UserRepository

Tests CRUD operations, password hashing, validation, and error handling.
"""

import pytest
import hashlib
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.persistence.user_repository import UserRepository, User
from src.persistence.database_manager import DatabaseManager


@pytest.fixture
def mock_db_manager():
    """Create a mock DatabaseManager for testing."""
    return Mock(spec=DatabaseManager)


@pytest.fixture
def user_repository(mock_db_manager):
    """Create a UserRepository instance with mock database."""
    return UserRepository(mock_db_manager)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'id': 1,
        'username': 'student1',
        'password_hash': hashlib.sha256('password123'.encode()).hexdigest(),
        'role': 'siswa',
        'full_name': 'Ahmad Rizki',
        'created_at': datetime(2025, 1, 15, 10, 30, 0),
        'updated_at': datetime(2025, 1, 15, 10, 30, 0)
    }


class TestUser:
    """Tests for User data model."""
    
    def test_user_initialization(self, sample_user_data):
        """Test User object initialization."""
        user = User.from_dict(sample_user_data)
        
        assert user.id == 1
        assert user.username == 'student1'
        assert user.role == 'siswa'
        assert user.full_name == 'Ahmad Rizki'
    
    def test_user_to_dict(self, sample_user_data):
        """Test User to dictionary conversion."""
        user = User.from_dict(sample_user_data)
        user_dict = user.to_dict()
        
        assert user_dict['id'] == sample_user_data['id']
        assert user_dict['username'] == sample_user_data['username']
        assert user_dict['role'] == sample_user_data['role']
    
    def test_user_repr(self, sample_user_data):
        """Test User string representation."""
        user = User.from_dict(sample_user_data)
        repr_str = repr(user)
        
        assert 'student1' in repr_str
        assert 'siswa' in repr_str


class TestPasswordHashing:
    """Tests for password hashing functionality."""
    
    def test_hash_password(self):
        """Test password hashing produces consistent results."""
        password = "mypassword123"
        hash1 = UserRepository.hash_password(password)
        hash2 = UserRepository.hash_password(password)
        
        # Same password should produce same hash
        assert hash1 == hash2
        
        # Hash should be SHA256 (64 hex characters)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)
    
    def test_hash_password_different_inputs(self):
        """Test different passwords produce different hashes."""
        hash1 = UserRepository.hash_password("password1")
        hash2 = UserRepository.hash_password("password2")
        
        assert hash1 != hash2
    
    def test_hash_password_empty_string(self):
        """Test hashing empty string."""
        hash_result = UserRepository.hash_password("")
        
        # Should still produce valid hash
        assert len(hash_result) == 64


class TestUserValidation:
    """Tests for user data validation."""
    
    def test_validate_valid_user_data(self, user_repository):
        """Test validation passes for valid data."""
        # Should not raise exception
        user_repository.validate_user_data(
            username="student1",
            role="siswa",
            password="password123"
        )
    
    def test_validate_username_too_short(self, user_repository):
        """Test validation fails for short username."""
        with pytest.raises(ValueError, match="at least 3 characters"):
            user_repository.validate_user_data(
                username="ab",
                role="siswa"
            )
    
    def test_validate_username_too_long(self, user_repository):
        """Test validation fails for long username."""
        long_username = "a" * 51
        with pytest.raises(ValueError, match="must not exceed 50 characters"):
            user_repository.validate_user_data(
                username=long_username,
                role="siswa"
            )
    
    def test_validate_invalid_role(self, user_repository):
        """Test validation fails for invalid role."""
        with pytest.raises(ValueError, match="Role must be one of"):
            user_repository.validate_user_data(
                username="student1",
                role="invalid_role"
            )
    
    def test_validate_password_too_short(self, user_repository):
        """Test validation fails for short password."""
        with pytest.raises(ValueError, match="at least 6 characters"):
            user_repository.validate_user_data(
                username="student1",
                role="siswa",
                password="12345"
            )
    
    def test_validate_all_valid_roles(self, user_repository):
        """Test validation passes for all valid roles."""
        for role in ['siswa', 'guru', 'admin']:
            user_repository.validate_user_data(
                username="testuser",
                role=role,
                password="password123"
            )


class TestCreateUser:
    """Tests for user creation."""
    
    def test_create_user_success(self, user_repository, mock_db_manager, sample_user_data):
        """Test successful user creation."""
        mock_db_manager.execute_query.return_value = sample_user_data
        
        user = user_repository.create_user(
            username="student1",
            password="password123",
            role="siswa",
            full_name="Ahmad Rizki"
        )
        
        assert user.username == "student1"
        assert user.role == "siswa"
        assert user.full_name == "Ahmad Rizki"
        
        # Verify database was called
        mock_db_manager.execute_query.assert_called_once()
        call_args = mock_db_manager.execute_query.call_args
        
        # Check password was hashed
        assert 'password_hash' in call_args[0][1]
        assert call_args[0][1]['password_hash'] != "password123"
    
    def test_create_user_without_full_name(self, user_repository, mock_db_manager, sample_user_data):
        """Test user creation without full name."""
        sample_user_data['full_name'] = None
        mock_db_manager.execute_query.return_value = sample_user_data
        
        user = user_repository.create_user(
            username="student1",
            password="password123",
            role="siswa"
        )
        
        assert user.username == "student1"
        assert user.full_name is None
    
    def test_create_user_invalid_username(self, user_repository, mock_db_manager):
        """Test user creation fails with invalid username."""
        with pytest.raises(ValueError):
            user_repository.create_user(
                username="ab",  # Too short
                password="password123",
                role="siswa"
            )
        
        # Database should not be called
        mock_db_manager.execute_query.assert_not_called()
    
    def test_create_user_invalid_role(self, user_repository, mock_db_manager):
        """Test user creation fails with invalid role."""
        with pytest.raises(ValueError):
            user_repository.create_user(
                username="student1",
                password="password123",
                role="invalid"
            )
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_create_user_invalid_password(self, user_repository, mock_db_manager):
        """Test user creation fails with invalid password."""
        with pytest.raises(ValueError):
            user_repository.create_user(
                username="student1",
                password="12345",  # Too short
                role="siswa"
            )
        
        mock_db_manager.execute_query.assert_not_called()


class TestGetUser:
    """Tests for user retrieval."""
    
    def test_get_user_by_username_found(self, user_repository, mock_db_manager, sample_user_data):
        """Test retrieving user by username when user exists."""
        mock_db_manager.execute_query.return_value = sample_user_data
        
        user = user_repository.get_user_by_username("student1")
        
        assert user is not None
        assert user.username == "student1"
        assert user.role == "siswa"
        
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_user_by_username_not_found(self, user_repository, mock_db_manager):
        """Test retrieving user by username when user doesn't exist."""
        mock_db_manager.execute_query.return_value = None
        
        user = user_repository.get_user_by_username("nonexistent")
        
        assert user is None
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_user_by_id_found(self, user_repository, mock_db_manager, sample_user_data):
        """Test retrieving user by ID when user exists."""
        mock_db_manager.execute_query.return_value = sample_user_data
        
        user = user_repository.get_user_by_id(1)
        
        assert user is not None
        assert user.id == 1
        assert user.username == "student1"
        
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_user_by_id_not_found(self, user_repository, mock_db_manager):
        """Test retrieving user by ID when user doesn't exist."""
        mock_db_manager.execute_query.return_value = None
        
        user = user_repository.get_user_by_id(999)
        
        assert user is None
        mock_db_manager.execute_query.assert_called_once()


class TestUpdateUser:
    """Tests for user updates."""
    
    def test_update_user_full_name(self, user_repository, mock_db_manager):
        """Test updating user's full name."""
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = user_repository.update_user(
            user_id=1,
            updates={'full_name': 'Ahmad Rizki Pratama'}
        )
        
        assert success is True
        mock_db_manager.execute_query.assert_called_once()
    
    def test_update_user_role(self, user_repository, mock_db_manager):
        """Test updating user's role."""
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = user_repository.update_user(
            user_id=1,
            updates={'role': 'guru'}
        )
        
        assert success is True
    
    def test_update_user_password(self, user_repository, mock_db_manager):
        """Test updating user's password."""
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = user_repository.update_user(
            user_id=1,
            updates={'password': 'newpassword123'}
        )
        
        assert success is True
        
        # Verify password was hashed
        call_args = mock_db_manager.execute_query.call_args
        assert 'password_hash' in call_args[0][1]
    
    def test_update_user_multiple_fields(self, user_repository, mock_db_manager):
        """Test updating multiple fields at once."""
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = user_repository.update_user(
            user_id=1,
            updates={
                'full_name': 'New Name',
                'role': 'guru'
            }
        )
        
        assert success is True
    
    def test_update_user_not_found(self, user_repository, mock_db_manager):
        """Test updating non-existent user."""
        mock_db_manager.execute_query.return_value = None
        
        success = user_repository.update_user(
            user_id=999,
            updates={'full_name': 'New Name'}
        )
        
        assert success is False
    
    def test_update_user_no_updates(self, user_repository, mock_db_manager):
        """Test update fails with no updates provided."""
        with pytest.raises(ValueError, match="No updates provided"):
            user_repository.update_user(user_id=1, updates={})
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_update_user_invalid_field(self, user_repository, mock_db_manager):
        """Test update fails with invalid field."""
        with pytest.raises(ValueError, match="Invalid update fields"):
            user_repository.update_user(
                user_id=1,
                updates={'invalid_field': 'value'}
            )
        
        mock_db_manager.execute_query.assert_not_called()
    
    def test_update_user_invalid_role(self, user_repository, mock_db_manager):
        """Test update fails with invalid role."""
        with pytest.raises(ValueError):
            user_repository.update_user(
                user_id=1,
                updates={'role': 'invalid_role'}
            )
        
        mock_db_manager.execute_query.assert_not_called()


class TestDeleteUser:
    """Tests for user deletion."""
    
    def test_delete_user_success(self, user_repository, mock_db_manager):
        """Test successful user deletion."""
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = user_repository.delete_user(user_id=1)
        
        assert success is True
        mock_db_manager.execute_query.assert_called_once()
    
    def test_delete_user_not_found(self, user_repository, mock_db_manager):
        """Test deleting non-existent user."""
        mock_db_manager.execute_query.return_value = None
        
        success = user_repository.delete_user(user_id=999)
        
        assert success is False
        mock_db_manager.execute_query.assert_called_once()


class TestVerifyPassword:
    """Tests for password verification."""
    
    def test_verify_password_success(self, user_repository, mock_db_manager, sample_user_data):
        """Test successful password verification."""
        mock_db_manager.execute_query.return_value = sample_user_data
        
        user = user_repository.verify_password("student1", "password123")
        
        assert user is not None
        assert user.username == "student1"
    
    def test_verify_password_wrong_password(self, user_repository, mock_db_manager, sample_user_data):
        """Test password verification fails with wrong password."""
        mock_db_manager.execute_query.return_value = sample_user_data
        
        user = user_repository.verify_password("student1", "wrongpassword")
        
        assert user is None
    
    def test_verify_password_user_not_found(self, user_repository, mock_db_manager):
        """Test password verification fails when user doesn't exist."""
        mock_db_manager.execute_query.return_value = None
        
        user = user_repository.verify_password("nonexistent", "password123")
        
        assert user is None


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_create_user_with_special_characters(self, user_repository, mock_db_manager, sample_user_data):
        """Test creating user with special characters in name."""
        sample_user_data['full_name'] = "O'Brien-Smith"
        mock_db_manager.execute_query.return_value = sample_user_data
        
        user = user_repository.create_user(
            username="student1",
            password="password123",
            role="siswa",
            full_name="O'Brien-Smith"
        )
        
        assert user.full_name == "O'Brien-Smith"
    
    def test_username_case_sensitivity(self, user_repository, mock_db_manager, sample_user_data):
        """Test that usernames are case-sensitive."""
        mock_db_manager.execute_query.return_value = sample_user_data
        
        user_repository.get_user_by_username("Student1")
        
        # Verify exact username was used in query
        call_args = mock_db_manager.execute_query.call_args
        assert call_args[0][1]['username'] == "Student1"
    
    def test_database_error_handling(self, user_repository, mock_db_manager):
        """Test proper error handling for database errors."""
        mock_db_manager.execute_query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            user_repository.get_user_by_username("student1")
