"""
Project Cleanup Manager

This module provides comprehensive project cleanup capabilities including
artifact identification, safe file removal, and directory structure optimization.
"""

import os
import shutil
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .models import CleanupReport, StructureReport, ValidationReport
from .config import OptimizationConfig
from .logger import OptimizationLoggerMixin


@dataclass
class FileBackup:
    """Backup information for rollback capability."""
    original_path: Path
    backup_path: Path
    file_hash: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CleanupOperation:
    """Record of a cleanup operation for rollback."""
    operation_type: str  # 'delete', 'move', 'modify'
    target_path: Path
    backup_info: Optional[FileBackup] = None
    timestamp: datetime = field(default_factory=datetime.now)


class FileCleanupEngine(OptimizationLoggerMixin):
    """
    Engine for identifying and safely removing development artifacts.
    
    Provides safe file removal with validation to preserve essential files
    and rollback capability for failed cleanup operations.
    """
    
    def __init__(self, config: OptimizationConfig):
        super().__init__()
        self.config = config
        self.project_root = config.project_root
        self.backup_dir = config.optimization_output_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Track operations for rollback
        self.operations: List[CleanupOperation] = []
        self.rollback_enabled = True
        
        self.log_info("File cleanup engine initialized", 
                     project_root=str(self.project_root))
    
    def identify_artifacts(self) -> Dict[str, List[Path]]:
        """
        Identify development artifacts for cleanup.
        
        Returns:
            Dictionary mapping artifact types to file paths
        """
        self.log_operation_start("artifact identification")
        start_time = time.time()
        
        artifacts = {
            'temp_files': [],
            'cache_dirs': [],
            'test_artifacts': [],
            'build_artifacts': [],
            'log_files': []
        }
        
        try:
            # Walk through project directory
            for root, dirs, files in os.walk(self.project_root):
                root_path = Path(root)
                
                # Skip essential directories
                if self._is_essential_directory(root_path):
                    continue
                
                # Check directories for cache/temp patterns
                for dir_name in dirs[:]:  # Use slice to allow modification
                    dir_path = root_path / dir_name
                    
                    if self._is_cache_directory(dir_path):
                        artifacts['cache_dirs'].append(dir_path)
                        dirs.remove(dir_name)  # Don't recurse into cache dirs
                    elif self._is_test_artifact_directory(dir_path):
                        artifacts['test_artifacts'].append(dir_path)
                        dirs.remove(dir_name)  # Don't recurse into test artifacts
                
                # Check files for temp/artifact patterns
                for file_name in files:
                    file_path = root_path / file_name
                    
                    if self._is_temp_file(file_path):
                        artifacts['temp_files'].append(file_path)
                    elif self._is_build_artifact(file_path):
                        artifacts['build_artifacts'].append(file_path)
                    elif self._is_log_file(file_path):
                        artifacts['log_files'].append(file_path)
            
            duration = time.time() - start_time
            total_artifacts = sum(len(files) for files in artifacts.values())
            
            self.log_operation_complete("artifact identification", duration,
                                      total_artifacts=total_artifacts)
            
            return artifacts
            
        except Exception as e:
            self.log_operation_error("artifact identification", e)
            raise
    
    def validate_essential_files(self, file_paths: List[Path]) -> Tuple[List[Path], List[Path]]:
        """
        Validate which files are safe to remove vs essential to preserve.
        
        Args:
            file_paths: List of file paths to validate
        
        Returns:
            Tuple of (safe_to_remove, essential_files)
        """
        safe_to_remove = []
        essential_files = []
        
        for file_path in file_paths:
            if self._is_essential_file(file_path):
                essential_files.append(file_path)
                self.log_warning(f"Essential file protected from cleanup: {file_path}")
            else:
                safe_to_remove.append(file_path)
        
        return safe_to_remove, essential_files
    
    def create_backup(self, file_path: Path) -> Optional[FileBackup]:
        """
        Create backup of file for rollback capability.
        
        Args:
            file_path: Path to file to backup
        
        Returns:
            FileBackup object or None if backup failed
        """
        if not self.rollback_enabled or not file_path.exists():
            return None
        
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.name}_{timestamp}.backup"
            backup_path = self.backup_dir / backup_name
            
            # Calculate file hash for integrity
            file_hash = self._calculate_file_hash(file_path)
            
            # Copy file to backup location
            if file_path.is_file():
                shutil.copy2(file_path, backup_path)
            elif file_path.is_dir():
                shutil.copytree(file_path, backup_path)
            
            backup = FileBackup(
                original_path=file_path,
                backup_path=backup_path,
                file_hash=file_hash
            )
            
            self.log_debug(f"Created backup: {file_path} -> {backup_path}")
            return backup
            
        except Exception as e:
            self.log_error(f"Failed to create backup for {file_path}", e)
            return None
    
    def safe_remove_file(self, file_path: Path) -> bool:
        """
        Safely remove a file with backup and validation.
        
        Args:
            file_path: Path to file to remove
        
        Returns:
            True if removal successful, False otherwise
        """
        try:
            # Validate file is safe to remove
            if self._is_essential_file(file_path):
                self.log_warning(f"Refusing to remove essential file: {file_path}")
                return False
            
            # Create backup if enabled
            backup = self.create_backup(file_path)
            
            # Remove file or directory
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                self.log_warning(f"Path does not exist or is not file/directory: {file_path}")
                return False
            
            # Record operation for rollback
            operation = CleanupOperation(
                operation_type='delete',
                target_path=file_path,
                backup_info=backup
            )
            self.operations.append(operation)
            
            self.log_debug(f"Successfully removed: {file_path}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to remove {file_path}", e)
            return False
    
    def cleanup_artifacts(self, artifacts: Dict[str, List[Path]]) -> CleanupReport:
        """
        Clean up identified artifacts with comprehensive reporting.
        
        Args:
            artifacts: Dictionary of artifact types and paths
        
        Returns:
            CleanupReport with cleanup results
        """
        self.log_operation_start("artifact cleanup")
        start_time = time.time()
        
        files_removed = 0
        directories_cleaned = 0
        space_freed_mb = 0.0
        issues_encountered = []
        
        try:
            # Process each artifact type
            for artifact_type, paths in artifacts.items():
                self.log_info(f"Cleaning {artifact_type}: {len(paths)} items")
                
                # Validate files before removal
                safe_paths, essential_paths = self.validate_essential_files(paths)
                
                if essential_paths:
                    issues_encountered.append(
                        f"Skipped {len(essential_paths)} essential files in {artifact_type}"
                    )
                
                # Remove safe files
                for path in safe_paths:
                    try:
                        # Calculate size before removal
                        if path.exists():
                            size_mb = self._get_path_size_mb(path)
                            
                            if self.safe_remove_file(path):
                                if path.suffix or path.is_file():
                                    files_removed += 1
                                else:
                                    directories_cleaned += 1
                                space_freed_mb += size_mb
                            else:
                                issues_encountered.append(f"Failed to remove: {path}")
                    
                    except Exception as e:
                        issues_encountered.append(f"Error removing {path}: {str(e)}")
                        self.log_error(f"Error removing {path}", e)
            
            duration = time.time() - start_time
            
            # Generate recommendations
            recommendations = self._generate_cleanup_recommendations(
                files_removed, directories_cleaned, space_freed_mb, issues_encountered
            )
            
            report = CleanupReport(
                files_removed=files_removed,
                directories_cleaned=directories_cleaned,
                cache_cleared_mb=space_freed_mb,
                space_freed_mb=space_freed_mb,
                cleanup_duration_seconds=duration,
                issues_encountered=issues_encountered,
                recommendations=recommendations
            )
            
            self.log_operation_complete("artifact cleanup", duration,
                                      files_removed=files_removed,
                                      directories_cleaned=directories_cleaned,
                                      space_freed_mb=space_freed_mb)
            
            return report
            
        except Exception as e:
            self.log_operation_error("artifact cleanup", e)
            raise
    
    def rollback_operations(self) -> bool:
        """
        Rollback all cleanup operations using backups.
        
        Returns:
            True if rollback successful, False otherwise
        """
        if not self.rollback_enabled or not self.operations:
            self.log_warning("No operations to rollback or rollback disabled")
            return False
        
        self.log_operation_start("cleanup rollback")
        start_time = time.time()
        
        success_count = 0
        failure_count = 0
        
        try:
            # Rollback operations in reverse order
            for operation in reversed(self.operations):
                try:
                    if operation.operation_type == 'delete' and operation.backup_info:
                        backup = operation.backup_info
                        
                        # Restore from backup
                        if backup.backup_path.exists():
                            if backup.backup_path.is_file():
                                shutil.copy2(backup.backup_path, backup.original_path)
                            elif backup.backup_path.is_dir():
                                shutil.copytree(backup.backup_path, backup.original_path)
                            
                            # Verify restoration
                            if self._verify_file_integrity(backup.original_path, backup.file_hash):
                                success_count += 1
                                self.log_debug(f"Restored: {backup.original_path}")
                            else:
                                failure_count += 1
                                self.log_error(f"Integrity check failed for restored file: {backup.original_path}")
                        else:
                            failure_count += 1
                            self.log_error(f"Backup file not found: {backup.backup_path}")
                    else:
                        failure_count += 1
                        self.log_warning(f"Cannot rollback operation: {operation.operation_type} for {operation.target_path}")
                
                except Exception as e:
                    failure_count += 1
                    self.log_error(f"Failed to rollback operation for {operation.target_path}", e)
            
            duration = time.time() - start_time
            rollback_success = failure_count == 0
            
            self.log_operation_complete("cleanup rollback", duration,
                                      success_count=success_count,
                                      failure_count=failure_count,
                                      rollback_success=rollback_success)
            
            return rollback_success
            
        except Exception as e:
            self.log_operation_error("cleanup rollback", e)
            return False
    
    def _is_essential_file(self, file_path: Path) -> bool:
        """Check if file is essential and should be preserved."""
        # Convert to relative path for pattern matching
        try:
            rel_path = file_path.relative_to(self.project_root)
            rel_path_str = str(rel_path)
            
            # Check against preserve patterns
            for pattern in self.config.preserve_essential_files:
                if pattern.endswith('/'):
                    # Directory pattern
                    if rel_path_str.startswith(pattern) or any(
                        part == pattern.rstrip('/') for part in rel_path.parts
                    ):
                        return True
                else:
                    # File pattern
                    if rel_path.name == pattern or rel_path_str == pattern:
                        return True
            
            return False
            
        except ValueError:
            # File is outside project root
            return True
    
    def _is_essential_directory(self, dir_path: Path) -> bool:
        """Check if directory is essential and should be preserved."""
        return self._is_essential_file(dir_path)
    
    def _is_temp_file(self, file_path: Path) -> bool:
        """Check if file matches temporary file patterns."""
        for pattern in self.config.temp_file_patterns:
            if pattern.startswith('*.'):
                # Extension pattern
                if file_path.suffix == pattern[1:]:
                    return True
            elif pattern.endswith('/'):
                # Directory pattern (shouldn't match files)
                continue
            else:
                # Exact name pattern
                if file_path.name == pattern:
                    return True
        return False
    
    def _is_cache_directory(self, dir_path: Path) -> bool:
        """Check if directory is a cache directory."""
        cache_patterns = [p for p in self.config.temp_file_patterns if p.endswith('/')]
        dir_name = dir_path.name
        
        for pattern in cache_patterns:
            pattern_name = pattern.rstrip('/')
            if dir_name == pattern_name:
                return True
        
        return False
    
    def _is_test_artifact_directory(self, dir_path: Path) -> bool:
        """Check if directory contains test artifacts."""
        test_patterns = ['.pytest_cache', '.coverage', 'htmlcov', '.tox', '.nox']
        return dir_path.name in test_patterns
    
    def _is_build_artifact(self, file_path: Path) -> bool:
        """Check if file is a build artifact."""
        build_extensions = ['.egg-info', '.whl', '.tar.gz']
        return any(str(file_path).endswith(ext) for ext in build_extensions)
    
    def _is_log_file(self, file_path: Path) -> bool:
        """Check if file is a log file."""
        return file_path.suffix in ['.log', '.out', '.err']
    
    def _get_path_size_mb(self, path: Path) -> float:
        """Get size of file or directory in MB."""
        try:
            if path.is_file():
                return path.stat().st_size / (1024 * 1024)
            elif path.is_dir():
                total_size = 0
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = Path(root) / file
                        if file_path.exists():
                            total_size += file_path.stat().st_size
                return total_size / (1024 * 1024)
            return 0.0
        except (OSError, PermissionError):
            return 0.0
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for integrity checking."""
        if not file_path.is_file():
            return ""
        
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def _verify_file_integrity(self, file_path: Path, expected_hash: str) -> bool:
        """Verify file integrity using hash comparison."""
        if not expected_hash:
            return True  # Skip verification if no hash available
        
        actual_hash = self._calculate_file_hash(file_path)
        return actual_hash == expected_hash
    
    def _generate_cleanup_recommendations(
        self, 
        files_removed: int, 
        directories_cleaned: int, 
        space_freed_mb: float,
        issues: List[str]
    ) -> List[str]:
        """Generate recommendations based on cleanup results."""
        recommendations = []
        
        if files_removed == 0 and directories_cleaned == 0:
            recommendations.append("No artifacts found to clean - project is already optimized")
        elif space_freed_mb > 100:
            recommendations.append("Significant space freed - consider running cleanup regularly")
        elif space_freed_mb < 10:
            recommendations.append("Minimal space freed - project is well-maintained")
        
        if issues:
            recommendations.append(f"Review {len(issues)} issues encountered during cleanup")
        
        if len(self.operations) > 50:
            recommendations.append("Large number of operations - consider more frequent cleanup")
        
        return recommendations


class DirectoryStructureOptimizer(OptimizationLoggerMixin):
    """
    Optimizer for project directory structure.
    
    Creates production-ready directory reorganization with validation
    for logical component grouping.
    """
    
    def __init__(self, config: OptimizationConfig):
        super().__init__()
        self.config = config
        self.project_root = config.project_root
        
        # Define ideal production structure
        self.production_structure = {
            'src/': 'Source code and application logic',
            'config/': 'Configuration files and templates',
            'docs/': 'Documentation and guides',
            'scripts/': 'Utility and deployment scripts',
            'tests/': 'Test files and fixtures',
            'data/': 'Data files and datasets',
            'models/': 'AI models and related files'
        }
        
        self.log_info("Directory structure optimizer initialized")
    
    def analyze_current_structure(self) -> Dict[str, Any]:
        """
        Analyze current directory structure.
        
        Returns:
            Analysis results with structure information
        """
        self.log_operation_start("structure analysis")
        
        structure_info = {
            'directories': [],
            'files_by_directory': {},
            'structure_score': 0.0,
            'recommendations': []
        }
        
        try:
            # Scan top-level directories
            for item in self.project_root.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    structure_info['directories'].append(item.name)
                    
                    # Count files in directory
                    file_count = sum(1 for _ in item.rglob('*') if _.is_file())
                    structure_info['files_by_directory'][item.name] = file_count
            
            # Calculate structure score
            structure_info['structure_score'] = self._calculate_structure_score(
                structure_info['directories']
            )
            
            # Generate recommendations
            structure_info['recommendations'] = self._generate_structure_recommendations(
                structure_info['directories']
            )
            
            self.log_operation_complete("structure analysis",
                                      directories=len(structure_info['directories']),
                                      structure_score=structure_info['structure_score'])
            
            return structure_info
            
        except Exception as e:
            self.log_operation_error("structure analysis", e)
            raise
    
    def validate_structure(self) -> ValidationReport:
        """
        Validate current directory structure against production standards.
        
        Returns:
            ValidationReport with structure validation results
        """
        self.log_operation_start("structure validation")
        
        try:
            analysis = self.analyze_current_structure()
            
            issues_found = []
            recommendations = []
            components_validated = 0
            
            # Check for required directories
            required_dirs = ['src', 'config', 'docs']
            for req_dir in required_dirs:
                components_validated += 1
                if req_dir not in analysis['directories']:
                    issues_found.append(f"Missing required directory: {req_dir}")
                    recommendations.append(f"Create {req_dir}/ directory for proper organization")
            
            # Check for logical grouping
            components_validated += 1
            if 'tests' not in analysis['directories']:
                issues_found.append("Tests not properly organized in tests/ directory")
                recommendations.append("Move test files to tests/ directory")
            
            # Check for production readiness
            components_validated += 1
            if analysis['structure_score'] < 0.8:
                issues_found.append("Directory structure not optimized for production")
                recommendations.extend(analysis['recommendations'])
            
            validation_passed = len(issues_found) == 0
            overall_score = max(0.0, 1.0 - (len(issues_found) / components_validated))
            
            report = ValidationReport(
                components_validated=components_validated,
                validation_passed=validation_passed,
                issues_found=issues_found,
                recommendations=recommendations,
                overall_score=overall_score
            )
            
            self.log_operation_complete("structure validation",
                                      validation_passed=validation_passed,
                                      overall_score=overall_score)
            
            return report
            
        except Exception as e:
            self.log_operation_error("structure validation", e)
            raise
    
    def optimize_structure(self) -> StructureReport:
        """
        Optimize directory structure for production readiness.
        
        Returns:
            StructureReport with optimization results
        """
        self.log_operation_start("structure optimization")
        start_time = time.time()
        
        directories_reorganized = 0
        files_moved = 0
        structure_improvements = []
        
        try:
            # Analyze current structure
            analysis = self.analyze_current_structure()
            
            # Create missing essential directories
            for dir_name, description in self.production_structure.items():
                dir_path = self.project_root / dir_name
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    directories_reorganized += 1
                    structure_improvements.append(f"Created {dir_name}: {description}")
                    self.log_info(f"Created directory: {dir_name}")
            
            # Validate final structure
            validation_report = self.validate_structure()
            validation_passed = validation_report.validation_passed
            
            if not validation_passed:
                structure_improvements.extend([
                    f"Validation issue: {issue}" for issue in validation_report.issues_found
                ])
            
            duration = time.time() - start_time
            
            report = StructureReport(
                directories_reorganized=directories_reorganized,
                files_moved=files_moved,
                structure_improvements=structure_improvements,
                validation_passed=validation_passed
            )
            
            self.log_operation_complete("structure optimization", duration,
                                      directories_reorganized=directories_reorganized,
                                      validation_passed=validation_passed)
            
            return report
            
        except Exception as e:
            self.log_operation_error("structure optimization", e)
            raise
    
    def _calculate_structure_score(self, directories: List[str]) -> float:
        """Calculate structure quality score (0.0 to 1.0)."""
        score = 0.0
        total_weight = 0.0
        
        # Weight different aspects of structure
        weights = {
            'has_src': 0.3,
            'has_config': 0.2,
            'has_docs': 0.2,
            'has_tests': 0.15,
            'has_scripts': 0.1,
            'logical_separation': 0.05
        }
        
        # Check for essential directories
        if 'src' in directories:
            score += weights['has_src']
        total_weight += weights['has_src']
        
        if 'config' in directories:
            score += weights['has_config']
        total_weight += weights['has_config']
        
        if 'docs' in directories:
            score += weights['has_docs']
        total_weight += weights['has_docs']
        
        if 'tests' in directories:
            score += weights['has_tests']
        total_weight += weights['has_tests']
        
        if 'scripts' in directories:
            score += weights['has_scripts']
        total_weight += weights['has_scripts']
        
        # Check for logical separation (no loose files in root)
        total_weight += weights['logical_separation']
        root_files = [f for f in self.project_root.iterdir() 
                     if f.is_file() and not f.name.startswith('.')]
        if len(root_files) <= 5:  # Allow some essential root files
            score += weights['logical_separation']
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _generate_structure_recommendations(self, directories: List[str]) -> List[str]:
        """Generate recommendations for structure improvement."""
        recommendations = []
        
        # Check for missing essential directories
        essential_dirs = ['src', 'config', 'docs', 'tests']
        for dir_name in essential_dirs:
            if dir_name not in directories:
                recommendations.append(f"Create {dir_name}/ directory for better organization")
        
        # Check for common issues
        if 'test' in directories and 'tests' not in directories:
            recommendations.append("Rename 'test' to 'tests' for consistency")
        
        if 'doc' in directories and 'docs' not in directories:
            recommendations.append("Rename 'doc' to 'docs' for consistency")
        
        # Check for too many top-level directories
        if len(directories) > 10:
            recommendations.append("Consider consolidating directories to reduce complexity")
        
        return recommendations


class ProjectCleanupManager(OptimizationLoggerMixin):
    """
    Main project cleanup manager that coordinates file cleanup and structure optimization.
    """
    
    def __init__(self, config: OptimizationConfig):
        super().__init__()
        self.config = config
        self.file_cleanup_engine = FileCleanupEngine(config)
        self.structure_optimizer = DirectoryStructureOptimizer(config)
        
        self.log_info("Project cleanup manager initialized")
    
    def cleanup_development_artifacts(self) -> CleanupReport:
        """
        Clean up development artifacts using the file cleanup engine.
        
        Returns:
            CleanupReport with cleanup results
        """
        self.log_operation_start("development artifact cleanup")
        
        try:
            # Identify artifacts
            artifacts = self.file_cleanup_engine.identify_artifacts()
            
            # Clean up artifacts
            report = self.file_cleanup_engine.cleanup_artifacts(artifacts)
            
            self.log_operation_complete("development artifact cleanup",
                                      files_removed=report.files_removed,
                                      space_freed_mb=report.space_freed_mb)
            
            return report
            
        except Exception as e:
            self.log_operation_error("development artifact cleanup", e)
            raise
    
    def optimize_directory_structure(self) -> StructureReport:
        """
        Optimize directory structure for production readiness.
        
        Returns:
            StructureReport with optimization results
        """
        self.log_operation_start("directory structure optimization")
        
        try:
            report = self.structure_optimizer.optimize_structure()
            
            self.log_operation_complete("directory structure optimization",
                                      directories_reorganized=report.directories_reorganized,
                                      validation_passed=report.validation_passed)
            
            return report
            
        except Exception as e:
            self.log_operation_error("directory structure optimization", e)
            raise
    
    def validate_production_readiness(self) -> ValidationReport:
        """
        Validate production readiness of project structure.
        
        Returns:
            ValidationReport with validation results
        """
        self.log_operation_start("production readiness validation")
        
        try:
            report = self.structure_optimizer.validate_structure()
            
            self.log_operation_complete("production readiness validation",
                                      validation_passed=report.validation_passed,
                                      overall_score=report.overall_score)
            
            return report
            
        except Exception as e:
            self.log_operation_error("production readiness validation", e)
            raise
    
    def generate_cleanup_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive cleanup summary.
        
        Returns:
            Dictionary with cleanup summary information
        """
        self.log_operation_start("cleanup summary generation")
        
        try:
            # Run cleanup and optimization
            cleanup_report = self.cleanup_development_artifacts()
            structure_report = self.optimize_directory_structure()
            validation_report = self.validate_production_readiness()
            
            summary = {
                'cleanup_report': cleanup_report.to_dict(),
                'structure_report': structure_report.to_dict(),
                'validation_report': validation_report.to_dict(),
                'overall_success': (
                    len(cleanup_report.issues_encountered) == 0 and
                    structure_report.validation_passed and
                    validation_report.validation_passed
                ),
                'timestamp': datetime.now().isoformat()
            }
            
            self.log_operation_complete("cleanup summary generation",
                                      overall_success=summary['overall_success'])
            
            return summary
            
        except Exception as e:
            self.log_operation_error("cleanup summary generation", e)
            raise
    
    def rollback_cleanup(self) -> bool:
        """
        Rollback cleanup operations if needed.
        
        Returns:
            True if rollback successful, False otherwise
        """
        self.log_operation_start("cleanup rollback")
        
        try:
            success = self.file_cleanup_engine.rollback_operations()
            
            self.log_operation_complete("cleanup rollback", rollback_success=success)
            
            return success
            
        except Exception as e:
            self.log_operation_error("cleanup rollback", e)
            return False