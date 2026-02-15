#!/usr/bin/env python3
"""
OpenClass Nexus AI - Phase 3 Cleanup Script
Removes development artifacts and optimizes project structure for production.
"""

import os
import shutil
import glob
from pathlib import Path

def cleanup_phase3():
    """Execute Phase 3 cleanup operations."""
    
    print("🧹 Starting Phase 3 cleanup...")
    
    # Files to remove (root level)
    files_to_remove = [
        "test_checkpoint_model_download_loading.py",
        "test_config_simple.py", 
        "test_config_standalone.py",
        "test_educational_validator.py",
        "test_error_handler.py",
        "test_error_handler_simple.py", 
        "test_model_download_integration.py",
        "validate_checkpoint_4.py",
        "validate_config_implementation.py",
        "checkpoint_4_test_report.md",
        "phase3_validation_report_20260126_222419.txt",
        "FINAL_CHECKPOINT_VALIDATION_SUMMARY.md"
    ]
    
    # Remove individual files
    removed_files = 0
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Removed: {file_path}")
            removed_files += 1
    
    # Remove directories
    dirs_to_remove = [
        ".hypothesis",
        "updates"
    ]
    
    removed_dirs = 0
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"✅ Removed directory: {dir_path}")
            removed_dirs += 1
    
    # Clean Python cache files
    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo"
    ]
    
    cache_removed = 0
    for pattern in cache_patterns:
        for path in glob.glob(pattern, recursive=True):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            cache_removed += 1
    
    # Create deployment directory structure
    deployment_dirs = [
        "scripts/deployment",
        "docs/api",
        "docs/deployment", 
        "docs/user_guide",
        "docs/development"
    ]
    
    created_dirs = 0
    for dir_path in deployment_dirs:
        os.makedirs(dir_path, exist_ok=True)
        if not os.path.exists(f"{dir_path}/.gitkeep"):
            Path(f"{dir_path}/.gitkeep").touch()
        created_dirs += 1
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   • Files removed: {removed_files}")
    print(f"   • Directories removed: {removed_dirs}")
    print(f"   • Cache files cleaned: {cache_removed}")
    print(f"   • New directories created: {created_dirs}")
    
    print(f"\n✨ Phase 3 cleanup complete! Project optimized for production.")

if __name__ == "__main__":
    cleanup_phase3()