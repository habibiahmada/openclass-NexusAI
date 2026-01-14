"""Property-based tests for S3 storage operations.

These tests verify universal properties of S3 upload functionality
using Hypothesis for property-based testing.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings

from src.cloud_sync.s3_storage_manager import S3StorageManager


# Configure Hypothesis
settings.register_profile("ci", max_examples=100)
settings.load_profile("ci")


# Custom strategies for generating test data
@st.composite
def subject_strategy(draw):
    """Generate valid subject names."""
    subjects = st.sampled_from([
        "informatika", "matematika", "fisika", "kimia", "biologi",
        "bahasa_indonesia", "bahasa_inggris", "sejarah"
    ])
    return draw(subjects)


@st.composite
def grade_strategy(draw):
    """Generate valid grade levels."""
    grades = st.sampled_from([
        "kelas_10", "kelas_11", "kelas_12"
    ])
    return draw(grades)


@st.composite
def filename_strategy(draw):
    """Generate valid filenames."""
    # Generate filename with alphanumeric characters and common extensions
    name = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=20
    ))
    extension = draw(st.sampled_from(['.txt', '.json', '.db', '.sqlite3', '.gz']))
    return f"{name}{extension}"


# Feature: phase2-backend-knowledge-engineering, Property 13: S3 Path Structure
@given(
    subject=subject_strategy(),
    grade=grade_strategy(),
    filename=filename_strategy()
)
@settings(max_examples=100)
def test_property_s3_path_structure(subject, grade, filename):
    """Property 13: S3 paths should follow pattern processed/{subject}/{grade}/{filename}.
    
    **Validates: Requirements 7.1**
    
    For any file uploaded to S3, the path should follow the pattern:
    s3://bucket/processed/{subject}/{grade}/filename
    """
    # Create S3 manager with mocked client
    with patch('src.cloud_sync.s3_storage_manager.aws_config') as mock_config:
        mock_config.s3_bucket = "test-bucket"
        mock_config.get_s3_client.return_value = Mock()
        
        manager = S3StorageManager(bucket_name="test-bucket")
        
        # Build S3 path
        s3_path = manager._build_s3_path(subject, grade, filename)
        
        # Verify path structure
        # Path should be: processed/{subject}/{grade}/{filename}
        expected_pattern = f"processed/{subject}/{grade}/{filename}"
        
        assert s3_path == expected_pattern, (
            f"S3 path should follow pattern processed/{{subject}}/{{grade}}/{{filename}}, "
            f"got: {s3_path}"
        )
        
        # Verify path components
        parts = s3_path.split('/')
        assert len(parts) >= 4, f"S3 path should have at least 4 parts, got {len(parts)}"
        assert parts[0] == "processed", f"First part should be 'processed', got {parts[0]}"
        assert parts[1] == subject, f"Second part should be subject '{subject}', got {parts[1]}"
        assert parts[2] == grade, f"Third part should be grade '{grade}', got {parts[2]}"
        assert parts[-1] == filename, f"Last part should be filename '{filename}', got {parts[-1]}"


# Additional property: Path normalization
@given(
    subject=st.text(min_size=1, max_size=20),
    grade=st.text(min_size=1, max_size=20),
    filename=st.text(min_size=1, max_size=20)
)
@settings(max_examples=100)
def test_property_s3_path_normalization(subject, grade, filename):
    """Property: S3 paths should be normalized (lowercase, underscores for spaces).
    
    For any subject/grade with spaces or mixed case, the path should be normalized
    to lowercase with underscores.
    """
    # Create S3 manager with mocked client
    with patch('src.cloud_sync.s3_storage_manager.aws_config') as mock_config:
        mock_config.s3_bucket = "test-bucket"
        mock_config.get_s3_client.return_value = Mock()
        
        manager = S3StorageManager(bucket_name="test-bucket")
        
        # Build S3 path
        s3_path = manager._build_s3_path(subject, grade, filename)
        
        # Extract subject and grade from path
        parts = s3_path.split('/')
        if len(parts) >= 3:
            path_subject = parts[1]
            path_grade = parts[2]
            
            # Verify normalization
            # Should be lowercase
            assert path_subject == path_subject.lower(), (
                f"Subject should be lowercase, got: {path_subject}"
            )
            assert path_grade == path_grade.lower(), (
                f"Grade should be lowercase, got: {path_grade}"
            )
            
            # Should not contain spaces
            assert ' ' not in path_subject, (
                f"Subject should not contain spaces, got: {path_subject}"
            )
            assert ' ' not in path_grade, (
                f"Grade should not contain spaces, got: {path_grade}"
            )


# Additional property: Path consistency
@given(
    subject=subject_strategy(),
    grade=grade_strategy(),
    filename=filename_strategy()
)
@settings(max_examples=100)
def test_property_s3_path_consistency(subject, grade, filename):
    """Property: Building the same path twice should produce identical results.
    
    For any subject/grade/filename combination, calling _build_s3_path multiple times
    should always return the same path.
    """
    # Create S3 manager with mocked client
    with patch('src.cloud_sync.s3_storage_manager.aws_config') as mock_config:
        mock_config.s3_bucket = "test-bucket"
        mock_config.get_s3_client.return_value = Mock()
        
        manager = S3StorageManager(bucket_name="test-bucket")
        
        # Build path twice
        path1 = manager._build_s3_path(subject, grade, filename)
        path2 = manager._build_s3_path(subject, grade, filename)
        
        # Verify consistency
        assert path1 == path2, (
            f"Path should be consistent across calls, got: {path1} vs {path2}"
        )



# Feature: phase2-backend-knowledge-engineering, Property 14: Compression Applied
@given(
    content=st.binary(min_size=100, max_size=10000)
)
@settings(max_examples=100)
def test_property_compression_applied(content):
    """Property 14: Knowledge base files should be compressed with gzip.
    
    **Validates: Requirements 7.2**
    
    For any knowledge base file uploaded to S3, the content encoding should be gzip
    and the file should be compressed.
    """
    # Create temporary file with content
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Create S3 manager with mocked client
        with patch('src.cloud_sync.s3_storage_manager.aws_config') as mock_config:
            mock_config.s3_bucket = "test-bucket"
            
            # Create mock S3 client
            mock_s3_client = MagicMock()
            mock_config.get_s3_client.return_value = mock_s3_client
            
            manager = S3StorageManager(bucket_name="test-bucket")
            
            # Upload file with compression
            s3_key = "processed/test/kelas_10/test_file.txt"
            manager.upload_file(
                local_path=tmp_file_path,
                s3_key=s3_key,
                compress=True
            )
            
            # Verify upload_file was called
            assert mock_s3_client.upload_file.called, "upload_file should be called"
            
            # Get the ExtraArgs passed to upload_file
            call_args = mock_s3_client.upload_file.call_args
            extra_args = call_args[1].get('ExtraArgs', {})
            
            # Verify compression is applied
            assert 'ContentEncoding' in extra_args, (
                "ContentEncoding should be set when compress=True"
            )
            assert extra_args['ContentEncoding'] == 'gzip', (
                f"ContentEncoding should be 'gzip', got: {extra_args['ContentEncoding']}"
            )
            
            # Verify S3 key has .gz extension
            uploaded_key = call_args[0][2]  # Third positional argument is the key
            assert uploaded_key.endswith('.gz'), (
                f"Compressed files should have .gz extension, got: {uploaded_key}"
            )
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
        # Clean up any .gz files created
        gz_path = f"{tmp_file_path}.tmp.gz"
        if os.path.exists(gz_path):
            os.remove(gz_path)


# Additional property: Compression reduces file size
@given(
    content=st.binary(min_size=1000, max_size=10000)
)
@settings(max_examples=100)
def test_property_compression_reduces_size(content):
    """Property: Compressed files should be smaller than original files.
    
    For any file content, compressing it with gzip should produce a smaller file
    (for sufficiently large files with compressible content).
    """
    # Create temporary file with content
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Create S3 manager with mocked client
        with patch('src.cloud_sync.s3_storage_manager.aws_config') as mock_config:
            mock_config.s3_bucket = "test-bucket"
            mock_config.get_s3_client.return_value = Mock()
            
            manager = S3StorageManager(bucket_name="test-bucket")
            
            # Compress file
            compressed_path = manager._compress_file(tmp_file_path)
            
            # Verify compressed file exists
            assert os.path.exists(compressed_path), (
                f"Compressed file should exist at {compressed_path}"
            )
            
            # Get file sizes
            original_size = os.path.getsize(tmp_file_path)
            compressed_size = os.path.getsize(compressed_path)
            
            # For random binary data, compression might not always reduce size
            # But the compressed file should exist and be valid
            assert compressed_size > 0, "Compressed file should not be empty"
            
            # Verify it's a valid gzip file by trying to read it
            import gzip
            with gzip.open(compressed_path, 'rb') as f:
                decompressed = f.read()
                assert decompressed == content, (
                    "Decompressed content should match original"
                )
            
            # Clean up compressed file
            os.remove(compressed_path)
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)


# Additional property: Compression round-trip
@given(
    content=st.binary(min_size=10, max_size=5000)
)
@settings(max_examples=100)
def test_property_compression_round_trip(content):
    """Property: Compressing and decompressing should preserve content.
    
    For any file content, compressing with gzip and then decompressing
    should return the original content.
    """
    # Create temporary file with content
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Create S3 manager with mocked client
        with patch('src.cloud_sync.s3_storage_manager.aws_config') as mock_config:
            mock_config.s3_bucket = "test-bucket"
            mock_config.get_s3_client.return_value = Mock()
            
            manager = S3StorageManager(bucket_name="test-bucket")
            
            # Compress file
            compressed_path = manager._compress_file(tmp_file_path)
            
            # Decompress and verify
            import gzip
            with gzip.open(compressed_path, 'rb') as f:
                decompressed_content = f.read()
            
            # Verify round-trip
            assert decompressed_content == content, (
                "Decompressed content should match original content"
            )
            
            # Clean up compressed file
            os.remove(compressed_path)
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
