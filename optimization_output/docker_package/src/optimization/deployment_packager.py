"""
Deployment Package Creator

This module creates final deployment packages with all dependencies,
configuration templates, and installation scripts for production deployment.
"""

import logging
import json
import shutil
import tarfile
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from .production_validator import ProductionReadinessValidator
from .models import DeploymentPackage, ConfigurationTemplates
from .config import OptimizationConfig

logger = logging.getLogger(__name__)


class DeploymentPackager:
    """Creates comprehensive deployment packages for production."""
    
    def __init__(self, config: OptimizationConfig):
        """Initialize the deployment packager."""
        self.config = config
        self.project_root = config.project_root
        self.output_dir = config.optimization_output_dir
        self.validator = ProductionReadinessValidator(config)
        
        logger.info("Deployment packager initialized")
    
    def create_final_deployment_packages(self) -> Dict[str, DeploymentPackage]:
        """Create final deployment packages for different environments."""
        logger.info("Creating final deployment packages")
        
        packages = {}
        
        try:
            # Create base deployment package
            base_package = self.validator.create_deployment_package()
            packages['base'] = base_package
            
            # Create environment-specific packages
            packages['docker'] = self._create_docker_package()
            packages['standalone'] = self._create_standalone_package()
            packages['cloud'] = self._create_cloud_package()
            
            # Create compressed archives
            self._create_compressed_archives(packages)
            
            logger.info("Final deployment packages created successfully")
            return packages
            
        except Exception as e:
            logger.error(f"Failed to create deployment packages: {e}")
            raise
    
    def _create_docker_package(self) -> DeploymentPackage:
        """Create Docker-specific deployment package."""
        logger.info("Creating Docker deployment package")
        
        docker_dir = self.output_dir / "docker_package"
        docker_dir.mkdir(exist_ok=True)
        
        # Copy base files
        self._copy_essential_files(docker_dir)
        
        # Create Docker-specific files
        self._create_dockerfile(docker_dir)
        self._create_docker_compose(docker_dir)
        self._create_docker_scripts(docker_dir)
        
        # Create Docker configuration
        docker_config = {
            "image_name": "openclass-nexus-ai",
            "version": "latest",
            "ports": ["8000:8000"],
            "volumes": [
                "./data:/app/data",
                "./models:/app/models",
                "./config:/app/config"
            ],
            "environment": {
                "OPENCLASS_ENV": "docker",
                "OPENCLASS_LOG_LEVEL": "INFO"
            }
        }
        
        config_file = docker_dir / "docker-config.json"
        config_file.write_text(json.dumps(docker_config, indent=2))
        
        package_size = self._calculate_directory_size(docker_dir)
        checksum = self._generate_package_checksum(docker_dir)
        
        return DeploymentPackage(
            package_path=str(docker_dir),
            dependencies_included=True,
            configuration_templates=["docker-compose.yml", "Dockerfile", "docker-config.json"],
            installation_scripts=["docker-build.sh", "docker-run.sh"],
            package_size_mb=package_size,
            checksum=checksum
        )
    
    def _create_standalone_package(self) -> DeploymentPackage:
        """Create standalone deployment package."""
        logger.info("Creating standalone deployment package")
        
        standalone_dir = self.output_dir / "standalone_package"
        standalone_dir.mkdir(exist_ok=True)
        
        # Copy all necessary files
        self._copy_essential_files(standalone_dir)
        
        # Create standalone scripts
        self._create_standalone_scripts(standalone_dir)
        
        # Create requirements with pinned versions
        self._create_pinned_requirements(standalone_dir)
        
        # Create standalone configuration
        standalone_config = {
            "deployment_type": "standalone",
            "python_version": "3.9+",
            "system_requirements": {
                "ram_gb": 4,
                "storage_gb": 10,
                "cpu_cores": 2
            },
            "dependencies": {
                "python_packages": "requirements.txt",
                "system_packages": ["gcc", "python3-dev"]
            }
        }
        
        config_file = standalone_dir / "standalone-config.json"
        config_file.write_text(json.dumps(standalone_config, indent=2))
        
        package_size = self._calculate_directory_size(standalone_dir)
        checksum = self._generate_package_checksum(standalone_dir)
        
        return DeploymentPackage(
            package_path=str(standalone_dir),
            dependencies_included=True,
            configuration_templates=["production.yaml", "standalone-config.json"],
            installation_scripts=["install.sh", "install.bat", "setup.py"],
            package_size_mb=package_size,
            checksum=checksum
        )
    
    def _create_cloud_package(self) -> DeploymentPackage:
        """Create cloud deployment package."""
        logger.info("Creating cloud deployment package")
        
        cloud_dir = self.output_dir / "cloud_package"
        cloud_dir.mkdir(exist_ok=True)
        
        # Copy essential files
        self._copy_essential_files(cloud_dir)
        
        # Create cloud-specific files
        self._create_cloud_configs(cloud_dir)
        self._create_cloud_scripts(cloud_dir)
        
        package_size = self._calculate_directory_size(cloud_dir)
        checksum = self._generate_package_checksum(cloud_dir)
        
        return DeploymentPackage(
            package_path=str(cloud_dir),
            dependencies_included=True,
            configuration_templates=["aws-config.yaml", "gcp-config.yaml", "azure-config.yaml"],
            installation_scripts=["deploy-aws.sh", "deploy-gcp.sh", "deploy-azure.sh"],
            package_size_mb=package_size,
            checksum=checksum
        )
    
    def _copy_essential_files(self, target_dir: Path):
        """Copy essential project files to target directory."""
        essential_dirs = ['src', 'config', 'scripts']
        essential_files = ['requirements.txt', 'README.md', 'SETUP_GUIDE.md']
        
        for dir_name in essential_dirs:
            src_dir = self.project_root / dir_name
            if src_dir.exists():
                dest_dir = target_dir / dir_name
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                shutil.copytree(src_dir, dest_dir)
        
        for file_name in essential_files:
            src_file = self.project_root / file_name
            if src_file.exists():
                shutil.copy2(src_file, target_dir / file_name)
    
    def _create_dockerfile(self, docker_dir: Path):
        """Create optimized Dockerfile."""
        dockerfile_content = """FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    python3-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/vector_db data/processed models/cache logs

# Set permissions
RUN chmod +x scripts/*.py

# Create non-root user
RUN useradd -m -u 1000 openclass && chown -R openclass:openclass /app
USER openclass

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD python -c "from src.local_inference.complete_pipeline import CompletePipeline; print('healthy')"

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "src.local_inference.complete_pipeline"]
"""
        dockerfile = docker_dir / "Dockerfile"
        dockerfile.write_text(dockerfile_content, encoding='utf-8')
    
    def _create_docker_compose(self, docker_dir: Path):
        """Create Docker Compose configuration."""
        compose_content = """version: '3.8'

services:
  openclass-ai:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - OPENCLASS_ENV=docker
      - OPENCLASS_LOG_LEVEL=INFO
      - OPENCLASS_MAX_MEMORY_GB=4
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "from src.local_inference.complete_pipeline import CompletePipeline; print('healthy')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  # Optional: Add monitoring
  # prometheus:
  #   image: prom/prometheus:latest
  #   ports:
  #     - "9090:9090"
  #   volumes:
  #     - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

networks:
  default:
    name: openclass-network
"""
        compose_file = docker_dir / "docker-compose.yml"
        compose_file.write_text(compose_content, encoding='utf-8')
    
    def _create_docker_scripts(self, docker_dir: Path):
        """Create Docker deployment scripts."""
        # Build script
        build_script = docker_dir / "docker-build.sh"
        build_script_content = """#!/bin/bash
# Docker build script for OpenClass Nexus AI

echo "Building OpenClass Nexus AI Docker image..."

# Build the image
docker build -t openclass-nexus-ai:latest .

# Tag for different environments
docker tag openclass-nexus-ai:latest openclass-nexus-ai:production
docker tag openclass-nexus-ai:latest openclass-nexus-ai:$(date +%Y%m%d)

echo "Docker image built successfully!"
echo "Run with: ./docker-run.sh"
"""
        build_script.write_text(build_script_content, encoding='utf-8')
        build_script.chmod(0o755)
        
        # Run script
        run_script = docker_dir / "docker-run.sh"
        run_script_content = """#!/bin/bash
# Docker run script for OpenClass Nexus AI

echo "Starting OpenClass Nexus AI..."

# Create necessary directories
mkdir -p data models config logs

# Run with Docker Compose
docker-compose up -d

echo "OpenClass Nexus AI started successfully!"
echo "Access at: http://localhost:8000"
echo "View logs: docker-compose logs -f"
echo "Stop with: docker-compose down"
"""
        run_script.write_text(run_script_content, encoding='utf-8')
        run_script.chmod(0o755)
    
    def _create_standalone_scripts(self, standalone_dir: Path):
        """Create standalone deployment scripts."""
        # Setup script
        setup_script = standalone_dir / "setup.py"
        setup_script_content = """#!/usr/bin/env python3
\"\"\"
OpenClass Nexus AI Setup Script
Automated setup for standalone deployment
\"\"\"

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    \"\"\"Check if Python version is compatible.\"\"\"
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def create_virtual_environment():
    \"\"\"Create virtual environment.\"\"\"
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "openclass-env"], check=True)
    print("✓ Virtual environment created")

def install_dependencies():
    \"\"\"Install Python dependencies.\"\"\"
    print("Installing dependencies...")
    
    # Determine pip path based on OS
    if platform.system() == "Windows":
        pip_path = "openclass-env/Scripts/pip"
    else:
        pip_path = "openclass-env/bin/pip"
    
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    print("✓ Dependencies installed")

def setup_configuration():
    \"\"\"Setup initial configuration.\"\"\"
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
    \"\"\"Create necessary directories.\"\"\"
    print("Creating directories...")
    
    directories = ["data/vector_db", "data/processed", "models/cache", "logs"]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directories created")

def main():
    \"\"\"Main setup function.\"\"\"
    print("OpenClass Nexus AI Setup")
    print("=" * 30)
    
    try:
        check_python_version()
        create_virtual_environment()
        install_dependencies()
        setup_configuration()
        create_directories()
        
        print("\\n✓ Setup completed successfully!")
        print("\\nNext steps:")
        if platform.system() == "Windows":
            print("1. Activate environment: openclass-env\\\\Scripts\\\\activate")
        else:
            print("1. Activate environment: source openclass-env/bin/activate")
        print("2. Configure AWS (if needed): python scripts/setup_phase2_aws.py")
        print("3. Run application: python -m src.local_inference.complete_pipeline")
        
    except Exception as e:
        print(f"\\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
        setup_script.write_text(setup_script_content, encoding='utf-8')
        setup_script.chmod(0o755)
    
    def _create_pinned_requirements(self, standalone_dir: Path):
        """Create requirements.txt with pinned versions for reproducible builds."""
        # Read current requirements
        current_req_file = self.project_root / "requirements.txt"
        if current_req_file.exists():
            shutil.copy2(current_req_file, standalone_dir / "requirements.txt")
        
        # Create additional requirements for production
        prod_requirements = standalone_dir / "requirements-prod.txt"
        prod_req_content = """# Production-specific requirements
