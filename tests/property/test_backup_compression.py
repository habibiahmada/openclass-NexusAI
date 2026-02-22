"""
Property Test: Backup Compression

**Validates: Requirements 10.3**

Property 24: Backup Compression
For any backup created (full or incremental), the backup should be compressed,
and the compressed size should be smaller than the original size.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime

from src.resilience.backup_manager import BackupManager


# Strategy for generating test backup data (ASCII-safe for Windows)
@st.composite
def backup_data_strategy(draw):
    """Generate test backup data with various sizes"""
    # Generate random text data of varying sizes
    size_kb = draw(st.integers(min_value=10, max_value=1000))  # 10KB to 1MB
    
    # Create compressible data (repeated patterns compress well) - ASCII only
    pattern = draw(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=10, max_size=100))
    data = (pattern * (size_kb * 1024 // max(len(pattern), 1)))[:size_kb * 1024]
    
    return data


@pytest.fixture
def temp_backup_dir():
    """Create a temporary backup directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def temp_data_dirs():
    """Create temporary data directories for testing"""
    temp_base = tempfile.mkdtemp()
    
    dirs = {
        'postgres': Path(temp_base) / 'postgres',
        'chromadb': Path(temp_base) / 'chromadb',
        'config': Path(temp_base) / 'config',
        'models': Path(temp_base) / 'models'
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    yield dirs
    
    # Cleanup
    if os.path.exists(temp_base):
        shutil.rmtree(temp_base)


@given(backup_data=backup_data_strategy())
@settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_backup_compression_reduces_size(backup_data, temp_backup_dir, temp_data_dirs):
    """
    Property: For any backup created, compression should reduce the size.
    
    This test verifies that:
    1. Backup can be compressed
    2. Compressed size is smaller than original size
    3. Compression ratio is reasonable (at least some reduction)
    """
    # Create test data files
    test_file = temp_data_dirs['config'] / 'test_data.txt'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(backup_data)
    
    # Create backup manager with test directories
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        postgres_db='test_db',
        postgres_user='test_user',
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    # Create a simple backup (just config for testing) with unique ID
    import time
    backup_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000000)}"
    backup_path = Path(temp_backup_dir) / backup_id
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Copy config to backup
    config_backup = backup_path / 'config'
    shutil.copytree(temp_data_dirs['config'], config_backup, dirs_exist_ok=True)
    
    # Create metadata
    import json
    metadata = {
        'backup_id': backup_id,
        'backup_type': 'test',
        'timestamp': datetime.now().isoformat(),
        'size_mb': backup_manager._get_directory_size(backup_path),
        'components': ['config']
    }
    
    with open(backup_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f)
    
    # Get original size
    original_size = backup_manager._get_directory_size(backup_path)
    assume(original_size > 0)  # Skip if no data
    
    # Compress backup
    compressed_path = backup_manager.compress_backup(backup_id)
    
    # Verify compressed file exists
    assert os.path.exists(compressed_path), "Compressed backup file should exist"
    
    # Get compressed size
    compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)  # Convert to MB
    
    # Property: Compressed size should be smaller than original
    assert compressed_size < original_size, \
        f"Compressed size ({compressed_size:.2f} MB) should be smaller than original ({original_size:.2f} MB)"
    
    # Property: Compression should achieve at least some reduction
    compression_ratio = (1 - compressed_size / original_size) * 100
    assert compression_ratio > 0, \
        f"Compression should reduce size (ratio: {compression_ratio:.1f}%)"


