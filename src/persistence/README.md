# Persistence Layer

This module provides database management and repository classes for persistent storage of user data, sessions, chat history, and metadata.

## DatabaseManager

The `DatabaseManager` class provides core database operations with connection pooling, query execution, transaction management, and health checks.

### Configuration

Connection pool settings:
- `POOL_SIZE`: 10 minimum connections
- `MAX_OVERFLOW`: 20 additional connections (30 total max)
- `POOL_TIMEOUT`: 30 seconds connection timeout
- `POOL_RECYCLE`: 3600 seconds (1 hour) connection recycle time

### Usage Examples

#### Basic Initialization

```python
from src.persistence.database_manager import DatabaseManager

# Initialize with connection string
db_manager = DatabaseManager(
    "postgresql://user:password@localhost:5432/nexusai"
)

# Check database health
if db_manager.health_check():
    print("Database is healthy")
```

#### Executing Queries

```python
# Execute SELECT query
users = db_manager.execute_query(
    "SELECT * FROM users WHERE role = %(role)s",
    {"role": "siswa"}
)

for user in users:
    print(f"User: {user['username']}")

# Fetch single result
user = db_manager.execute_query(
    "SELECT * FROM users WHERE id = %(id)s",
    {"id": 1},
    fetch_one=True
)
```

#### Executing Transactions

```python
# Execute multiple queries atomically
queries = [
    (
        "INSERT INTO users (username, password_hash, role) VALUES (%(username)s, %(password)s, %(role)s)",
        {"username": "student1", "password": "hash123", "role": "siswa"}
    ),
    (
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (%(user_id)s, %(token)s, NOW() + INTERVAL '24 hours')",
        {"user_id": 1, "token": "abc123"}
    )
]

success = db_manager.execute_transaction(queries)
if success:
    print("Transaction completed successfully")
```

#### Using Context Manager

```python
# Automatically closes pool on exit
with DatabaseManager("postgresql://...") as db:
    result = db.health_check()
    print(f"Health check: {result}")
```

#### Manual Connection Management

```python
# Get connection from pool
with db_manager.get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
```

### Error Handling

The DatabaseManager raises `psycopg2.Error` exceptions on database errors:

```python
import psycopg2

try:
    result = db_manager.execute_query("INVALID SQL")
except psycopg2.Error as e:
    print(f"Database error: {e}")
```

### Graceful Degradation

If PostgreSQL is unavailable:
1. Log error with stack trace
2. Return HTTP 503 Service Unavailable
3. Display user-friendly message: "Database temporarily unavailable"
4. Do NOT fallback to in-memory (data loss risk)
5. Health monitor attempts auto-restart

### Requirements

- PostgreSQL 12 or later
- psycopg2-binary >= 2.9.9

### Related Components

- `UserRepository`: User CRUD operations
- `SessionRepository`: Session management
- `ChatHistoryRepository`: Chat history persistence
- `SubjectRepository`: Subject management
- `BookRepository`: Curriculum book metadata

See design document for complete architecture details.
