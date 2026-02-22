"""
VersionManager - System version management and rollback capability
"""

import os
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class VersionSnapshot:
    """Snapshot of a system version"""
    version: str
    timestamp: str
    backup_id: str
    description: Optional[str] = None
    metadata: Optional[Dict] = None


class VersionManager:
    """
    Manages system versions and provides rollback capability.
    
    Features:
    - Track current system version
    - Create version snapshots
    - Rollback to previous versions
    - Store version metadata in PostgreSQL
    """
    
    def __init__(
        self,
        version_file: str = '/etc/nexusai/version.json',
        db_manager=None
    ):
        self.version_file = Path(version_file)
        self.db_manager = db_manager
        
        # Ensure version file directory exists
        self.version_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize version file if it doesn't exist
        if not self.version_file.exists():
            self._initialize_version_file()
        
        logger.info(f"VersionManager initialized (version_file: {self.version_file})")
    
    def get_current_version(self) -> str:
        """
        Get the current system version.
        
        Returns:
            str: Current version string (e.g., "1.0.0")
        """
        try:
            with open(self.version_file) as f:
                version_data = json.load(f)
                return version_data.get('version', '0.0.0')
        except Exception as e:
            logger.error(f"Failed to get current version: {e}", exc_info=True)
            return '0.0.0'
    
    def list_available_versions(self) -> List[VersionSnapshot]:
        """
        List all available version snapshots.
        
        Returns:
            List[VersionSnapshot]: List of available versions
        """
        try:
            with open(self.version_file) as f:
                version_data = json.load(f)
                snapshots_data = version_data.get('snapshots', [])
                
                snapshots = [
                    VersionSnapshot(**snapshot)
                    for snapshot in snapshots_data
                ]
                
                # Sort by timestamp (newest first)
                snapshots.sort(key=lambda s: s.timestamp, reverse=True)
                
                return snapshots
                
        except Exception as e:
            logger.error(f"Failed to list versions: {e}", exc_info=True)
            return []
    
    def create_version_snapshot(
        self,
        version: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Create a snapshot of the current system version.
        
        Args:
            version: Version string (if None, uses current version)
            description: Optional description of the snapshot
        
        Returns:
            str: Snapshot version identifier
        """
        if version is None:
            version = self.get_current_version()
        
        logger.info(f"Creating version snapshot: {version}")
        
        try:
            # Import BackupManager
            from .backup_manager import BackupManager
            
            # Create full backup
            backup_manager = BackupManager()
            backup_metadata = backup_manager.create_full_backup()
            
            # Create snapshot record
            snapshot = VersionSnapshot(
                version=version,
                timestamp=datetime.now().isoformat(),
                backup_id=backup_metadata.backup_id,
                description=description or f"Snapshot of version {version}",
                metadata={
                    'backup_size_mb': backup_metadata.size_mb,
                    'backup_components': backup_metadata.components
                }
            )
            
            # Save snapshot to version file
            self._save_snapshot(snapshot)
            
            # Store in PostgreSQL if available
            if self.db_manager:
                self._store_snapshot_in_db(snapshot)
            
            logger.info(f"Version snapshot created: {version} (backup: {backup_metadata.backup_id})")
            return version
            
        except Exception as e:
            logger.error(f"Failed to create version snapshot: {e}", exc_info=True)
            raise
    
    def rollback_to_version(self, version: str, verify: bool = True) -> bool:
        """
        Rollback system to a previous version.
        
        Args:
            version: Version to rollback to
            verify: Whether to verify backup integrity before rollback
        
        Returns:
            bool: True if rollback was successful
        """
        logger.info(f"Rolling back to version: {version}")
        
        try:
            # 1. Find snapshot for the target version
            snapshot = self._find_snapshot(version)
            if not snapshot:
                logger.error(f"Version snapshot not found: {version}")
                return False
            
            # 2. Create snapshot of current state (for safety)
            current_version = self.get_current_version()
            logger.info(f"Creating safety snapshot of current version: {current_version}")
            safety_snapshot = self.create_version_snapshot(
                description=f"Safety snapshot before rollback to {version}"
            )
            
            # 3. Stop services
            logger.info("Stopping services...")
            self._stop_services()
            
            # 4. Restore backup
            logger.info(f"Restoring backup: {snapshot.backup_id}")
            from .backup_manager import BackupManager
            backup_manager = BackupManager()
            
            if not backup_manager.restore_backup(snapshot.backup_id, verify=verify):
                logger.error("Backup restoration failed")
                # Try to restore safety snapshot
                logger.info("Attempting to restore safety snapshot...")
                self._restore_safety_snapshot(safety_snapshot)
                return False
            
            # 5. Update version metadata
            self._set_current_version(version)
            
            # 6. Restart services
            logger.info("Restarting services...")
            self._start_services()
            
            # 7. Verify health
            logger.info("Verifying system health...")
            from .health_monitor import HealthMonitor
            health_monitor = HealthMonitor()
            health = health_monitor.run_health_checks()
            
            if not health.healthy:
                logger.error("Rollback health check failed - reverting to safety snapshot")
                self._restore_safety_snapshot(safety_snapshot)
                return False
            
            logger.info(f"Successfully rolled back to version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)
            return False
    
    def get_version_info(self) -> dict:
        """
        Get detailed information about the current version.
        
        Returns:
            dict: Version information
        """
        try:
            with open(self.version_file) as f:
                version_data = json.load(f)
            
            return {
                'current_version': version_data.get('version', '0.0.0'),
                'updated_at': version_data.get('updated_at'),
                'snapshots_count': len(version_data.get('snapshots', [])),
                'available_versions': [s['version'] for s in version_data.get('snapshots', [])]
            }
        except Exception as e:
            logger.error(f"Failed to get version info: {e}", exc_info=True)
            return {
                'current_version': '0.0.0',
                'error': str(e)
            }
    
    # Private helper methods
    
    def _initialize_version_file(self):
        """Initialize version file with default values"""
        default_data = {
            'version': '1.0.0',
            'updated_at': datetime.now().isoformat(),
            'snapshots': []
        }
        
        # Ensure parent directory exists
        self.version_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.version_file, 'w') as f:
            json.dump(default_data, f, indent=2)
        
        logger.info("Initialized version file with default values")
    
    def _save_snapshot(self, snapshot: VersionSnapshot):
        """Save snapshot to version file"""
        with open(self.version_file) as f:
            version_data = json.load(f)
        
        # Add snapshot to list
        snapshots = version_data.get('snapshots', [])
        snapshots.append(asdict(snapshot))
        version_data['snapshots'] = snapshots
        
        # Save updated data
        with open(self.version_file, 'w') as f:
            json.dump(version_data, f, indent=2)
    
    def _find_snapshot(self, version: str) -> Optional[VersionSnapshot]:
        """Find snapshot by version"""
        snapshots = self.list_available_versions()
        for snapshot in snapshots:
            if snapshot.version == version:
                return snapshot
        return None
    
    def _set_current_version(self, version: str):
        """Set current version in version file"""
        try:
            with open(self.version_file) as f:
                content = f.read().strip()
                if not content:
                    # File is empty, initialize it
                    version_data = {
                        'version': version,
                        'updated_at': datetime.now().isoformat(),
                        'snapshots': []
                    }
                else:
                    version_data = json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            # File doesn't exist or is corrupted, initialize it
            version_data = {
                'version': version,
                'updated_at': datetime.now().isoformat(),
                'snapshots': []
            }
        
        version_data['version'] = version
        version_data['updated_at'] = datetime.now().isoformat()
        
        with open(self.version_file, 'w') as f:
            json.dump(version_data, f, indent=2)
        
        logger.info(f"Updated current version to: {version}")
    
    def _stop_services(self):
        """Stop system services"""
        services = ['nexusai-api', 'nexusai-health-monitor']
        
        for service in services:
            try:
                subprocess.run(
                    ['systemctl', 'stop', service],
                    check=True,
                    capture_output=True,
                    timeout=30
                )
                logger.info(f"Stopped service: {service}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to stop service {service}: {e.stderr}")
            except FileNotFoundError:
                logger.warning(f"systemctl not found, cannot stop service: {service}")
            except Exception as e:
                logger.warning(f"Error stopping service {service}: {e}")
    
    def _start_services(self):
        """Start system services"""
        services = ['nexusai-api', 'nexusai-health-monitor']
        
        for service in services:
            try:
                subprocess.run(
                    ['systemctl', 'start', service],
                    check=True,
                    capture_output=True,
                    timeout=30
                )
                logger.info(f"Started service: {service}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to start service {service}: {e.stderr}")
            except FileNotFoundError:
                logger.warning(f"systemctl not found, cannot start service: {service}")
            except Exception as e:
                logger.warning(f"Error starting service {service}: {e}")
    
    def _restore_safety_snapshot(self, safety_version: str):
        """Restore safety snapshot after failed rollback"""
        logger.info(f"Restoring safety snapshot: {safety_version}")
        
        try:
            snapshot = self._find_snapshot(safety_version)
            if not snapshot:
                logger.error(f"Safety snapshot not found: {safety_version}")
                return False
            
            from .backup_manager import BackupManager
            backup_manager = BackupManager()
            
            if backup_manager.restore_backup(snapshot.backup_id, verify=False):
                self._set_current_version(safety_version)
                self._start_services()
                logger.info("Safety snapshot restored successfully")
                return True
            else:
                logger.error("Failed to restore safety snapshot")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore safety snapshot: {e}", exc_info=True)
            return False
    
    def _store_snapshot_in_db(self, snapshot: VersionSnapshot):
        """Store snapshot metadata in PostgreSQL"""
        try:
            if not self.db_manager:
                return
            
            query = """
                INSERT INTO version_snapshots 
                (version, timestamp, backup_id, description, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            self.db_manager.execute_query(
                query,
                (
                    snapshot.version,
                    snapshot.timestamp,
                    snapshot.backup_id,
                    snapshot.description,
                    json.dumps(snapshot.metadata) if snapshot.metadata else None
                )
            )
            
            logger.info(f"Stored snapshot in database: {snapshot.version}")
            
        except Exception as e:
            logger.warning(f"Failed to store snapshot in database: {e}")
            # Don't raise - database storage is optional
