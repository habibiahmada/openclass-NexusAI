"""
Delta Update System for Phase 3 Model Optimization.

This module provides functionality for:
- Creating incremental update packages
- Applying delta updates to existing models
- Bandwidth optimization for model updates
- Version tracking and rollback capabilities

Requirements: 7.5
"""

import os
import json
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

try:
    import bsdiff4
    BSDIFF_AVAILABLE = True
except ImportError:
    BSDIFF_AVAILABLE = False

try:
    from .model_packager import ModelPackageMetadata, ChecksumCalculator
except ImportError:
    # Fallback for direct imports
    try:
        from src.local_inference.model_packager import ModelPackageMetadata, ChecksumCalculator
    except ImportError:
        # Mock for testing
        from dataclasses import dataclass
        from typing import List
        
        @dataclass
        class ModelPackageMetadata:
            pass
        
        class ChecksumCalculator:
            @staticmethod
            def calculate_sha256(file_path):
                import hashlib
                sha256_hash = hashlib.sha256()
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)
                return sha256_hash.hexdigest()


@dataclass
class DeltaUpdateMetadata:
    """Metadata for delta update packages."""
    
    # Update identification
    update_id: str
    from_version: str
    to_version: str
    
    # Model information
    model_id: str
    package_name: str
    
    # Delta information
    delta_type: str = "binary"  # "binary" or "file-based"
    compression_ratio: float = 0.0
    original_size_bytes: int = 0
    delta_size_bytes: int = 0
    
    # Checksums
    from_checksum: str = ""
    to_checksum: str = ""
    delta_checksum: str = ""
    
    # Metadata
    created_at: str = ""
    created_by: str = "OpenClass Nexus AI"
    description: str = ""
    
    # Bandwidth optimization info
    bandwidth_savings_percent: float = 0.0
    estimated_download_time_seconds: Dict[str, float] = None
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"
        
        if self.estimated_download_time_seconds is None:
            # Estimate download times for different connection speeds (in Mbps)
            connection_speeds = {
                "dial-up": 0.056,      # 56k modem
                "dsl": 1.0,            # 1 Mbps DSL
                "broadband": 10.0,     # 10 Mbps broadband
                "fiber": 100.0         # 100 Mbps fiber
            }
            
            self.estimated_download_time_seconds = {}
            if self.delta_size_bytes > 0:
                for speed_name, speed_mbps in connection_speeds.items():
                    # Convert bytes to megabits and calculate time
                    size_megabits = (self.delta_size_bytes * 8) / (1024 * 1024)
                    time_seconds = size_megabits / speed_mbps
                    self.estimated_download_time_seconds[speed_name] = time_seconds
        
        # Calculate compression ratio and bandwidth savings
        if self.original_size_bytes > 0 and self.delta_size_bytes > 0:
            self.compression_ratio = self.delta_size_bytes / self.original_size_bytes
            self.bandwidth_savings_percent = (1 - self.compression_ratio) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeltaUpdateMetadata':
        """Create from dictionary."""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate metadata and return list of errors."""
        errors = []
        
        if not self.update_id:
            errors.append("update_id is required")
        
        if not self.from_version:
            errors.append("from_version is required")
        
        if not self.to_version:
            errors.append("to_version is required")
        
        if not self.model_id:
            errors.append("model_id is required")
        
        if not self.package_name:
            errors.append("package_name is required")
        
        if self.delta_size_bytes <= 0:
            errors.append("delta_size_bytes must be positive")
        
        if not self.delta_checksum:
            errors.append("delta_checksum is required")
        
        return errors


class BinaryDiffer:
    """Binary diff utility for creating and applying patches."""
    
    @staticmethod
    def create_patch(old_file: Path, new_file: Path, patch_file: Path) -> bool:
        """Create a binary patch between two files."""
        if not BSDIFF_AVAILABLE:
            logging.warning("bsdiff4 not available, falling back to file replacement")
            return False
        
        try:
            with open(old_file, 'rb') as old_f, open(new_file, 'rb') as new_f:
                old_data = old_f.read()
                new_data = new_f.read()
            
            # Create binary diff
            patch_data = bsdiff4.diff(old_data, new_data)
            
            with open(patch_file, 'wb') as patch_f:
                patch_f.write(patch_data)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to create binary patch: {e}")
            return False
    
    @staticmethod
    def apply_patch(old_file: Path, patch_file: Path, new_file: Path) -> bool:
        """Apply a binary patch to create a new file."""
        if not BSDIFF_AVAILABLE:
            logging.error("bsdiff4 not available, cannot apply binary patch")
            return False
        
        try:
            with open(old_file, 'rb') as old_f, open(patch_file, 'rb') as patch_f:
                old_data = old_f.read()
                patch_data = patch_f.read()
            
            # Apply binary patch
            new_data = bsdiff4.patch(old_data, patch_data)
            
            with open(new_file, 'wb') as new_f:
                new_f.write(new_data)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to apply binary patch: {e}")
            return False


class DeltaUpdater:
    """Main class for creating and applying delta updates."""
    
    def __init__(self, 
                 cache_dir: str = "./models",
                 updates_dir: str = "./updates"):
        """Initialize delta updater.
        
        Args:
            cache_dir: Directory containing model files
            updates_dir: Directory to store delta updates
        """
        self.cache_dir = Path(cache_dir)
        self.updates_dir = Path(updates_dir)
        
        # Create directories if they don't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.updates_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
    
    def create_delta_update(self,
                           old_model_path: Path,
                           new_model_path: Path,
                           from_version: str,
                           to_version: str,
                           model_id: str,
                           package_name: str) -> Path:
        """Create a delta update package.
        
        Args:
            old_model_path: Path to the old model file
            new_model_path: Path to the new model file
            from_version: Version of the old model
            to_version: Version of the new model
            model_id: Model identifier
            package_name: Package name
            
        Returns:
            Path to created delta update package
        """
        if not old_model_path.exists():
            raise FileNotFoundError(f"Old model file not found: {old_model_path}")
        
        if not new_model_path.exists():
            raise FileNotFoundError(f"New model file not found: {new_model_path}")
        
        # Generate update ID
        update_id = f"{package_name}-{from_version}-to-{to_version}"
        
        # Calculate checksums
        self.logger.info("Calculating checksums...")
        from_checksum = ChecksumCalculator.calculate_sha256(old_model_path)
        to_checksum = ChecksumCalculator.calculate_sha256(new_model_path)
        
        # Get file sizes
        old_size = old_model_path.stat().st_size
        new_size = new_model_path.stat().st_size
        
        # Create temporary directory for delta creation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Try to create binary patch first
            patch_file = temp_path / "model.patch"
            binary_patch_success = BinaryDiffer.create_patch(
                old_model_path, new_model_path, patch_file
            )
            
            if binary_patch_success and patch_file.exists():
                delta_type = "binary"
                delta_file = patch_file
                self.logger.info("Created binary delta patch")
            else:
                # Fallback to full file replacement
                delta_type = "file-based"
                delta_file = temp_path / "model_full.gguf"
                shutil.copy2(new_model_path, delta_file)
                self.logger.info("Using full file replacement (binary diff not available)")
            
            # Calculate delta checksum and size
            delta_checksum = ChecksumCalculator.calculate_sha256(delta_file)
            delta_size = delta_file.stat().st_size
            
            # Create metadata
            metadata = DeltaUpdateMetadata(
                update_id=update_id,
                from_version=from_version,
                to_version=to_version,
                model_id=model_id,
                package_name=package_name,
                delta_type=delta_type,
                original_size_bytes=new_size,
                delta_size_bytes=delta_size,
                from_checksum=from_checksum,
                to_checksum=to_checksum,
                delta_checksum=delta_checksum,
                description=f"Delta update from {from_version} to {to_version}"
            )
            
            # Validate metadata
            errors = metadata.validate()
            if errors:
                raise ValueError(f"Invalid delta metadata: {', '.join(errors)}")
            
            # Create update package directory
            update_dir = self.updates_dir / update_id
            update_dir.mkdir(exist_ok=True)
            
            # Copy delta file
            final_delta_file = update_dir / f"delta.{delta_type}"
            shutil.copy2(delta_file, final_delta_file)
            
            # Create metadata file
            metadata_file = update_dir / "delta_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Create update info file
            self._create_update_info(update_dir, metadata)
            
            self.logger.info(f"Delta update created: {update_dir}")
            self.logger.info(f"Size reduction: {metadata.bandwidth_savings_percent:.1f}%")
            
            return update_dir
    
    def apply_delta_update(self,
                          current_model_path: Path,
                          delta_update_dir: Path,
                          output_path: Optional[Path] = None) -> Path:
        """Apply a delta update to a model file.
        
        Args:
            current_model_path: Path to the current model file
            delta_update_dir: Directory containing the delta update
            output_path: Output path for updated model (optional)
            
        Returns:
            Path to the updated model file
        """
        if not current_model_path.exists():
            raise FileNotFoundError(f"Current model file not found: {current_model_path}")
        
        if not delta_update_dir.exists():
            raise FileNotFoundError(f"Delta update directory not found: {delta_update_dir}")
        
        # Load metadata
        metadata_file = delta_update_dir / "delta_metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"Delta metadata not found: {metadata_file}")
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata_dict = json.load(f)
        
        metadata = DeltaUpdateMetadata.from_dict(metadata_dict)
        
        # Verify current model checksum
        current_checksum = ChecksumCalculator.calculate_sha256(current_model_path)
        if current_checksum != metadata.from_checksum:
            raise ValueError(
                f"Current model checksum mismatch. "
                f"Expected: {metadata.from_checksum}, "
                f"Got: {current_checksum}"
            )
        
        # Determine output path
        if output_path is None:
            output_path = current_model_path.parent / f"{current_model_path.stem}_updated{current_model_path.suffix}"
        
        # Find delta file
        delta_file = None
        for ext in ["binary", "file-based"]:
            candidate = delta_update_dir / f"delta.{ext}"
            if candidate.exists():
                delta_file = candidate
                break
        
        if delta_file is None:
            raise FileNotFoundError("No delta file found in update directory")
        
        # Apply update based on type
        if metadata.delta_type == "binary":
            self.logger.info("Applying binary delta patch...")
            success = BinaryDiffer.apply_patch(current_model_path, delta_file, output_path)
            if not success:
                raise RuntimeError("Failed to apply binary delta patch")
        
        elif metadata.delta_type == "file-based":
            self.logger.info("Applying file-based update...")
            shutil.copy2(delta_file, output_path)
        
        else:
            raise ValueError(f"Unknown delta type: {metadata.delta_type}")
        
        # Verify updated model checksum
        updated_checksum = ChecksumCalculator.calculate_sha256(output_path)
        if updated_checksum != metadata.to_checksum:
            # Clean up failed update
            if output_path.exists():
                output_path.unlink()
            raise ValueError(
                f"Updated model checksum mismatch. "
                f"Expected: {metadata.to_checksum}, "
                f"Got: {updated_checksum}"
            )
        
        self.logger.info(f"Delta update applied successfully: {output_path}")
        return output_path
    
    def _create_update_info(self, update_dir: Path, metadata: DeltaUpdateMetadata):
        """Create human-readable update information file."""
        info_content = f"""# Delta Update: {metadata.update_id}

