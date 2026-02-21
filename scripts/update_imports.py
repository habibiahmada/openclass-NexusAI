#!/usr/bin/env python3
"""
Script to update import statements after folder restructuring.
Updates:
- src.local_inference -> src.edge_runtime
- src.cloud_sync -> src.aws_control_plane
- local_inference -> edge_runtime
- cloud_sync -> aws_control_plane
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def find_python_files(root_dir: str) -> List[Path]:
    """Find all Python files in the project."""
    python_files = []
    root_path = Path(root_dir)
    
    # Exclude certain directories
    exclude_dirs = {
        '.git', '__pycache__', '.pytest_cache', '.hypothesis',
        'openclass-env', 'venv', 'env', '.venv',
        'node_modules', 'optimization_output'
    }
    
    for path in root_path.rglob('*.py'):
        # Check if any parent directory is in exclude list
        if not any(excluded in path.parts for excluded in exclude_dirs):
            python_files.append(path)
    
    return python_files


def update_imports_in_file(file_path: Path) -> Tuple[bool, int]:
    """
    Update import statements in a single file.
    
    Returns:
        Tuple of (was_modified, num_replacements)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacements = 0
        
        # Define replacement patterns
        patterns = [
            # Pattern 1: from src.edge_runtime -> from src.edge_runtime
            (r'from src\.local_inference', 'from src.edge_runtime'),
            # Pattern 2: import src.edge_runtime -> import src.edge_runtime
            (r'import src\.local_inference', 'import src.edge_runtime'),
            # Pattern 3: from edge_runtime -> from edge_runtime (for relative imports)
            (r'from edge_runtime', 'from edge_runtime'),
            # Pattern 4: import edge_runtime -> import edge_runtime
            (r'import edge_runtime', 'import edge_runtime'),
            
            # Pattern 5: from src.aws_control_plane -> from src.aws_control_plane
            (r'from src\.cloud_sync', 'from src.aws_control_plane'),
            # Pattern 6: import src.aws_control_plane -> import src.aws_control_plane
            (r'import src\.cloud_sync', 'import src.aws_control_plane'),
            # Pattern 7: from aws_control_plane -> from aws_control_plane
            (r'from aws_control_plane', 'from aws_control_plane'),
            # Pattern 8: import aws_control_plane -> import aws_control_plane
            (r'import aws_control_plane', 'import aws_control_plane'),
            
            # Pattern 9: String references in patch decorators and similar
            (r"'src\.local_inference\.", "'src.edge_runtime."),
            (r'"src\.local_inference\.', '"src.edge_runtime.'),
            (r"'src\.cloud_sync\.", "'src.aws_control_plane."),
            (r'"src\.cloud_sync\.', '"src.aws_control_plane.'),
            
            # Pattern 10: Logger names
            (r"'src\.local_inference'", "'src.edge_runtime'"),
            (r'"src\.local_inference"', '"src.edge_runtime"'),
            (r"'src\.cloud_sync'", "'src.aws_control_plane'"),
            (r'"src\.cloud_sync"', '"src.aws_control_plane"'),
        ]
        
        # Apply all patterns
        for pattern, replacement in patterns:
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                content = new_content
                replacements += count
        
        # Write back if modified
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, replacements
        
        return False, 0
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0


def main():
    """Main function to update all imports."""
    print("=" * 70)
    print("Import Path Update Script")
    print("=" * 70)
    print()
    print("Updating import statements:")
    print("  - src.local_inference -> src.edge_runtime")
    print("  - src.cloud_sync -> src.aws_control_plane")
    print()
    
    # Get project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"Project root: {project_root}")
    print()
    
    # Find all Python files
    print("Scanning for Python files...")
    python_files = find_python_files(project_root)
    print(f"Found {len(python_files)} Python files")
    print()
    
    # Update imports in each file
    print("Updating imports...")
    modified_files = []
    total_replacements = 0
    
    for file_path in python_files:
        was_modified, num_replacements = update_imports_in_file(file_path)
        if was_modified:
            relative_path = file_path.relative_to(project_root)
            modified_files.append((relative_path, num_replacements))
            total_replacements += num_replacements
            print(f"  ✓ {relative_path} ({num_replacements} replacements)")
    
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Files scanned: {len(python_files)}")
    print(f"Files modified: {len(modified_files)}")
    print(f"Total replacements: {total_replacements}")
    print()
    
    if modified_files:
        print("Modified files:")
        for file_path, count in modified_files:
            print(f"  - {file_path} ({count} replacements)")
    else:
        print("No files needed modification.")
    
    print()
    print("Import update complete!")


if __name__ == "__main__":
    main()
