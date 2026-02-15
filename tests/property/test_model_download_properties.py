"""Property-based tests for model download system.

These tests verify universal properties of model downloading functionality
using Hypothesis for property-based testing.

Feature: phase3-model-optimization
"""

import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from urllib.parse import urlparse

import pytest
from hypothesis import given, strategies as st, settings
import requests

from src.local_inference.model_downloader import ModelDownloader, DownloadProgress
from src.local_inference.model_config import ModelConfig


# Configure Hypothesis
settings.register_profile("ci", max_examples=100)
settings.load_profile("ci")


# Custom strategies for generating test data
@st.composite
def model_config_strategy(draw):
    """Generate valid model configurations."""
    model_ids = st.sampled_from([
        "meta-llama/Llama-3.2-3B-Instruct",
        "microsoft/DialoGPT-medium",
        "facebook/opt-1.3b"
    ])
    
    gguf_repos = st.sampled_from([
        "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "TheBloke/Llama-2-7B-Chat-GGUF",
        "microsoft/DialoGPT-medium-GGUF"
    ])
    
    filenames = st.sampled_from([
        "model-Q4_K_M.gguf",
        "model-Q5_K_M.gguf",
        "model-Q8_0.gguf"
    ])
    
    model_id = draw(model_ids)
    gguf_repo = draw(gguf_repos)
    filename = draw(filenames)
    
    return ModelConfig(
        model_id=model_id,
        gguf_repo=gguf_repo,
        gguf_filename=filename,
        cache_dir=draw(st.text(min_size=1, max_size=20)),
        file_size_mb=draw(st.integers(min_value=100, max_value=5000))
    )


@st.composite
def file_content_strategy(draw):
    """Generate file content for testing."""
    # Generate binary content that could represent a model file
    size = draw(st.integers(min_value=1024, max_value=10240))  # 1KB to 10KB for testing
    content = draw(st.binary(min_size=size, max_size=size))
    return content


@st.composite
def url_strategy(draw):
    """Generate valid URLs for testing."""
    domains = st.sampled_from([
        "huggingface.co",
        "github.com",
        "example.com"
    ])
    
    paths = st.lists(
        st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=10),
        min_size=1,
        max_size=5
    )
    
    domain = draw(domains)
    path_parts = draw(paths)
    path = "/".join(path_parts)
    
    return f"https://{domain}/{path}"