## Update Information
- **From Version**: {metadata.from_version}
- **To Version**: {metadata.to_version}
- **Model ID**: {metadata.model_id}
- **Package**: {metadata.package_name}

## Delta Information
- **Type**: {metadata.delta_type}
- **Original Size**: {metadata.original_size_bytes / (1024**2):.2f} MB
- **Delta Size**: {metadata.delta_size_bytes / (1024**2):.2f} MB
- **Compression Ratio**: {metadata.compression_ratio:.3f}
- **Bandwidth Savings**: {metadata.bandwidth_savings_percent:.1f}%

## Estimated Download Times
"""
        
        for speed_name, time_seconds in metadata.estimated_download_time_seconds.items():
            if time_seconds < 60:
                time_str = f"{time_seconds:.1f} seconds"
            elif time_seconds < 3600:
                time_str = f"{time_seconds/60:.1f} minutes"
            else:
                time_str = f"{time_seconds/3600:.1f} hours"
            
            info_content += f"- **{speed_name.title()}**: {time_str}\n"
        
        info_content += f"""
## Checksums
- **From Model**: {metadata.from_checksum}
- **To Model**: {metadata.to_checksum}
- **Delta**: {metadata.delta_checksum}

## Created
- **Date**: {metadata.created_at}
- **By**: {metadata.created_by}

