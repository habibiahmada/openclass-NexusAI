"""Unit tests for S3 Storage Manager.

These tests verify specific examples and edge cases for S3 upload functionality.
"""

import gzip
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

import pytest
from botocore.exceptions import ClientError

from src.aws_control_plane.s3_storage_manager import S3StorageManager, UploadResult


@pytest.fixture
def mock_aws_config():
    """Mock AWS configuration."""
    with patch('src.aws_control_plane.s3_storage_manager.aws_config') as mock_config:
        mock_config.s3_bucket = "test-bucket"
        mock_config.get_s3_client.return_value = MagicMock()
        yield mock_config


@pytest.fixture
def s3_manager(mock_aws_config):
    """Create S3 storage manager with mocked AWS config."""
    return S3StorageManager(bucket_name="test-bucket")


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content for S3 upload\n" * 100)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)
    # Clean up any .gz files
    gz_path = f"{temp_path}.tmp.gz"
    if os.path.exists(gz_path):
        os.remove(gz_path)


class TestS3PathStructure:
    """Test S3 path structure generation."""
    
    def test_build_s3_path_correct_structure(self, s3_manager):
        """Test that S3 path follows correct structure."""
        # Requirements: 7.1
        s3_path = s3_manager._build_s3_path(
            subject="informatika",
            grade="kelas_10",
            filename="test.txt"
        )
        
        assert s3_path == "processed/informatika/kelas_10/test.txt"
    
    def test_build_s3_path_normalizes_subject(self, s3_manager):
        """Test that subject is normalized to lowercase with underscores."""
        # Requirements: 7.1
        s3_path = s3_manager._build_s3_path(
            subject="Bahasa Indonesia",
            grade="kelas_10",
            filename="test.txt"
        )
        
        assert "bahasa_indonesia" in s3_path
        assert " " not in s3_path
    
    def test_build_s3_path_normalizes_grade(self, s3_manager):
        """Test that grade is normalized to lowercase with underscores."""
        # Requirements: 7.1
        s3_path = s3_manager._build_s3_path(
            subject="informatika",
            grade="Kelas 10",
            filename="test.txt"
        )
        
        assert "kelas_10" in s3_path
        assert " " not in s3_path
    
    def test_build_s3_path_with_nested_filename(self, s3_manager):
        """Test path building with nested filename (e.g., chromadb/file.db)."""
        # Requirements: 7.1
        s3_path = s3_manager._build_s3_path(
            subject="informatika",
            grade="kelas_10",
            filename="chromadb/chroma.sqlite3"
        )
        
        assert s3_path == "processed/informatika/kelas_10/chromadb/chroma.sqlite3"


class TestCompression:
    """Test file compression functionality."""
    
    def test_compress_file_creates_gz_file(self, s3_manager, temp_file):
        """Test that compression creates a .gz file."""
        # Requirements: 7.2
        compressed_path = s3_manager._compress_file(temp_file)
        
        assert compressed_path.endswith('.gz')
        assert os.path.exists(compressed_path)
        
        # Cleanup
        os.remove(compressed_path)
    
    def test_compress_file_preserves_content(self, s3_manager, temp_file):
        """Test that compression preserves file content."""
        # Requirements: 7.2
        # Read original content
        with open(temp_file, 'rb') as f:
            original_content = f.read()
        
        # Compress
        compressed_path = s3_manager._compress_file(temp_file)
        
        # Decompress and verify
        with gzip.open(compressed_path, 'rb') as f:
            decompressed_content = f.read()
        
        assert decompressed_content == original_content
        
        # Cleanup
        os.remove(compressed_path)
    
    def test_compress_file_reduces_size(self, s3_manager):
        """Test that compression reduces file size for compressible content."""
        # Requirements: 7.2
        # Create file with highly compressible content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("A" * 10000)  # Highly compressible
            temp_path = f.name
        
        try:
            compressed_path = s3_manager._compress_file(temp_path)
            
            original_size = os.path.getsize(temp_path)
            compressed_size = os.path.getsize(compressed_path)
            
            # Compressed should be significantly smaller
            assert compressed_size < original_size
            assert compressed_size < original_size * 0.1  # At least 90% reduction
            
            # Cleanup
            os.remove(compressed_path)
        finally:
            os.remove(temp_path)
    
    def test_compress_file_custom_output_path(self, s3_manager, temp_file):
        """Test compression with custom output path."""
        # Requirements: 7.2
        custom_output = temp_file + ".custom.gz"
        
        compressed_path = s3_manager._compress_file(temp_file, custom_output)
        
        assert compressed_path == custom_output
        assert os.path.exists(custom_output)
        
        # Cleanup
        os.remove(custom_output)


