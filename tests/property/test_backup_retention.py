"""
Property Test: Backup Retention Policy

**Validates: Requirements 10.7**

Property 26: Backup Retention Policy
For any point in time, the backup directory should only contain backups from the
last 28 days, and older backups should be automatically cleaned up.
"""

import pytest
import os
import tempfile
import shutil
import json
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta

from src.resilience.backup_scheduler import BackupScheduler
from src.resilience.backup_manager import BackupManager


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
    """Create temporary data directories"""
    temp_base = tempfile.mkdtemp()
    
    dirs = {
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


def create_test_backup(backup_dir: Path, backup_id: str, days_ago: int, backup_manager: BackupManager):
    """Helper function to create a test backup with a specific age"""
    backup_path = backup_dir / backup_id
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Create dummy backup data
    test_file = backup_path / 'test_data.txt'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(f"Backup data for {backup_id}")
    
    # Create metadata with timestamp in the past
    timestamp = datetime.now() - timedelta(days=days_ago)
    metadata = {
        'backup_id': backup_id,
        'backup_type': 'full',
        'timestamp': timestamp.isoformat(),
        'size_mb': backup_manager._get_directory_size(backup_path),
        'components': ['test']
    }
    
    with open(backup_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f)
    
    return backup_path


@given(
    retention_days=st.integers(min_value=7, max_value=90),
    old_backup_age=st.integers(min_value=30, max_value=180)
)
@settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much])
def test_backup_retention_removes_old_backups(
    retention_days,
    old_backup_age,
    temp_backup_dir,
    temp_data_dirs
):
    """
    Property: Backups older than retention period should be removed.
    
    This test verifies that:
    1. Backups older than retention_days are deleted
    2. Backups within retention_days are kept
    3. Cleanup returns correct count of deleted backups
    """
    assume(old_backup_age > retention_days)
    
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    scheduler = BackupScheduler(
        backup_manager=backup_manager,
        retention_days=retention_days
    )
    
    # Clean up any existing backups first
    import shutil
    for item in Path(temp_backup_dir).iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    
    # Create unique backup IDs to avoid conflicts between test runs
    import time
    unique_suffix = int(time.time() * 1000000)
    
    # Create old backup (should be deleted)
    old_backup_id = f"old_backup_{old_backup_age}d_{unique_suffix}"
    old_backup_path = create_test_backup(
        Path(temp_backup_dir),
        old_backup_id,
        old_backup_age,
        backup_manager
    )
    
    # Create recent backup (should be kept)
    recent_backup_id = f"recent_backup_{retention_days - 1}d_{unique_suffix}"
    recent_backup_path = create_test_backup(
        Path(temp_backup_dir),
        recent_backup_id,
        retention_days - 1,
        backup_manager
    )
    
    # Verify both backups exist before cleanup
    assert old_backup_path.exists(), "Old backup should exist before cleanup"
    assert recent_backup_path.exists(), "Recent backup should exist before cleanup"
    
    # Run cleanup
    deleted_count = scheduler.cleanup_old_backups()
    
    # Property: Old backup should be deleted
    assert not old_backup_path.exists(), \
        f"Backup older than {retention_days} days should be deleted"
    
    # Property: Recent backup should be kept
    assert recent_backup_path.exists(), \
        f"Backup within {retention_days} days should be kept"
    
    # Property: Deleted count should be correct
    assert deleted_count == 1, \
        f"Should have deleted 1 backup (got {deleted_count})"


