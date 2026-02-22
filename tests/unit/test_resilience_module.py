"""
Unit Tests for Resilience Module

Tests backup creation, restoration, health checks, auto-restart logic, and version rollback.
Validates Requirements 10.1-10.7
"""

import pytest
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.resilience.backup_manager import BackupManager, BackupMetadata
from src.resilience.backup_scheduler import BackupScheduler
from src.resilience.health_monitor import HealthMonitor, HealthStatus, HealthLevel, SystemHealth
from src.resilience.auto_restart_service import AutoRestartService
from src.resilience.version_manager import VersionManager, VersionSnapshot


# Fixtures

@pytest.fixture
def temp_backup_dir():
    """Create temporary backup directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
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
        # Create test file
        (dir_path / 'test.txt').write_text('test data')
    
    yield dirs
    
    if os.path.exists(temp_base):
        shutil.rmtree(temp_base)


@pytest.fixture
def temp_version_file():
    """Create temporary version file"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    # Write initial version data
    json.dump({
        'version': '1.0.0',
        'updated_at': datetime.now().isoformat(),
        'snapshots': []
    }, temp_file, indent=2)
    temp_file.close()
    yield temp_file.name
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


# BackupManager Tests

class TestBackupManager:
    """Test BackupManager class"""
    
    def test_backup_manager_initialization(self, temp_backup_dir, temp_data_dirs):
        """Test BackupManager initializes correctly"""
        manager = BackupManager(
            backup_dir=temp_backup_dir,
            chromadb_path=str(temp_data_dirs['chromadb']),
            config_path=str(temp_data_dirs['config']),
            models_path=str(temp_data_dirs['models'])
        )
        
        assert manager.backup_dir == Path(temp_backup_dir)
        assert manager.backup_dir.exists()
    
    def test_get_directory_size(self, temp_backup_dir, temp_data_dirs):
        """Test directory size calculation"""
        manager = BackupManager(backup_dir=temp_backup_dir)
        
        # Create test file with known size
        test_dir = Path(temp_data_dirs['config'])
        test_file = test_dir / 'size_test.txt'
        test_data = 'x' * 1024  # 1KB
        test_file.write_text(test_data)
        
        size_mb = manager._get_directory_size(test_dir)
        assert size_mb > 0
        assert size_mb < 1  # Should be less than 1MB
    
    def test_backup_chromadb(self, temp_backup_dir, temp_data_dirs):
        """Test ChromaDB backup"""
        manager = BackupManager(
            backup_dir=temp_backup_dir,
            chromadb_path=str(temp_data_dirs['chromadb'])
        )
        
        output_dir = Path(temp_backup_dir) / 'chromadb_backup'
        manager._backup_chromadb(output_dir)
        
        assert output_dir.exists()
        assert (output_dir / 'test.txt').exists()
    
    def test_backup_config(self, temp_backup_dir, temp_data_dirs):
        """Test configuration backup"""
        manager = BackupManager(
            backup_dir=temp_backup_dir,
            config_path=str(temp_data_dirs['config'])
        )
        
        output_dir = Path(temp_backup_dir) / 'config_backup'
        manager._backup_config(output_dir)
        
        assert output_dir.exists()
        assert (output_dir / 'test.txt').exists()
    
    def test_verify_backup_integrity_valid(self, temp_backup_dir, temp_data_dirs):
        """Test backup integrity verification with valid backup"""
        manager = BackupManager(backup_dir=temp_backup_dir)
        
        # Create valid backup structure
        backup_id = 'test_backup'
        backup_path = Path(temp_backup_dir) / backup_id
        backup_path.mkdir()
        
        # Create config backup
        config_backup = backup_path / 'config'
        config_backup.mkdir()
        (config_backup / 'test.txt').write_text('test')
        
        # Create metadata
        metadata = {
            'backup_id': backup_id,
            'backup_type': 'full',
            'timestamp': datetime.now().isoformat(),
            'size_mb': 0.001,
            'components': ['config']
        }
        
        with open(backup_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f)
        
        # Verify
        assert manager.verify_backup_integrity(backup_id) is True
    
    def test_verify_backup_integrity_missing_metadata(self, temp_backup_dir):
        """Test backup integrity verification with missing metadata"""
        manager = BackupManager(backup_dir=temp_backup_dir)
        
        # Create backup without metadata
        backup_id = 'test_backup'
        backup_path = Path(temp_backup_dir) / backup_id
        backup_path.mkdir()
        
        # Verify should fail
        assert manager.verify_backup_integrity(backup_id) is False
    
    def test_verify_backup_integrity_missing_component(self, temp_backup_dir):
        """Test backup integrity verification with missing component"""
        manager = BackupManager(backup_dir=temp_backup_dir)
        
        # Create backup with metadata but missing component
        backup_id = 'test_backup'
        backup_path = Path(temp_backup_dir) / backup_id
        backup_path.mkdir()
        
        metadata = {
            'backup_id': backup_id,
            'backup_type': 'full',
            'timestamp': datetime.now().isoformat(),
            'size_mb': 0.001,
            'components': ['config']  # Claims to have config but doesn't
        }
        
        with open(backup_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f)
        
        # Verify should fail
        assert manager.verify_backup_integrity(backup_id) is False


