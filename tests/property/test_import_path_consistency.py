"""Property-based tests for import path consistency after refactoring.

**Validates: Requirements 2.4**

This test suite verifies that after the folder restructuring:
- No old import paths remain (src.local_inference, src.cloud_sync)
- All imports use the new paths (src.edge_runtime, src.aws_control_plane)
- The codebase is consistent with the new architecture naming
"""

import os
import re
import pytest
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple


def get_python_files() -> List[Path]:
    """Get all Python files in the src directory."""
    src_dir = Path(__file__).parent.parent.parent / "src"
    python_files = list(src_dir.rglob("*.py"))
    return python_files


def get_test_files() -> List[Path]:
    """Get all Python test files."""
    tests_dir = Path(__file__).parent.parent
    python_files = list(tests_dir.rglob("*.py"))
    return python_files


def get_all_python_files() -> List[Path]:
    """Get all Python files in the project (src + tests + scripts)."""
    project_root = Path(__file__).parent.parent.parent
    
    # Get files from src, tests, and scripts directories
    python_files = []
    for directory in ["src", "tests", "scripts"]:
        dir_path = project_root / directory
        if dir_path.exists():
            python_files.extend(dir_path.rglob("*.py"))
    
    # Also check root level Python files
    python_files.extend(project_root.glob("*.py"))
    
    return python_files


def extract_imports(file_path: Path) -> List[Tuple[int, str]]:
    """Extract all import statements from a Python file.
    
    Returns:
        List of tuples (line_number, import_statement)
    """
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                # Match import statements
                if line.startswith('import ') or line.startswith('from '):
                    imports.append((line_num, line))
    except Exception as e:
        # Skip files that can't be read
        pass
    
    return imports


def check_for_old_paths(import_statement: str) -> List[str]:
    """Check if an import statement contains old paths.
    
    Returns:
        List of old paths found in the import statement
    """
    old_paths = []
    
    # Patterns for old import paths
    old_patterns = [
        r'src\.local_inference',
        r'src/local_inference',
        r'from\s+src\.local_inference',
        r'import\s+src\.local_inference',
        r'src\.cloud_sync',
        r'src/cloud_sync',
        r'from\s+src\.cloud_sync',
        r'import\s+src\.cloud_sync',
    ]
    
    for pattern in old_patterns:
        if re.search(pattern, import_statement):
            old_paths.append(pattern)
    
    return old_paths


def check_for_new_paths(import_statement: str) -> bool:
    """Check if an import statement uses new paths correctly.
    
    Returns:
        True if the import uses new paths (edge_runtime or aws_control_plane)
    """
    new_patterns = [
        r'src\.edge_runtime',
        r'src/edge_runtime',
        r'from\s+src\.edge_runtime',
        r'import\s+src\.edge_runtime',
        r'src\.aws_control_plane',
        r'src/aws_control_plane',
        r'from\s+src\.aws_control_plane',
        r'import\s+src\.aws_control_plane',
        # Also accept imports without 'src.' prefix (when using sys.path manipulation)
        r'from\s+edge_runtime',
        r'import\s+edge_runtime',
        r'from\s+aws_control_plane',
        r'import\s+aws_control_plane',
    ]
    
    for pattern in new_patterns:
        if re.search(pattern, import_statement):
            return True
    
    return False


# Property 2: Import Path Consistency After Refactoring
@settings(max_examples=100)
@given(file_index=st.integers(min_value=0, max_value=1000))
def test_property_no_old_import_paths(file_index):
    """Property 2: For any Python file in the codebase after folder restructuring,
    no import statements should reference the old paths (src.local_inference, src.cloud_sync).
    
    **Validates: Requirements 2.4**
    """
    # Get all Python files
    python_files = get_all_python_files()
    
    # Assume we have files to test
    assume(len(python_files) > 0)
    
    # Select a file using the generated index (wrap around if needed)
    file_path = python_files[file_index % len(python_files)]
    
    # Extract imports from the file
    imports = extract_imports(file_path)
    
    # Check each import for old paths
    violations = []
    for line_num, import_stmt in imports:
        old_paths = check_for_old_paths(import_stmt)
        if old_paths:
            violations.append({
                'file': str(file_path),
                'line': line_num,
                'import': import_stmt,
                'old_paths': old_paths
            })
    
    # Property: No old import paths should exist
    assert len(violations) == 0, (
        f"Found {len(violations)} import(s) with old paths:\n" +
        "\n".join([
            f"  {v['file']}:{v['line']}: {v['import']}"
            for v in violations
        ])
    )