def test_backup_retention_default_28_days(temp_backup_dir, temp_data_dirs):
    """
    Test that default retention period is 28 days.
    """
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    scheduler = BackupScheduler(backup_manager=backup_manager)
    
    # Verify default retention is 28 days
    assert scheduler.retention_days == 28, \
        "Default retention period should be 28 days"
    
    # Create backups at various ages
    backups = [
        ('backup_27d', 27, True),   # Should be kept
        ('backup_28d', 28, True),   # Should be kept (exactly 28 days)
        ('backup_29d', 29, False),  # Should be deleted
        ('backup_30d', 30, False),  # Should be deleted
    ]
    
    for backup_id, days_ago, should_keep in backups:
        create_test_backup(
            Path(temp_backup_dir),
            backup_id,
            days_ago,
            backup_manager
        )
    
    # Run cleanup
    deleted_count = scheduler.cleanup_old_backups()
    
    # Verify correct backups were kept/deleted
    for backup_id, days_ago, should_keep in backups:
        backup_path = Path(temp_backup_dir) / backup_id
        if should_keep:
            assert backup_path.exists(), \
                f"Backup {backup_id} ({days_ago} days old) should be kept"
        else:
            assert not backup_path.exists(), \
                f"Backup {backup_id} ({days_ago} days old) should be deleted"
    
    # Verify deleted count
    expected_deleted = sum(1 for _, _, should_keep in backups if not should_keep)
    assert deleted_count == expected_deleted, \
        f"Should have deleted {expected_deleted} backups (got {deleted_count})"


@given(
    backup_count=st.integers(min_value=5, max_value=20),
    retention_days=st.integers(min_value=14, max_value=60)
)
@settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much])
def test_backup_retention_multiple_backups(
    backup_count,
    retention_days,
    temp_backup_dir,
    temp_data_dirs
):
    """
    Property: Cleanup should correctly handle multiple backups of varying ages.
    """
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    scheduler = BackupScheduler(
        backup_manager=backup_manager,
        retention_days=retention_days
    )
    
    # Clean up any existing backups first
    import shutil
    for item in Path(temp_backup_dir).iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    
    # Create backups with ages from 0 to backup_count days
    expected_kept = 0
    expected_deleted = 0
    
    # Create unique suffix to avoid conflicts
    import time
    unique_suffix = int(time.time() * 1000000)
    
    for i in range(backup_count):
        days_ago = i
        backup_id = f"backup_{i:03d}_{unique_suffix}"
        create_test_backup(
            Path(temp_backup_dir),
            backup_id,
            days_ago,
            backup_manager
        )
        
        # Backup is kept if days_ago <= retention_days (not strictly less than)
        if days_ago <= retention_days:
            expected_kept += 1
        else:
            expected_deleted += 1
    
    # Run cleanup
    deleted_count = scheduler.cleanup_old_backups()
    
    # Verify correct number of backups were deleted
    assert deleted_count == expected_deleted, \
        f"Should have deleted {expected_deleted} backups (got {deleted_count})"
    
    # Verify correct backups remain
    remaining_backups = list(Path(temp_backup_dir).iterdir())
    remaining_count = len([b for b in remaining_backups if b.is_dir()])
    
    assert remaining_count == expected_kept, \
        f"Should have {expected_kept} backups remaining (got {remaining_count})"


def test_backup_retention_compressed_files(temp_backup_dir, temp_data_dirs):
    """
    Test that cleanup also removes compressed backup files.
    """
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    scheduler = BackupScheduler(backup_manager=backup_manager, retention_days=28)
    
    # Create old backup
    old_backup_id = 'old_backup_30d'
    old_backup_path = create_test_backup(
        Path(temp_backup_dir),
        old_backup_id,
        30,
        backup_manager
    )
    
    # Create compressed file
    compressed_file = Path(temp_backup_dir) / f"{old_backup_id}.tar.gz"
    with open(compressed_file, 'w') as f:
        f.write("Compressed backup data")
    
    # Create encrypted file
    encrypted_file = Path(temp_backup_dir) / f"{old_backup_id}.tar.gz.enc"
    with open(encrypted_file, 'w') as f:
        f.write("Encrypted backup data")
    
    # Verify files exist
    assert old_backup_path.exists()
    assert compressed_file.exists()
    assert encrypted_file.exists()
    
    # Run cleanup
    deleted_count = scheduler.cleanup_old_backups()
    
    # Verify all files were deleted
    assert not old_backup_path.exists(), \
        "Backup directory should be deleted"
    assert not compressed_file.exists(), \
        "Compressed file should be deleted"
    assert not encrypted_file.exists(), \
        "Encrypted file should be deleted"
    
    assert deleted_count == 1, \
        "Should count as 1 deleted backup"


