"""
BackupScheduler - Schedules and manages automated backups
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from .backup_manager import BackupManager, BackupMetadata

logger = logging.getLogger(__name__)


class BackupScheduler:
    """
    Schedules and manages automated backups:
    - Weekly full backups (Sunday 2 AM)
    - Daily incremental backups (Monday-Saturday 2 AM)
    - Cleanup of old backups (28-day retention)
    """
    
    def __init__(
        self,
        backup_manager: Optional[BackupManager] = None,
        retention_days: int = 28
    ):
        self.backup_manager = backup_manager or BackupManager()
        self.retention_days = retention_days
        
        logger.info(f"BackupScheduler initialized with {retention_days}-day retention")
    
    def schedule_weekly_full_backup(self) -> bool:
        """
        Schedule a weekly full backup (Sunday 2 AM).
        This method should be called by a cron job.
        
        Returns:
            bool: True if backup was scheduled/executed successfully
        """
        logger.info("Scheduling weekly full backup...")
        
        try:
            # Check if today is Sunday
            if datetime.now().weekday() != 6:  # 6 = Sunday
                logger.info("Not Sunday, skipping full backup")
                return False
            
            # Execute full backup
            metadata = self.backup_manager.create_full_backup()
            
            # Compress backup
            compressed_path = self.backup_manager.compress_backup(metadata.backup_id)
            logger.info(f"Full backup compressed: {compressed_path}")
            
            # Optional: Encrypt backup
            if os.getenv('BACKUP_ENCRYPTION_ENABLED', 'false').lower() == 'true':
                encrypted_path = self.backup_manager.encrypt_backup(compressed_path)
                logger.info(f"Full backup encrypted: {encrypted_path}")
            
            # Optional: Upload to S3
            if os.getenv('BACKUP_S3_ENABLED', 'false').lower() == 'true':
                self._upload_to_s3(compressed_path)
            
            logger.info(f"Weekly full backup completed: {metadata.backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Weekly full backup failed: {e}", exc_info=True)
            return False
    
    def schedule_daily_incremental_backup(self) -> bool:
        """
        Schedule a daily incremental backup (Monday-Saturday 2 AM).
        This method should be called by a cron job.
        
        Returns:
            bool: True if backup was scheduled/executed successfully
        """
        logger.info("Scheduling daily incremental backup...")
        
        try:
            # Check if today is Monday-Saturday
            weekday = datetime.now().weekday()
            if weekday == 6:  # Sunday - full backup day
                logger.info("Sunday, skipping incremental backup (full backup day)")
                return False
            
            # Execute incremental backup
            metadata = self.backup_manager.create_incremental_backup()
            
            # Compress backup
            compressed_path = self.backup_manager.compress_backup(metadata.backup_id)
            logger.info(f"Incremental backup compressed: {compressed_path}")
            
            # Optional: Encrypt backup
            if os.getenv('BACKUP_ENCRYPTION_ENABLED', 'false').lower() == 'true':
                encrypted_path = self.backup_manager.encrypt_backup(compressed_path)
                logger.info(f"Incremental backup encrypted: {encrypted_path}")
            
            # Optional: Upload to S3
            if os.getenv('BACKUP_S3_ENABLED', 'false').lower() == 'true':
                self._upload_to_s3(compressed_path)
            
            logger.info(f"Daily incremental backup completed: {metadata.backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Daily incremental backup failed: {e}", exc_info=True)
            return False
    
    def cleanup_old_backups(self) -> int:
        """
        Clean up backups older than retention period (default 28 days).
        
        Returns:
            int: Number of backups deleted
        """
        logger.info(f"Cleaning up backups older than {self.retention_days} days...")
        
        backup_dir = self.backup_manager.backup_dir
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        deleted_count = 0
        
        try:
            for backup_folder in backup_dir.iterdir():
                if not backup_folder.is_dir():
                    continue
                
                # Read metadata
                metadata_file = backup_folder / 'metadata.json'
                if not metadata_file.exists():
                    continue
                
                import json
                with open(metadata_file) as f:
                    metadata = json.load(f)
                
                backup_date = datetime.fromisoformat(metadata['timestamp'])
                
                # Delete if older than retention period
                days_old = (datetime.now() - backup_date).days
                if days_old > self.retention_days:
                    logger.info(f"Deleting old backup: {backup_folder.name} "
                               f"(created {backup_date.strftime('%Y-%m-%d')}, {days_old} days old)")
                    
                    # Delete backup directory
                    import shutil
                    shutil.rmtree(backup_folder)
                    
                    # Delete compressed file if exists
                    compressed_file = backup_dir / f"{backup_folder.name}.tar.gz"
                    if compressed_file.exists():
                        compressed_file.unlink()
                    
                    # Delete encrypted file if exists
                    encrypted_file = backup_dir / f"{backup_folder.name}.tar.gz.enc"
                    if encrypted_file.exists():
                        encrypted_file.unlink()
                    
                    deleted_count += 1
            
            logger.info(f"Cleanup completed: {deleted_count} backups deleted")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}", exc_info=True)
            return deleted_count
    
    def run_scheduled_backup(self) -> bool:
        """
        Run the appropriate backup based on the day of the week.
        This is the main entry point for the cron job.
        
        Returns:
            bool: True if backup was successful
        """
        weekday = datetime.now().weekday()
        
        if weekday == 6:  # Sunday
            success = self.schedule_weekly_full_backup()
        else:  # Monday-Saturday
            success = self.schedule_daily_incremental_backup()
        
        # Always run cleanup after backup
        if success:
            self.cleanup_old_backups()
        
        return success
    
    def _upload_to_s3(self, file_path: str):
        """
        Upload backup to S3 (optional feature).
        
        Args:
            file_path: Path to the backup file to upload
        """
        try:
            import boto3
            
            s3_bucket = os.getenv('BACKUP_S3_BUCKET', 'nexusai-backups')
            s3_client = boto3.client('s3')
            
            file_name = Path(file_path).name
            s3_key = f"backups/{file_name}"
            
            logger.info(f"Uploading backup to S3: s3://{s3_bucket}/{s3_key}")
            
            s3_client.upload_file(file_path, s3_bucket, s3_key)
            
            logger.info(f"Backup uploaded to S3 successfully")
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}", exc_info=True)
            # Don't raise - S3 upload is optional
    
    def get_backup_schedule_info(self) -> dict:
        """
        Get information about the backup schedule.
        
        Returns:
            dict: Schedule information
        """
        return {
            'full_backup_schedule': 'Sunday 2 AM',
            'incremental_backup_schedule': 'Monday-Saturday 2 AM',
            'retention_days': self.retention_days,
            'encryption_enabled': os.getenv('BACKUP_ENCRYPTION_ENABLED', 'false').lower() == 'true',
            's3_upload_enabled': os.getenv('BACKUP_S3_ENABLED', 'false').lower() == 'true',
            's3_bucket': os.getenv('BACKUP_S3_BUCKET', 'nexusai-backups') if os.getenv('BACKUP_S3_ENABLED', 'false').lower() == 'true' else None
        }
