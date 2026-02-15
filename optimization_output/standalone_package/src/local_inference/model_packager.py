"""
Model Packaging and Distribution System for Phase 3 Model Optimization.

This module provides functionality for:
- Creating compressed archives with metadata
- S3 upload functionality for model distribution
- Semantic versioning for model updates
- Integrity verification with checksums

Requirements: 7.1, 7.2, 7.3
"""

import os
import json
import hashlib
import tarfile
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import re

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from .model_config import ModelConfig
except ImportError:
    # Fallback for direct imports
    try:
        from src.local_inference.model_config import ModelConfig
    except ImportError:
        # Mock for testing
        class ModelConfig:
            pass


@dataclass
class ModelPackageMetadata:
    """Metadata for model packages."""
    
    # Package identification
    package_name: str
    version: str
    model_id: str
    
    # Model information
    model_type: str = "llama"
    quantization: str = "Q4_K_M"
    file_size_bytes: int = 0
    
    # Checksums and integrity
    sha256_checksum: str = ""
    md5_checksum: str = ""
    
    # Package information
    created_at: str = ""
    created_by: str = "OpenClass Nexus AI"
    description: str = ""
    
    # Educational metadata
    supports_indonesian: bool = True
    educational_optimized: bool = True
    curriculum_subjects: List[str] = None
    
    # Technical specifications
    context_window: int = 4096
    memory_requirements_mb: int = 3072
    cpu_threads_recommended: int = 4
    
    # Distribution information
    download_url: str = ""
    s3_bucket: str = ""
    s3_key: str = ""
    cloudfront_url: str = ""
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if self.curriculum_subjects is None:
            self.curriculum_subjects = [
                "Informatika", "Matematika", "Fisika", "Kimia",
                "Biologi", "Bahasa Indonesia", "Bahasa Inggris"
            ]
        
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelPackageMetadata':
        """Create from dictionary."""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate metadata and return list of errors."""
        errors = []
        
        if not self.package_name:
            errors.append("package_name is required")
        
        if not self.version:
            errors.append("version is required")
        
        if not self.model_id:
            errors.append("model_id is required")
        
        # Validate semantic version format
        if not re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$', self.version):
            errors.append("version must follow semantic versioning (e.g., 1.0.0)")
        
        if self.file_size_bytes <= 0:
            errors.append("file_size_bytes must be positive")
        
        if not self.sha256_checksum:
            errors.append("sha256_checksum is required")
        
        return errors


class ChecksumCalculator:
    """Utility for calculating file checksums."""
    
    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    @staticmethod
    def calculate_md5(file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        md5_hash = hashlib.md5()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        
        return md5_hash.hexdigest()
    
    @staticmethod
    def verify_checksum(file_path: Path, expected_sha256: str) -> bool:
        """Verify file checksum against expected value."""
        actual_checksum = ChecksumCalculator.calculate_sha256(file_path)
        return actual_checksum.lower() == expected_sha256.lower()


class SemanticVersionManager:
    """Semantic version management utilities."""
    
    @staticmethod
    def parse_version(version: str) -> Dict[str, Union[int, str]]:
        """Parse semantic version string."""
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(-([a-zA-Z0-9]+))?$', version)
        if not match:
            raise ValueError(f"Invalid semantic version: {version}")
        
        major, minor, patch, _, prerelease = match.groups()
        
        return {
            'major': int(major),
            'minor': int(minor),
            'patch': int(patch),
            'prerelease': prerelease or None
        }
    
    @staticmethod
    def compare_versions(version1: str, version2: str) -> int:
        """Compare two semantic versions. Returns -1, 0, or 1."""
        v1 = SemanticVersionManager.parse_version(version1)
        v2 = SemanticVersionManager.parse_version(version2)
        
        # Compare major.minor.patch
        for component in ['major', 'minor', 'patch']:
            if v1[component] < v2[component]:
                return -1
            elif v1[component] > v2[component]:
                return 1
        
        # Handle prerelease versions
        if v1['prerelease'] is None and v2['prerelease'] is None:
            return 0
        elif v1['prerelease'] is None:
            return 1  # Release > prerelease
        elif v2['prerelease'] is None:
            return -1  # Prerelease < release
        else:
            # Both are prerelease, compare alphabetically
            if v1['prerelease'] < v2['prerelease']:
                return -1
            elif v1['prerelease'] > v2['prerelease']:
                return 1
            else:
                return 0
    
    @staticmethod
    def increment_version(version: str, component: str = 'patch') -> str:
        """Increment version component (major, minor, or patch)."""
        parsed = SemanticVersionManager.parse_version(version)
        
        if component == 'major':
            parsed['major'] += 1
            parsed['minor'] = 0
            parsed['patch'] = 0
        elif component == 'minor':
            parsed['minor'] += 1
            parsed['patch'] = 0
        elif component == 'patch':
            parsed['patch'] += 1
        else:
            raise ValueError(f"Invalid component: {component}")
        
        # Remove prerelease for incremented versions
        new_version = f"{parsed['major']}.{parsed['minor']}.{parsed['patch']}"
        return new_version


class ModelPackager:
    """Main class for packaging and distributing AI models."""
    
    def __init__(self, 
                 output_dir: str = "./packages",
                 s3_bucket: Optional[str] = None,
                 aws_region: str = "us-east-1"):
        """Initialize model packager.
        
        Args:
            output_dir: Directory to store created packages
            s3_bucket: S3 bucket name for distribution
            aws_region: AWS region for S3 operations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.s3_bucket = s3_bucket
        self.aws_region = aws_region
        
        # Initialize S3 client if available
        self.s3_client = None
        if BOTO3_AVAILABLE and s3_bucket:
            try:
                self.s3_client = boto3.client('s3', region_name=aws_region)
            except NoCredentialsError:
                logging.warning("AWS credentials not found. S3 upload will be disabled.")
        
        self.logger = logging.getLogger(__name__)
    
    def create_package(self,
                      model_path: Path,
                      metadata: ModelPackageMetadata,
                      compression: str = "tar.gz",
                      include_config: bool = True) -> Path:
        """Create a compressed package with model and metadata.
        
        Args:
            model_path: Path to the model file
            metadata: Package metadata
            compression: Compression format ('tar.gz', 'zip')
            include_config: Whether to include default config files
            
        Returns:
            Path to created package file
        """
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Calculate checksums and file size first
        self.logger.info(f"Calculating checksums for {model_path}")
        metadata.sha256_checksum = ChecksumCalculator.calculate_sha256(model_path)
        metadata.md5_checksum = ChecksumCalculator.calculate_md5(model_path)
        metadata.file_size_bytes = model_path.stat().st_size
        
        # Validate metadata after calculating checksums
        errors = metadata.validate()
        if errors:
            raise ValueError(f"Invalid metadata: {', '.join(errors)}")
        
        # Create package filename
        package_name = f"{metadata.package_name}-{metadata.version}"
        if compression == "tar.gz":
            package_file = self.output_dir / f"{package_name}.tar.gz"
        elif compression == "zip":
            package_file = self.output_dir / f"{package_name}.zip"
        else:
            raise ValueError(f"Unsupported compression format: {compression}")
        
        # Create temporary directory for package contents
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / package_name
            package_dir.mkdir()
            
            # Copy model file
            model_dest = package_dir / model_path.name
            shutil.copy2(model_path, model_dest)
            
            # Create metadata file
            metadata_file = package_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Include default configuration if requested
            if include_config:
                self._add_default_config(package_dir, metadata)
            
            # Create README
            self._create_readme(package_dir, metadata)
            
            # Create compressed archive
            self.logger.info(f"Creating package: {package_file}")
            if compression == "tar.gz":
                with tarfile.open(package_file, "w:gz") as tar:
                    tar.add(package_dir, arcname=package_name)
            elif compression == "zip":
                with zipfile.ZipFile(package_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file_path in package_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = package_name / file_path.relative_to(package_dir)
                            zip_file.write(file_path, arcname)
        
        self.logger.info(f"Package created successfully: {package_file}")
        return package_file
    
    def _add_default_config(self, package_dir: Path, metadata: ModelPackageMetadata):
        """Add default configuration files to package."""
        config_dir = package_dir / "config"
        config_dir.mkdir()
        
        # Create inference configuration
        inference_config = {
            "model": {
                "model_id": metadata.model_id,
                "model_type": metadata.model_type,
                "quantization": metadata.quantization,
                "context_window": metadata.context_window
            },
            "inference": {
                "n_ctx": metadata.context_window,
                "n_threads": metadata.cpu_threads_recommended,
                "memory_limit_mb": metadata.memory_requirements_mb,
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 512
            },
            "educational": {
                "supports_indonesian": metadata.supports_indonesian,
                "curriculum_subjects": metadata.curriculum_subjects,
                "educational_optimized": metadata.educational_optimized
            }
        }
        
        config_file = config_dir / "inference_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(inference_config, f, indent=2, ensure_ascii=False)
    
    def _create_readme(self, package_dir: Path, metadata: ModelPackageMetadata):
        """Create README file for the package."""
        readme_content = f"""# {metadata.package_name} v{metadata.version}

## Model Information
- **Model ID**: {metadata.model_id}
- **Model Type**: {metadata.model_type}
- **Quantization**: {metadata.quantization}
- **File Size**: {metadata.file_size_bytes / (1024**3):.2f} GB
- **Context Window**: {metadata.context_window} tokens

## Educational Features
- **Indonesian Language Support**: {'Yes' if metadata.supports_indonesian else 'No'}
- **Educational Optimization**: {'Yes' if metadata.educational_optimized else 'No'}
- **Supported Subjects**: {', '.join(metadata.curriculum_subjects)}

## System Requirements
- **Memory**: {metadata.memory_requirements_mb} MB RAM minimum
- **CPU Threads**: {metadata.cpu_threads_recommended} recommended
- **Storage**: {metadata.file_size_bytes / (1024**2):.0f} MB available space

## Installation
1. Extract the package to your models directory
2. Update your configuration to point to the model file
3. Ensure you have llama-cpp-python installed
4. Run inference with the provided configuration

## Verification
- **SHA256**: {metadata.sha256_checksum}
- **MD5**: {metadata.md5_checksum}

## Created
- **Date**: {metadata.created_at}
- **By**: {metadata.created_by}

{metadata.description}
"""
        
        readme_file = package_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def upload_to_s3(self, 
                     package_path: Path, 
                     s3_key: Optional[str] = None,
                     public_read: bool = True) -> Dict[str, str]:
        """Upload package to S3 bucket.
        
        Args:
            package_path: Path to package file
            s3_key: S3 object key (defaults to filename)
            public_read: Whether to make object publicly readable
            
        Returns:
            Dictionary with upload information
        """
        if not self.s3_client:
            raise RuntimeError("S3 client not available. Check AWS credentials and boto3 installation.")
        
        if not self.s3_bucket:
            raise ValueError("S3 bucket not configured")
        
        if not package_path.exists():
            raise FileNotFoundError(f"Package file not found: {package_path}")
        
        # Use filename as S3 key if not provided
        if s3_key is None:
            s3_key = f"models/{package_path.name}"
        
        try:
            # Upload file
            self.logger.info(f"Uploading {package_path} to s3://{self.s3_bucket}/{s3_key}")
            
            extra_args = {}
            if public_read:
                extra_args['ACL'] = 'public-read'
            
            self.s3_client.upload_file(
                str(package_path),
                self.s3_bucket,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Generate URLs
            s3_url = f"https://{self.s3_bucket}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            
            # Try to get CloudFront URL if available
            cloudfront_url = self._get_cloudfront_url(s3_key)
            
            upload_info = {
                "s3_bucket": self.s3_bucket,
                "s3_key": s3_key,
                "s3_url": s3_url,
                "cloudfront_url": cloudfront_url,
                "upload_time": datetime.utcnow().isoformat() + "Z"
            }
            
            self.logger.info(f"Upload completed successfully: {s3_url}")
            return upload_info
            
        except ClientError as e:
            self.logger.error(f"S3 upload failed: {e}")
            raise
    
    def _get_cloudfront_url(self, s3_key: str) -> str:
        """Try to construct CloudFront URL if distribution exists."""
        # This is a simplified implementation
        # In practice, you'd need to query CloudFront distributions
        # or have the CloudFront domain configured
        
        # For now, return empty string - can be enhanced later
        return ""
    
    def list_packages(self) -> List[Dict[str, Any]]:
        """List all packages in the output directory."""
        packages = []
        
        for package_file in self.output_dir.glob("*.tar.gz"):
            packages.append(self._get_package_info(package_file))
        
        for package_file in self.output_dir.glob("*.zip"):
            packages.append(self._get_package_info(package_file))
        
        return sorted(packages, key=lambda x: x['created_time'], reverse=True)
    
    def _get_package_info(self, package_path: Path) -> Dict[str, Any]:
        """Get basic information about a package file."""
        stat = package_path.stat()
        
        return {
            "filename": package_path.name,
            "path": str(package_path),
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    
    def extract_metadata(self, package_path: Path) -> Optional[ModelPackageMetadata]:
        """Extract metadata from an existing package."""
        if not package_path.exists():
            return None
        
        try:
            if package_path.suffix == '.gz':
                with tarfile.open(package_path, "r:gz") as tar:
                    # Find metadata.json in the archive
                    for member in tar.getmembers():
                        if member.name.endswith('metadata.json'):
                            f = tar.extractfile(member)
                            if f:
                                metadata_dict = json.load(f)
                                return ModelPackageMetadata.from_dict(metadata_dict)
            
            elif package_path.suffix == '.zip':
                with zipfile.ZipFile(package_path, 'r') as zip_file:
                    for filename in zip_file.namelist():
                        if filename.endswith('metadata.json'):
                            with zip_file.open(filename) as f:
                                metadata_dict = json.load(f)
                                return ModelPackageMetadata.from_dict(metadata_dict)
        
        except Exception as e:
            self.logger.error(f"Failed to extract metadata from {package_path}: {e}")
        
        return None
    
    def verify_package(self, package_path: Path) -> Dict[str, Any]:
        """Verify package integrity and contents."""
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "metadata": None,
            "files": []
        }
        
        if not package_path.exists():
            result["errors"].append(f"Package file not found: {package_path}")
            return result
        
        try:
            # Extract and validate metadata
            metadata = self.extract_metadata(package_path)
            if not metadata:
                result["errors"].append("Could not extract metadata from package")
                return result
            
            result["metadata"] = metadata.to_dict()
            
            # Validate metadata
            metadata_errors = metadata.validate()
            if metadata_errors:
                result["errors"].extend(metadata_errors)
            
            # List package contents
            if package_path.suffix == '.gz':
                with tarfile.open(package_path, "r:gz") as tar:
                    result["files"] = [member.name for member in tar.getmembers()]
            elif package_path.suffix == '.zip':
                with zipfile.ZipFile(package_path, 'r') as zip_file:
                    result["files"] = zip_file.namelist()
            
            # Check for required files
            required_files = ['metadata.json', 'README.md']
            for req_file in required_files:
                if not any(f.endswith(req_file) for f in result["files"]):
                    result["warnings"].append(f"Missing recommended file: {req_file}")
            
            # Check for model file
            model_files = [f for f in result["files"] if f.endswith('.gguf')]
            if not model_files:
                result["errors"].append("No GGUF model file found in package")
            elif len(model_files) > 1:
                result["warnings"].append(f"Multiple model files found: {model_files}")
            
            result["valid"] = len(result["errors"]) == 0
            
        except Exception as e:
            result["errors"].append(f"Package verification failed: {str(e)}")
        
        return result


# Convenience functions for common operations
def create_model_package(model_path: str,
                        package_name: str,
                        version: str,
                        model_id: str,
                        output_dir: str = "./packages",
                        **kwargs) -> Path:
    """Convenience function to create a model package."""
    
    metadata = ModelPackageMetadata(
        package_name=package_name,
        version=version,
        model_id=model_id,
        **kwargs
    )
    
    packager = ModelPackager(output_dir=output_dir)
    return packager.create_package(Path(model_path), metadata)


def upload_model_package(package_path: str,
                        s3_bucket: str,
                        aws_region: str = "us-east-1",
                        s3_key: Optional[str] = None) -> Dict[str, str]:
    """Convenience function to upload a model package to S3."""
    
    packager = ModelPackager(s3_bucket=s3_bucket, aws_region=aws_region)
    return packager.upload_to_s3(Path(package_path), s3_key)