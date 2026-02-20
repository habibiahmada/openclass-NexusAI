"""
OpenClass Nexus AI - FastAPI Backend Server
Web-based local server untuk akses multi-user via browser
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path
import secrets
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import existing components (with error handling)
try:
    from src.local_inference.complete_pipeline import CompletePipeline, PipelineConfig
    RAG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RAG components not available: {e}")
    logger.warning("Server will run in demo mode without AI functionality")
    CompletePipeline = None
    PipelineConfig = None
    RAG_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title="OpenClass Nexus AI API",
    description="Local AI Tutor API untuk Kurikulum Nasional",
    version="1.0.0"
)

# CORS middleware untuk akses dari browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Untuk local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# ===========================
# Authentication Models
# ===========================
class LoginRequest(BaseModel):
    username: str
    password: str
    role: str

class LoginResponse(BaseModel):
    success: bool
    token: str
    message: str
    role: str

class TokenVerifyRequest(BaseModel):
    pass

class TokenVerifyResponse(BaseModel):
    valid: bool
    role: Optional[str] = None
    username: Optional[str] = None

# ===========================
# Data Models
# ===========================
class ChatRequest(BaseModel):
    message: str
    subject_filter: Optional[str] = "all"
    history: Optional[List[Dict]] = []

class ChatResponse(BaseModel):
    response: str
    source: Optional[str] = None
    confidence: Optional[float] = None

class TeacherStats(BaseModel):
    total_questions: int
    popular_topic: str
    active_students: int
    topics: List[Dict]

class AdminStatus(BaseModel):
    model_status: str
    db_status: str
    version: str
    ram_usage: str
    storage_usage: str

# ===========================
# Authentication System (Offline-First)
# ===========================
security = HTTPBearer()

# Demo users (stored locally - offline-first)
# In production, use proper database with hashed passwords
DEMO_USERS = {
    "siswa": {
        "password": hashlib.sha256("siswa123".encode()).hexdigest(),
        "role": "siswa",
        "name": "Siswa Demo"
    },
    "guru": {
        "password": hashlib.sha256("guru123".encode()).hexdigest(),
        "role": "guru",
        "name": "Guru Demo"
    },
    "admin": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "name": "Admin Demo"
    }
}

# Token storage (in-memory for offline-first)
# In production, use Redis or database
active_tokens = {}

def generate_token() -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(32)

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify JWT token and return user info"""
    token = credentials.credentials
    
    if token not in active_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    token_data = active_tokens[token]
    
    # Check if token expired (24 hours)
    if datetime.now() > token_data['expires']:
        del active_tokens[token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    return token_data

def require_role(allowed_roles: List[str]):
    """Dependency to check if user has required role"""
    def role_checker(token_data: Dict = Depends(verify_token)) -> Dict:
        if token_data['role'] not in allowed_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return token_data
    return role_checker

# ===========================
# Global State
# ===========================
class AppState:
    def __init__(self):
        self.pipeline = None
        self.chat_logs = []
        self.is_initialized = False
    
    def initialize(self):
        """Initialize complete pipeline"""
        if not RAG_AVAILABLE:
            logger.warning("RAG components not available - running in demo mode")
            self.is_initialized = False
            return
        
        try:
            logger.info("Initializing complete inference pipeline...")
            
            # Create pipeline configuration
            config = PipelineConfig(
                model_cache_dir="./models",  # Model is in ./models/ not ./models/cache/
                chroma_db_path="./data/vector_db",
                chroma_collection_name="educational_content",
                enable_performance_monitoring=True,
                enable_batch_processing=False,  # Disable for web server
                enable_graceful_degradation=True,
                memory_limit_mb=3072,
                log_level="INFO"
            )
            
            # Initialize pipeline
            self.pipeline = CompletePipeline(config)
            
            # Initialize and start pipeline
            if self.pipeline.initialize():
                if self.pipeline.start():
                    self.is_initialized = True
                    logger.info("Complete pipeline initialized and started successfully")
                else:
                    logger.error("Failed to start pipeline")
                    self.is_initialized = False
            else:
                logger.error("Failed to initialize pipeline")
                self.is_initialized = False
                
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            logger.warning("Server will run in demo mode")
            self.is_initialized = False

state = AppState()

# ===========================
# Startup Event
# ===========================
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        state.initialize()
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")
        logger.info("Server starting in demo mode")
        logger.info("Server starting in demo mode")
    try:
        state.initialize()
    except Exception as e:
        logger.error(f"Startup failed: {e}")

# ===========================
# Root & Health Endpoints
# ===========================
@app.get("/")
async def root():
    """Serve landing page"""
    return FileResponse("frontend/index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "initialized": state.is_initialized,
        "timestamp": datetime.now().isoformat()
    }

# ===========================
# Authentication Endpoints
# ===========================
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint - offline-first authentication
    """
    username = request.username.lower()
    password = request.password
    role = request.role.lower()
    
    # Verify user exists
    if username not in DEMO_USERS:
        return LoginResponse(
            success=False,
            token="",
            message="Username tidak ditemukan",
            role=""
        )
    
    user = DEMO_USERS[username]
    
    # Verify password
    if hash_password(password) != user['password']:
        return LoginResponse(
            success=False,
            token="",
            message="Password salah",
            role=""
        )
    
    # Verify role matches
    if user['role'] != role:
        return LoginResponse(
            success=False,
            token="",
            message=f"Role tidak sesuai. User ini adalah {user['role']}",
            role=""
        )
    
    # Generate token
    token = generate_token()
    
    # Store token (expires in 24 hours)
    active_tokens[token] = {
        'username': username,
        'role': role,
        'name': user['name'],
        'created': datetime.now(),
        'expires': datetime.now() + timedelta(hours=24)
    }
    
    logger.info(f"User logged in: {username} ({role})")
    
    return LoginResponse(
        success=True,
        token=token,
        message="Login berhasil",
        role=role
    )

@app.post("/api/auth/verify", response_model=TokenVerifyResponse)
async def verify_token_endpoint(token_data: Dict = Depends(verify_token)):
    """
    Verify token validity
    """
    return TokenVerifyResponse(
        valid=True,
        role=token_data['role'],
        username=token_data['username']
    )

@app.post("/api/auth/logout")
async def logout(token_data: Dict = Depends(verify_token)):
    """
    Logout endpoint - invalidate token
    """
    # Find and remove token
    for token, data in list(active_tokens.items()):
        if data['username'] == token_data['username']:
            del active_tokens[token]
    
    logger.info(f"User logged out: {token_data['username']}")
    
    return {"success": True, "message": "Logout berhasil"}

# ===========================
# Role-Specific Pages
# ===========================
@app.get("/siswa")
async def siswa_page():
    """Serve student page (auth handled client-side via JS)"""
    return FileResponse("frontend/pages/siswa.html")

@app.get("/guru")
async def guru_page():
    """Serve teacher page (auth handled client-side via JS)"""
    return FileResponse("frontend/pages/guru.html")

@app.get("/admin")
async def admin_page():
    """Serve admin page (auth handled client-side via JS)"""
    return FileResponse("frontend/pages/admin.html")

# ===========================
# Chat Endpoints (Student Mode)
# ===========================
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint untuk student mode
    """
    if not state.is_initialized:
        # Demo mode response with helpful instructions
        logger.warning("RAG not initialized - returning demo response")
        return ChatResponse(
            response=(
                "⚠️ Sistem AI belum diinisialisasi.\n\n"
                "Untuk menggunakan AI Tutor, jalankan setup berikut:\n\n"
                "1. Process dokumen pembelajaran:\n"
                "   python scripts/run_etl_pipeline.py\n\n"
                "2. Download model AI (~2GB):\n"
                "   python scripts/download_model.py\n\n"
                "3. Check status sistem:\n"
                "   python scripts/check_system_ready.py\n\n"
                "4. Restart web server\n\n"
                "Untuk testing UI tanpa AI, ini adalah response demo."
            ),
            source="Demo Mode",
            confidence=0.0
        )
    
    try:
        logger.info(f"Received question: {request.message[:50]}...")
        
        # Process with complete pipeline
        result = state.pipeline.process_query(
            query=request.message,
            subject_filter=request.subject_filter if request.subject_filter != "all" else None
        )
        
        # Log the interaction
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": request.message,
            "subject": request.subject_filter,
            "response_length": len(result.response)
        }
        state.chat_logs.append(log_entry)
        
        # Extract source information
        source = None
        if result.sources:
            source = ", ".join([s.get("title", "Unknown") for s in result.sources[:2]])
        
        return ChatResponse(
            response=result.response,
            source=source,
            confidence=result.confidence
        )
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# Teacher Dashboard Endpoints
# ===========================
@app.get("/api/teacher/stats", response_model=TeacherStats)
async def get_teacher_stats():
    """
    Get statistics for teacher dashboard
    """
    try:
        # Analyze chat logs
        total_questions = len(state.chat_logs)
        
        # Count topics (simplified)
        topic_counts = {}
        for log in state.chat_logs:
            subject = log.get("subject", "unknown")
            topic_counts[subject] = topic_counts.get(subject, 0) + 1
        
        # Get most popular topic
        popular_topic = max(topic_counts.items(), key=lambda x: x[1])[0] if topic_counts else "Belum ada data"
        
        # Format topics list
        topics = [
            {"name": subject.capitalize(), "count": count}
            for subject, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return TeacherStats(
            total_questions=total_questions,
            popular_topic=popular_topic.capitalize(),
            active_students=1,  # Simplified for local mode
            topics=topics[:10]  # Top 10
        )
        
    except Exception as e:
        logger.error(f"Error getting teacher stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/teacher/export")
async def export_report(format: str = "pdf"):
    """
    Export teacher report in PDF or CSV format
    """
    try:
        if format == "csv":
            # Generate CSV
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=["timestamp", "question", "subject"])
            writer.writeheader()
            writer.writerows(state.chat_logs)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=laporan_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        else:
            # For PDF, return JSON for now (can be enhanced with reportlab)
            return {"message": "PDF export coming soon", "data": state.chat_logs}
            
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# Admin Panel Endpoints
# ===========================
@app.get("/api/admin/status", response_model=AdminStatus)
async def get_admin_status():
    """
    Get system status for admin panel
    """
    try:
        import psutil
        
        # Get system info
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return AdminStatus(
            model_status="Aktif" if state.is_initialized else "Tidak Aktif",
            db_status="Terhubung" if state.pipeline and state.pipeline.is_running else "Terputus",
            version="1.0.0",
            ram_usage=f"{ram.used / (1024**3):.1f} GB / {ram.total / (1024**3):.1f} GB",
            storage_usage=f"{disk.used / (1024**3):.1f} GB / {disk.total / (1024**3):.1f} GB"
        )
        
    except Exception as e:
        logger.error(f"Error getting admin status: {e}")
        # Return default values if psutil not available
        return AdminStatus(
            model_status="Aktif" if state.is_initialized else "Tidak Aktif",
            db_status="Terhubung" if state.pipeline and state.pipeline.is_running else "Terputus",
            version="1.0.0",
            ram_usage="N/A",
            storage_usage="N/A"
        )

@app.post("/api/admin/update-model")
async def update_model():
    """
    Update AI model (placeholder)
    """
    return {"message": "Fitur update model akan segera tersedia"}

@app.post("/api/admin/update-curriculum")
async def update_curriculum():
    """
    Update curriculum data (placeholder)
    """
    return {"message": "Fitur update kurikulum akan segera tersedia"}

@app.post("/api/admin/backup")
async def create_backup():
    """
    Create system backup
    """
    try:
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        backup_file = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "chat_logs": state.chat_logs,
            "config": "placeholder"
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        return {"message": f"Backup berhasil dibuat: {backup_file.name}"}
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# Run Server
# ===========================
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("OpenClass Nexus AI - Local Server")
    print("=" * 60)
    print("Server akan berjalan di: http://localhost:8000")
    print("Buka browser dan akses URL di atas")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",  # Accessible dari LAN
        port=8000,
        log_level="info"
    )
