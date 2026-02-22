"""
OpenClass Nexus AI - FastAPI Backend Server
Modular web-based local server untuk akses multi-user via browser

This is the main entry point for the API server.
All business logic has been modularized into separate modules.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import configuration
from src.api.config import config

# Import state management
from src.api.state import app_state

# Import authentication
from src.api.auth import AuthService, create_auth_dependency, create_role_dependency

# Import routers
from src.api.routers.pages_router import create_pages_router
from src.api.routers.auth_router import create_auth_router
from src.api.routers.chat_router import create_chat_router
from src.api.routers.teacher_router import create_teacher_router
from src.api.routers.admin_router import create_admin_router
from src.api.routers.pedagogy_router import create_pedagogy_router
from src.api.routers.queue_router import create_queue_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===========================
# Initialize FastAPI App
# ===========================
app = FastAPI(
    title="OpenClass Nexus AI API",
    description="Local AI Tutor API untuk Kurikulum Nasional",
    version="1.0.0",
    debug=config.DEBUG
)

# ===========================
# CORS Middleware
# ===========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================
# Mount Static Files
# ===========================
if config.FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(config.FRONTEND_DIR)), name="static")
else:
    logger.warning(f"Frontend directory not found: {config.FRONTEND_DIR}")

# ===========================
# Startup Event
# ===========================
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("=" * 60)
    logger.info("OpenClass Nexus AI - Starting Server")
    logger.info("=" * 60)
    
    # Validate configuration
    config_errors = config.validate()
    if config_errors:
        logger.warning("Configuration validation warnings:")
        for error in config_errors:
            logger.warning(f"  - {error}")
    
    # Initialize application state
    try:
        app_state.initialize()
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}", exc_info=True)
        logger.info("Server starting in demo mode")
    
    logger.info("=" * 60)
    logger.info(f"Server running at: http://{config.HOST}:{config.PORT}")
    logger.info("=" * 60)

# ===========================
# Shutdown Event
# ===========================
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down server...")
    app_state.shutdown()
    logger.info("Server shutdown complete")

# ===========================
# Health Check Endpoint
# ===========================
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "initialized": app_state.is_initialized,
        "database": app_state.db_initialized,
        "concurrency": app_state.concurrency_initialized,
        "pedagogy": app_state.pedagogy_initialized,
        "telemetry": app_state.telemetry_initialized,
        "version": "1.0.0"
    }

# ===========================
# Initialize Authentication Service
# ===========================
auth_service = AuthService(
    session_repo=app_state.session_repo,
    user_repo=app_state.user_repo
)

# Create authentication dependencies
verify_token = create_auth_dependency(auth_service)
require_teacher = create_role_dependency(['guru', 'admin'], auth_service)
require_admin = create_role_dependency(['admin'], auth_service)

# ===========================
# Register Routers
# ===========================

# Pages router (HTML pages)
pages_router = create_pages_router()
app.include_router(pages_router)

# Authentication router
auth_router = create_auth_router(auth_service, verify_token)
app.include_router(auth_router)

# Chat router (student interactions)
chat_router = create_chat_router(app_state, verify_token)
app.include_router(chat_router)

# Teacher router (dashboard and reports)
teacher_router = create_teacher_router(app_state, verify_token)
app.include_router(teacher_router)

# Admin router (system management)
admin_router = create_admin_router(app_state, require_admin)
app.include_router(admin_router)

# Pedagogy router (student progress and practice)
pedagogy_router = create_pedagogy_router(app_state, verify_token, require_teacher)
app.include_router(pedagogy_router)

# Queue router (concurrency statistics)
queue_router = create_queue_router(app_state, verify_token)
app.include_router(queue_router)

# ===========================
# Run Server
# ===========================
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("OpenClass Nexus AI - Local Server")
    print("=" * 60)
    print(f"Server akan berjalan di: http://{config.HOST}:{config.PORT}")
    print("Buka browser dan akses URL di atas")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower()
    )
