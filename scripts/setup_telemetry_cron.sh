#!/bin/bash
# Setup Telemetry Upload Cron Job (Linux/macOS)
#
# This script configures a cron job to run telemetry upload every hour.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_PATH="${PROJECT_ROOT}/openclass-env/bin/python3"
CRON_SCRIPT="${SCRIPT_DIR}/telemetry_upload_cron.py"

echo "Setting up telemetry upload cron job..."
echo "Project root: $PROJECT_ROOT"
echo "Python path: $PYTHON_PATH"
echo "Cron script: $CRON_SCRIPT"

# Ensure logs directory exists
mkdir -p "${PROJECT_ROOT}/logs"

# Create cron job entry
CRON_ENTRY="0 * * * * cd $PROJECT_ROOT && $PYTHON_PATH $CRON_SCRIPT >> ${PROJECT_ROOT}/logs/telemetry_cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "telemetry_upload_cron.py"; then
    echo "Telemetry cron job already exists"
    echo "Current crontab:"
    crontab -l | grep "telemetry_upload_cron.py"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "Telemetry cron job added successfully"
    echo "Cron entry: $CRON_ENTRY"
fi

echo ""
echo "Cron job will run every hour at minute 0"
echo "Logs will be written to: ${PROJECT_ROOT}/logs/telemetry_cron.log"
echo ""
echo "To view current crontab: crontab -l"
echo "To remove cron job: crontab -e (then delete the line)"
echo ""
echo "Setup complete!"
