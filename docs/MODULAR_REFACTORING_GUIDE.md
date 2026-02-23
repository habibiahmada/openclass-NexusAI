# 🔄 Modular Refactoring Guide

## 📋 Ringkasan Perubahan

API server telah berhasil direfactor dari **monolithic file (1000+ baris)** menjadi **struktur modular** yang lebih maintainable, scalable, dan secure.

## ✅ Apa yang Sudah Dilakukan

### 1. **Pemisahan Kode Berdasarkan Fungsi**

**Sebelum:**
```
api_server.py (1000+ lines)
├── Imports
├── Configuration
├── Models
├── Authentication
├── State Management
├── All Endpoints
└── Main
```

**Sesudah:**
```
api_server.py (150 lines - clean entry point)
│
src/api/
├── config.py          # Configuration management
├── models.py          # Pydantic models
├── auth.py            # Authentication service
├── state.py           # Application state
│
└── routers/           # Organized endpoints
    ├── auth_router.py
    ├── chat_router.py
    ├── teacher_router.py
    ├── admin_router.py
    ├── pedagogy_router.py
    ├── queue_router.py
    └── pages_router.py
```

### 2. **Keamanan yang Ditingkatkan**

✅ **Semua rahasia dipindahkan ke `.env`:**
- `SECRET_KEY` - Token signing key
- `DATABASE_URL` - Database credentials
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` - AWS credentials
- `API_HOST` & `API_PORT` - Server configuration

✅ **Tidak ada hardcoded secrets** di kode

✅ **Centralized authentication** dengan `AuthService`

### 3. **Konfigurasi Terpusat**

Semua konfigurasi sekarang di `src/api/config.py`:
```python
from src.api.config import config

# Akses konfigurasi dengan mudah
print(config.HOST)
print(config.PORT)
print(config.DATABASE_URL)
```

### 4. **Modular Routers**

Setiap domain memiliki router sendiri:
- **Auth Router** - Login, logout, token verification
- **Chat Router** - Student chat interactions
- **Teacher Router** - Dashboard & reports
- **Admin Router** - System management
- **Pedagogy Router** - Student progress & practice
- **Queue Router** - Concurrency statistics
- **Pages Router** - HTML pages

### 5. **State Management yang Lebih Baik**

`AppState` class mengelola semua komponen global:
```python
from src.api.state import app_state

# Akses komponen
app_state.pipeline
app_state.db_manager
app_state.concurrency_manager
app_state.pedagogical_integration
```

## 🚀 Cara Menggunakan

### 1. **Menjalankan Server**

**Cara lama (masih berfungsi):**
```bash
python api_server.py
```

**Atau dengan launcher:**
```bash
# Windows
start_web_ui.bat

# Linux/Mac
./start_web_ui.sh
```

### 2. **Konfigurasi**

Edit file `.env` untuk mengubah konfigurasi:
```bash
# Server
API_HOST=0.0.0.0
API_PORT=8000

# Security
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/nexusai_db

# Performance
MAX_CONCURRENT_REQUESTS=5
MAX_QUEUE_SIZE=20
```

### 3. **Menambah Endpoint Baru**

**Contoh: Menambah endpoint baru di chat router**

Edit `src/api/routers/chat_router.py`:
```python
@router.get("/history")
async def get_chat_history(token_data: Dict = Depends(verify_token_dependency)):
    """Get user chat history"""
    # Implementation here
    return {"history": []}
```

### 4. **Menambah Router Baru**

1. Buat file baru: `src/api/routers/new_router.py`
2. Implementasi router:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/new", tags=["new"])

def create_new_router(state, verify_token):
    @router.get("/endpoint")
    async def new_endpoint():
        return {"message": "Hello"}
    
    return router
```

3. Register di `api_server.py`:
```python
from src.api.routers.new_router import create_new_router

new_router = create_new_router(app_state, verify_token)
app.include_router(new_router)
```

## 📊 Perbandingan

| Aspek | Sebelum | Sesudah |
|-------|---------|---------|
| **Lines per file** | 1000+ | < 300 |
| **Maintainability** | ❌ Sulit | ✅ Mudah |
| **Testability** | ❌ Sulit | ✅ Mudah |
| **Scalability** | ❌ Terbatas | ✅ Scalable |
| **Security** | ⚠️ Hardcoded | ✅ Environment vars |
| **Readability** | ❌ Sulit | ✅ Jelas |
| **Reusability** | ❌ Minimal | ✅ Tinggi |