def test_backup_compression_full_backup(temp_backup_dir, temp_data_dirs):
    """
    Test backup compression with a full backup scenario.
    
    This test creates a more realistic backup with multiple components
    and verifies compression works correctly.
    """
    # Create test data in multiple directories
    test_data = "This is test data that should compress well. " * 100
    
    for dir_name, dir_path in temp_data_dirs.items():
        test_file = dir_path / f'{dir_name}_data.txt'
        with open(test_file, 'w') as f:
            f.write(test_data)
    
    # Create backup manager
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        postgres_db='test_db',
        postgres_user='test_user',
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    # Create a test backup manually (since we can't run actual pg_dump)
    backup_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path = Path(temp_backup_dir) / backup_id
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Copy all directories
    for component, dir_path in temp_data_dirs.items():
        dest = backup_path / component
        shutil.copytree(dir_path, dest)
    
    # Create metadata
    import json
    metadata = {
        'backup_id': backup_id,
        'backup_type': 'full',
        'timestamp': datetime.now().isoformat(),
        'size_mb': backup_manager._get_directory_size(backup_path),
        'components': list(temp_data_dirs.keys())
    }
    
    with open(backup_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f)
    
    # Get original size
    original_size = backup_manager._get_directory_size(backup_path)
    
    # Compress backup
    compressed_path = backup_manager.compress_backup(backup_id)
    
    # Verify compression
    assert os.path.exists(compressed_path)
    compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
    
    # Verify size reduction
    assert compressed_size < original_size
    compression_ratio = (1 - compressed_size / original_size) * 100
    
    print(f"Original size: {original_size:.2f} MB")
    print(f"Compressed size: {compressed_size:.2f} MB")
    print(f"Compression ratio: {compression_ratio:.1f}%")
    
    # For text data, we should get good compression
    assert compression_ratio > 50, \
        f"Text data should compress well (got {compression_ratio:.1f}%)"


def test_backup_compression_metadata_updated(temp_backup_dir, temp_data_dirs):
    """
    Test that backup metadata is updated after compression.
    """
    # Create test data
    test_file = temp_data_dirs['config'] / 'test.txt'
    with open(test_file, 'w') as f:
        f.write("Test data " * 1000)
    
    # Create backup manager
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    # Create test backup
    backup_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path = Path(temp_backup_dir) / backup_id
    backup_path.mkdir(parents=True, exist_ok=True)
    
    config_backup = backup_path / 'config'
    shutil.copytree(temp_data_dirs['config'], config_backup)
    
    # Create metadata
    import json
    metadata = {
        'backup_id': backup_id,
        'backup_type': 'test',
        'timestamp': datetime.now().isoformat(),
        'size_mb': backup_manager._get_directory_size(backup_path),
        'components': ['config'],
        'compressed': False
    }
    
    with open(backup_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f)
    
    # Compress backup
    compressed_path = backup_manager.compress_backup(backup_id)
    
    # Verify metadata was updated
    with open(backup_path / 'metadata.json') as f:
        updated_metadata = json.load(f)
    
    assert updated_metadata['compressed'] is True, \
        "Metadata should indicate backup is compressed"
    assert 'compressed_path' in updated_metadata, \
        "Metadata should include compressed file path"
    assert updated_metadata['compressed_path'] == compressed_path, \
        "Compressed path should match actual file"


@given(
    file_count=st.integers(min_value=1, max_value=10),
    file_size_kb=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_backup_compression_multiple_files(file_count, file_size_kb, temp_backup_dir, temp_data_dirs):
    """
    Property: Compression should work with varying numbers and sizes of files.
    """
    # Create multiple test files
    for i in range(file_count):
        test_file = temp_data_dirs['config'] / f'test_{i}.txt'
        data = f"Test data {i} " * (file_size_kb * 100)
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(data)
    
    # Create backup manager
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    # Create test backup with unique timestamp to avoid conflicts
    import time
    backup_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000000)}"
    backup_path = Path(temp_backup_dir) / backup_id
    backup_path.mkdir(parents=True, exist_ok=True)
    
    config_backup = backup_path / 'config'
    shutil.copytree(temp_data_dirs['config'], config_backup, dirs_exist_ok=True)
    
    # Create metadata
    import json
    metadata = {
        'backup_id': backup_id,
        'backup_type': 'test',
        'timestamp': datetime.now().isoformat(),
        'size_mb': backup_manager._get_directory_size(backup_path),
        'components': ['config']
    }
    
    with open(backup_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f)
    
    # Get original size
    original_size = backup_manager._get_directory_size(backup_path)
    assume(original_size > 0)
    
    # Compress backup
    compressed_path = backup_manager.compress_backup(backup_id)
    
    # Verify compression
    assert os.path.exists(compressed_path)
    compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
    
    # Property: Compressed size should be smaller
    assert compressed_size < original_size, \
        f"Compression failed for {file_count} files of {file_size_kb}KB each"