class TestUploadFile:
    """Test single file upload functionality."""
    
    def test_upload_file_with_compression(self, s3_manager, temp_file):
        """Test uploading file with compression enabled."""
        # Requirements: 7.2, 7.3, 7.5
        s3_key = "processed/informatika/kelas_10/test.txt"
        
        success = s3_manager.upload_file(
            local_path=temp_file,
            s3_key=s3_key,
            compress=True
        )
        
        assert success
        
        # Verify S3 client was called
        assert s3_manager.s3_client.upload_file.called
        
        # Verify ExtraArgs
        call_args = s3_manager.s3_client.upload_file.call_args
        extra_args = call_args[1]['ExtraArgs']
        
        assert extra_args['ContentEncoding'] == 'gzip'
        assert extra_args['StorageClass'] == 'STANDARD_IA'
        assert extra_args['ServerSideEncryption'] == 'AES256'
    
    def test_upload_file_without_compression(self, s3_manager, temp_file):
        """Test uploading file without compression."""
        # Requirements: 7.3, 7.5
        s3_key = "processed/informatika/kelas_10/test.txt"
        
        success = s3_manager.upload_file(
            local_path=temp_file,
            s3_key=s3_key,
            compress=False
        )
        
        assert success
        
        # Verify ExtraArgs
        call_args = s3_manager.s3_client.upload_file.call_args
        extra_args = call_args[1]['ExtraArgs']
        
        assert 'ContentEncoding' not in extra_args
        assert extra_args['StorageClass'] == 'STANDARD_IA'
        assert extra_args['ServerSideEncryption'] == 'AES256'
    
    def test_upload_file_storage_class_configuration(self, s3_manager, temp_file):
        """Test that storage class is set to Standard-IA."""
        # Requirements: 7.3
        s3_key = "processed/informatika/kelas_10/test.txt"
        
        s3_manager.upload_file(
            local_path=temp_file,
            s3_key=s3_key,
            storage_class="STANDARD_IA"
        )
        
        call_args = s3_manager.s3_client.upload_file.call_args
        extra_args = call_args[1]['ExtraArgs']
        
        assert extra_args['StorageClass'] == 'STANDARD_IA'
    
    def test_upload_file_encryption_settings(self, s3_manager, temp_file):
        """Test that server-side encryption is enabled with AES-256."""
        # Requirements: 7.5
        s3_key = "processed/informatika/kelas_10/test.txt"
        
        s3_manager.upload_file(
            local_path=temp_file,
            s3_key=s3_key,
            encryption="AES256"
        )
        
        call_args = s3_manager.s3_client.upload_file.call_args
        extra_args = call_args[1]['ExtraArgs']
        
        assert extra_args['ServerSideEncryption'] == 'AES256'
    
    def test_upload_file_nonexistent_file(self, s3_manager):
        """Test uploading a file that doesn't exist."""
        success = s3_manager.upload_file(
            local_path="/nonexistent/file.txt",
            s3_key="processed/test/test.txt"
        )
        
        assert not success
    
    def test_upload_file_s3_error(self, s3_manager, temp_file):
        """Test handling S3 upload errors."""
        # Mock S3 client to raise error
        s3_manager.s3_client.upload_file.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
            'upload_file'
        )
        
        success = s3_manager.upload_file(
            local_path=temp_file,
            s3_key="processed/test/test.txt"
        )
        
        assert not success


