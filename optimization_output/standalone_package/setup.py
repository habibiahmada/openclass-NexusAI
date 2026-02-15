#!/usr/bin/env python3
"""
OpenClass Nexus AI Setup Script
Automated setup for standalone deployment
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def create_virtual_environment():
    """Create virtual environment."""
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "openclass-env"], check=True)
    print("✓ Virtual environment created")

def install_dependencies():
    """Install Python dependencies."""
    print("Installing dependencies...")
    
    # Determine pip path based on OS
    if platform.system() == "Windows":
        pip_path = "openclass-env/Scripts/pip"
    else:
        pip_path = "openclass-env/bin/pip"
    
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    print("✓ Dependencies installed")

def setup_configuration():
    """Setup initial configuration."""
    print("Setting up configuration...")
    
    config_dir = Path("config")
    if not config_dir.exists():
        config_dir.mkdir()
    
    # Copy default configuration
    default_config = config_dir / "templates" / "production.yaml"
    if default_config.exists():
        import shutil
        shutil.copy2(default_config, config_dir / "app_config.yaml")
        print("✓ Configuration setup complete")
    else:
        print("⚠ Default configuration not found, manual setup required")

def create_directories():
    """Create necessary directories."""
    print("Creating directories...")
    
    directories = ["data/vector_db", "data/processed", "models/cache", "logs"]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directories created")

def main():
    """Main setup function."""
    print("OpenClass Nexus AI Setup")
    print("=" * 30)
    
    try:
        check_python_version()
        create_virtual_environment()
        install_dependencies()
        setup_configuration()
        create_directories()
        
        print("\n✓ Setup completed successfully!")
        print("\nNext steps:")
        if platform.system() == "Windows":
            print("1. Activate environment: openclass-env\\Scripts\\activate")
        else:
            print("1. Activate environment: source openclass-env/bin/activate")
        print("2. Configure AWS (if needed): python scripts/setup_phase2_aws.py")
        print("3. Run application: python -m src.local_inference.complete_pipeline")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