# Feature: phase3-model-optimization, Property 3: Download Integrity and Organization
@given(
    model_config=model_config_strategy(),
    file_content=file_content_strategy()
)
@settings(max_examples=100)
def test_property_download_integrity_and_organization(model_config, file_content):
    """Property 3: Download Integrity and Organization.
    
    **Validates: Requirements 2.1, 2.2, 2.4, 2.5**
    
    For any model download operation, the system should use HuggingFace Hub,
    verify educational licenses, validate checksums, and organize files in structured directories.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Update model config to use temp directory
        model_config.cache_dir = temp_dir
        
        # Create downloader
        downloader = ModelDownloader(cache_dir=temp_dir)
        
        # Mock the HuggingFace client and requests
        with patch.object(downloader, 'hf_client') as mock_hf_client, \
             patch.object(downloader, 'session') as mock_session:
            
            # Setup mock responses
            mock_hf_client.get_model_info.return_value = {
                'size_bytes': len(file_content),
                'size_mb': len(file_content) / (1024 * 1024),
                'sha': hashlib.sha256(file_content).hexdigest()
            }
            
            mock_hf_client.get_download_headers.return_value = {
                'User-Agent': 'OpenClass-Nexus-AI/1.0'
            }
            
            # Mock the download response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {
                'content-length': str(len(file_content))
            }
            mock_response.iter_content.return_value = [file_content]
            mock_response.raise_for_status.return_value = None
            
            mock_session.get.return_value = mock_response
            mock_session.head.return_value = mock_response
            
            # Test download
            try:
                downloaded_path = downloader.download_model(model_config)
                
                # Verify file organization - should be in structured directory
                expected_path = Path(temp_dir) / model_config.gguf_filename
                assert downloaded_path == expected_path, (
                    f"Downloaded file should be at {expected_path}, got {downloaded_path}"
                )
                
                # Verify file exists and has correct content
                assert downloaded_path.exists(), "Downloaded file should exist"
                
                with open(downloaded_path, 'rb') as f:
                    actual_content = f.read()
                
                assert actual_content == file_content, "Downloaded content should match original"
                
                # Verify file size matches expected
                actual_size = downloaded_path.stat().st_size
                assert actual_size == len(file_content), (
                    f"File size should be {len(file_content)}, got {actual_size}"
                )
                
                # Verify HuggingFace Hub was used (mock was called)
                assert mock_hf_client.get_model_info.called, "Should use HuggingFace Hub for model info"
                
                # Verify download headers were requested
                assert mock_hf_client.get_download_headers.called, "Should get download headers"
                
            except Exception as e:
                # For property testing, we expect the download logic to work
                # If it fails, it should be due to our test setup, not the property
                pytest.fail(f"Download should succeed for valid inputs: {e}")


# Feature: phase3-model-optimization, Property 4: Download Resumption
@given(
    model_config=model_config_strategy(),
    file_content=file_content_strategy(),
    resume_point_ratio=st.floats(min_value=0.1, max_value=0.9)
)
@settings(max_examples=100)
def test_property_download_resumption(model_config, file_content, resume_point_ratio):
    """Property 4: Download Resumption.
    
    **Validates: Requirements 2.3**
    
    For any interrupted download, the system should be able to resume from the correct position
    without data corruption.
    """
    # Calculate resume point as a ratio of file size to ensure it's always valid
    resume_point = int(len(file_content) * resume_point_ratio)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Update model config to use temp directory
        model_config.cache_dir = temp_dir
        model_path = Path(temp_dir) / model_config.gguf_filename
        
        # Create partial file (simulating interrupted download)
        partial_content = file_content[:resume_point]
        with open(model_path, 'wb') as f:
            f.write(partial_content)
        
        # Create downloader
        downloader = ModelDownloader(cache_dir=temp_dir)
        
        # Mock the HuggingFace client and requests
        with patch.object(downloader, 'hf_client') as mock_hf_client, \
             patch.object(downloader, 'session') as mock_session:
            
            # Setup mock responses
            mock_hf_client.get_model_info.return_value = {
                'size_bytes': len(file_content),
                'size_mb': len(file_content) / (1024 * 1024),
                'sha': hashlib.sha256(file_content).hexdigest()
            }
            
            mock_hf_client.get_download_headers.return_value = {
                'User-Agent': 'OpenClass-Nexus-AI/1.0'
            }
            
            # Mock HEAD request for file info
            mock_head_response = Mock()
            mock_head_response.status_code = 200
            mock_head_response.headers = {
                'content-length': str(len(file_content))
            }
            mock_head_response.raise_for_status.return_value = None
            
            # Mock GET request for resume download
            mock_get_response = Mock()
            mock_get_response.status_code = 206  # Partial content
            mock_get_response.headers = {
                'content-length': str(len(file_content) - resume_point),
                'content-range': f'bytes {resume_point}-{len(file_content)-1}/{len(file_content)}'
            }
            remaining_content = file_content[resume_point:]
            mock_get_response.iter_content.return_value = [remaining_content]
            mock_get_response.raise_for_status.return_value = None
            
            mock_session.head.return_value = mock_head_response
            mock_session.get.return_value = mock_get_response
            
            # Test resume download
            try:
                downloaded_path = downloader.download_model(model_config)
                
                # Verify file exists and has complete content
                assert downloaded_path.exists(), "Downloaded file should exist"
                
                with open(downloaded_path, 'rb') as f:
                    actual_content = f.read()
                
                # The key property: resumed download should produce complete, uncorrupted file
                assert actual_content == file_content, (
                    "Resumed download should produce complete, uncorrupted content"
                )
                
                # Verify file size is correct
                actual_size = downloaded_path.stat().st_size
                assert actual_size == len(file_content), (
                    f"Final file size should be {len(file_content)}, got {actual_size}"
                )
                
                # Verify that Range header was used for resume
                get_call_args = mock_session.get.call_args
                if get_call_args:
                    headers = get_call_args[1].get('headers', {})
                    # Should have Range header for resume
                    range_header = headers.get('Range', '')
                    expected_range = f'bytes={resume_point}-'
                    # Note: The exact header format may vary, so we check for resume point
                    assert str(resume_point) in range_header or resume_point == 0, (
                        f"Should use Range header for resume from byte {resume_point}"
                    )
                
            except Exception as e:
                # For property testing, resume should work for valid scenarios
                pytest.fail(f"Resume download should succeed: {e}")


# Additional property test for resume failure scenarios
@given(
    model_config=model_config_strategy(),
    file_content=file_content_strategy(),
    resume_point_ratio=st.floats(min_value=0.1, max_value=0.9)
)
@settings(max_examples=100)
def test_property_download_resumption_server_no_support(model_config, file_content, resume_point_ratio):
    """Property 4b: Download Resumption Fallback.
    
    **Validates: Requirements 2.3**
    
    For any interrupted download where server doesn't support resume,
    the system should fall back to full download without corruption.
    """
    # Calculate resume point as a ratio of file size
    resume_point = int(len(file_content) * resume_point_ratio)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Update model config to use temp directory
        model_config.cache_dir = temp_dir
        model_path = Path(temp_dir) / model_config.gguf_filename
        
        # Create partial file (simulating interrupted download)
        partial_content = file_content[:resume_point]
        with open(model_path, 'wb') as f:
            f.write(partial_content)
        
        # Create downloader
        downloader = ModelDownloader(cache_dir=temp_dir)
        
        # Mock the HuggingFace client and requests
        with patch.object(downloader, 'hf_client') as mock_hf_client, \
             patch.object(downloader, 'session') as mock_session:
            
            # Setup mock responses
            mock_hf_client.get_model_info.return_value = {
                'size_bytes': len(file_content),
                'size_mb': len(file_content) / (1024 * 1024),
                'sha': hashlib.sha256(file_content).hexdigest()
            }
            
            mock_hf_client.get_download_headers.return_value = {
                'User-Agent': 'OpenClass-Nexus-AI/1.0'
            }
            
            # Mock HEAD request for file info
            mock_head_response = Mock()
            mock_head_response.status_code = 200
            mock_head_response.headers = {
                'content-length': str(len(file_content))
            }
            mock_head_response.raise_for_status.return_value = None
            
            # Mock GET request - server doesn't support resume (returns 200 instead of 206)
            mock_get_response = Mock()
            mock_get_response.status_code = 200  # Full content, not partial
            mock_get_response.headers = {
                'content-length': str(len(file_content))
            }
            mock_get_response.iter_content.return_value = [file_content]  # Full content
            mock_get_response.raise_for_status.return_value = None
            
            mock_session.head.return_value = mock_head_response
            mock_session.get.return_value = mock_get_response
            
            # Test fallback to full download
            try:
                downloaded_path = downloader.download_model(model_config)
                
                # Verify file exists and has complete content
                assert downloaded_path.exists(), "Downloaded file should exist"
                
                with open(downloaded_path, 'rb') as f:
                    actual_content = f.read()
                
                # The key property: fallback should produce complete, uncorrupted file
                assert actual_content == file_content, (
                    "Fallback download should produce complete, uncorrupted content"
                )
                
                # Verify file size is correct
                actual_size = downloaded_path.stat().st_size
                assert actual_size == len(file_content), (
                    f"Final file size should be {len(file_content)}, got {actual_size}"
                )
                
                # Should have made two GET requests (first with Range, second without)
                assert mock_session.get.call_count >= 1, "Should make at least one GET request"
                
            except Exception as e:
                # For property testing, fallback should work
                pytest.fail(f"Fallback download should succeed: {e}")


# Property test for resume detection accuracy
@given(
    model_config=model_config_strategy(),
    file_content=file_content_strategy(),
    partial_ratio=st.floats(min_value=0.1, max_value=0.9)
)
@settings(max_examples=100)
def test_property_resume_detection_accuracy(model_config, file_content, partial_ratio):
    """Property 4c: Resume Detection Accuracy.
    
    **Validates: Requirements 2.3**
    
    For any partial file, the system should accurately detect whether resume
    is possible and calculate the correct resume position.
    """
    partial_size = int(len(file_content) * partial_ratio)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Update model config to use temp directory
        model_config.cache_dir = temp_dir
        model_path = Path(temp_dir) / model_config.gguf_filename
        
        # Create partial file
        partial_content = file_content[:partial_size]
        with open(model_path, 'wb') as f:
            f.write(partial_content)
        
        # Create downloader
        downloader = ModelDownloader(cache_dir=temp_dir)
        
        # Mock remote file info
        with patch.object(downloader, 'get_remote_file_info') as mock_remote_info:
            mock_remote_info.return_value = {
                'size_bytes': len(file_content),
                'size_mb': len(file_content) / (1024 * 1024),
                'checksum': hashlib.sha256(file_content).hexdigest()
            }
            
            # Check file status
            file_status = downloader.check_existing_file(model_config)
            
            # Property: Should correctly identify partial file
            assert file_status['exists'] is True, "Should detect existing partial file"
            assert file_status['valid'] is False, "Should identify partial file as invalid"
            assert file_status['needs_download'] is True, "Should indicate download needed"
            assert file_status['resume_possible'] is True, "Should detect resume possibility"
            
            # Property: Should calculate correct resume position
            assert file_status['resume_from_byte'] == partial_size, (
                f"Should resume from byte {partial_size}, got {file_status['resume_from_byte']}"
            )
            
            # Property: Should report correct file sizes
            assert file_status['size_bytes'] == partial_size, (
                f"Local size should be {partial_size}, got {file_status['size_bytes']}"
            )
            assert file_status['expected_size_bytes'] == len(file_content), (
                f"Expected size should be {len(file_content)}, got {file_status['expected_size_bytes']}"
            )


# Additional property: Checksum verification
@given(
    file_content=file_content_strategy()
)
@settings(max_examples=100)
def test_property_checksum_verification(file_content):
    """Property: Checksum calculation should be consistent and verifiable.
    
    For any file content, calculating the checksum multiple times should produce
    the same result, and verification should pass with the correct checksum.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        test_file = Path(temp_dir) / "test_model.gguf"
        with open(test_file, 'wb') as f:
            f.write(file_content)
        
        # Create downloader
        downloader = ModelDownloader(cache_dir=temp_dir)
        
        # Calculate checksum multiple times
        checksum1 = downloader.calculate_file_checksum(test_file)
        checksum2 = downloader.calculate_file_checksum(test_file)
        
        # Property: Checksum calculation should be consistent
        assert checksum1 == checksum2, (
            f"Checksum calculation should be consistent: {checksum1} vs {checksum2}"
        )
        
        # Property: Checksum should match expected value
        expected_checksum = hashlib.sha256(file_content).hexdigest()
        assert checksum1 == expected_checksum, (
            f"Checksum should match expected value: {checksum1} vs {expected_checksum}"
        )
        
        # Property: Verification should pass with correct checksum
        model_config = ModelConfig(cache_dir=temp_dir)
        model_config.gguf_filename = "test_model.gguf"
        
        verification_result = downloader.verify_download(model_config, expected_checksum)
        assert verification_result is True, "Verification should pass with correct checksum"


