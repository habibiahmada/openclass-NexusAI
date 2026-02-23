"""
Unit tests for SubjectRepository and BookRepository

Tests the CRUD operations for subjects and books with VKP version tracking.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.persistence import (
    DatabaseManager,
    SubjectRepository,
    Subject,
    BookRepository,
    Book
)


@pytest.fixture
def mock_db_manager():
    """Create a mock DatabaseManager for testing."""
    return Mock(spec=DatabaseManager)


@pytest.fixture
def subject_repo(mock_db_manager):
    """Create a SubjectRepository instance with mock database."""
    return SubjectRepository(mock_db_manager)


@pytest.fixture
def book_repo(mock_db_manager):
    """Create a BookRepository instance with mock database."""
    return BookRepository(mock_db_manager)


class TestSubjectRepository:
    """Test cases for SubjectRepository."""
    
    def test_create_subject(self, subject_repo, mock_db_manager):
        """Test creating a new subject."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'grade': 10,
            'name': 'Matematika',
            'code': 'MAT_10',
            'created_at': datetime.now()
        }
        
        subject = subject_repo.create_subject(
            grade=10,
            name="Matematika",
            code="MAT_10"
        )
        
        assert subject.id == 1
        assert subject.grade == 10
        assert subject.name == "Matematika"
        assert subject.code == "MAT_10"
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_all_subjects(self, subject_repo, mock_db_manager):
        """Test retrieving all subjects."""
        mock_db_manager.execute_query.return_value = [
            {'id': 1, 'grade': 10, 'name': 'Matematika', 'code': 'MAT_10', 'created_at': datetime.now()},
            {'id': 2, 'grade': 11, 'name': 'Informatika', 'code': 'INF_11', 'created_at': datetime.now()}
        ]
        
        subjects = subject_repo.get_all_subjects()
        
        assert len(subjects) == 2
        assert subjects[0].code == "MAT_10"
        assert subjects[1].code == "INF_11"
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_subjects_by_grade(self, subject_repo, mock_db_manager):
        """Test retrieving subjects by grade."""
        mock_db_manager.execute_query.return_value = [
            {'id': 1, 'grade': 10, 'name': 'Matematika', 'code': 'MAT_10', 'created_at': datetime.now()},
            {'id': 2, 'grade': 10, 'name': 'Fisika', 'code': 'FIS_10', 'created_at': datetime.now()}
        ]
        
        subjects = subject_repo.get_subjects_by_grade(10)
        
        assert len(subjects) == 2
        assert all(s.grade == 10 for s in subjects)
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_subject_by_id(self, subject_repo, mock_db_manager):
        """Test retrieving subject by ID."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'grade': 10,
            'name': 'Matematika',
            'code': 'MAT_10',
            'created_at': datetime.now()
        }
        
        subject = subject_repo.get_subject_by_id(1)
        
        assert subject is not None
        assert subject.id == 1
        assert subject.name == "Matematika"
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_subject_by_code(self, subject_repo, mock_db_manager):
        """Test retrieving subject by code."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'grade': 10,
            'name': 'Matematika',
            'code': 'MAT_10',
            'created_at': datetime.now()
        }
        
        subject = subject_repo.get_subject_by_code("MAT_10")
        
        assert subject is not None
        assert subject.code == "MAT_10"
        mock_db_manager.execute_query.assert_called_once()
    
    def test_update_subject(self, subject_repo, mock_db_manager):
        """Test updating a subject."""
        # Mock get_subject_by_id for validation
        mock_db_manager.execute_query.side_effect = [
            {'id': 1, 'grade': 10, 'name': 'Matematika', 'code': 'MAT_10', 'created_at': datetime.now()},
            {'id': 1}  # Update result
        ]
        
        success = subject_repo.update_subject(
            1,
            {'name': 'Matematika Lanjutan'}
        )
        
        assert success is True
        assert mock_db_manager.execute_query.call_count == 2
    
    def test_delete_subject(self, subject_repo, mock_db_manager):
        """Test deleting a subject."""
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = subject_repo.delete_subject(1)
        
        assert success is True
        mock_db_manager.execute_query.assert_called_once()
    
    def test_validate_grade_invalid(self, subject_repo):
        """Test grade validation with invalid grade."""
        with pytest.raises(ValueError, match="Grade must be 10, 11, or 12"):
            subject_repo.create_subject(9, "Invalid", "INV_9")
    
    def test_validate_name_too_short(self, subject_repo):
        """Test name validation with short name."""
        with pytest.raises(ValueError, match="at least 2 characters"):
            subject_repo.create_subject(10, "M", "MAT_10")
    
    def test_validate_code_too_long(self, subject_repo):
        """Test code validation with long code."""
        long_code = "A" * 51
        with pytest.raises(ValueError, match="must not exceed 50 characters"):
            subject_repo.create_subject(10, "Matematika", long_code)


