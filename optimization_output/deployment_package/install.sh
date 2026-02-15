#!/bin/bash
# OpenClass Nexus AI Installation Script

echo "Installing OpenClass Nexus AI..."

# Check Python version
python3 --version || { echo "Python 3.8+ required"; exit 1; }

# Create virtual environment
python3 -m venv openclass-env
source openclass-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp config/templates/default_config.yaml config/app_config.yaml

echo "Installation completed successfully!"
echo "Activate environment: source openclass-env/bin/activate"
echo "Run setup: python scripts/setup_phase2_aws.py"
