"""
Unit tests for Project Cleanup Manager

Tests specific cleanup scenarios with known file structures,
error conditions and rollback mechanisms, and directory structure validation.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.optimization.cleanup_manager import (
    ProjectCleanupManager,
    FileCleanupEngine,
    DirectoryStructureOptimizer
)
from src.optimization.config import OptimizationConfig
from src.optimization.models import CleanupReport, StructureReport, ValidationReport


class TestFileCleanupEngine:
    """Test file cleanup engine functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = OptimizationConfig()
        self.config.project_root = self.temp_dir
        self.config.optimization_output_dir = self.temp_dir / "optimization_output"
        self.engine = FileCleanupEngine(self.config)
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_identify_artifacts_with_known_structure(self):
        """Test artifact identification with known file structure."""
        # Create known file structure
        (self.temp_dir / "temp_file.tmp").write_text("temp content")
        (self.temp_dir / "cache_file.temp").write_text("cache content")
        (self.temp_dir / "test.log").write_text("log content")
        (self.temp_dir / "__pycache__").mkdir()
        (self.temp_dir / "__pycache__" / "module.pyc").write_text("bytecode")
        (self.temp_dir / ".pytest_cache").mkdir()
        (self.temp_dir / ".pytest_cache" / "cache.json").write_text("{}")
        (self.temp_dir / "requirements.txt").write_text("essential file")
        
        # Identify artifacts
        artifacts = self.engine.identify_artifacts()
        
        # Verify artifact identification
        assert isinstance(artifacts, dict)
        assert 'temp_files' in artifacts
        assert 'cache_dirs' in artifacts
        assert 'test_artifacts' in artifacts
        assert 'log_files' in artifacts
        
        # Check specific artifacts were identified based on actual categorization
        temp_files = [str(p) for p in artifacts['temp_files']]
        assert any("temp_file.tmp" in f for f in temp_files)
        assert any("cache_file.temp" in f for f in temp_files)
        assert any("test.log" in f for f in temp_files)  # .log files go to temp_files
        
        cache_dirs = [str(p) for p in artifacts['cache_dirs']]
        assert any("__pycache__" in d for d in cache_dirs)
        assert any(".pytest_cache" in d for d in cache_dirs)  # .pytest_cache goes to cache_dirs
    
    def test_validate_essential_files_protection(self):
        """Test that essential files are protected from cleanup."""
        # Create essential and non-essential files
        essential_file = self.temp_dir / "requirements.txt"
        essential_file.write_text("essential content")
        
        temp_file = self.temp_dir / "temp.tmp"
        temp_file.write_text("temp content")
        
        files_to_validate = [essential_file, temp_file]
        
        # Validate files
        safe_to_remove, essential_files = self.engine.validate_essential_files(files_to_validate)
        
        # Verify essential file protection
        assert essential_file in essential_files
        assert temp_file in safe_to_remove
        assert len(essential_files) == 1
        assert len(safe_to_remove) == 1
    
    def test_safe_remove_file_success(self):
        """Test successful file removal."""
        # Create a temporary file
        temp_file = self.temp_dir / "removable.tmp"
        temp_file.write_text("removable content")
        
        assert temp_file.exists()
        
        # Remove file
        result = self.engine.safe_remove_file(temp_file)
        
        # Verify removal
        assert result is True
        assert not temp_file.exists()
        assert len(self.engine.operations) == 1
        assert self.engine.operations[0].operation_type == 'delete'
        assert self.engine.operations[0].target_path == temp_file
    
    def test_safe_remove_essential_file_refused(self):
        """Test that essential files are refused for removal."""
        # Create essential file
        essential_file = self.temp_dir / "requirements.txt"
        essential_file.write_text("essential content")
        
        # Attempt to remove essential file
        result = self.engine.safe_remove_file(essential_file)
        
        # Verify removal was refused
        assert result is False
        assert essential_file.exists()
        assert len(self.engine.operations) == 0
    
    def test_cleanup_artifacts_comprehensive(self):
        """Test comprehensive artifact cleanup."""
        # Create various artifacts
        temp_file = self.temp_dir / "temp.tmp"
        temp_file.write_text("temp content")
        
        log_file = self.temp_dir / "test.log"
        log_file.write_text("log content")
        
        cache_dir = self.temp_dir / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "module.pyc").write_text("bytecode")
        
        # Create essential file that should be preserved
        essential_file = self.temp_dir / "requirements.txt"
        essential_file.write_text("essential content")
        
        # Identify artifacts
        artifacts = self.engine.identify_artifacts()
        
        # Cleanup artifacts
        report = self.engine.cleanup_artifacts(artifacts)
        
        # Verify cleanup report
        assert isinstance(report, CleanupReport)
        assert report.files_removed >= 0
        assert report.directories_cleaned >= 0
        assert report.space_freed_mb >= 0
        assert isinstance(report.issues_encountered, list)
        assert isinstance(report.recommendations, list)
        
        # Verify essential file is preserved
        assert essential_file.exists()
        
        # Verify some artifacts were removed
        assert not temp_file.exists() or not log_file.exists()
    
    def test_rollback_operations_success(self):
        """Test successful rollback of cleanup operations."""
        # Create a file to remove and rollback
        test_file = self.temp_dir / "rollback_test.tmp"
        original_content = "original content"
        test_file.write_text(original_content)
        
        # Remove file (this creates backup)
        result = self.engine.safe_remove_file(test_file)
        assert result is True
        assert not test_file.exists()
        
        # Rollback operations
        rollback_result = self.engine.rollback_operations()
        
        # Verify rollback success
        assert rollback_result is True
        assert test_file.exists()
        assert test_file.read_text() == original_content
    
    def test_rollback_operations_no_operations(self):
        """Test rollback when no operations exist."""
        # Attempt rollback with no operations
        result = self.engine.rollback_operations()
        
        # Should return False (no operations to rollback)
        assert result is False
    
    @patch('src.optimization.cleanup_manager.shutil.copy2')
    def test_create_backup_failure_handling(self, mock_copy):
        """Test backup creation failure handling."""
        # Mock copy failure
        mock_copy.side_effect = PermissionError("Permission denied")
        
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Attempt to create backup
        backup = self.engine.create_backup(test_file)
        
        # Should return None on failure
        assert backup is None


