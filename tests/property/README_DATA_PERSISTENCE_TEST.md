# Data Persistence Property Test - Setup Guide

## Overview

This document describes the property-based test for data persistence across restarts (Task 2.8).

**Property 3: Data Persistence Across Restarts**
- **Validates: Requirements 3.3**
- **Test File**: `tests/property/test_data_persistence.py`

## Test Description

The property test verifies that all data stored in the PostgreSQL database persists correctly across server restarts:

1. **User data** - usernames, passwords, roles, full names
2. **Session data** - authentication tokens, expiration times
3. **Chat history** - questions, responses, confidence scores
4. **Subject metadata** - subject names, codes, grades
5. **Book metadata** - titles, filenames, VKP versions

## Test Strategy

The test uses Hypothesis to generate random test data and follows this pattern:

1. **Phase 1: Create Data**
   - Create a database connection
   - Insert test data (users, sessions, chats, subjects, books)
   - Store the original data for comparison
   - Close the database connection (simulate shutdown)

2. **Phase 2: Simulate Restart**
   - Create a new database connection (simulates restart)
   - Query the database for the previously created data
   - Verify all data matches the original data
   - Clean up test data

3. **Verification**
   - All records must be retrievable after restart
   - All field values must match exactly
   - Referential integrity must be maintained

## Test Cases

### 1. `test_data_persists_across_restarts`
- **Iterations**: 100 (as specified in design)
- **Strategy**: Generates random user, session, chat, subject, and book data
- **Validates**: Single record persistence across one restart

### 2. `test_multiple_records_persist_across_restarts`
- **Iterations**: 100
- **Strategy**: Creates multiple users (1-10) with multiple chats each (1-5)
- **Validates**: Multiple records and referential integrity across restart

### 3. `test_data_persists_across_multiple_restarts`
- **Iterations**: 50
- **Strategy**: Creates data and simulates 2-5 consecutive restarts
- **Validates**: Long-term persistence reliability

## Prerequisites

### 1. PostgreSQL Installation
```bash
# Windows (using chocolatey)
choco install postgresql

# Or download from: https://www.postgresql.org/download/windows/
```

### 2. Create Test Database
```bash
# Create test database
createdb nexusai_test

# Or using psql
psql -U postgres -c "CREATE DATABASE nexusai_test;"
```

### 3. Apply Schema
```bash
# Apply the schema to test database
psql -U postgres -d nexusai_test -f database/schema.sql
```

### 4. Set Environment Variable
```bash
# Windows PowerShell
$env:TEST_DATABASE_URL="postgresql://postgres:your_password@localhost:5432/nexusai_test"

# Windows CMD
set TEST_DATABASE_URL=postgresql://postgres:your_password@localhost:5432/nexusai_test

# Linux/Mac
export TEST_DATABASE_URL="postgresql://postgres:your_password@localhost:5432/nexusai_test"
```

## Running the Tests

### Run All Data Persistence Tests
```bash
pytest tests/property/test_data_persistence.py -v
```

### Run Specific Test
```bash
pytest tests/property/test_data_persistence.py::test_data_persists_across_restarts -v
```

### Run with Hypothesis Statistics
```bash
pytest tests/property/test_data_persistence.py -v --hypothesis-show-statistics
```

### Run with Verbose Output
```bash
pytest tests/property/test_data_persistence.py -v -s
```

## Expected Output

When tests pass, you should see:
```
tests/property/test_data_persistence.py::test_data_persists_across_restarts PASSED [33%]
tests/property/test_data_persistence.py::test_multiple_records_persist_across_restarts PASSED [66%]
tests/property/test_data_persistence.py::test_data_persists_across_multiple_restarts PASSED [100%]

============= 3 passed in X.XXs =============
```

## Troubleshooting

### Tests Skipped
**Issue**: Tests show "SKIPPED (PostgreSQL test database not configured)"

**Solution**: Set the TEST_DATABASE_URL environment variable:
```bash
$env:TEST_DATABASE_URL="postgresql://postgres:password@localhost:5432/nexusai_test"
```

### Connection Refused
**Issue**: `psycopg2.OperationalError: could not connect to server`

**Solution**: 
1. Check if PostgreSQL is running:
   ```bash
   # Windows
   Get-Service postgresql*
   
   # Linux
   sudo systemctl status postgresql
   ```

2. Start PostgreSQL if not running:
   ```bash
   # Windows
   Start-Service postgresql-x64-XX
   
   # Linux
   sudo systemctl start postgresql
   ```

### Database Does Not Exist
**Issue**: `psycopg2.OperationalError: database "nexusai_test" does not exist`

**Solution**: Create the test database:
```bash
createdb nexusai_test
psql -U postgres -d nexusai_test -f database/schema.sql
```

### Authentication Failed
**Issue**: `psycopg2.OperationalError: FATAL: password authentication failed`

**Solution**: Update the connection string with correct credentials:
```bash
$env:TEST_DATABASE_URL="postgresql://postgres:YOUR_ACTUAL_PASSWORD@localhost:5432/nexusai_test"
```

### Schema Not Applied
**Issue**: `psycopg2.errors.UndefinedTable: relation "users" does not exist`

**Solution**: Apply the schema to the test database:
```bash
psql -U postgres -d nexusai_test -f database/schema.sql
```

## Test Data Cleanup

The tests automatically clean up after themselves by deleting created records. However, if tests fail or are interrupted, you may need to manually clean up:

```sql
-- Connect to test database
psql -U postgres -d nexusai_test

-- View test data
SELECT * FROM users WHERE username LIKE 'testuser_%';

-- Clean up test data (if needed)
DELETE FROM users WHERE username LIKE 'testuser_%';
DELETE FROM chat_history WHERE created_at < NOW() - INTERVAL '1 hour';
```

## Integration with CI/CD

For automated testing in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Setup PostgreSQL
  run: |
    sudo systemctl start postgresql
    sudo -u postgres createdb nexusai_test
    sudo -u postgres psql -d nexusai_test -f database/schema.sql

- name: Run Property Tests
  env:
    TEST_DATABASE_URL: postgresql://postgres:postgres@localhost:5432/nexusai_test
  run: |
    pytest tests/property/test_data_persistence.py -v
```

## Performance Notes

- Each test iteration creates and deletes records
- 100 iterations per test = ~300 total test cases
- Expected runtime: 30-60 seconds (depends on database performance)
- Tests use connection pooling for efficiency

## Design Document Reference

For detailed property specifications, see:
- **Design Document**: `.kiro/specs/architecture-alignment-refactoring/design.md`
- **Section**: "Property 3: Data Persistence Across Restarts"
- **Requirements**: Requirements 3.3 in `requirements.md`

## Related Files

- Test implementation: `tests/property/test_data_persistence.py`
- Database schema: `database/schema.sql`
- Database manager: `src/persistence/database_manager.py`
- User repository: `src/persistence/user_repository.py`
- Session repository: `src/persistence/session_repository.py`
- Chat history repository: `src/persistence/chat_history_repository.py`
- Subject repository: `src/persistence/subject_repository.py`
- Book repository: `src/persistence/book_repository.py`