{metadata.description}
"""
        
        info_file = update_dir / "UPDATE_INFO.md"
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(info_content)
    
    def list_available_updates(self) -> List[Dict[str, Any]]:
        """List all available delta updates."""
        updates = []
        
        for update_dir in self.updates_dir.iterdir():
            if update_dir.is_dir():
                metadata_file = update_dir / "delta_metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata_dict = json.load(f)
                        
                        metadata = DeltaUpdateMetadata.from_dict(metadata_dict)
                        
                        update_info = {
                            "update_id": metadata.update_id,
                            "from_version": metadata.from_version,
                            "to_version": metadata.to_version,
                            "model_id": metadata.model_id,
                            "package_name": metadata.package_name,
                            "delta_size_mb": metadata.delta_size_bytes / (1024**2),
                            "bandwidth_savings_percent": metadata.bandwidth_savings_percent,
                            "created_at": metadata.created_at,
                            "path": str(update_dir)
                        }
                        
                        updates.append(update_info)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to load update metadata from {update_dir}: {e}")
        
        return sorted(updates, key=lambda x: x['created_at'], reverse=True)
    
    def verify_update(self, delta_update_dir: Path) -> Dict[str, Any]:
        """Verify a delta update package."""
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "metadata": None
        }
        
        if not delta_update_dir.exists():
            result["errors"].append(f"Update directory not found: {delta_update_dir}")
            return result
        
        try:
            # Load and validate metadata
            metadata_file = delta_update_dir / "delta_metadata.json"
            if not metadata_file.exists():
                result["errors"].append("Delta metadata file not found")
                return result
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            
            metadata = DeltaUpdateMetadata.from_dict(metadata_dict)
            result["metadata"] = metadata.to_dict()
            
            # Validate metadata
            metadata_errors = metadata.validate()
            if metadata_errors:
                result["errors"].extend(metadata_errors)
            
            # Check for delta file
            delta_file = None
            for ext in ["binary", "file-based"]:
                candidate = delta_update_dir / f"delta.{ext}"
                if candidate.exists():
                    delta_file = candidate
                    break
            
            if delta_file is None:
                result["errors"].append("No delta file found")
            else:
                # Verify delta file checksum
                actual_checksum = ChecksumCalculator.calculate_sha256(delta_file)
                if actual_checksum != metadata.delta_checksum:
                    result["errors"].append(
                        f"Delta file checksum mismatch. "
                        f"Expected: {metadata.delta_checksum}, "
                        f"Got: {actual_checksum}"
                    )
            
            # Check for info file
            info_file = delta_update_dir / "UPDATE_INFO.md"
            if not info_file.exists():
                result["warnings"].append("UPDATE_INFO.md file missing")
            
            result["valid"] = len(result["errors"]) == 0
            
        except Exception as e:
            result["errors"].append(f"Update verification failed: {str(e)}")
        
        return result
    
    def cleanup_old_updates(self, keep_latest: int = 5):
        """Clean up old delta updates, keeping only the latest ones."""
        updates = self.list_available_updates()
        
        if len(updates) <= keep_latest:
            return
        
        # Group by package name
        by_package = {}
        for update in updates:
            package = update["package_name"]
            if package not in by_package:
                by_package[package] = []
            by_package[package].append(update)
        
        # Clean up old updates for each package
        for package_name, package_updates in by_package.items():
            if len(package_updates) > keep_latest:
                # Sort by creation date and keep only the latest
                package_updates.sort(key=lambda x: x['created_at'], reverse=True)
                to_remove = package_updates[keep_latest:]
                
                for update in to_remove:
                    update_path = Path(update["path"])
                    if update_path.exists():
                        shutil.rmtree(update_path)
                        self.logger.info(f"Removed old update: {update['update_id']}")


# Convenience functions
def create_delta_update(old_model_path: str,
                       new_model_path: str,
                       from_version: str,
                       to_version: str,
                       model_id: str,
                       package_name: str,
                       updates_dir: str = "./updates") -> Path:
    """Convenience function to create a delta update."""
    
    updater = DeltaUpdater(updates_dir=updates_dir)
    return updater.create_delta_update(
        Path(old_model_path),
        Path(new_model_path),
        from_version,
        to_version,
        model_id,
        package_name
    )


def apply_delta_update(current_model_path: str,
                      delta_update_dir: str,
                      output_path: Optional[str] = None) -> Path:
    """Convenience function to apply a delta update."""
    
    updater = DeltaUpdater()
    return updater.apply_delta_update(
        Path(current_model_path),
        Path(delta_update_dir),
        Path(output_path) if output_path else None
    )