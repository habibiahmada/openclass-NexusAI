# Streamlit to FastAPI Migration Guide

## Overview

OpenClass Nexus AI has migrated from Streamlit to FastAPI with HTML/CSS/JS frontend for better multi-user support and school deployment.

## What Changed

### Removed Components

1. **Streamlit Dependency**
   - Removed from `requirements.txt`
   - No longer needed for installation

2. **Streamlit UI Files** (Archived)
   - `app.py` → `app.py.legacy`
   - `src/ui/` → `src/ui_legacy/`

### New Architecture

```
Old (Streamlit):
User → Streamlit UI (app.py) → RAG Pipeline

New (FastAPI):
User → Browser → FastAPI Server (api_server.py) → RAG Pipeline
```

## Migration for Developers

### Old Way (Deprecated)

```bash
# Install with Streamlit
pip install -r requirements.txt

# Run Streamlit app
streamlit run app.py
```

### New Way (Current)

```bash
# Install without Streamlit
pip install -r requirements.txt

# Run FastAPI server
python api_server.py
# or
start_web_ui.bat
```

## Benefits of Migration

### 1. Better Multi-User Support
- Streamlit: Single-user sessions, limited concurrency
- FastAPI: True multi-user with concurrent request handling

### 2. School LAN Deployment
- Streamlit: Each user needs separate session
- FastAPI: Single server, multiple browser clients

### 3. Performance
- Streamlit: Reruns entire script on interaction
- FastAPI: Efficient request-response cycle

### 4. Resource Usage
- Streamlit: Higher memory per user
- FastAPI: Shared resources, better scaling

### 5. Customization
- Streamlit: Limited UI customization
- FastAPI: Full control with HTML/CSS/JS

## API Endpoints

### Pages (HTML)
- `GET /` - Landing page
- `GET /siswa` - Student interface
- `GET /guru` - Teacher dashboard
- `GET /admin` - Admin panel

### API Routes
- `POST /api/auth/login` - User authentication
- `POST /api/chat` - Chat with AI
- `GET /api/student/progress` - Student progress
- `GET /api/teacher/dashboard` - Teacher analytics
- `GET /api/admin/status` - System status

## Frontend Structure

```
frontend/
├── index.html          # Landing page
├── pages/
│   ├── siswa.html     # Student interface
│   ├── guru.html      # Teacher dashboard
│   └── admin.html     # Admin panel
├── css/
│   └── styles.css     # Shared styles
└── js/
    ├── auth.js        # Authentication
    ├── chat.js        # Chat functionality
    └── api.js         # API client
```

## Legacy Code

Legacy Streamlit code is preserved for reference:
- `app.py.legacy` - Old Streamlit entry point
- `src/ui_legacy/` - Old Streamlit components

These files are archived and not used in production.

## Troubleshooting

### Issue: "streamlit: command not found"
**Solution:** Streamlit is no longer needed. Use `python api_server.py` instead.

### Issue: "Cannot import streamlit"
**Solution:** This is expected. The application no longer uses Streamlit.

### Issue: "Port 8501 not responding"
**Solution:** Streamlit used port 8501. FastAPI uses port 8000. Access http://localhost:8000

## For Contributors

If you're contributing to the project:

1. **Don't use Streamlit** - All UI development should be in HTML/CSS/JS
2. **Use FastAPI routers** - Add new endpoints in `src/api/routers/`
3. **Follow REST principles** - Use proper HTTP methods and status codes
4. **Test with multiple users** - Ensure concurrent access works

## Questions?

See:
- [Developer Guide](development/DEVELOPER_GUIDE.md)
- [API Documentation](technical/API_MODULAR_STRUCTURE.md)
- [System Architecture](architecture/SYSTEM_ARCHITECTURE.md)

---

**Migration Date:** February 23, 2026  
**Status:** Complete  
**Streamlit Version (deprecated):** 1.28.0  
**FastAPI Version (current):** 0.104.0+