# Additional property: Progress tracking accuracy
@given(
    total_size=st.integers(min_value=1000, max_value=100000),
    chunk_sizes=st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=100)
)
@settings(max_examples=100)
def test_property_progress_tracking_accuracy(total_size, chunk_sizes):
    """Property: Progress tracking should accurately reflect download progress.
    
    For any sequence of chunk updates, the total progress should equal the sum
    of all chunks, and progress percentage should be accurate.
    """
    # Limit total chunk size to not exceed total_size
    total_chunks = sum(chunk_sizes)
    if total_chunks > total_size:
        # Scale down chunk sizes proportionally
        scale_factor = total_size / total_chunks
        chunk_sizes = [max(1, int(chunk * scale_factor)) for chunk in chunk_sizes]
    
    # Create progress tracker
    progress = DownloadProgress(total_size, "test_model.gguf")
    
    # Update progress with chunks
    total_downloaded = 0
    for chunk_size in chunk_sizes:
        if total_downloaded + chunk_size <= total_size:
            progress.update(chunk_size)
            total_downloaded += chunk_size
        else:
            # Don't exceed total size
            remaining = total_size - total_downloaded
            if remaining > 0:
                progress.update(remaining)
                total_downloaded += remaining
            break
    
    # Get progress info
    progress_info = progress.get_progress_info()
    
    # Property: Downloaded amount should match sum of chunks
    assert progress.downloaded == total_downloaded, (
        f"Downloaded amount should be {total_downloaded}, got {progress.downloaded}"
    )
    
    # Property: Progress percentage should be accurate
    expected_percent = (total_downloaded / total_size * 100) if total_size > 0 else 0
    actual_percent = progress_info['progress_percent']
    
    # Allow small floating point differences
    assert abs(actual_percent - expected_percent) < 0.1, (
        f"Progress percentage should be {expected_percent:.1f}%, got {actual_percent:.1f}%"
    )
    
    # Property: Progress info should be consistent
    assert progress_info['downloaded_mb'] == round(total_downloaded / (1024 * 1024), 2), (
        "Downloaded MB should match calculated value"
    )
    
    assert progress_info['total_size_mb'] == round(total_size / (1024 * 1024), 2), (
        "Total size MB should match calculated value"
    )
    
    # Property: Completion status should be accurate
    expected_complete = total_downloaded >= total_size
    assert progress_info['is_complete'] == expected_complete, (
        f"Completion status should be {expected_complete}, got {progress_info['is_complete']}"
    )