gunicorn==21.2.0
uvicorn[standard]==0.24.0
fastapi==0.104.1
prometheus-client==0.19.0
psutil==5.9.6
"""
        prod_requirements.write_text(prod_req_content, encoding='utf-8')
    
    def _create_cloud_configs(self, cloud_dir: Path):
        """Create cloud-specific configuration files."""
        # AWS configuration
        aws_config = {
            "provider": "aws",
            "region": "us-east-1",
            "instance_type": "t3.medium",
            "storage": {
                "type": "gp3",
                "size_gb": 20
            },
            "security_groups": ["openclass-sg"],
            "key_pair": "openclass-key",
            "environment_variables": {
                "OPENCLASS_ENV": "aws",
                "AWS_DEFAULT_REGION": "us-east-1"
            }
        }
        
        aws_config_file = cloud_dir / "aws-config.yaml"
        aws_config_file.write_text(json.dumps(aws_config, indent=2), encoding='utf-8')
        
        # GCP configuration
        gcp_config = {
            "provider": "gcp",
            "project_id": "openclass-nexus-ai",
            "zone": "us-central1-a",
            "machine_type": "e2-standard-2",
            "disk": {
                "type": "pd-standard",
                "size_gb": 20
            },
            "network": "default",
            "environment_variables": {
                "OPENCLASS_ENV": "gcp",
                "GOOGLE_CLOUD_PROJECT": "openclass-nexus-ai"
            }
        }
        
        gcp_config_file = cloud_dir / "gcp-config.yaml"
        gcp_config_file.write_text(json.dumps(gcp_config, indent=2), encoding='utf-8')
        
        # Azure configuration
        azure_config = {
            "provider": "azure",
            "resource_group": "openclass-rg",
            "location": "East US",
            "vm_size": "Standard_B2s",
            "storage_account": "openclassstorage",
            "network_security_group": "openclass-nsg",
            "environment_variables": {
                "OPENCLASS_ENV": "azure",
                "AZURE_LOCATION": "eastus"
            }
        }
        
        azure_config_file = cloud_dir / "azure-config.yaml"
        azure_config_file.write_text(json.dumps(azure_config, indent=2), encoding='utf-8')
    
    def _create_cloud_scripts(self, cloud_dir: Path):
        """Create cloud deployment scripts."""
        # AWS deployment script
        aws_script = cloud_dir / "deploy-aws.sh"
        aws_script_content = """#!/bin/bash
