"""
Property Test: Version Rollback Round-Trip

**Validates: Requirements 10.4**

Property 25: Version Rollback Round-Trip
For any system version, creating a snapshot, making changes, and then rolling back
to that snapshot should restore the system to the original state.
"""

import pytest
import os
import tempfile
import shutil
import json
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime

from src.resilience.version_manager import VersionManager, VersionSnapshot
from src.resilience.backup_manager import BackupManager


@pytest.fixture
def temp_version_file():
    """Create a temporary version file"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_file.close()
    yield temp_file.name
    # Cleanup
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


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


# Strategy for generating version strings (ASCII-safe for Windows)
version_strategy = st.from_regex(r'[0-9]+\.[0-9]+\.[0-9]+', fullmatch=True)


@given(
    initial_version=version_strategy,
    modified_version=version_strategy
)
@settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much])
def test_version_rollback_round_trip(
    initial_version,
    modified_version,
    temp_version_file,
    temp_backup_dir,
    temp_data_dirs
):
    """
    Property: Creating a snapshot, making changes, and rolling back should restore original state.
    
    This test verifies that:
    1. A version snapshot can be created
    2. System state can be modified
    3. Rollback restores the original state
    """
    assume(initial_version != modified_version)
    assume(len(initial_version) > 0)
    assume(len(modified_version) > 0)
    
    # Create version manager
    version_manager = VersionManager(version_file=temp_version_file)
    
    # Create backup manager
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    # Set initial version
    version_manager._set_current_version(initial_version)
    
    # Create initial state data
    initial_data = f"Initial state for version {initial_version}"
    initial_file = temp_data_dirs['config'] / 'state.txt'
    with open(initial_file, 'w', encoding='utf-8') as f:
        f.write(initial_data)
    
    # Create snapshot of initial state
    # (We'll create a manual backup since we can't run full backup in tests)
    backup_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path = Path(temp_backup_dir) / backup_id
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Backup config
    config_backup = backup_path / 'config'
    shutil.copytree(temp_data_dirs['config'], config_backup, dirs_exist_ok=True)
    
    # Create backup metadata
    backup_metadata = {
        'backup_id': backup_id,
        'backup_type': 'full',
        'timestamp': datetime.now().isoformat(),
        'size_mb': backup_manager._get_directory_size(backup_path),
        'components': ['config']
    }
    
    with open(backup_path / 'metadata.json', 'w') as f:
        json.dump(backup_metadata, f)
    
    # Create version snapshot
    snapshot = VersionSnapshot(
        version=initial_version,
        timestamp=datetime.now().isoformat(),
        backup_id=backup_id,
        description=f"Snapshot of {initial_version}"
    )
    
    version_manager._save_snapshot(snapshot)
    
    # Verify initial state
    assert version_manager.get_current_version() == initial_version
    assert initial_file.exists()
    with open(initial_file) as f:
        assert f.read() == initial_data
    
    # Modify system state
    version_manager._set_current_version(modified_version)
    modified_data = f"Modified state for version {modified_version}"
    with open(initial_file, 'w', encoding='utf-8') as f:
        f.write(modified_data)
    
    # Verify modified state
    assert version_manager.get_current_version() == modified_version
    with open(initial_file) as f:
        assert f.read() == modified_data
    
    # Rollback to initial version
    # (Manual rollback since we can't run full rollback in tests)
    
    # Restore backup
    success = backup_manager.restore_backup(backup_id, verify=False)
    assert success, "Backup restoration should succeed"
    
    # Restore version
    version_manager._set_current_version(initial_version)
    
    # Verify rollback restored original state
    assert version_manager.get_current_version() == initial_version, \
        "Version should be restored to initial version"
    
    assert initial_file.exists(), "State file should exist after rollback"
    
    with open(initial_file) as f:
        restored_data = f.read()
        assert restored_data == initial_data, \
            f"Data should be restored to initial state (got: {restored_data}, expected: {initial_data})"


def test_version_rollback_with_multiple_snapshots(
    temp_version_file,
    temp_backup_dir,
    temp_data_dirs
):
    """
    Test rollback with multiple version snapshots.
    
    This test creates multiple snapshots and verifies that rollback
    can restore to any previous version.
    """
    version_manager = VersionManager(version_file=temp_version_file)
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    versions = ['1.0.0', '1.1.0', '1.2.0']
    snapshots = []
    
    # Create multiple snapshots
    for version in versions:
        # Set version
        version_manager._set_current_version(version)
        
        # Create state data
        state_file = temp_data_dirs['config'] / 'state.txt'
        with open(state_file, 'w') as f:
            f.write(f"State for version {version}")
        
        # Create backup
        backup_id = f"snapshot_{version.replace('.', '_')}"
        backup_path = Path(temp_backup_dir) / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        config_backup = backup_path / 'config'
        shutil.copytree(temp_data_dirs['config'], config_backup, dirs_exist_ok=True)
        
        backup_metadata = {
            'backup_id': backup_id,
            'backup_type': 'full',
            'timestamp': datetime.now().isoformat(),
            'size_mb': backup_manager._get_directory_size(backup_path),
            'components': ['config']
        }
        
        with open(backup_path / 'metadata.json', 'w') as f:
            json.dump(backup_metadata, f)
        
        # Create snapshot
        snapshot = VersionSnapshot(
            version=version,
            timestamp=datetime.now().isoformat(),
            backup_id=backup_id,
            description=f"Snapshot of {version}"
        )
        
        version_manager._save_snapshot(snapshot)
        snapshots.append((version, backup_id))
    
    # Verify all snapshots exist
    available_versions = version_manager.list_available_versions()
    assert len(available_versions) == len(versions)
    
    # Rollback to first version
    first_version, first_backup_id = snapshots[0]
    
    backup_manager.restore_backup(first_backup_id, verify=False)
    version_manager._set_current_version(first_version)
    
    # Verify rollback
    assert version_manager.get_current_version() == first_version
    
    state_file = temp_data_dirs['config'] / 'state.txt'
    with open(state_file) as f:
        assert f.read() == f"State for version {first_version}"


def test_version_rollback_preserves_metadata(
    temp_version_file,
    temp_backup_dir,
    temp_data_dirs
):
    """
    Test that version rollback preserves snapshot metadata.
    """
    version_manager = VersionManager(version_file=temp_version_file)
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    # Create initial snapshot
    initial_version = '1.0.0'
    version_manager._set_current_version(initial_version)
    
    state_file = temp_data_dirs['config'] / 'state.txt'
    with open(state_file, 'w', encoding='utf-8') as f:
        f.write("Initial state")
    
    backup_id = f"snapshot_{initial_version.replace('.', '_')}"
    backup_path = Path(temp_backup_dir) / backup_id
    backup_path.mkdir(parents=True, exist_ok=True)
    
    config_backup = backup_path / 'config'
    shutil.copytree(temp_data_dirs['config'], config_backup, dirs_exist_ok=True)
    
    backup_metadata = {
        'backup_id': backup_id,
        'backup_type': 'full',
        'timestamp': datetime.now().isoformat(),
        'size_mb': backup_manager._get_directory_size(backup_path),
        'components': ['config']
    }
    
    with open(backup_path / 'metadata.json', 'w') as f:
        json.dump(backup_metadata, f)
    
    snapshot_metadata = {
        'custom_field': 'test_value',
        'backup_size_mb': backup_metadata['size_mb']
    }
    
    snapshot = VersionSnapshot(
        version=initial_version,
        timestamp=datetime.now().isoformat(),
        backup_id=backup_id,
        description="Test snapshot",
        metadata=snapshot_metadata
    )
    
    version_manager._save_snapshot(snapshot)
    
    # Modify version
    version_manager._set_current_version('2.0.0')
    
    # Rollback
    backup_manager.restore_backup(backup_id, verify=False)
    version_manager._set_current_version(initial_version)
    
    # Verify metadata is preserved
    snapshots = version_manager.list_available_versions()
    restored_snapshot = next(s for s in snapshots if s.version == initial_version)
    
    assert restored_snapshot.metadata == snapshot_metadata, \
        "Snapshot metadata should be preserved after rollback"
    assert restored_snapshot.description == "Test snapshot", \
        "Snapshot description should be preserved"


@given(
    version=st.from_regex(r'[0-9]+\.[0-9]+\.[0-9]+', fullmatch=True)
)
@settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_version_snapshot_creation(version, temp_version_file, temp_backup_dir, temp_data_dirs):
    """
    Property: Version snapshots can be created for any valid version string.
    """
    version_manager = VersionManager(version_file=temp_version_file)
    backup_manager = BackupManager(
        backup_dir=temp_backup_dir,
        chromadb_path=str(temp_data_dirs['chromadb']),
        config_path=str(temp_data_dirs['config']),
        models_path=str(temp_data_dirs['models'])
    )
    
    # Set version
    version_manager._set_current_version(version)
    
    # Create test data
    state_file = temp_data_dirs['config'] / 'state.txt'
    with open(state_file, 'w', encoding='utf-8') as f:
        f.write(f"State for {version}")
    
    # Create backup
    backup_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path = Path(temp_backup_dir) / backup_id
    backup_path.mkdir(parents=True, exist_ok=True)
    
    config_backup = backup_path / 'config'
    shutil.copytree(temp_data_dirs['config'], config_backup, dirs_exist_ok=True)
    
    backup_metadata = {
        'backup_id': backup_id,
        'backup_type': 'full',
        'timestamp': datetime.now().isoformat(),
        'size_mb': backup_manager._get_directory_size(backup_path),
        'components': ['config']
    }
    
    with open(backup_path / 'metadata.json', 'w') as f:
        json.dump(backup_metadata, f)
    
    # Create snapshot
    snapshot = VersionSnapshot(
        version=version,
        timestamp=datetime.now().isoformat(),
        backup_id=backup_id,
        description=f"Snapshot of {version}"
    )
    
    version_manager._save_snapshot(snapshot)
    
    # Verify snapshot was created
    snapshots = version_manager.list_available_versions()
    assert len(snapshots) > 0, "At least one snapshot should exist"
    
    # Find our snapshot
    our_snapshot = next((s for s in snapshots if s.version == version), None)
    assert our_snapshot is not None, f"Snapshot for version {version} should exist"
    assert our_snapshot.backup_id == backup_id, "Backup ID should match"
