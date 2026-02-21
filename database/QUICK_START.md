# Quick Start Guide - Database Setup

This guide will help you set up the PostgreSQL database for OpenClass Nexus AI in under 5 minutes.

## Prerequisites

- PostgreSQL 12+ installed
- Python 3.9+ with psycopg2 package

## Installation Steps

### Option 1: Automated Setup (Recommended)

```bash
# Install psycopg2 if not already installed
pip install psycopg2-binary

# Set database credentials (optional, defaults to localhost/postgres)
export DB_HOST=127.0.0.1
export DB_PORT=5432
export DB_NAME=nexusai
export DB_USER=root
export DB_PASSWORD=root

# Run complete setup (creates database, applies schema, seeds data)
python database/init_database.py --all
```

### Option 2: Manual Setup

```bash
# 1. Create database
createdb nexusai

# 2. Apply schema
psql -U postgres -d nexusai -f database/schema.sql

# 3. Verify installation
psql -U postgres -d nexusai -c "\dt"
```

## Verification

After installation, verify the setup:

```bash
python database/init_database.py --verify
```

Expected output:
```
✓ Tables: 8/8
✓ Indexes: 8+
✓ Users: 3
✓ Subjects: 6
```

## Test Credentials

After seeding, you can use these credentials for testing:

| Role    | Username | Password  |
|---------|----------|-----------|
| Admin   | admin    | admin123  |
| Teacher | guru1    | guru123   |
| Student | siswa1   | siswa123  |

**⚠️ IMPORTANT**: Change these passwords in production!

## Connection String

Update your application configuration:

```python
# .env file
DATABASE_URL=postgresql://postgres:password@localhost:5432/nexusai
```

Or in Python:

```python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='nexusai',
    user='postgres',
    password='your_password'
)
```

## Common Commands

### Check Database Status
```bash
psql -U postgres -d nexusai -c "SELECT COUNT(*) FROM users;"
```

### View All Tables
```bash
psql -U postgres -d nexusai -c "\dt"
```

### View Table Structure
```bash
psql -U postgres -d nexusai -c "\d users"
```

### Backup Database
```bash
pg_dump -U postgres nexusai > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
psql -U postgres -d nexusai < backup_20250115.sql
```

## Troubleshooting

### Connection Refused
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql
```

### Permission Denied
```bash
# Grant privileges to user
psql -U postgres -d nexusai -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;"
```

### Schema Already Exists
```bash
# Drop and recreate database (⚠️ destroys all data)
dropdb nexusai
createdb nexusai
psql -U postgres -d nexusai -f database/schema.sql
```

## Next Steps

1. ✅ Database installed
2. ⏭️ Implement DatabaseManager class (Task 2.2)
3. ⏭️ Implement Repository classes (Tasks 2.3-2.6)
4. ⏭️ Replace in-memory storage (Task 2.7)

## Support

For issues or questions:
- Check `database/README.md` for detailed documentation
- Review design document: `.kiro/specs/architecture-alignment-refactoring/design.md`
- See requirements: `.kiro/specs/architecture-alignment-refactoring/requirements.md` (Requirement 3.1)
