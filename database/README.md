# Database Schema Documentation

This directory contains the PostgreSQL database schema for OpenClass Nexus AI.

## Overview

The database schema supports:
- User authentication and session management
- Dynamic curriculum management (subjects and books)
- Complete chat history persistence
- Pedagogical intelligence engine (mastery tracking, weak area detection)
- Adaptive practice question generation

## Schema File

- `schema.sql` - Complete PostgreSQL schema with tables, indexes, and constraints

## Tables

### Core User Management

1. **users** - User accounts (students, teachers, administrators)
   - Primary key: `id`
   - Unique constraint: `username`
   - Roles: `siswa` (student), `guru` (teacher), `admin`
   - Password security: SHA256 hashing

2. **sessions** - Authentication tokens
   - Primary key: `id`
   - Foreign key: `user_id` → `users(id)`
   - Expiration: 24 hours from creation
   - Automatic cleanup of expired sessions

### Curriculum Management

3. **subjects** - Subject metadata
   - Primary key: `id`
   - Unique constraint: `code`
   - Grades: 10-12 (CHECK constraint)
   - Examples: "MAT_10" (Matematika Kelas 10), "INF_11" (Informatika Kelas 11)

4. **books** - Curriculum books
   - Primary key: `id`
   - Foreign key: `subject_id` → `subjects(id)`
   - VKP version tracking (semantic versioning)
   - Chunk count for monitoring

### Chat History

5. **chat_history** - Student-AI interactions
   - Primary key: `id`
   - Foreign keys: `user_id` → `users(id)`, `subject_id` → `subjects(id)`
   - Stores complete question-response pairs
   - Confidence scores for quality monitoring
   - Indexed by user, subject, and timestamp

### Pedagogical Intelligence Engine

6. **topic_mastery** - Student mastery tracking
   - Primary key: `id`
   - Foreign keys: `user_id` → `users(id)`, `subject_id` → `subjects(id)`
   - Mastery level: 0.0 (novice) to 1.0 (expert)
   - Unique constraint: (user_id, subject_id, topic)
   - Tracks question count and correct responses

7. **weak_areas** - Weak area detection
   - Primary key: `id`
   - Foreign keys: `user_id` → `users(id)`, `subject_id` → `subjects(id)`
   - Weakness score calculation
   - Recommended practice activities

8. **practice_questions** - Adaptive practice questions
   - Primary key: `id`
   - Foreign key: `subject_id` → `subjects(id)`
   - Difficulty levels: easy, medium, hard
   - Topic-based organization

## Installation

### Prerequisites

- PostgreSQL 12 or later
- Database user with CREATE privileges

### Setup Instructions

1. **Create Database**
   ```bash
   createdb nexusai
   ```

2. **Apply Schema**
   ```bash
   psql -U postgres -d nexusai -f database/schema.sql
   ```

3. **Verify Installation**
   ```bash
   psql -U postgres -d nexusai -c "\dt"
   ```

   Expected output: 8 tables (users, sessions, subjects, books, chat_history, topic_mastery, weak_areas, practice_questions)

4. **Check Indexes**
   ```bash
   psql -U postgres -d nexusai -c "\di"
   ```

   Expected output: 8 indexes for performance optimization

## Connection Configuration

Update your application configuration with database connection details:

```python
# config/app_config.py or .env
DATABASE_URL = "postgresql://username:password@localhost:5432/nexusai"
```

## Performance Optimization

The schema includes the following indexes for optimal performance:

- **Chat History**: `user_id`, `created_at`, `subject_id`
- **Sessions**: `token`, `expires_at`
- **Topic Mastery**: `(user_id, subject_id)`
- **Weak Areas**: `(user_id, subject_id)`
- **Practice Questions**: `(subject_id, topic)`

## Data Retention

- **Chat History**: Unlimited retention (for learning analytics)
- **Sessions**: Automatic expiration after 24 hours
- **Topic Mastery**: Persistent (tracks long-term progress)
- **Weak Areas**: Updated dynamically based on recent interactions

## Security Considerations

1. **Password Storage**: All passwords are SHA256 hashed before storage
2. **Session Management**: Tokens expire after 24 hours of inactivity
3. **Data Privacy**: Chat history stored locally only (never sent to AWS)
4. **Access Control**: Role-based access (siswa, guru, admin)
5. **SQL Injection Prevention**: Use parameterized queries in application code

## Backup and Recovery

Recommended backup strategy:
- **Full Backup**: Weekly (Sunday 2 AM)
- **Incremental Backup**: Daily (Monday-Saturday 2 AM)
- **Retention**: 28 days

```bash
# Full backup
pg_dump -U postgres nexusai > backup_$(date +%Y%m%d).sql

# Restore
psql -U postgres -d nexusai < backup_20250115.sql
```

## Migration Notes

This schema replaces the previous in-memory storage:
- `active_tokens` dict → `sessions` table
- `state.chat_logs` list → `chat_history` table
- Dynamic subjects and books (no hardcoded data)

## Entity Relationship Diagram

```
users (1) ──── (N) sessions
users (1) ──── (N) chat_history
users (1) ──── (N) topic_mastery
users (1) ──── (N) weak_areas

subjects (1) ──── (N) books
subjects (1) ──── (N) chat_history
subjects (1) ──── (N) topic_mastery
subjects (1) ──── (N) weak_areas
subjects (1) ──── (N) practice_questions
```

## Troubleshooting

### Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U postgres -d nexusai -c "SELECT 1;"
```

### Permission Issues

```bash
# Grant privileges to application user
psql -U postgres -d nexusai -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nexusai_user;"
psql -U postgres -d nexusai -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nexusai_user;"
```

### Performance Issues

```bash
# Analyze query performance
psql -U postgres -d nexusai -c "EXPLAIN ANALYZE SELECT * FROM chat_history WHERE user_id = 1;"

# Rebuild indexes
psql -U postgres -d nexusai -c "REINDEX DATABASE nexusai;"
```

## References

- Design Document: `.kiro/specs/architecture-alignment-refactoring/design.md`
- Requirements: `.kiro/specs/architecture-alignment-refactoring/requirements.md` (Requirement 3.1)
- Architecture: `README_DEPLOYMENT_SCENARIOS.md`