# BackupScheduler Tests

class TestBackupScheduler:
    """Test BackupScheduler class"""
    
    def test_scheduler_initialization(self, temp_backup_dir):
        """Test BackupScheduler initializes correctly"""
        manager = BackupManager(backup_dir=temp_backup_dir)
        scheduler = BackupScheduler(backup_manager=manager, retention_days=28)
        
        assert scheduler.backup_manager == manager
        assert scheduler.retention_days == 28
    
    def test_get_backup_schedule_info(self, temp_backup_dir):
        """Test getting backup schedule information"""
        manager = BackupManager(backup_dir=temp_backup_dir)
        scheduler = BackupScheduler(backup_manager=manager, retention_days=30)
        
        info = scheduler.get_backup_schedule_info()
        
        assert info['full_backup_schedule'] == 'Sunday 2 AM'
        assert info['incremental_backup_schedule'] == 'Monday-Saturday 2 AM'
        assert info['retention_days'] == 30
        assert 'encryption_enabled' in info
        assert 's3_upload_enabled' in info


# HealthMonitor Tests

class TestHealthMonitor:
    """Test HealthMonitor class"""
    
    def test_health_monitor_initialization(self):
        """Test HealthMonitor initializes correctly"""
        monitor = HealthMonitor(
            disk_warning_threshold=80.0,
            disk_critical_threshold=90.0,
            ram_warning_threshold=80.0,
            ram_critical_threshold=90.0
        )
        
        assert monitor.disk_warning_threshold == 80.0
        assert monitor.disk_critical_threshold == 90.0
        assert monitor.ram_warning_threshold == 80.0
        assert monitor.ram_critical_threshold == 90.0
    
    def test_check_disk_space_healthy(self):
        """Test disk space check when healthy"""
        monitor = HealthMonitor(disk_warning_threshold=80.0, disk_critical_threshold=90.0)
        
        with patch('psutil.disk_usage') as mock_disk:
            mock_disk.return_value = Mock(percent=50.0)
            
            status = monitor.check_disk_space()
            
            assert status.healthy is True
            assert status.level == HealthLevel.HEALTHY
            assert 'normal' in status.message.lower()
    
    def test_check_disk_space_warning(self):
        """Test disk space check when warning threshold exceeded"""
        monitor = HealthMonitor(disk_warning_threshold=80.0, disk_critical_threshold=90.0)
        
        with patch('psutil.disk_usage') as mock_disk:
            mock_disk.return_value = Mock(percent=85.0)
            
            status = monitor.check_disk_space()
            
            assert status.healthy is True
            assert status.level == HealthLevel.WARNING
            assert status.warning is True
            assert 'high' in status.message.lower()
    
    def test_check_disk_space_critical(self):
        """Test disk space check when critical threshold exceeded"""
        monitor = HealthMonitor(disk_warning_threshold=80.0, disk_critical_threshold=90.0)
        
        with patch('psutil.disk_usage') as mock_disk:
            mock_disk.return_value = Mock(percent=95.0)
            
            status = monitor.check_disk_space()
            
            assert status.healthy is False
            assert status.level == HealthLevel.CRITICAL
            assert status.critical is True
            assert 'critical' in status.message.lower()
    
    def test_check_ram_usage_healthy(self):
        """Test RAM usage check when healthy"""
        monitor = HealthMonitor(ram_warning_threshold=80.0, ram_critical_threshold=90.0)
        
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = Mock(percent=60.0)
            
            status = monitor.check_ram_usage()
            
            assert status.healthy is True
            assert status.level == HealthLevel.HEALTHY
    
    def test_check_ram_usage_warning(self):
        """Test RAM usage check when warning threshold exceeded"""
        monitor = HealthMonitor(ram_warning_threshold=80.0, ram_critical_threshold=90.0)
        
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = Mock(percent=85.0)
            
            status = monitor.check_ram_usage()
            
            assert status.healthy is True
            assert status.level == HealthLevel.WARNING
            assert status.warning is True
    
    def test_check_ram_usage_critical(self):
        """Test RAM usage check when critical threshold exceeded"""
        monitor = HealthMonitor(ram_warning_threshold=80.0, ram_critical_threshold=90.0)
        
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = Mock(percent=95.0)
            
            status = monitor.check_ram_usage()
            
            assert status.healthy is False
            assert status.level == HealthLevel.CRITICAL
            assert status.critical is True
    
    def test_get_detailed_system_info(self):
        """Test getting detailed system information"""
        monitor = HealthMonitor()
        
        with patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.cpu_count', return_value=8), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_memory.return_value = Mock(
                total=16 * 1024**3,
                available=8 * 1024**3,
                used=8 * 1024**3,
                percent=50.0
            )
            
            mock_disk.return_value = Mock(
                total=512 * 1024**3,
                used=256 * 1024**3,
                free=256 * 1024**3,
                percent=50.0
            )
            
            info = monitor.get_detailed_system_info()
            
            assert 'cpu' in info
            assert 'memory' in info
            assert 'disk' in info
            assert info['cpu']['percent'] == 50.0
            assert info['memory']['percent'] == 50.0
            assert info['disk']['percent'] == 50.0


