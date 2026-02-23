#!/bin/bash
# Install NexusAI systemd services

set -e

echo "Installing NexusAI systemd services..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Project directory: $PROJECT_DIR"

# Copy service files to systemd directory
echo "Copying service files..."
cp "$PROJECT_DIR/systemd/nexusai-api.service" /etc/systemd/system/
cp "$PROJECT_DIR/systemd/nexusai-health-monitor.service" /etc/systemd/system/

# Set correct permissions
chmod 644 /etc/systemd/system/nexusai-api.service
chmod 644 /etc/systemd/system/nexusai-health-monitor.service

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable services to start on boot
echo "Enabling services..."
systemctl enable nexusai-api.service
systemctl enable nexusai-health-monitor.service

# Create log directory
echo "Creating log directory..."
mkdir -p /var/log/nexusai
chown nexusai:nexusai /var/log/nexusai

# Create backup directory
echo "Creating backup directory..."
mkdir -p /backups
chown nexusai:nexusai /backups

# Create version file directory
echo "Creating version file directory..."
mkdir -p /etc/nexusai
chown nexusai:nexusai /etc/nexusai

echo ""
echo "✓ Systemd services installed successfully!"
echo ""
echo "To start the services, run:"
echo "  sudo systemctl start nexusai-api"
echo "  sudo systemctl start nexusai-health-monitor"
echo ""
echo "To check service status:"
echo "  sudo systemctl status nexusai-api"
echo "  sudo systemctl status nexusai-health-monitor"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u nexusai-api -f"
echo "  sudo journalctl -u nexusai-health-monitor -f"
echo ""
