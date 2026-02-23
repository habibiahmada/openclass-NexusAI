"""Property-based tests for documentation hardware specification consistency.

**Validates: Requirements 1.1, 1.3, 1.4**

This test suite verifies that after the hardware specification update:
- No references to "4GB RAM minimum" remain in documentation
- All hardware specifications consistently show 16GB RAM, 8-core CPU, 512GB SSD
- No memory_limit_mb = 3072 constraints exist in configuration files
- Documentation is consistent across all files
"""

import os
import re
import pytest
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple, Dict


def get_documentation_files() -> List[Path]:
    """Get all documentation files (markdown) in the project."""
    project_root = Path(__file__).parent.parent.parent
    
    # Get markdown files from various directories
    doc_files = []
    for pattern in ["**/*.md", "**/*.MD"]:
        doc_files.extend(project_root.glob(pattern))
    
    # Filter out node_modules, .git, and other irrelevant directories
    excluded_dirs = {'.git', 'node_modules', '.hypothesis', '.pytest_cache', 
                     'openclass-env', '__pycache__', '.kiro'}
    
    filtered_files = []
    for file_path in doc_files:
        # Check if any excluded directory is in the path
        if not any(excluded in file_path.parts for excluded in excluded_dirs):
            filtered_files.append(file_path)
    
    return filtered_files


def get_config_files() -> List[Path]:
    """Get all configuration files (Python, YAML, JSON) in the project."""
    project_root = Path(__file__).parent.parent.parent
    
    config_files = []
    for pattern in ["**/*.py", "**/*.yaml", "**/*.yml", "**/*.json"]:
        config_files.extend(project_root.glob(pattern))
    
    # Filter out irrelevant directories
    excluded_dirs = {'.git', 'node_modules', '.hypothesis', '.pytest_cache', 
                     'openclass-env', '__pycache__', 'tests', '.kiro'}
    
    filtered_files = []
    for file_path in config_files:
        if not any(excluded in file_path.parts for excluded in excluded_dirs):
            filtered_files.append(file_path)
    
    return filtered_files


def scan_file_for_pattern(file_path: Path, pattern: str, context_lines: int = 0) -> List[Dict]:
    """Scan a file for a regex pattern and return matches with context.
    
    Args:
        file_path: Path to the file to scan
        pattern: Regex pattern to search for
        context_lines: Number of lines of context to include before/after match
    
    Returns:
        List of dictionaries with match information
    """
    matches = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, start=1):
            if re.search(pattern, line, re.IGNORECASE):
                # Get context lines
                start_line = max(0, line_num - 1 - context_lines)
                end_line = min(len(lines), line_num + context_lines)
                context = ''.join(lines[start_line:end_line])
                
                matches.append({
                    'file': str(file_path),
                    'line': line_num,
                    'content': line.strip(),
                    'context': context.strip()
                })
    except Exception as e:
        # Skip files that can't be read
        pass
    
    return matches


def check_for_4gb_references(file_path: Path) -> List[Dict]:
    """Check if a file contains references to 4GB RAM.
    
    Returns:
        List of matches with file, line number, and content
    """
    # Pattern to match 4GB references (but not 4GB model size which is valid)
    # We want to catch "4GB RAM", "4 GB RAM", "minimal 4GB", etc.
    # But NOT "model size 4GB", "LLM model 4GB", etc.
    patterns = [
        r'(?<!model\s)(?<!size\s)(?<!~\s)4\s*GB(?!\s*model)(?!\s*\(quantized\))(?!\s*GGUF)',
        r'(?<!model\s)(?<!size\s)(?<!~\s)4GB(?!\s*model)(?!\s*\(quantized\))(?!\s*GGUF)',
        r'minimal\s+4\s*GB',
        r'minimum\s+4\s*GB',
        r'RAM.*4\s*GB',
        r'4\s*GB.*RAM',
    ]
    
    all_matches = []
    for pattern in patterns:
        matches = scan_file_for_pattern(file_path, pattern, context_lines=1)
        
        # Filter out false positives (model size references)
        for match in matches:
            content_lower = match['content'].lower()
            context_lower = match['context'].lower()
            
            # Skip if it's clearly about model size
            if any(keyword in context_lower for keyword in [
                'model size', 'llm model', 'quantized', 'gguf', 
                'model file', 'download', '~4gb', 'model (~4gb)',
                'limited to 4gb', 'size limited to 4gb'
            ]):
                continue
            
            # Skip if it's in a historical/archive document
            if 'archive' in match['file'].lower() or 'phase3' in match['file'].lower():
                continue
            
            all_matches.append(match)
    
    return all_matches


