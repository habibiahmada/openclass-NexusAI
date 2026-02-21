# Database Setup Instructions

## Prerequisites
- PostgreSQL 12 or later installed
- PostgreSQL service running

## Setup Steps

### 1. Create Database User
```bash
# On Linux/Mac
sudo -u postgres psql -c "CREATE USER nexusai WITH PASSWORD 'nexusai123';"

# On Windows (run in psql as postgres user)
CREATE USER nexusai WITH PASSWORD 'nexusai123';
```

### 2. Create Database
```bash
# On Linux/Mac
sudo -u postgres psql -c "CREATE DATABASE nexusai_db OWNER nexusai;"

# On Windows (run in psql as postgres user)
CREATE DATABASE nexusai_db OWNER nexusai;
```

### 3. Grant Privileges
```bash
# On Linux/Mac
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE nexusai_db TO nexusai;"

# On Windows (run in psql as postgres user)
GRANT ALL PRIVILEGES ON DATABASE nexusai_db TO nexusai;
```

### 4. Run Schema Creation
```bash
# Connect to the database and run the schema
psql -U nexusai -d nexusai_db -f database/schema.sql

# Or on Windows
psql -U nexusai -d nexusai_db -f database\schema.sql
```

### 5. Verify Setup
```bash
# Test connection
python -c "import psycopg2; import os; from dotenv import load_dotenv; load_dotenv(); conn = psycopg2.connect(os.getenv('DATABASE_URL')); print('Database connection successful'); conn.close()"
```

## Environment Configuration

Make sure your `.env` file contains:
```
DATABASE_URL=postgresql://nexusai:nexusai123@localhost:5432/nexusai_db
```

## Troubleshooting

### Connection Refused
- Ensure PostgreSQL service is running
- Check if PostgreSQL is listening on port 5432

### Authentication Failed
- Verify username and password in DATABASE_URL
- Check pg_hba.conf for authentication method

### Database Does Not Exist
- Run the database creation commands above
- Verify database name matches DATABASE_URL

## Testing Database Integration

After setup, test the API server:
```bash
python api_server.py
```

Then test login:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "siswa", "password": "siswa123", "role": "siswa"}'
```

The response should include a token, and the session should be stored in the database.