# AutoRestartService Tests

class TestAutoRestartService:
    """Test AutoRestartService class"""
    
    def test_auto_restart_initialization(self):
        """Test AutoRestartService initializes correctly"""
        service = AutoRestartService()
        
        assert service.MAX_RESTART_ATTEMPTS == 3
        assert service.RESTART_COOLDOWN_SECONDS == 300
        assert len(service.restart_history) == 0
    
    def test_detect_failure_active_service(self):
        """Test failure detection for active service"""
        service = AutoRestartService()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='active')
            
            is_failed = service.detect_failure('test-service')
            
            assert is_failed is False
    
    def test_detect_failure_inactive_service(self):
        """Test failure detection for inactive service"""
        service = AutoRestartService()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=3, stdout='inactive')
            
            is_failed = service.detect_failure('test-service')
            
            assert is_failed is True
    
    def test_attempt_restart_success(self):
        """Test successful service restart"""
        service = AutoRestartService()
        
        with patch('subprocess.run') as mock_run, \
             patch.object(service, 'detect_failure', return_value=False):
            
            mock_run.return_value = Mock(returncode=0)
            
            success = service.attempt_restart('test-service')
            
            assert success is True
            assert 'test-service' in service.restart_history
    
    def test_attempt_restart_cooldown(self):
        """Test restart cooldown prevents immediate retry"""
        service = AutoRestartService()
        
        # Add recent restart to history
        service.restart_history['test-service'] = (datetime.now(), 1, [])
        
        success = service.attempt_restart('test-service')
        
        assert success is False
    
    def test_attempt_restart_max_attempts(self):
        """Test max restart attempts limit"""
        service = AutoRestartService()
        
        # Add max attempts to history
        service.restart_history['test-service'] = (
            datetime.now() - timedelta(seconds=400),  # Past cooldown
            3,  # Max attempts
            []
        )
        
        with patch.object(service, 'escalate_failure') as mock_escalate:
            success = service.attempt_restart('test-service')
            
            assert success is False
            mock_escalate.assert_called_once_with('test-service')
    
    def test_get_restart_history(self):
        """Test getting restart history"""
        service = AutoRestartService()
        
        # Add some history
        from src.resilience.auto_restart_service import RestartAttempt
        attempt = RestartAttempt(timestamp=datetime.now(), success=True)
        service.restart_history['test-service'] = (datetime.now(), 1, [attempt])
        
        history = service.get_restart_history('test-service')
        
        assert history['service'] == 'test-service'
        assert history['attempts'] == 1
        assert len(history['history']) == 1
    
    def test_reset_restart_history(self):
        """Test resetting restart history"""
        service = AutoRestartService()
        
        # Add history
        service.restart_history['test-service'] = (datetime.now(), 2, [])
        
        service.reset_restart_history('test-service')
        
        assert 'test-service' not in service.restart_history


# VersionManager Tests