# AWS deployment script for OpenClass Nexus AI

echo "Deploying OpenClass Nexus AI to AWS..."

# Check AWS CLI
aws --version || { echo "AWS CLI required"; exit 1; }

# Create EC2 instance
aws ec2 run-instances \\
    --image-id ami-0c02fb55956c7d316 \\
    --instance-type t3.medium \\
    --key-name openclass-key \\
    --security-group-ids sg-xxxxxxxxx \\
    --user-data file://user-data.sh \\
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=OpenClass-Nexus-AI}]'

echo "AWS deployment initiated!"
"""
        aws_script.write_text(aws_script_content, encoding='utf-8')
        aws_script.chmod(0o755)
    
    def _create_compressed_archives(self, packages: Dict[str, DeploymentPackage]):
        """Create compressed archives of deployment packages."""
        logger.info("Creating compressed archives")
        
        archives_dir = self.output_dir / "archives"
        archives_dir.mkdir(exist_ok=True)
        
        for package_name, package in packages.items():
            package_path = Path(package.package_path)
            
            # Create tar.gz archive
            tar_file = archives_dir / f"{package_name}_package.tar.gz"
            with tarfile.open(tar_file, "w:gz") as tar:
                tar.add(package_path, arcname=package_name)
            
            # Create zip archive
            zip_file = archives_dir / f"{package_name}_package.zip"
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in package_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(package_path.parent)
                        zipf.write(file_path, arcname)
            
            logger.info(f"Created archives for {package_name} package")
    
    def _calculate_directory_size(self, directory: Path) -> float:
        """Calculate total size of directory in MB."""
        total_size = 0
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)  # Convert to MB
    
    def _generate_package_checksum(self, package_dir: Path) -> str:
        """Generate SHA256 checksum for the package."""
        import hashlib
        
        hash_sha256 = hashlib.sha256()
        
        for file_path in sorted(package_dir.rglob('*')):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def generate_deployment_summary(self, packages: Dict[str, DeploymentPackage]) -> str:
        """Generate deployment summary documentation."""
        summary = f"""# Deployment Packages Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Packages:** {len(packages)}