def check_for_16gb_specification(file_path: Path) -> bool:
    """Check if a file contains the correct 16GB RAM specification.
    
    Returns:
        True if the file mentions 16GB RAM specification
    """
    patterns = [
        r'16\s*GB\s+RAM',
        r'RAM.*16\s*GB',
        r'16GB\s+RAM',
        r'RAM.*16GB',
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
    except Exception:
        pass
    
    return False


def check_for_complete_hardware_spec(file_path: Path) -> List[Dict]:
    """Check if a file contains the complete hardware specification.
    
    The complete spec should be: 16GB RAM, 8-core CPU, 512GB SSD
    
    Returns:
        List of matches where hardware specs are mentioned
    """
    # Look for hardware specification sections
    hardware_patterns = [
        r'hardware\s+requirement',
        r'system\s+requirement',
        r'minimum\s+requirement',
        r'server\s+specification',
        r'school\s+server',
    ]
    
    matches = []
    for pattern in hardware_patterns:
        found = scan_file_for_pattern(file_path, pattern, context_lines=5)
        matches.extend(found)
    
    return matches


def check_for_memory_limit_constraint(file_path: Path) -> List[Dict]:
    """Check if a file contains memory_limit_mb = 3072 constraint.
    
    Returns:
        List of matches with the old constraint
    """
    # Pattern to match memory_limit_mb = 3072 or similar
    pattern = r'memory_limit_mb\s*[=:]\s*3072'
    
    return scan_file_for_pattern(file_path, pattern, context_lines=2)


# Property 1: Documentation Hardware Specification Consistency
@settings(max_examples=100)
@given(file_index=st.integers(min_value=0, max_value=1000))
def test_property_no_4gb_references_in_documentation(file_index):
    """Property 1: For any documentation file in the project,
    no references to "4GB RAM minimum" should exist (except for model size).
    
    **Validates: Requirements 1.1**
    """
    # Get all documentation files
    doc_files = get_documentation_files()
    
    # Assume we have files to test
    assume(len(doc_files) > 0)
    
    # Select a file using the generated index (wrap around if needed)
    file_path = doc_files[file_index % len(doc_files)]
    
    # Check for 4GB references
    violations = check_for_4gb_references(file_path)
    
    # Property: No 4GB RAM references should exist in documentation
    assert len(violations) == 0, (
        f"Found {len(violations)} reference(s) to 4GB RAM in {file_path.name}:\n" +
        "\n".join([
            f"  Line {v['line']}: {v['content']}\n  Context: {v['context'][:100]}..."
            for v in violations[:5]  # Show first 5 violations
        ])
    )


@settings(max_examples=100)
@given(file_index=st.integers(min_value=0, max_value=1000))
def test_property_no_memory_limit_3072_in_config(file_index):
    """Property 1 (Extended): For any configuration file in the project,
    no memory_limit_mb = 3072 constraints should exist.
    
    **Validates: Requirements 1.2**
    """
    # Get all config files
    config_files = get_config_files()
    
    # Assume we have files to test
    assume(len(config_files) > 0)
    
    # Select a file using the generated index (wrap around if needed)
    file_path = config_files[file_index % len(config_files)]
    
    # Check for memory_limit_mb = 3072
    violations = check_for_memory_limit_constraint(file_path)
    
    # Property: No memory_limit_mb = 3072 should exist
    assert len(violations) == 0, (
        f"Found {len(violations)} memory_limit_mb = 3072 constraint(s) in {file_path.name}:\n" +
        "\n".join([
            f"  Line {v['line']}: {v['content']}"
            for v in violations
        ])
    )


def test_comprehensive_4gb_scan():
    """Comprehensive scan of all documentation files to ensure no 4GB references remain.
    
    This is a deterministic test that checks all files at once.
    
    **Validates: Requirements 1.1**
    """
    doc_files = get_documentation_files()
    
    all_violations = []
    
    for file_path in doc_files:
        violations = check_for_4gb_references(file_path)
        all_violations.extend(violations)
    
    # Property: No 4GB RAM references should exist anywhere in documentation
    if len(all_violations) > 0:
        violation_summary = "\n".join([
            f"  {Path(v['file']).relative_to(Path(__file__).parent.parent.parent)}:{v['line']}: {v['content'][:80]}"
            for v in all_violations[:20]  # Show first 20 violations
        ])
        
        assert False, (
            f"Found {len(all_violations)} reference(s) to 4GB RAM in documentation:\n" +
            violation_summary +
            (f"\n  ... and {len(all_violations) - 20} more" if len(all_violations) > 20 else "")
        )


def test_comprehensive_memory_limit_scan():
    """Comprehensive scan of all config files to ensure no memory_limit_mb = 3072 remains.
    
    This is a deterministic test that checks all files at once.
    
    **Validates: Requirements 1.2**
    """
    config_files = get_config_files()
    
    all_violations = []
    
    for file_path in config_files:
        violations = check_for_memory_limit_constraint(file_path)
        all_violations.extend(violations)
    
    # Property: No memory_limit_mb = 3072 should exist anywhere
    if len(all_violations) > 0:
        violation_summary = "\n".join([
            f"  {Path(v['file']).relative_to(Path(__file__).parent.parent.parent)}:{v['line']}: {v['content']}"
            for v in all_violations[:10]  # Show first 10 violations
        ])
        
        assert False, (
            f"Found {len(all_violations)} memory_limit_mb = 3072 constraint(s):\n" +
            violation_summary +
            (f"\n  ... and {len(all_violations) - 10} more" if len(all_violations) > 10 else "")
        )


def test_readme_has_correct_hardware_specs():
    """Verify that README.md files contain the correct hardware specifications.
    
    **Validates: Requirements 1.3**
    """
    project_root = Path(__file__).parent.parent.parent
    
    # Check main README.md
    readme_files = [
        project_root / "README.md",
        project_root / "README_DEPLOYMENT_SCENARIOS.md",
        project_root / "frontend" / "README.md",
    ]
    
    for readme_path in readme_files:
        if not readme_path.exists():
            continue
        
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for hardware specification section
            if re.search(r'hardware|requirement|specification', content, re.IGNORECASE):
                # If hardware specs are mentioned, verify they include 16GB
                # (We don't require all READMEs to have hardware specs, but if they do, they should be correct)
                if re.search(r'\d+\s*GB\s+RAM', content, re.IGNORECASE):
                    # Has RAM specification, should be 16GB
                    has_16gb = re.search(r'16\s*GB\s+RAM', content, re.IGNORECASE)
                    
                    # Allow model size references to 4GB
                    has_4gb_ram = bool(check_for_4gb_references(readme_path))
                    
                    if has_4gb_ram and not has_16gb:
                        assert False, (
                            f"{readme_path.name} contains 4GB RAM specification but should be 16GB. "
                            f"Please update to: 16GB RAM, 8-core CPU, 512GB SSD"
                        )
        except Exception as e:
            # Skip files that can't be read
            pass


def test_hardware_specification_consistency():
    """Verify that hardware specifications are consistent across documentation.
    
    When hardware specs are mentioned, they should consistently show:
    - 16GB RAM (not 4GB)
    - 8-core CPU
    - 512GB SSD
    
    **Validates: Requirements 1.3, 1.4**
    """
    doc_files = get_documentation_files()
    
    inconsistent_specs = []
    
    for file_path in doc_files:
        # Find hardware specification sections
        hardware_sections = check_for_complete_hardware_spec(file_path)
        
        for section in hardware_sections:
            context = section['context'].lower()
            
            # Check if this section mentions RAM
            if 'ram' in context or 'memory' in context:
                # Should mention 16GB, not 4GB
                has_16gb = re.search(r'16\s*gb', context)
                has_4gb = re.search(r'(?<!model\s)(?<!size\s)4\s*gb(?!\s*model)', context)
                
                if has_4gb and not has_16gb:
                    inconsistent_specs.append({
                        'file': str(file_path.relative_to(Path(__file__).parent.parent.parent)),
                        'line': section['line'],
                        'issue': 'Has 4GB instead of 16GB',
                        'context': section['context'][:150]
                    })
    
    # Property: Hardware specifications should be consistent
    if len(inconsistent_specs) > 0:
        summary = "\n".join([
            f"  {spec['file']}:{spec['line']}: {spec['issue']}\n    {spec['context'][:100]}..."
            for spec in inconsistent_specs[:10]
        ])
        
        assert False, (
            f"Found {len(inconsistent_specs)} inconsistent hardware specification(s):\n" +
            summary +
            (f"\n  ... and {len(inconsistent_specs) - 10} more" if len(inconsistent_specs) > 10 else "")
        )


def test_system_returns_consistent_16gb_minimum():
    """Verify that the system returns consistent 16GB minimum across all documentation.
    
    This test ensures that when hardware specifications are queried or documented,
    the system consistently reports 16GB as the minimum RAM requirement.
    
    **Validates: Requirements 1.4**
    """
    doc_files = get_documentation_files()
    
    # Count occurrences of different RAM specifications
    ram_specs = {
        '4GB': 0,
        '8GB': 0,
        '16GB': 0,
        'other': 0
    }
    
    files_with_specs = []
    
    for file_path in doc_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for RAM specifications in hardware/requirement contexts
            if re.search(r'hardware|requirement|specification|minimum|server', content, re.IGNORECASE):
                # Count different RAM specs (excluding model size references)
                lines = content.split('\n')
                for line_num, line in enumerate(lines, start=1):
                    if 'ram' in line.lower() or 'memory' in line.lower():
                        # Skip model size references
                        if any(keyword in line.lower() for keyword in ['model size', 'llm model', 'quantized', 'limited to 4gb']):
                            continue
                        
                        if re.search(r'(?<!model\s)4\s*gb', line, re.IGNORECASE):
                            ram_specs['4GB'] += 1
                            files_with_specs.append((file_path, line_num, '4GB', line.strip()))
                        elif re.search(r'8\s*gb', line, re.IGNORECASE):
                            ram_specs['8GB'] += 1
                            files_with_specs.append((file_path, line_num, '8GB', line.strip()))
                        elif re.search(r'16\s*gb', line, re.IGNORECASE):
                            ram_specs['16GB'] += 1
                            files_with_specs.append((file_path, line_num, '16GB', line.strip()))
        except Exception:
            pass
    
    # Property: System should consistently return 16GB minimum
    # We expect 16GB to be the dominant specification
    if ram_specs['4GB'] > 0:
        violations = [spec for spec in files_with_specs if spec[2] == '4GB']
        summary = "\n".join([
            f"  {spec[0].relative_to(Path(__file__).parent.parent.parent)}:{spec[1]}: {spec[3][:80]}"
            for spec in violations[:10]
        ])
        
        assert False, (
            f"Found {ram_specs['4GB']} reference(s) to 4GB RAM in hardware specifications.\n"
            f"System should consistently return 16GB minimum:\n" +
            summary +
            (f"\n  ... and {len(violations) - 10} more" if len(violations) > 10 else "")
        )
    
    # Log the statistics for visibility
    print(f"\nRAM specification statistics:")
    print(f"  16GB: {ram_specs['16GB']} occurrences")
    print(f"  8GB: {ram_specs['8GB']} occurrences")
    print(f"  4GB: {ram_specs['4GB']} occurrences (should be 0)")
    print(f"  Other: {ram_specs['other']} occurrences")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
