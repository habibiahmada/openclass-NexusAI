#!/usr/bin/env python3
"""
Backup Execution Script

This script is called by cron to execute scheduled backups.
It runs the appropriate backup based on the day of the week:
- Sunday: Full backup
- Monday-Saturday: Incremental backup

Usage:
    python scripts/run_backup.py [--full] [--incremental] [--cleanup-only]
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.resilience.backup_scheduler import BackupScheduler
from src.resilience.backup_manager import BackupManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nexusai/backup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for backup execution"""
    parser = argparse.ArgumentParser(description='Execute NexusAI backups')
    parser.add_argument('--full', action='store_true', help='Force full backup')
    parser.add_argument('--incremental', action='store_true', help='Force incremental backup')
    parser.add_argument('--cleanup-only', action='store_true', help='Only run cleanup')
    parser.add_argument('--retention-days', type=int, default=28, help='Backup retention days')
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 80)
        logger.info("Starting backup execution")
        logger.info("=" * 80)
        
        # Initialize backup manager and scheduler
        backup_manager = BackupManager()
        scheduler = BackupScheduler(
            backup_manager=backup_manager,
            retention_days=args.retention_days
        )
        
        # Execute requested operation
        if args.cleanup_only:
            logger.info("Running cleanup only...")
            deleted_count = scheduler.cleanup_old_backups()
            logger.info(f"Cleanup completed: {deleted_count} backups deleted")
            
        elif args.full:
            logger.info("Forcing full backup...")
            success = scheduler.schedule_weekly_full_backup()
            if success:
                logger.info("Full backup completed successfully")
                scheduler.cleanup_old_backups()
            else:
                logger.error("Full backup failed")
                sys.exit(1)
                
        elif args.incremental:
            logger.info("Forcing incremental backup...")
            success = scheduler.schedule_daily_incremental_backup()
            if success:
                logger.info("Incremental backup completed successfully")
                scheduler.cleanup_old_backups()
            else:
                logger.error("Incremental backup failed")
                sys.exit(1)
                
        else:
            # Run scheduled backup (auto-detect based on day of week)
            logger.info("Running scheduled backup...")
            success = scheduler.run_scheduled_backup()
            if success:
                logger.info("Scheduled backup completed successfully")
            else:
                logger.error("Scheduled backup failed")
                sys.exit(1)
        
        logger.info("=" * 80)
        logger.info("Backup execution completed")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Backup execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