class TestBookRepository:
    """Test cases for BookRepository."""
    
    def test_create_book(self, book_repo, mock_db_manager):
        """Test creating a new book."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'subject_id': 1,
            'title': 'Matematika Kelas 10 Semester 1',
            'filename': 'Matematika_Kelas_10_Semester_1.pdf',
            'vkp_version': '1.0.0',
            'chunk_count': 0,
            'created_at': datetime.now()
        }
        
        book = book_repo.create_book(
            subject_id=1,
            title="Matematika Kelas 10 Semester 1",
            filename="Matematika_Kelas_10_Semester_1.pdf",
            vkp_version="1.0.0"
        )
        
        assert book.id == 1
        assert book.subject_id == 1
        assert book.title == "Matematika Kelas 10 Semester 1"
        assert book.vkp_version == "1.0.0"
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_books_by_subject(self, book_repo, mock_db_manager):
        """Test retrieving books by subject."""
        mock_db_manager.execute_query.return_value = [
            {
                'id': 1,
                'subject_id': 1,
                'title': 'Book 1',
                'filename': 'book1.pdf',
                'vkp_version': '1.0.0',
                'chunk_count': 100,
                'created_at': datetime.now()
            },
            {
                'id': 2,
                'subject_id': 1,
                'title': 'Book 2',
                'filename': 'book2.pdf',
                'vkp_version': '1.1.0',
                'chunk_count': 150,
                'created_at': datetime.now()
            }
        ]
        
        books = book_repo.get_books_by_subject(1)
        
        assert len(books) == 2
        assert books[0].title == "Book 1"
        assert books[1].title == "Book 2"
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_book_by_id(self, book_repo, mock_db_manager):
        """Test retrieving book by ID."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'subject_id': 1,
            'title': 'Test Book',
            'filename': 'test.pdf',
            'vkp_version': '1.0.0',
            'chunk_count': 100,
            'created_at': datetime.now()
        }
        
        book = book_repo.get_book_by_id(1)
        
        assert book is not None
        assert book.id == 1
        assert book.title == "Test Book"
        mock_db_manager.execute_query.assert_called_once()
    
    def test_update_book_version(self, book_repo, mock_db_manager):
        """Test updating book VKP version."""
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = book_repo.update_book_version(1, "1.2.0")
        
        assert success is True
        mock_db_manager.execute_query.assert_called_once()
    
    def test_update_book_chunk_count(self, book_repo, mock_db_manager):
        """Test updating book chunk count."""
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = book_repo.update_book_chunk_count(1, 450)
        
        assert success is True
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_book_by_version(self, book_repo, mock_db_manager):
        """Test retrieving book by VKP version."""
        mock_db_manager.execute_query.return_value = {
            'id': 1,
            'subject_id': 1,
            'title': 'Test Book',
            'filename': 'test.pdf',
            'vkp_version': '1.5.0',
            'chunk_count': 100,
            'created_at': datetime.now()
        }
        
        book = book_repo.get_book_by_version("1.5.0")
        
        assert book is not None
        assert book.vkp_version == "1.5.0"
        mock_db_manager.execute_query.assert_called_once()
    
    def test_validate_vkp_version_format_invalid(self, book_repo):
        """Test VKP version format validation with invalid format."""
        with pytest.raises(ValueError, match="semantic versioning"):
            book_repo.create_book(
                subject_id=1,
                title="Test Book",
                vkp_version="1.0"  # Invalid: should be MAJOR.MINOR.PATCH
            )
    
    def test_validate_title_too_short(self, book_repo):
        """Test title validation with short title."""
        with pytest.raises(ValueError, match="at least 2 characters"):
            book_repo.create_book(
                subject_id=1,
                title="A",
                vkp_version="1.0.0"
            )
    
    def test_validate_chunk_count_negative(self, book_repo):
        """Test chunk count validation with negative value."""
        with pytest.raises(ValueError, match="cannot be negative"):
            book_repo.update_book_chunk_count(1, -10)
    
    def test_delete_book(self, book_repo, mock_db_manager):
        """Test deleting a book."""
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = book_repo.delete_book(1)
        
        assert success is True
        mock_db_manager.execute_query.assert_called_once()
    
    def test_get_all_books(self, book_repo, mock_db_manager):
        """Test retrieving all books."""
        mock_db_manager.execute_query.return_value = [
            {
                'id': 1,
                'subject_id': 1,
                'title': 'Book 1',
                'filename': 'book1.pdf',
                'vkp_version': '1.0.0',
                'chunk_count': 100,
                'created_at': datetime.now()
            },
            {
                'id': 2,
                'subject_id': 2,
                'title': 'Book 2',
                'filename': 'book2.pdf',
                'vkp_version': '1.1.0',
                'chunk_count': 150,
                'created_at': datetime.now()
            }
        ]
        
        books = book_repo.get_all_books()
        
        assert len(books) == 2
        assert books[0].title == "Book 1"
        assert books[1].title == "Book 2"
        mock_db_manager.execute_query.assert_called_once()
    
    def test_update_book(self, book_repo, mock_db_manager):
        """Test updating book information."""
        mock_db_manager.execute_query.return_value = {'id': 1}
        
        success = book_repo.update_book(
            1,
            {
                'title': 'Updated Title',
                'vkp_version': '1.3.0'
            }
        )
        
        assert success is True
        mock_db_manager.execute_query.assert_called_once()
    
    def test_update_book_invalid_field(self, book_repo):
        """Test updating book with invalid field."""
        with pytest.raises(ValueError, match="Invalid update fields"):
            book_repo.update_book(
                1,
                {'invalid_field': 'value'}
            )


