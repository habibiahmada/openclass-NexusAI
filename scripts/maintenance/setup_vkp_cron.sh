#!/bin/bash
# Setup VKP Pull Cron Job (Linux)
#
# This script sets up the hourly VKP pull cron job on Linux systems.
#
# Usage:
#   sudo bash scripts/setup_vkp_cron.sh

set -e

echo "Setting up VKP Pull Cron Job..."

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Project root: $PROJECT_ROOT"

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"
chmod 755 "$PROJECT_ROOT/logs"

# Make cron script executable
chmod +x "$PROJECT_ROOT/scripts/vkp_pull_cron.py"

# Get Python path
PYTHON_PATH=$(which python3)
echo "Python path: $PYTHON_PATH"

# Create cron job entry
CRON_ENTRY="0 * * * * $PYTHON_PATH $PROJECT_ROOT/scripts/vkp_pull_cron.py >> $PROJECT_ROOT/logs/vkp_pull.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "vkp_pull_cron.py"; then
    echo "VKP pull cron job already exists. Updating..."
    # Remove old entry
    crontab -l 2>/dev/null | grep -v "vkp_pull_cron.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✓ VKP pull cron job installed successfully"
echo "  Schedule: Every hour (at minute 0)"
echo "  Log file: $PROJECT_ROOT/logs/vkp_pull.log"

# Verify cron job
echo ""
echo "Current crontab:"
crontab -l | grep "vkp_pull_cron.py"

echo ""
echo "To manually run the VKP pull:"
echo "  $PYTHON_PATH $PROJECT_ROOT/scripts/vkp_pull_cron.py"

echo ""
echo "To view logs:"
echo "  tail -f $PROJECT_ROOT/logs/vkp_pull.log"

echo ""
echo "Setup complete!"