## 🔍 Verifikasi

### 1. **Cek Struktur File**
```bash
python scripts/migrate_to_modular_api.py
```

Output harus menunjukkan semua file ✓

### 2. **Test Import**
```bash
python -c "from src.api.config import config; print('OK')"
python -c "from src.api.models import ChatRequest; print('OK')"
python -c "from src.api.auth import AuthService; print('OK')"
python -c "from src.api.state import AppState; print('OK')"
```

### 3. **Test Server**
```bash
# Dry run (tidak start server)
python -m py_compile api_server.py

# Start server
python api_server.py
```

### 4. **Test Endpoints**

**Health Check:**
```bash
curl http://localhost:8000/api/health
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"siswa","password":"siswa123","role":"siswa"}'
```

## 🐛 Troubleshooting

### Issue: Import Error
```
ModuleNotFoundError: No module named 'src.api'
```

**Solution:** Pastikan Anda menjalankan dari root directory project:
```bash
cd D:\Projects\NexusAI
python api_server.py
```

### Issue: Config Error
```
Configuration validation warnings
```

**Solution:** Periksa file `.env` dan pastikan semua variabel yang diperlukan ada.

### Issue: Database Error
```
Database temporarily unavailable
```

**Solution:** 
1. Pastikan PostgreSQL running
2. Periksa `DATABASE_URL` di `.env`
3. Test koneksi: `psql -U root -d nexusai_db`

### Issue: Port Already in Use
```
Address already in use
```

**Solution:** Ubah port di `.env`:
```bash
API_PORT=8001
```

## 📝 Backup & Rollback

### Backup Otomatis
Migration script otomatis membuat backup di:
```
backups/api_migration/api_server_backup_YYYYMMDD_HHMMSS.py
```

### Rollback Manual
Jika ada masalah, restore backup:
```bash
cp backups/api_migration/api_server_backup_20260222_141126.py api_server.py
```

## 🎯 Best Practices

### 1. **Jangan Hardcode Secrets**
❌ **Buruk:**
```python
DATABASE_URL = "postgresql://root:root@localhost/db"
```

✅ **Baik:**
```python
DATABASE_URL = os.getenv('DATABASE_URL')
```

### 2. **Gunakan Type Hints**
❌ **Buruk:**
```python
def process_chat(request):
    return {"response": "..."}
```

✅ **Baik:**
```python
def process_chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(response="...")
```

### 3. **Pisahkan Concerns**
❌ **Buruk:** Semua logic di satu file

✅ **Baik:** 
- Auth logic → `auth.py`
- Chat logic → `chat_router.py`
- Config → `config.py`

### 4. **Error Handling**
❌ **Buruk:**
```python
result = db.query()  # Bisa crash
```

✅ **Baik:**
```python
try:
    result = db.query()
except Exception as e:
    logger.error(f"Query failed: {e}")
    raise HTTPException(status_code=500)
```

## 📚 Dokumentasi Lengkap

Lihat dokumentasi lengkap di:
- [API_MODULAR_STRUCTURE.md](./API_MODULAR_STRUCTURE.md) - Struktur detail
- [ARCHITECTURE_ANALYSIS.md](../ARCHITECTURE_ANALYSIS.md) - Analisis arsitektur

## ✨ Fitur Baru yang Mudah Ditambahkan

Dengan struktur modular, fitur-fitur ini sekarang mudah ditambahkan:

1. **API Versioning** - `/api/v1/`, `/api/v2/`
2. **WebSocket Support** - Real-time chat
3. **Rate Limiting** - Per-user throttling
4. **Caching Layer** - Redis integration
5. **Microservices** - Split services independently
6. **GraphQL API** - Alternative to REST
7. **Monitoring Dashboard** - Metrics visualization
8. **A/B Testing** - Feature flags

## 🎉 Kesimpulan

Refactoring ini membuat codebase:
- ✅ **Lebih mudah dibaca** - File kecil, fokus
- ✅ **Lebih mudah di-maintain** - Perubahan terisolasi
- ✅ **Lebih aman** - No hardcoded secrets
- ✅ **Lebih scalable** - Easy to extend
- ✅ **Lebih testable** - Unit tests per module
- ✅ **Production-ready** - Best practices applied

---

**Tanggal Refactoring:** 2026-02-22  
**Status:** ✅ Completed & Tested  
**Backward Compatible:** ✅ Yes  
**Breaking Changes:** ❌ None