class TestSubjectModel:
    """Test cases for Subject data model."""
    
    def test_subject_to_dict(self):
        """Test Subject to_dict conversion."""
        subject = Subject(
            id=1,
            grade=10,
            name="Matematika",
            code="MAT_10",
            created_at=datetime.now()
        )
        
        data = subject.to_dict()
        
        assert data['id'] == 1
        assert data['grade'] == 10
        assert data['name'] == "Matematika"
        assert data['code'] == "MAT_10"
    
    def test_subject_from_dict(self):
        """Test Subject from_dict creation."""
        data = {
            'id': 1,
            'grade': 10,
            'name': 'Matematika',
            'code': 'MAT_10',
            'created_at': datetime.now()
        }
        
        subject = Subject.from_dict(data)
        
        assert subject.id == 1
        assert subject.grade == 10
        assert subject.name == "Matematika"
        assert subject.code == "MAT_10"


class TestBookModel:
    """Test cases for Book data model."""
    
    def test_book_to_dict(self):
        """Test Book to_dict conversion."""
        book = Book(
            id=1,
            subject_id=1,
            title="Test Book",
            filename="test.pdf",
            vkp_version="1.0.0",
            chunk_count=100,
            created_at=datetime.now()
        )
        
        data = book.to_dict()
        
        assert data['id'] == 1
        assert data['subject_id'] == 1
        assert data['title'] == "Test Book"
        assert data['vkp_version'] == "1.0.0"
        assert data['chunk_count'] == 100
    
    def test_book_from_dict(self):
        """Test Book from_dict creation."""
        data = {
            'id': 1,
            'subject_id': 1,
            'title': 'Test Book',
            'filename': 'test.pdf',
            'vkp_version': '1.0.0',
            'chunk_count': 100,
            'created_at': datetime.now()
        }
        
        book = Book.from_dict(data)
        
        assert book.id == 1
        assert book.subject_id == 1
        assert book.title == "Test Book"
        assert book.vkp_version == "1.0.0"
        assert book.chunk_count == 100