def test_backup_retention_boundary_conditions(temp_backup_dir, temp_data_dirs):
    """
    Test backup retention at exact boundary (retention_days).
    """
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    retention_days = 28
    scheduler = BackupScheduler(
        backup_manager=backup_manager,
        retention_days=retention_days
    )
    
    # Create backup exactly at retention boundary
    boundary_backup_id = f"boundary_backup_{retention_days}d"
    boundary_backup_path = create_test_backup(
        Path(temp_backup_dir),
        boundary_backup_id,
        retention_days,
        backup_manager
    )
    
    # Create backup just before boundary (should be kept)
    before_backup_id = f"before_backup_{retention_days - 1}d"
    before_backup_path = create_test_backup(
        Path(temp_backup_dir),
        before_backup_id,
        retention_days - 1,
        backup_manager
    )
    
    # Create backup just after boundary (should be deleted)
    after_backup_id = f"after_backup_{retention_days + 1}d"
    after_backup_path = create_test_backup(
        Path(temp_backup_dir),
        after_backup_id,
        retention_days + 1,
        backup_manager
    )
    
    # Run cleanup
    deleted_count = scheduler.cleanup_old_backups()
    
    # Verify boundary behavior
    # Backup at exactly retention_days should be kept (< cutoff, not >=)
    assert boundary_backup_path.exists(), \
        f"Backup at exactly {retention_days} days should be kept"
    
    assert before_backup_path.exists(), \
        f"Backup before {retention_days} days should be kept"
    
    assert not after_backup_path.exists(), \
        f"Backup after {retention_days} days should be deleted"
    
    assert deleted_count == 1, \
        "Should have deleted 1 backup"


def test_backup_retention_no_metadata(temp_backup_dir, temp_data_dirs):
    """
    Test that cleanup skips backups without metadata files.
    """
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    scheduler = BackupScheduler(backup_manager=backup_manager, retention_days=28)
    
    # Create backup without metadata
    no_metadata_backup = Path(temp_backup_dir) / 'no_metadata_backup'
    no_metadata_backup.mkdir(parents=True, exist_ok=True)
    with open(no_metadata_backup / 'data.txt', 'w') as f:
        f.write("Backup without metadata")
    
    # Create normal old backup
    old_backup_id = 'old_backup_30d'
    old_backup_path = create_test_backup(
        Path(temp_backup_dir),
        old_backup_id,
        30,
        backup_manager
    )
    
    # Run cleanup
    deleted_count = scheduler.cleanup_old_backups()
    
    # Verify backup without metadata was skipped
    assert no_metadata_backup.exists(), \
        "Backup without metadata should be skipped"
    
    # Verify old backup with metadata was deleted
    assert not old_backup_path.exists(), \
        "Old backup with metadata should be deleted"
    
    assert deleted_count == 1, \
        "Should have deleted 1 backup (only the one with metadata)"


@given(retention_days=st.integers(min_value=1, max_value=365))
@settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_backup_retention_configurable(retention_days, temp_backup_dir, temp_data_dirs):
    """
    Property: Retention period should be configurable to any positive number of days.
    """
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    scheduler = BackupScheduler(
        backup_manager=backup_manager,
        retention_days=retention_days
    )
    
    # Verify retention period is set correctly
    assert scheduler.retention_days == retention_days, \
        f"Retention period should be {retention_days} days"
    
    # Create backup just outside retention period
    old_backup_id = f"old_backup_{retention_days + 1}d"
    old_backup_path = create_test_backup(
        Path(temp_backup_dir),
        old_backup_id,
        retention_days + 1,
        backup_manager
    )
    
    # Create backup just inside retention period
    recent_backup_id = f"recent_backup_{max(0, retention_days - 1)}d"
    recent_backup_path = create_test_backup(
        Path(temp_backup_dir),
        recent_backup_id,
        max(0, retention_days - 1),
        backup_manager
    )
    
    # Run cleanup
    deleted_count = scheduler.cleanup_old_backups()
    
    # Verify cleanup respects configured retention period
    assert not old_backup_path.exists(), \
        f"Backup older than {retention_days} days should be deleted"
    
    assert recent_backup_path.exists(), \
        f"Backup within {retention_days} days should be kept"