class TestVersionManager:
    """Test VersionManager class"""
    
    def test_version_manager_initialization(self, temp_version_file):
        """Test VersionManager initializes correctly"""
        manager = VersionManager(version_file=temp_version_file)
        
        assert manager.version_file == Path(temp_version_file)
        assert manager.version_file.exists()
    
    def test_get_current_version(self, temp_version_file):
        """Test getting current version"""
        manager = VersionManager(version_file=temp_version_file)
        
        version = manager.get_current_version()
        
        assert version == '1.0.0'  # Default version
    
    def test_set_current_version(self, temp_version_file):
        """Test setting current version"""
        manager = VersionManager(version_file=temp_version_file)
        
        manager._set_current_version('2.0.0')
        
        assert manager.get_current_version() == '2.0.0'
    
    def test_save_snapshot(self, temp_version_file):
        """Test saving version snapshot"""
        manager = VersionManager(version_file=temp_version_file)
        
        snapshot = VersionSnapshot(
            version='1.0.0',
            timestamp=datetime.now().isoformat(),
            backup_id='test_backup',
            description='Test snapshot'
        )
        
        manager._save_snapshot(snapshot)
        
        snapshots = manager.list_available_versions()
        assert len(snapshots) == 1
        assert snapshots[0].version == '1.0.0'
    
    def test_list_available_versions(self, temp_version_file):
        """Test listing available versions"""
        manager = VersionManager(version_file=temp_version_file)
        
        # Add multiple snapshots
        for i in range(3):
            snapshot = VersionSnapshot(
                version=f'1.{i}.0',
                timestamp=datetime.now().isoformat(),
                backup_id=f'backup_{i}',
                description=f'Snapshot {i}'
            )
            manager._save_snapshot(snapshot)
        
        snapshots = manager.list_available_versions()
        
        assert len(snapshots) == 3
        # Should be sorted by timestamp (newest first)
        assert all(isinstance(s, VersionSnapshot) for s in snapshots)
    
    def test_find_snapshot(self, temp_version_file):
        """Test finding specific snapshot"""
        manager = VersionManager(version_file=temp_version_file)
        
        snapshot = VersionSnapshot(
            version='1.0.0',
            timestamp=datetime.now().isoformat(),
            backup_id='test_backup',
            description='Test'
        )
        manager._save_snapshot(snapshot)
        
        found = manager._find_snapshot('1.0.0')
        
        assert found is not None
        assert found.version == '1.0.0'
        assert found.backup_id == 'test_backup'
    
    def test_get_version_info(self, temp_version_file):
        """Test getting version information"""
        manager = VersionManager(version_file=temp_version_file)
        
        # Add snapshot
        snapshot = VersionSnapshot(
            version='1.0.0',
            timestamp=datetime.now().isoformat(),
            backup_id='test_backup',
            description='Test'
        )
        manager._save_snapshot(snapshot)
        
        info = manager.get_version_info()
        
        assert 'current_version' in info
        assert 'snapshots_count' in info
        assert 'available_versions' in info
        assert info['snapshots_count'] == 1
        assert '1.0.0' in info['available_versions']


# Integration Tests

class TestResilienceIntegration:
    """Integration tests for resilience module"""
    
    def test_backup_and_restore_workflow(self, temp_backup_dir, temp_data_dirs):
        """Test complete backup and restore workflow"""
        manager = BackupManager(
            backup_dir=temp_backup_dir,
            chromadb_path=str(temp_data_dirs['chromadb']),
            config_path=str(temp_data_dirs['config']),
            models_path=str(temp_data_dirs['models'])
        )
        
        # Create test backup manually
        backup_id = 'test_backup'
        backup_path = Path(temp_backup_dir) / backup_id
        backup_path.mkdir()
        
        # Backup config
        config_backup = backup_path / 'config'
        shutil.copytree(temp_data_dirs['config'], config_backup)
        
        # Create metadata
        metadata = {
            'backup_id': backup_id,
            'backup_type': 'full',
            'timestamp': datetime.now().isoformat(),
            'size_mb': manager._get_directory_size(backup_path),
            'components': ['config']
        }
        
        with open(backup_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f)
        
        # Modify original data
        test_file = temp_data_dirs['config'] / 'test.txt'
        test_file.write_text('modified data')
        
        # Restore backup
        success = manager.restore_backup(backup_id, verify=True)
        
        assert success is True
        assert test_file.read_text() == 'test data'  # Original data restored
    
    def test_health_monitoring_workflow(self):
        """Test health monitoring workflow"""
        monitor = HealthMonitor()
        
        with patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.virtual_memory') as mock_memory:
            
            mock_disk.return_value = Mock(percent=50.0)
            mock_memory.return_value = Mock(percent=60.0)
            
            health = monitor.run_health_checks()
            
            assert isinstance(health, SystemHealth)
            assert 'disk_space' in health.checks
            assert 'ram_usage' in health.checks