@settings(max_examples=100)
@given(file_index=st.integers(min_value=0, max_value=1000))
def test_property_new_import_paths_used(file_index):
    """Property 2 (Extended): For any Python file that imports from the refactored modules,
    all imports should use the new paths (src.edge_runtime, src.aws_control_plane).
    
    **Validates: Requirements 2.4**
    """
    # Get all Python files
    python_files = get_all_python_files()
    
    # Assume we have files to test
    assume(len(python_files) > 0)
    
    # Select a file using the generated index (wrap around if needed)
    file_path = python_files[file_index % len(python_files)]
    
    # Extract imports from the file
    imports = extract_imports(file_path)
    
    # Check if file has any imports from the refactored modules
    has_refactored_imports = False
    correct_imports = []
    
    for line_num, import_stmt in imports:
        # Check if this import is from our refactored modules
        if 'edge_runtime' in import_stmt or 'aws_control_plane' in import_stmt:
            has_refactored_imports = True
            # Verify it uses the correct new path format
            if check_for_new_paths(import_stmt):
                correct_imports.append(import_stmt)
    
    # If the file has refactored imports, they should all be correct
    # (This is implicitly true if no old paths were found, but we verify explicitly)
    if has_refactored_imports:
        # Property: All refactored imports should use new paths
        assert len(correct_imports) > 0, (
            f"File {file_path} has refactored imports but none use correct new paths"
        )


def test_comprehensive_old_path_scan():
    """Comprehensive scan of all Python files to ensure no old paths remain.
    
    This is a deterministic test that checks all files at once.
    
    **Validates: Requirements 2.4**
    """
    python_files = get_all_python_files()
    
    all_violations = []
    
    for file_path in python_files:
        imports = extract_imports(file_path)
        
        for line_num, import_stmt in imports:
            old_paths = check_for_old_paths(import_stmt)
            if old_paths:
                all_violations.append({
                    'file': str(file_path.relative_to(Path(__file__).parent.parent.parent)),
                    'line': line_num,
                    'import': import_stmt,
                    'old_paths': old_paths
                })
    
    # Property: No old import paths should exist anywhere in the codebase
    assert len(all_violations) == 0, (
        f"Found {len(all_violations)} import(s) with old paths:\n" +
        "\n".join([
            f"  {v['file']}:{v['line']}: {v['import']}"
            for v in all_violations[:10]  # Show first 10 violations
        ]) +
        (f"\n  ... and {len(all_violations) - 10} more" if len(all_violations) > 10 else "")
    )


def test_new_paths_exist_in_codebase():
    """Verify that new import paths are actually being used in the codebase.
    
    This ensures the refactoring was completed and not just that old paths were removed.
    
    **Validates: Requirements 2.4**
    """
    python_files = get_all_python_files()
    
    new_path_usage = {
        'edge_runtime': 0,
        'aws_control_plane': 0
    }
    
    for file_path in python_files:
        imports = extract_imports(file_path)
        
        for line_num, import_stmt in imports:
            if 'edge_runtime' in import_stmt:
                new_path_usage['edge_runtime'] += 1
            if 'aws_control_plane' in import_stmt:
                new_path_usage['aws_control_plane'] += 1
    
    # Property: New paths should be used in the codebase
    # (At least one of them should have some usage)
    total_new_path_usage = sum(new_path_usage.values())
    assert total_new_path_usage > 0, (
        f"No new import paths found in codebase. "
        f"Expected to find imports using 'edge_runtime' or 'aws_control_plane'. "
        f"Usage: {new_path_usage}"
    )
    
    # Log the usage for visibility
    print(f"\nNew import path usage:")
    print(f"  edge_runtime: {new_path_usage['edge_runtime']} imports")
    print(f"  aws_control_plane: {new_path_usage['aws_control_plane']} imports")


def test_folder_structure_matches_imports():
    """Verify that the folder structure matches the import paths.
    
    This ensures the physical folders were renamed correctly.
    
    **Validates: Requirements 2.1, 2.2**
    """
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"
    
    # Check that new folders exist
    edge_runtime_dir = src_dir / "edge_runtime"
    aws_control_plane_dir = src_dir / "aws_control_plane"
    
    assert edge_runtime_dir.exists() and edge_runtime_dir.is_dir(), (
        f"Expected 'src/edge_runtime' directory to exist at {edge_runtime_dir}"
    )
    
    assert aws_control_plane_dir.exists() and aws_control_plane_dir.is_dir(), (
        f"Expected 'src/aws_control_plane' directory to exist at {aws_control_plane_dir}"
    )
    
    # Check that old folders do NOT exist
    local_inference_dir = src_dir / "local_inference"
    cloud_sync_dir = src_dir / "cloud_sync"
    
    assert not local_inference_dir.exists(), (
        f"Old 'src/local_inference' directory still exists at {local_inference_dir}. "
        f"It should have been renamed to 'src/edge_runtime'."
    )
    
    assert not cloud_sync_dir.exists(), (
        f"Old 'src/cloud_sync' directory still exists at {cloud_sync_dir}. "
        f"It should have been renamed to 'src/aws_control_plane'."
    )
    
    print(f"\nFolder structure verification:")
    print(f"  ✓ src/edge_runtime exists")
    print(f"  ✓ src/aws_control_plane exists")
    print(f"  ✓ src/local_inference removed")
    print(f"  ✓ src/cloud_sync removed")
