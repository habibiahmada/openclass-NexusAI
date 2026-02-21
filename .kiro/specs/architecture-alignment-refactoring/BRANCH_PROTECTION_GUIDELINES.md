# Branch Protection Guidelines

## Overview

This document outlines the Git branching strategy and protection rules for the Architecture Alignment Refactoring project.

## Branch Structure

### Main Branch
- **Branch:** `main`
- **Purpose:** Production-ready code
- **Protection:** 
  - Requires pull request reviews
  - All tests must pass before merge
  - No direct commits allowed

### Phase Branches
Each refactoring phase has its own branch following the naming convention:
- `refactoring/phase-0-preparation`
- `refactoring/phase-1-folder-restructuring`
- `refactoring/phase-2-database-persistence`
- `refactoring/phase-3-aws-infrastructure`
- `refactoring/phase-4-vkp-pull`
- `refactoring/phase-5-pedagogy`
- `refactoring/phase-6-resilience`
- `refactoring/phase-7-documentation`

**Protection Rules:**
- Each phase branch is created from the previous phase (or main for phase-0)
- All tests must pass before committing
- Backward compatibility must be maintained
- Each phase is committed as a complete unit

## Branching Workflow

### Phase Execution Flow

```
main
  └─> refactoring/phase-0-preparation
        └─> refactoring/phase-1-folder-restructuring
              └─> refactoring/phase-2-database-persistence
                    └─> ... (subsequent phases)
```

### Step-by-Step Process

1. **Start Phase:**
   ```bash
   git checkout -b refactoring/phase-N-name
   ```

2. **Implement Phase:**
   - Make incremental changes
   - Run tests after each significant change
   - Commit frequently with descriptive messages

3. **Verify Phase:**
   ```bash
   # Run full test suite
   pytest tests/ -v
   
   # Verify backward compatibility
   # Check all existing functionality still works
   ```

4. **Complete Phase:**
   ```bash
   # Add all changes
   git add .
   
   # Commit with template
   git commit
   # (Template will open - fill in details)
   ```

5. **Merge to Next Phase or Main:**
   ```bash
   # For final phase, merge to main
   git checkout main
   git merge refactoring/phase-N-name
   
   # For intermediate phases, create next phase branch
   git checkout -b refactoring/phase-N+1-name
   ```

## Commit Message Template

A commit message template (`.gitmessage`) has been configured to ensure consistent formatting:

### Template Structure
```
# Refactoring: [Phase Name] - [Component/Module]
#
# Type: [feat|fix|refactor|docs|test|chore]
# Phase: [0-7] - [Phase Name]
# Component: [Affected component or module]
#
# Description:
# - What was changed
# - Why it was changed
# - Impact on system
#
# Requirements: [Requirement numbers]
# Tests: [Pass/Fail] - [Test suite or specific tests run]
# Backward Compatible: [Yes/No]
```

### Example Commit Message
```
refactor: Phase 1 - Rename local_inference to edge_runtime

Type: refactor
Phase: 1 - Folder Restructuring
Component: src/edge_runtime/

Description:
- Renamed src/local_inference/ to src/edge_runtime/
- Updated all import statements across codebase
- Preserved Git history using git mv

Requirements: 2.1, 2.4, 2.6
Tests: Pass - All 45 tests passing
Backward Compatible: Yes
```

## Branch Protection Rules (For Repository Administrators)

### Recommended GitHub/GitLab Settings

**Main Branch:**
- ✅ Require pull request reviews before merging (1 reviewer minimum)
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Include administrators in restrictions
- ✅ Require linear history
- ❌ Allow force pushes
- ❌ Allow deletions

**Phase Branches:**
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Allow force pushes (for phase development only)
- ❌ Allow deletions (until phase is merged)

### Status Checks Required

All branches must pass these checks before merging:
1. **Unit Tests:** All unit tests must pass
2. **Integration Tests:** All integration tests must pass
3. **Linting:** Code must pass PEP 8 style checks
4. **Type Checking:** Type hints must be valid (if using mypy)
5. **Coverage:** Test coverage must be ≥ 70% for critical paths

## Rollback Strategy

### If Phase Fails

If a phase introduces breaking changes or fails tests:

