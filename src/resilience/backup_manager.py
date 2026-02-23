"""
BackupManager - Handles backup creation, restoration, compression, and encryption
"""

import os
import json
import gzip
import shutil
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for a backup"""
    backup_id: str
    backup_type: str  # 'full' or 'incremental'
    timestamp: str
    size_mb: float
    components: list
    base_backup: Optional[str] = None  # For incremental backups
    compressed: bool = False
    encrypted: bool = False
    checksum: Optional[str] = None


class BackupManager:
    """
    Manages backup creation, restoration, compression, and encryption
    for PostgreSQL, ChromaDB, and configuration files.
    """
    
    def __init__(
        self,
        backup_dir: str = '/backups',
        postgres_db: str = 'nexusai_school',
        postgres_user: str = 'nexusai',
        chromadb_path: str = '/data/vector_db',
        config_path: str = '/config',
        models_path: str = '/models'
    ):
        self.backup_dir = Path(backup_dir)
        self.postgres_db = postgres_db
        self.postgres_user = postgres_user
        self.chromadb_path = Path(chromadb_path)
        self.config_path = Path(config_path)
        self.models_path = Path(models_path)
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"BackupManager initialized with backup_dir: {self.backup_dir}")
    
    def create_full_backup(self) -> BackupMetadata:
        """
        Create a full backup of PostgreSQL, ChromaDB, and configuration files.
        
        Returns:
            BackupMetadata: Metadata about the created backup
        """
        backup_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Creating full backup: {backup_id}")
        
        components = []
        
        try:
            # 1. Backup PostgreSQL
            logger.info("Backing up PostgreSQL...")
            postgres_file = backup_path / 'postgres.sql'
            self._backup_postgres(postgres_file)
            components.append('postgres')
            
            # 2. Backup ChromaDB
            logger.info("Backing up ChromaDB...")
            chromadb_backup = backup_path / 'vector_db'
            self._backup_chromadb(chromadb_backup)
            components.append('chromadb')
            
            # 3. Backup configuration
            logger.info("Backing up configuration...")
            config_backup = backup_path / 'config'
            self._backup_config(config_backup)
            components.append('config')
            
            # 4. Backup models (if they exist)
            if self.models_path.exists():
                logger.info("Backing up models...")
                models_backup = backup_path / 'models'
                self._backup_models(models_backup)
                components.append('models')
            
            # 5. Calculate size
            size_mb = self._get_directory_size(backup_path)
            
            # 6. Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type='full',
                timestamp=datetime.now().isoformat(),
                size_mb=size_mb,
                components=components
            )
            
            # 7. Save metadata
            metadata_file = backup_path / 'metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)
            
            logger.info(f"Full backup completed: {backup_id} ({size_mb:.2f} MB)")
            return metadata
            
        except Exception as e:
            logger.error(f"Full backup failed: {e}", exc_info=True)
            # Cleanup partial backup
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise
    
    def create_incremental_backup(self, since: Optional[datetime] = None) -> BackupMetadata:
        """
        Create an incremental backup of chat history since the last backup.
        
        Args:
            since: Timestamp to backup from. If None, uses last backup timestamp.
        
        Returns:
            BackupMetadata: Metadata about the created backup
        """
        backup_id = f"incr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Get last backup timestamp if not provided
        if since is None:
            since = self._get_last_backup_timestamp()
        
        logger.info(f"Creating incremental backup: {backup_id} (since {since})")
        
        components = []
        
        try:
            # 1. Backup PostgreSQL (only new chat history)
            logger.info("Backing up PostgreSQL incremental...")
            postgres_file = backup_path / 'postgres_incremental.sql'
            self._backup_postgres_incremental(postgres_file, since)
            components.append('postgres_incremental')
            
            # 2. Backup ChromaDB only if VKP updated
            if self._check_vkp_updated_since(since):
                logger.info("VKP updated, backing up ChromaDB...")
                chromadb_backup = backup_path / 'vector_db'
                self._backup_chromadb(chromadb_backup)
                components.append('chromadb')
            
            # 3. Calculate size
            size_mb = self._get_directory_size(backup_path)
            
            # 4. Get last full backup ID
            last_full_backup = self._get_last_full_backup_id()
            
            # 5. Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type='incremental',
                timestamp=datetime.now().isoformat(),
                size_mb=size_mb,
                components=components,
                base_backup=last_full_backup
            )
            
            # 6. Save metadata
            metadata_file = backup_path / 'metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)
            
            logger.info(f"Incremental backup completed: {backup_id} ({size_mb:.2f} MB)")
            return metadata
            
        except Exception as e:
            logger.error(f"Incremental backup failed: {e}", exc_info=True)
            # Cleanup partial backup
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise
    
    def restore_backup(self, backup_id: str, verify: bool = True) -> bool:
        """
        Restore a backup with optional verification.
        
        Args:
            backup_id: ID of the backup to restore
            verify: Whether to verify backup integrity before restoring
        
        Returns:
            bool: True if restoration successful
        """
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_id}")
            return False
        
        logger.info(f"Restoring backup: {backup_id}")
        
        try:
            # 1. Load metadata
            metadata_file = backup_path / 'metadata.json'
            with open(metadata_file) as f:
                metadata_dict = json.load(f)
                metadata = BackupMetadata(**metadata_dict)
            
            # 2. Verify integrity if requested
            if verify:
                logger.info("Verifying backup integrity...")
                if not self.verify_backup_integrity(backup_id):
                    logger.error("Backup integrity verification failed")
                    return False
            
            # 3. Restore PostgreSQL
            if 'postgres' in metadata.components or 'postgres_incremental' in metadata.components:
                logger.info("Restoring PostgreSQL...")
                postgres_file = backup_path / ('postgres.sql' if 'postgres' in metadata.components 
                                               else 'postgres_incremental.sql')
                self._restore_postgres(postgres_file)
            
            # 4. Restore ChromaDB
            if 'chromadb' in metadata.components:
                logger.info("Restoring ChromaDB...")
                chromadb_backup = backup_path / 'vector_db'
                self._restore_chromadb(chromadb_backup)
            
            # 5. Restore configuration
            if 'config' in metadata.components:
                logger.info("Restoring configuration...")
                config_backup = backup_path / 'config'
                self._restore_config(config_backup)
            
            # 6. Restore models
            if 'models' in metadata.components:
                logger.info("Restoring models...")
                models_backup = backup_path / 'models'
                self._restore_models(models_backup)
            
            logger.info(f"Backup restored successfully: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}", exc_info=True)
            return False
    
    def compress_backup(self, backup_id: str) -> str:
        """
        Compress a backup using gzip.
        
        Args:
            backup_id: ID of the backup to compress
        
        Returns:
            str: Path to the compressed backup file
        """
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")
        
        logger.info(f"Compressing backup: {backup_id}")
        
        # Create tar.gz archive
        archive_path = self.backup_dir / f"{backup_id}.tar.gz"
        
        try:
            # Use tar with gzip compression
            subprocess.run(
                ['tar', '-czf', str(archive_path), '-C', str(self.backup_dir), backup_id],
                check=True,
                capture_output=True
            )
            
            # Update metadata
            metadata_file = backup_path / 'metadata.json'
            with open(metadata_file) as f:
                metadata_dict = json.load(f)
            
            metadata_dict['compressed'] = True
            metadata_dict['compressed_path'] = str(archive_path)
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
            
            original_size = self._get_directory_size(backup_path)
            compressed_size = os.path.getsize(archive_path) / (1024 * 1024)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            logger.info(f"Backup compressed: {archive_path} "
                       f"({original_size:.2f} MB -> {compressed_size:.2f} MB, "
                       f"{compression_ratio:.1f}% reduction)")
            
            return str(archive_path)
            
        except Exception as e:
            logger.error(f"Backup compression failed: {e}", exc_info=True)
            if archive_path.exists():
                os.remove(archive_path)
            raise
    
    def encrypt_backup(self, backup_path: str, encryption_key: Optional[str] = None) -> str:
        """
        Encrypt a backup file using AES encryption.
        
        Args:
            backup_path: Path to the backup file to encrypt
            encryption_key: Encryption key (if None, uses environment variable)
        
        Returns:
            str: Path to the encrypted backup file
        """
        if encryption_key is None:
            encryption_key = os.getenv('BACKUP_ENCRYPTION_KEY')
            if not encryption_key:
                raise ValueError("No encryption key provided")
        
        logger.info(f"Encrypting backup: {backup_path}")
        
        encrypted_path = f"{backup_path}.enc"
        
        try:
            # Use openssl for encryption (AES-256-CBC)
            subprocess.run(
                ['openssl', 'enc', '-aes-256-cbc', '-salt', '-pbkdf2',
                 '-in', backup_path, '-out', encrypted_path,
                 '-k', encryption_key],
                check=True,
                capture_output=True
            )
            
            logger.info(f"Backup encrypted: {encrypted_path}")
            return encrypted_path
            
        except Exception as e:
            logger.error(f"Backup encryption failed: {e}", exc_info=True)
            if os.path.exists(encrypted_path):
                os.remove(encrypted_path)
            raise
    
    def verify_backup_integrity(self, backup_id: str) -> bool:
        """
        Verify the integrity of a backup by checking file existence and metadata.
        
        Args:
            backup_id: ID of the backup to verify
        
        Returns:
            bool: True if backup is valid
        """
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_id}")
            return False
        
        try:
            # 1. Check metadata exists
            metadata_file = backup_path / 'metadata.json'
            if not metadata_file.exists():
                logger.error("Metadata file missing")
                return False
            
            # 2. Load metadata
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            # 3. Verify components exist
            for component in metadata['components']:
                if component == 'postgres':
                    if not (backup_path / 'postgres.sql').exists():
                        logger.error("PostgreSQL backup file missing")
                        return False
                elif component == 'postgres_incremental':
                    if not (backup_path / 'postgres_incremental.sql').exists():
                        logger.error("PostgreSQL incremental backup file missing")
                        return False
                elif component == 'chromadb':
                    if not (backup_path / 'vector_db').exists():
                        logger.error("ChromaDB backup directory missing")
                        return False
                elif component == 'config':
                    if not (backup_path / 'config').exists():
                        logger.error("Config backup directory missing")
                        return False
                elif component == 'models':
                    if not (backup_path / 'models').exists():
                        logger.error("Models backup directory missing")
                        return False
            
            logger.info(f"Backup integrity verified: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}", exc_info=True)
            return False
    
    # Private helper methods
    
    def _backup_postgres(self, output_file: Path):
        """Backup PostgreSQL database"""
        try:
            subprocess.run(
                ['pg_dump', '-U', self.postgres_user, self.postgres_db],
                stdout=open(output_file, 'w'),
                check=True,
                capture_output=False
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"PostgreSQL backup failed: {e}")
    
    def _backup_postgres_incremental(self, output_file: Path, since: datetime):
        """Backup PostgreSQL incrementally (only new chat history)"""
        try:
            # Dump only chat_history table with WHERE clause
            query = f"SELECT * FROM chat_history WHERE created_at > '{since.isoformat()}'"
            subprocess.run(
                ['pg_dump', '-U', self.postgres_user, self.postgres_db,
                 '--table=chat_history', f"--where=created_at > '{since.isoformat()}'"],
                stdout=open(output_file, 'w'),
                check=True,
                capture_output=False
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"PostgreSQL incremental backup failed: {e}")
    
    def _backup_chromadb(self, output_dir: Path):
        """Backup ChromaDB directory"""
        if self.chromadb_path.exists():
            shutil.copytree(self.chromadb_path, output_dir, dirs_exist_ok=True)
        else:
            logger.warning(f"ChromaDB path not found: {self.chromadb_path}")
    
    def _backup_config(self, output_dir: Path):
        """Backup configuration directory"""
        if self.config_path.exists():
            shutil.copytree(self.config_path, output_dir, dirs_exist_ok=True)
        else:
            logger.warning(f"Config path not found: {self.config_path}")
    
    def _backup_models(self, output_dir: Path):
        """Backup models directory"""
        if self.models_path.exists():
            shutil.copytree(self.models_path, output_dir, dirs_exist_ok=True)
        else:
            logger.warning(f"Models path not found: {self.models_path}")
    
    def _restore_postgres(self, backup_file: Path):
        """Restore PostgreSQL database"""
        try:
            subprocess.run(
                ['psql', '-U', self.postgres_user, self.postgres_db],
                stdin=open(backup_file, 'r'),
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"PostgreSQL restore failed: {e}")
    
    def _restore_chromadb(self, backup_dir: Path):
        """Restore ChromaDB directory"""
        if backup_dir.exists():
            # Remove existing ChromaDB data
            if self.chromadb_path.exists():
                shutil.rmtree(self.chromadb_path)
            # Copy backup
            shutil.copytree(backup_dir, self.chromadb_path)
        else:
            raise FileNotFoundError(f"ChromaDB backup not found: {backup_dir}")
    
    def _restore_config(self, backup_dir: Path):
        """Restore configuration directory"""
        if backup_dir.exists():
            # Remove existing config
            if self.config_path.exists():
                shutil.rmtree(self.config_path)
            # Copy backup
            shutil.copytree(backup_dir, self.config_path)
        else:
            raise FileNotFoundError(f"Config backup not found: {backup_dir}")
    
    def _restore_models(self, backup_dir: Path):
        """Restore models directory"""
        if backup_dir.exists():
            # Remove existing models
            if self.models_path.exists():
                shutil.rmtree(self.models_path)
            # Copy backup
            shutil.copytree(backup_dir, self.models_path)
        else:
            raise FileNotFoundError(f"Models backup not found: {backup_dir}")
    
    def _get_directory_size(self, path: Path) -> float:
        """Get directory size in MB"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size / (1024 * 1024)  # Convert to MB
    
    def _get_last_backup_timestamp(self) -> datetime:
        """Get timestamp of the last backup"""
        backups = []
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        backups.append(datetime.fromisoformat(metadata['timestamp']))
        
        if backups:
            return max(backups)
        else:
            # Default to 24 hours ago if no backups exist
            from datetime import timedelta
            return datetime.now() - timedelta(days=1)
    
    def _get_last_full_backup_id(self) -> Optional[str]:
        """Get ID of the last full backup"""
        full_backups = []
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        if metadata['backup_type'] == 'full':
                            full_backups.append((
                                datetime.fromisoformat(metadata['timestamp']),
                                metadata['backup_id']
                            ))
        
        if full_backups:
            full_backups.sort(reverse=True)
            return full_backups[0][1]
        return None
    
    def _check_vkp_updated_since(self, since: datetime) -> bool:
        """Check if VKP was updated since the given timestamp"""
        # This would check the VKP version metadata in PostgreSQL
        # For now, return False (no VKP update detection)
        # TODO: Implement VKP update detection
        return False