class TestUploadChromaDBFiles:
    """Test ChromaDB files upload functionality."""
    
    def test_upload_chromadb_files_success(self, s3_manager):
        """Test uploading ChromaDB files successfully."""
        # Requirements: 7.1, 7.2, 7.3, 7.5
        # Create temporary ChromaDB directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock ChromaDB files
            db_file = Path(temp_dir) / "chroma.sqlite3"
            db_file.write_text("mock database content")
            
            index_dir = Path(temp_dir) / "index"
            index_dir.mkdir()
            index_file = index_dir / "index.bin"
            index_file.write_text("mock index content")
            
            # Upload
            result = s3_manager.upload_chromadb_files(
                chromadb_dir=temp_dir,
                subject="informatika",
                grade="kelas_10"
            )
            
            assert result.successful_uploads == 2
            assert result.failed_uploads == 0
            assert len(result.uploaded_files) == 2
    
    def test_upload_chromadb_files_nonexistent_directory(self, s3_manager):
        """Test uploading from nonexistent directory."""
        result = s3_manager.upload_chromadb_files(
            chromadb_dir="/nonexistent/directory",
            subject="informatika",
            grade="kelas_10"
        )
        
        assert result.successful_uploads == 0
        assert len(result.errors) > 0


class TestUploadProcessedText:
    """Test processed text files upload functionality."""
    
    def test_upload_processed_text_success(self, s3_manager):
        """Test uploading processed text files successfully."""
        # Requirements: 7.1, 7.2, 7.3, 7.5
        # Create temporary text directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock text files
            text_file1 = Path(temp_dir) / "file1.txt"
            text_file1.write_text("content 1")
            
            text_file2 = Path(temp_dir) / "file2.txt"
            text_file2.write_text("content 2")
            
            # Upload
            result = s3_manager.upload_processed_text(
                text_dir=temp_dir,
                subject="informatika",
                grade="kelas_10"
            )
            
            assert result.successful_uploads == 2
            assert result.failed_uploads == 0
            assert len(result.uploaded_files) == 2


class TestUploadMetadata:
    """Test metadata files upload functionality."""
    
    def test_upload_metadata_success(self, s3_manager):
        """Test uploading metadata files successfully."""
        # Requirements: 7.1, 7.3, 7.5
        # Create temporary metadata directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock metadata files
            meta_file = Path(temp_dir) / "pipeline_report.json"
            meta_file.write_text(json.dumps({"status": "success"}))
            
            # Upload
            result = s3_manager.upload_metadata(
                metadata_dir=temp_dir,
                subject="informatika",
                grade="kelas_10"
            )
            
            assert result.successful_uploads == 1
            assert result.failed_uploads == 0
            assert len(result.uploaded_files) == 1


class TestVerifyUpload:
    """Test upload verification functionality."""
    
    def test_verify_upload_exists(self, s3_manager):
        """Test verifying an existing file."""
        # Mock head_object to succeed
        s3_manager.s3_client.head_object.return_value = {'ContentLength': 100}
        
        exists = s3_manager.verify_upload("processed/test/file.txt")
        
        assert exists
    
    def test_verify_upload_not_exists(self, s3_manager):
        """Test verifying a non-existent file."""
        # Mock head_object to raise error
        s3_manager.s3_client.head_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
            'head_object'
        )
        
        exists = s3_manager.verify_upload("processed/test/nonexistent.txt")
        
        assert not exists


class TestListUploadedFiles:
    """Test listing uploaded files functionality."""
    
    def test_list_uploaded_files_success(self, s3_manager):
        """Test listing files with a prefix."""
        # Mock list_objects_v2 response
        s3_manager.s3_client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'processed/informatika/kelas_10/file1.txt',
                    'Size': 1024,
                    'LastModified': '2026-01-14',
                    'StorageClass': 'STANDARD_IA'
                },
                {
                    'Key': 'processed/informatika/kelas_10/file2.txt',
                    'Size': 2048,
                    'LastModified': '2026-01-14',
                    'StorageClass': 'STANDARD_IA'
                }
            ]
        }
        
        files = s3_manager.list_uploaded_files("processed/informatika/kelas_10/")
        
        assert len(files) == 2
        assert files[0]['key'] == 'processed/informatika/kelas_10/file1.txt'
        assert files[0]['size'] == 1024
    
    def test_list_uploaded_files_empty(self, s3_manager):
        """Test listing files when no files exist."""
        # Mock empty response
        s3_manager.s3_client.list_objects_v2.return_value = {}
        
        files = s3_manager.list_uploaded_files("processed/empty/")
        
        assert len(files) == 0
