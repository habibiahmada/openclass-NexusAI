# Database Schema Documentation

PostgreSQL database schema untuk OpenClass Nexus AI.

## Quick Setup

### Automated (Recommended)
```bash
# Install dependencies
pip install psycopg2-binary

# Set credentials (optional)
export DB_HOST=127.0.0.1
export DB_NAME=nexusai_db
export DB_USER=root
export DB_PASSWORD=root

# Run complete setup
python database/init_database.py --all
```

### Manual Setup
```bash
# 1. Create database
createdb nexusai_db

# 2. Apply schema
psql -U postgres -d nexusai_db -f database/schema.sql

# 3. Verify
psql -U postgres -d nexusai_db -c "\dt"
```

## Configuration

Update `.env` file:
```env
DATABASE_URL=postgresql://root:root@127.0.0.1:5432/nexusai_db
```

## Tables

### Core Tables
1. **users** - User accounts (siswa, guru, admin)
2. **sessions** - Authentication tokens (24h expiration)
3. **subjects** - Subject metadata (grade 10-12)
4. **books** - Curriculum books with VKP versioning
5. **chat_history** - Student-AI interactions
6. **topic_mastery** - Student mastery tracking (0.0-1.0)
7. **weak_areas** - Weak area detection
8. **practice_questions** - Adaptive practice questions

## Test Credentials

After seeding with `--seed-data`:

| Role    | Username | Password  |
|---------|----------|-----------|
| Admin   | admin    | admin123  |
| Teacher | guru1    | guru123   |
| Student | siswa1   | siswa123  |

⚠️ Change in production!

## Common Commands

```bash
# Verify installation
python database/init_database.py --verify

# Check tables
psql -U postgres -d nexusai_db -c "\dt"

# Backup
pg_dump -U postgres nexusai_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U postgres -d nexusai_db < backup.sql
```

## Troubleshooting

### Connection Refused
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### Permission Denied
```bash
psql -U postgres -d nexusai_db -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;"
```

### Reset Database
```bash
dropdb nexusai_db
createdb nexusai_db
psql -U postgres -d nexusai_db -f database/schema.sql
```

## Performance

Indexes optimized for:
- Chat history queries (user_id, created_at, subject_id)
- Session lookups (token, expires_at)
- Topic mastery (user_id, subject_id)
- Practice questions (subject_id, topic)

## Security

- Passwords: SHA256 hashed
- Sessions: 24h auto-expiration
- Chat history: Local only (never sent to AWS)
- Access control: Role-based (siswa, guru, admin)

## Backup Strategy

Recommended:
- Full backup: Weekly (Sunday 2 AM)
- Incremental: Daily (Monday-Saturday 2 AM)
- Retention: 28 days

```bash
# Automated backup
pg_dump -U postgres nexusai_db > backup_$(date +%Y%m%d).sql
```
