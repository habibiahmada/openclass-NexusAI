# API Server - Modular Structure Documentation

## 📋 Overview

API server telah direfactor dari monolithic file (1000+ lines) menjadi struktur modular yang lebih maintainable dan scalable.

## 🏗️ New Structure

```
api_server.py                    # Main entry point (clean & minimal)
│
src/api/
├── __init__.py
├── config.py                    # Centralized configuration
├── models.py                    # Pydantic models (request/response)
├── auth.py                      # Authentication & authorization
├── state.py                     # Application state management
│
└── routers/                     # API endpoints organized by domain
    ├── __init__.py
    ├── pages_router.py          # HTML pages (/, /siswa, /guru, /admin)
    ├── auth_router.py           # Authentication endpoints
    ├── chat_router.py           # Student chat interactions
    ├── teacher_router.py        # Teacher dashboard & reports
    ├── admin_router.py          # Admin panel & system management
    ├── pedagogy_router.py       # Student progress & practice
    └── queue_router.py          # Concurrency queue statistics
```

## 📦 Module Descriptions

### 1. `config.py` - Configuration Management
**Purpose:** Centralized configuration from environment variables

**Key Features:**
- All environment variables in one place
- Configuration validation
- Type-safe configuration access
- Default values for development

**Usage:**
```python
from src.api.config import config

print(config.HOST)  # 0.0.0.0
print(config.PORT)  # 8000
print(config.DATABASE_URL)
```

**Environment Variables:**
```bash
# Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key
TOKEN_EXPIRY_HOURS=24

# Database
DATABASE_URL=postgresql://...

# Performance
MAX_CONCURRENT_REQUESTS=5
MAX_QUEUE_SIZE=20
```

---

### 2. `models.py` - Data Models
**Purpose:** Pydantic models for request/response validation

**Models:**
- `LoginRequest`, `LoginResponse`
- `ChatRequest`, `ChatResponse`
- `TeacherStats`
- `AdminStatus`
- `QueueStats`
- `StudentProgress`, `WeakArea`, `PracticeQuestion`

**Benefits:**
- Automatic validation
- Type safety
- API documentation (OpenAPI/Swagger)
- Clear contracts between frontend/backend

---

### 3. `auth.py` - Authentication Service
**Purpose:** Handle user authentication and authorization

**Key Components:**
- `AuthService` class - Core authentication logic
- `generate_token()` - Secure token generation
- `hash_password()` - Password hashing
- `create_auth_dependency()` - FastAPI dependency for token verification
- `create_role_dependency()` - Role-based access control

**Usage:**
```python
from src.api.auth import AuthService, create_auth_dependency

auth_service = AuthService(session_repo, user_repo)
verify_token = create_auth_dependency(auth_service)

@router.get("/protected")
async def protected_route(token_data: Dict = Depends(verify_token)):
    return {"user": token_data['username']}
```

**Security Features:**
- SHA256 password hashing
- Secure token generation (secrets.token_urlsafe)
- Database-backed sessions
- Token expiration (24 hours default)
- Role-based access control

---

### 4. `state.py` - Application State
**Purpose:** Manage global application state and initialization

**Key Components:**
- `AppState` class - Global state container
- Component initialization (database, pipeline, concurrency, telemetry)
- Graceful degradation (components can fail independently)
- Shutdown cleanup

**State Components:**
```python
app_state.pipeline              # RAG pipeline
app_state.db_manager            # Database connection
app_state.session_repo          # Session repository
app_state.chat_history_repo     # Chat history repository
app_state.user_repo             # User repository
app_state.subject_repo          # Subject repository
app_state.pedagogical_integration  # Pedagogical engine
app_state.concurrency_manager   # Queue manager
app_state.telemetry_collector   # Metrics collector
```

**Initialization Flow:**
1. Database → Repositories
2. Pedagogical Engine (if DB available)
3. Concurrency Manager
4. Telemetry Collector
5. RAG Pipeline

---

### 5. Routers - API Endpoints

#### `pages_router.py` - HTML Pages
**Endpoints:**
- `GET /` - Landing page
- `GET /siswa` - Student page
- `GET /guru` - Teacher page
- `GET /admin` - Admin page

---

#### `auth_router.py` - Authentication
**Endpoints:**
- `POST /api/auth/login` - User login
- `POST /api/auth/verify` - Token verification
- `POST /api/auth/logout` - User logout

**Features:**
- Database-backed sessions
- Token expiration
- Role validation

---

#### `chat_router.py` - Student Chat
**Endpoints:**
- `POST /api/chat` - Synchronous chat
- `POST /api/chat/stream` - Streaming chat (SSE)

**Features:**
- RAG pipeline integration
- Concurrency queue management
- Database persistence
- Pedagogical tracking
- Telemetry recording
- Graceful degradation (demo mode if pipeline unavailable)

---

#### `teacher_router.py` - Teacher Dashboard
**Endpoints:**
- `GET /api/teacher/stats` - Dashboard statistics
- `GET /api/teacher/export` - Export reports (CSV/JSON)

**Features:**
- Aggregate statistics from database
- Topic analysis
- Active student tracking
- CSV export

---

#### `admin_router.py` - Admin Panel
**Endpoints:**
- `GET /api/admin/status` - System status
- `POST /api/admin/update-model` - Update AI model (placeholder)
- `POST /api/admin/update-curriculum` - Update curriculum (placeholder)
- `POST /api/admin/backup` - Create system backup

