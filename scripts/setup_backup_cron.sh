#!/bin/bash
# Setup cron jobs for automated backups

set -e

echo "Setting up backup cron jobs..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Project directory: $PROJECT_DIR"

# Create backup script
BACKUP_SCRIPT="/opt/nexusai/scripts/run_backup.py"
cat > "$BACKUP_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
Backup execution script for cron jobs
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.resilience.backup_scheduler import BackupScheduler

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
    """Run scheduled backup"""
    logger.info("Starting scheduled backup...")
    
    try:
        scheduler = BackupScheduler()
        success = scheduler.run_scheduled_backup()
        
        if success:
            logger.info("Scheduled backup completed successfully")
            sys.exit(0)
        else:
            logger.error("Scheduled backup failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Backup script failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
EOF

# Make backup script executable
chmod +x "$BACKUP_SCRIPT"
chown nexusai:nexusai "$BACKUP_SCRIPT"

# Create cron job file
CRON_FILE="/etc/cron.d/nexusai-backup"
cat > "$CRON_FILE" << EOF
# NexusAI Automated Backup Schedule
# Runs daily at 2 AM (full backup on Sunday, incremental Monday-Saturday)

SHELL=/bin/bash
PATH=/opt/nexusai/openclass-env/bin:/usr/local/bin:/usr/bin:/bin
PYTHONPATH=/opt/nexusai

# Daily backup at 2 AM
0 2 * * * nexusai /opt/nexusai/openclass-env/bin/python /opt/nexusai/scripts/run_backup.py >> /var/log/nexusai/backup_cron.log 2>&1
EOF

# Set correct permissions
chmod 644 "$CRON_FILE"

echo ""
echo "✓ Backup cron jobs installed successfully!"
echo ""
echo "Backup schedule:"
echo "  - Sunday 2 AM: Full backup (PostgreSQL + ChromaDB + config + models)"
echo "  - Monday-Saturday 2 AM: Incremental backup (chat history)"
echo "  - Automatic cleanup: Backups older than 28 days"
echo ""
echo "Backup logs:"
echo "  - /var/log/nexusai/backup.log"
echo "  - /var/log/nexusai/backup_cron.log"
echo ""
echo "To manually run a backup:"
echo "  sudo -u nexusai /opt/nexusai/openclass-env/bin/python /opt/nexusai/scripts/run_backup.py"
echo ""