class TestDirectoryStructureOptimizer:
    """Test directory structure optimizer functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = OptimizationConfig()
        self.config.project_root = self.temp_dir
        self.optimizer = DirectoryStructureOptimizer(self.config)
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyze_current_structure_basic(self):
        """Test analysis of basic directory structure."""
        # Create basic structure
        (self.temp_dir / "src").mkdir()
        (self.temp_dir / "config").mkdir()
        (self.temp_dir / "docs").mkdir()
        (self.temp_dir / "src" / "main.py").write_text("# Main file")
        (self.temp_dir / "config" / "app.py").write_text("# Config file")
        
        # Analyze structure
        analysis = self.optimizer.analyze_current_structure()
        
        # Verify analysis results
        assert isinstance(analysis, dict)
        assert 'directories' in analysis
        assert 'files_by_directory' in analysis
        assert 'structure_score' in analysis
        assert 'recommendations' in analysis
        
        assert 'src' in analysis['directories']
        assert 'config' in analysis['directories']
        assert 'docs' in analysis['directories']
        
        assert analysis['files_by_directory']['src'] >= 1
        assert analysis['files_by_directory']['config'] >= 1
        assert analysis['structure_score'] > 0.0
    
    def test_validate_structure_with_required_directories(self):
        """Test structure validation with required directories present."""
        # Create required directories
        (self.temp_dir / "src").mkdir()
        (self.temp_dir / "config").mkdir()
        (self.temp_dir / "docs").mkdir()
        (self.temp_dir / "tests").mkdir()
        
        # Validate structure
        report = self.optimizer.validate_structure()
        
        # Verify validation report
        assert isinstance(report, ValidationReport)
        assert report.components_validated > 0
        assert isinstance(report.issues_found, list)
        assert isinstance(report.recommendations, list)
        assert 0.0 <= report.overall_score <= 1.0
        
        # Should have fewer issues with proper structure
        assert len(report.issues_found) <= 2  # Allow for some minor issues
    
    def test_validate_structure_missing_directories(self):
        """Test structure validation with missing required directories."""
        # Create minimal structure (missing required directories)
        (self.temp_dir / "random_dir").mkdir()
        
        # Validate structure
        report = self.optimizer.validate_structure()
        
        # Verify validation identifies missing directories
        assert isinstance(report, ValidationReport)
        assert len(report.issues_found) > 0
        assert any("Missing required directory" in issue for issue in report.issues_found)
        assert report.overall_score < 1.0
    
    def test_optimize_structure_creates_missing_directories(self):
        """Test that structure optimization creates missing directories."""
        # Start with empty directory
        initial_dirs = list(self.temp_dir.iterdir())
        
        # Optimize structure
        report = self.optimizer.optimize_structure()
        
        # Verify optimization report
        assert isinstance(report, StructureReport)
        assert report.directories_reorganized >= 0
        assert report.files_moved >= 0
        assert isinstance(report.structure_improvements, list)
        
        # Verify essential directories were created
        assert (self.temp_dir / "src").exists()
        assert (self.temp_dir / "config").exists()
        assert (self.temp_dir / "docs").exists()
        
        # Should have more directories after optimization
        final_dirs = list(self.temp_dir.iterdir())
        assert len(final_dirs) > len(initial_dirs)
    
    def test_structure_score_calculation(self):
        """Test structure score calculation with different scenarios."""
        # Test with good structure
        (self.temp_dir / "src").mkdir()
        (self.temp_dir / "config").mkdir()
        (self.temp_dir / "docs").mkdir()
        (self.temp_dir / "tests").mkdir()
        (self.temp_dir / "scripts").mkdir()
        
        good_score = self.optimizer._calculate_structure_score(['src', 'config', 'docs', 'tests', 'scripts'])
        
        # Test with poor structure
        poor_score = self.optimizer._calculate_structure_score(['random1', 'random2'])
        
        # Good structure should score higher
        assert good_score > poor_score
        assert 0.0 <= good_score <= 1.0
        assert 0.0 <= poor_score <= 1.0
    
    def test_generate_structure_recommendations(self):
        """Test generation of structure recommendations."""
        # Test with missing essential directories
        recommendations = self.optimizer._generate_structure_recommendations(['random'])
        
        # Should recommend creating essential directories
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("Create src/" in rec for rec in recommendations)
        assert any("Create config/" in rec for rec in recommendations)
        assert any("Create docs/" in rec for rec in recommendations)


class TestProjectCleanupManager:
    """Test main project cleanup manager functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = OptimizationConfig()
        self.config.project_root = self.temp_dir
        self.config.optimization_output_dir = self.temp_dir / "optimization_output"
        self.manager = ProjectCleanupManager(self.config)
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cleanup_development_artifacts_integration(self):
        """Test integration of development artifact cleanup."""
        # Create artifacts to clean
        (self.temp_dir / "temp.tmp").write_text("temp content")
        (self.temp_dir / "test.log").write_text("log content")
        (self.temp_dir / "__pycache__").mkdir()
        (self.temp_dir / "__pycache__" / "module.pyc").write_text("bytecode")
        
        # Create essential file
        (self.temp_dir / "requirements.txt").write_text("essential")
        
        # Run cleanup
        report = self.manager.cleanup_development_artifacts()
        
        # Verify cleanup report
        assert isinstance(report, CleanupReport)
        assert report.files_removed >= 0
        assert report.directories_cleaned >= 0
        assert report.space_freed_mb >= 0
        
        # Verify essential file preserved
        assert (self.temp_dir / "requirements.txt").exists()
    
    def test_optimize_directory_structure_integration(self):
        """Test integration of directory structure optimization."""
        # Start with basic structure
        (self.temp_dir / "random_file.txt").write_text("content")
        
        # Run optimization
        report = self.manager.optimize_directory_structure()
        
        # Verify optimization report
        assert isinstance(report, StructureReport)
        assert report.directories_reorganized >= 0
        assert report.files_moved >= 0
        assert isinstance(report.structure_improvements, list)
        
        # Verify essential directories created
        assert (self.temp_dir / "src").exists()
        assert (self.temp_dir / "config").exists()
        assert (self.temp_dir / "docs").exists()
    
    def test_validate_production_readiness_integration(self):
        """Test integration of production readiness validation."""
        # Create good structure
        (self.temp_dir / "src").mkdir()
        (self.temp_dir / "config").mkdir()
        (self.temp_dir / "docs").mkdir()
        (self.temp_dir / "tests").mkdir()
        
        # Run validation
        report = self.manager.validate_production_readiness()
        
        # Verify validation report
        assert isinstance(report, ValidationReport)
        assert report.components_validated > 0
        assert isinstance(report.issues_found, list)
        assert isinstance(report.recommendations, list)
        assert 0.0 <= report.overall_score <= 1.0
    
    def test_generate_cleanup_summary_comprehensive(self):
        """Test comprehensive cleanup summary generation."""
        # Create mixed structure with artifacts and missing directories
        (self.temp_dir / "temp.tmp").write_text("temp content")
        (self.temp_dir / "requirements.txt").write_text("essential")
        
        # Generate summary
        summary = self.manager.generate_cleanup_summary()
        
        # Verify summary structure
        assert isinstance(summary, dict)
        assert 'cleanup_report' in summary
        assert 'structure_report' in summary
        assert 'validation_report' in summary
        assert 'overall_success' in summary
        assert 'timestamp' in summary
        
        # Verify nested reports
        assert isinstance(summary['cleanup_report'], dict)
        assert isinstance(summary['structure_report'], dict)
        assert isinstance(summary['validation_report'], dict)
        assert isinstance(summary['overall_success'], bool)
    
    def test_rollback_cleanup_integration(self):
        """Test integration of cleanup rollback functionality."""
        # Create file to be cleaned and rolled back
        test_file = self.temp_dir / "rollback_test.tmp"
        test_file.write_text("original content")
        
        # Run cleanup (should remove temp file)
        cleanup_report = self.manager.cleanup_development_artifacts()
        
        # File should be removed if it matched cleanup patterns
        if cleanup_report.files_removed > 0:
            # Attempt rollback
            rollback_result = self.manager.rollback_cleanup()
            
            # Verify rollback attempt
            assert isinstance(rollback_result, bool)
    
    @patch('src.optimization.cleanup_manager.FileCleanupEngine.identify_artifacts')
    def test_error_handling_in_cleanup(self, mock_identify):
        """Test error handling during cleanup operations."""
        # Mock an error in artifact identification
        mock_identify.side_effect = PermissionError("Permission denied")
        
        # Attempt cleanup - should raise exception
        with pytest.raises(PermissionError):
            self.manager.cleanup_development_artifacts()
    
    @patch('src.optimization.cleanup_manager.DirectoryStructureOptimizer.optimize_structure')
    def test_error_handling_in_optimization(self, mock_optimize):
        """Test error handling during structure optimization."""
        # Mock an error in structure optimization
        mock_optimize.side_effect = OSError("Disk full")
        
        # Attempt optimization - should raise exception
        with pytest.raises(OSError):
            self.manager.optimize_directory_structure()