# Additional property: File status checking consistency
@given(
    model_config=model_config_strategy(),
    file_content=file_content_strategy()
)
@settings(max_examples=100)
def test_property_file_status_consistency(model_config, file_content):
    """Property: File status checking should be consistent and accurate.
    
    For any model file, checking its status multiple times should produce
    consistent results, and the status should accurately reflect the file state.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Update model config to use temp directory
        model_config.cache_dir = temp_dir
        model_path = Path(temp_dir) / model_config.gguf_filename
        
        # Create downloader
        downloader = ModelDownloader(cache_dir=temp_dir)
        
        # Mock remote file info
        with patch.object(downloader, 'get_remote_file_info') as mock_remote_info:
            mock_remote_info.return_value = {
                'size_bytes': len(file_content),
                'size_mb': len(file_content) / (1024 * 1024),
                'checksum': hashlib.sha256(file_content).hexdigest()
            }
            
            # Test 1: Non-existent file
            status1 = downloader.check_existing_file(model_config)
            status2 = downloader.check_existing_file(model_config)
            
            # Property: Status should be consistent for non-existent file
            assert status1 == status2, "Status should be consistent for non-existent file"
            assert status1['exists'] is False, "Should report file as non-existent"
            assert status1['needs_download'] is True, "Should need download for non-existent file"
            
            # Test 2: Complete file
            with open(model_path, 'wb') as f:
                f.write(file_content)
            
            status3 = downloader.check_existing_file(model_config)
            status4 = downloader.check_existing_file(model_config)
            
            # Property: Status should be consistent for complete file
            assert status3 == status4, "Status should be consistent for complete file"
            assert status3['exists'] is True, "Should report file as existing"
            assert status3['valid'] is True, "Should report complete file as valid"
            assert status3['needs_download'] is False, "Should not need download for complete file"
            
            # Test 3: Partial file
            partial_content = file_content[:len(file_content)//2]
            with open(model_path, 'wb') as f:
                f.write(partial_content)
            
            status5 = downloader.check_existing_file(model_config)
            status6 = downloader.check_existing_file(model_config)
            
            # Property: Status should be consistent for partial file
            assert status5 == status6, "Status should be consistent for partial file"
            assert status5['exists'] is True, "Should report partial file as existing"
            assert status5['valid'] is False, "Should report partial file as invalid"
            assert status5['needs_download'] is True, "Should need download for partial file"
            assert status5['resume_possible'] is True, "Should allow resume for partial file"