1. **Immediate Rollback:**
   ```bash
   # Revert to previous phase
   git checkout refactoring/phase-N-1-name
   
   # Create new branch to fix issues
   git checkout -b refactoring/phase-N-name-fix
   ```

2. **Investigate and Fix:**
   - Identify root cause of failure
   - Implement fix
   - Re-run all tests

3. **Retry Phase:**
   ```bash
   # Once fixed, merge back to phase branch
   git checkout refactoring/phase-N-name
   git merge refactoring/phase-N-name-fix
   ```

### Emergency Rollback to Main

If critical issues are discovered after merge:

```bash
# Create rollback branch
git checkout main
git checkout -b rollback/phase-N-emergency

# Revert the merge commit
git revert -m 1 <merge-commit-hash>

# Test thoroughly
pytest tests/ -v

# Merge rollback
git checkout main
git merge rollback/phase-N-emergency
```

## Testing Requirements

### Before Each Commit

```bash
# Run quick tests
pytest tests/ -v --tb=short

# Check for obvious errors
python -m py_compile src/**/*.py
```

### Before Phase Completion

```bash
# Run full test suite
pytest tests/ -v --cov=src --cov-report=term-missing

# Run integration tests
pytest tests/integration/ -v

# Manual verification
# - Test key user workflows
# - Verify backward compatibility
# - Check system startup and shutdown
```

### Before Merge to Main

```bash
# Full regression testing
pytest tests/ -v --cov=src --cov-report=html

# Load testing (if applicable)
# Performance benchmarking
# Security scanning
```

## Backward Compatibility Checklist

Before completing each phase, verify:

- [ ] All existing API endpoints still work
- [ ] All existing CLI commands still work
- [ ] All existing configuration files are compatible
- [ ] All existing data formats are supported
- [ ] No breaking changes to public interfaces
- [ ] Migration path provided for any schema changes
- [ ] Documentation updated for any new features

## Phase Completion Criteria

A phase is considered complete when:

1. ✅ All phase tasks are implemented
2. ✅ All tests pass (100% of existing tests)
3. ✅ New tests added for new functionality
4. ✅ Code coverage ≥ 70% for critical paths
5. ✅ Backward compatibility verified
6. ✅ Documentation updated
7. ✅ Commit message follows template
8. ✅ No merge conflicts with base branch
9. ✅ Performance benchmarks meet requirements
10. ✅ Security review completed (if applicable)

## Git Configuration

### Local Configuration

The following Git configuration has been applied:

```bash
# Commit message template
git config commit.template .gitmessage

# Optional: Set default branch name
git config init.defaultBranch main

# Optional: Enable auto-rebase
git config pull.rebase true
```

### Recommended Global Configuration

```bash
# User identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Editor for commit messages
git config --global core.editor "code --wait"  # VS Code
# or
git config --global core.editor "vim"  # Vim

# Diff and merge tools
git config --global merge.tool vscode
git config --global diff.tool vscode
```

## Troubleshooting

### Common Issues

**Issue: Merge conflicts during phase merge**
```bash
# Resolve conflicts manually
git status  # See conflicting files
# Edit files to resolve conflicts
git add <resolved-files>
git commit
```

**Issue: Tests fail after merge**
```bash
# Identify failing tests
pytest tests/ -v --tb=short

# Fix issues
# Re-run tests
pytest tests/ -v

# Commit fixes
git add .
git commit -m "fix: Resolve test failures after merge"
```

**Issue: Accidentally committed to wrong branch**
```bash
# Move commit to correct branch
git log  # Find commit hash
git checkout correct-branch
git cherry-pick <commit-hash>
git checkout wrong-branch
git reset --hard HEAD~1
```

## References

- **Requirements Document:** `.kiro/specs/architecture-alignment-refactoring/requirements.md`
- **Design Document:** `.kiro/specs/architecture-alignment-refactoring/design.md`
- **Tasks Document:** `.kiro/specs/architecture-alignment-refactoring/tasks.md`
- **Requirement 13.3:** Incremental Refactoring Process with Git branching

## Maintenance

This document should be updated:
- When new phases are added
- When branch protection rules change
- When testing requirements evolve
- When rollback procedures are refined

---

**Last Updated:** 2025-01-15
**Version:** 1.0.0
**Maintained By:** Development Team