**Features:**
- System resource monitoring (RAM, disk)
- Backup creation
- Admin-only access (role-based)

---

#### `pedagogy_router.py` - Pedagogical Engine
**Endpoints:**
- `GET /api/student/progress` - Student progress summary
- `GET /api/student/weak-areas` - Weak areas detection
- `GET /api/student/practice-questions` - Adaptive practice questions
- `GET /api/student/{student_id}/report` - Teacher view of student (teacher/admin only)

**Features:**
- Mastery level tracking
- Weak area detection
- Adaptive question generation
- Teacher reporting

---

#### `queue_router.py` - Concurrency Queue
**Endpoints:**
- `GET /api/queue/stats` - Queue statistics

**Features:**
- Active request count
- Queued request count
- Queue capacity monitoring

---

## 🔄 Migration Guide

### Step 1: Backup
```bash
# Automatic backup via migration script
python scripts/migrate_to_modular_api.py
```

### Step 2: Update Environment Variables
Add new variables to `.env`:
```bash
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key-change-in-production
TOKEN_EXPIRY_HOURS=24
CORS_ORIGINS=*
MAX_CONCURRENT_REQUESTS=5
MAX_QUEUE_SIZE=20
```

### Step 3: Test
```bash
# Test the new modular server
python api_server.py
```

### Step 4: Verify
- Check all endpoints work
- Verify authentication
- Test chat functionality
- Check teacher dashboard
- Verify admin panel

---

## 🎯 Benefits of Modular Structure

### 1. **Maintainability**
- Each module has single responsibility
- Easy to locate and fix bugs
- Clear separation of concerns

### 2. **Scalability**
- Easy to add new routers
- Can split into microservices later
- Independent module testing

### 3. **Readability**
- Small, focused files (< 300 lines each)
- Clear module names
- Self-documenting structure

### 4. **Testability**
- Each module can be tested independently
- Mock dependencies easily
- Unit tests per module

### 5. **Reusability**
- Auth service can be reused
- State management is centralized
- Models are shared across routers

### 6. **Security**
- Centralized authentication
- Environment variable management
- No hardcoded secrets

---

## 🔒 Security Best Practices

### 1. **Environment Variables**
All sensitive data in `.env`:
- `SECRET_KEY` - Token signing
- `DATABASE_URL` - Database credentials
- `AWS_ACCESS_KEY_ID` - AWS credentials

### 2. **Password Hashing**
- SHA256 for demo users
- Should use bcrypt/argon2 in production

### 3. **Token Management**
- Secure random tokens (secrets.token_urlsafe)
- Database-backed sessions
- Automatic expiration

### 4. **Role-Based Access Control**
- `verify_token` - Any authenticated user
- `require_teacher` - Teacher or admin only
- `require_admin` - Admin only

---

## 📊 Performance Considerations

### 1. **Concurrency Management**
- Max 5 concurrent inference threads
- Queue for additional requests
- Prevents server overload

### 2. **Database Connection Pooling**
- Managed by DatabaseManager
- Automatic reconnection
- Health checks

### 3. **Graceful Degradation**
- Components can fail independently
- Demo mode if pipeline unavailable
- Fallback to synchronous processing

### 4. **Telemetry**
- Track query latency
- Monitor error rates
- Resource usage tracking

---

## 🧪 Testing

### Unit Tests (Recommended)
```python
# Test auth service
def test_verify_credentials():
    auth_service = AuthService(mock_session_repo, mock_user_repo)
    result = auth_service.verify_credentials("siswa", "siswa123", "siswa")
    assert result['success'] == True

# Test config validation
def test_config_validation():
    errors = config.validate()
    assert len(errors) == 0
```

### Integration Tests
```bash
# Test full API flow
pytest tests/integration/test_api_flow.py
```

### Load Tests
```bash
# Test concurrency limits
locust -f tests/load/locustfile.py
```

---

## 🐛 Troubleshooting

### Issue: "Database temporarily unavailable"
**Solution:** Check DATABASE_URL in `.env` and ensure PostgreSQL is running

### Issue: "RAG components not available"
**Solution:** Run ETL pipeline and download model:
```bash
python scripts/run_etl_pipeline.py
python scripts/download_model.py
```

### Issue: "Concurrency manager not available"
**Solution:** Check if concurrency module is installed and initialized

### Issue: Import errors
**Solution:** Ensure all modules are in correct locations and `__init__.py` files exist

---

## 📝 Future Enhancements

### 1. **Microservices Split**
- Auth service → Separate service
- Chat service → Separate service
- Admin service → Separate service

### 2. **API Versioning**
- `/api/v1/chat`
- `/api/v2/chat`

### 3. **WebSocket Support**
- Real-time chat streaming
- Live dashboard updates

### 4. **GraphQL API**
- Alternative to REST
- Flexible queries

### 5. **Rate Limiting**
- Per-user rate limits
- IP-based throttling

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Models](https://docs.pydantic.dev/)
- [Python Logging](https://docs.python.org/3/library/logging.html)
- [Environment Variables Best Practices](https://12factor.net/config)

---

**Last Updated:** 2026-02-20  
**Version:** 1.0.0  
**Maintainer:** Development Team