## Package Overview

"""
        
        for package_name, package in packages.items():
            summary += f"""### {package_name.title()} Package
- **Path:** `{package.package_path}`
- **Size:** {package.package_size_mb:.2f} MB
- **Checksum:** `{package.checksum[:16]}...`
- **Dependencies Included:** {'✅' if package.dependencies_included else '❌'}
- **Configuration Templates:** {len(package.configuration_templates)}
- **Installation Scripts:** {len(package.installation_scripts)}

"""
        
        summary += """## Deployment Instructions

### Docker Package
1. Extract the docker package
2. Run `./docker-build.sh` to build the image
3. Run `./docker-run.sh` to start the application
4. Access at http://localhost:8000

### Standalone Package
1. Extract the standalone package
2. Run `python setup.py` for automated setup
3. Or manually run `./install.sh` (Linux/Mac) or `install.bat` (Windows)
4. Activate virtual environment and run the application

### Cloud Package
1. Extract the cloud package
2. Configure cloud provider credentials
3. Run the appropriate deployment script (deploy-aws.sh, deploy-gcp.sh, etc.)
4. Follow cloud-specific setup instructions

## System Requirements
- Python 3.8+
- 4GB RAM minimum
- 10GB storage space
- Internet connection for initial setup

## Support
For deployment issues, refer to the troubleshooting guide in the documentation package.

---
*Generated by OpenClass Nexus AI Optimization System*
"""
        
        return summary