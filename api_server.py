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
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import existing components (with error handling)
try:
    from src.edge_runtime.complete_pipeline import CompletePipeline, PipelineConfig
    RAG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RAG components not available: {e}")
    logger.warning("Server will run in demo mode without AI functionality")
    CompletePipeline = None
    PipelineConfig = None
    RAG_AVAILABLE = False

# Import database components
try:
    from src.persistence.database_manager import DatabaseManager
    from src.persistence.session_repository import SessionRepository
    from src.persistence.chat_history_repository import ChatHistoryRepository
    from src.persistence.user_repository import UserRepository
    from src.persistence.subject_repository import SubjectRepository
    DB_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Database components not available: {e}")
    logger.warning("Server will run without database persistence")
    DatabaseManager = None
    SessionRepository = None
    ChatHistoryRepository = None
    UserRepository = None
    SubjectRepository = None
    DB_AVAILABLE = False

# Import pedagogical engine
try:
    from src.pedagogy.integration import create_pedagogical_integration
    PEDAGOGY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Pedagogical engine not available: {e}")
    logger.warning("Server will run without pedagogical tracking")
    create_pedagogical_integration = None
    PEDAGOGY_AVAILABLE = False

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

# Token storage - now using database instead of in-memory
# active_tokens = {}  # REMOVED: Replaced with SessionRepository

def generate_token() -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(32)

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify JWT token and return user info"""
    token = credentials.credentials
    
    # Check if database is available
    if not DB_AVAILABLE or not state.session_repo:
        # Fallback to demo mode without persistence
        logger.error("Database unavailable during token verification")
        raise HTTPException(
            status_code=503, 
            detail="Database temporarily unavailable. Please try again later."
        )
    
    try:
        # Get session from database
        session = state.session_repo.get_session_by_token(token)
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # Get user info from database
        user = state.user_repo.get_user_by_id(session.user_id)
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Return token data in expected format
        return {
            'username': user.username,
            'role': user.role,
            'name': user.full_name,
            'user_id': user.id,
            'created': session.created_at,
            'expires': session.expires_at
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions (401, 403, etc.)
        raise
    except Exception as e:
        # Log database errors with stack trace
        logger.error(f"Database error during token verification: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )

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
        # Chat logs now stored in database instead of in-memory
        # self.chat_logs = []  # REMOVED: Replaced with ChatHistoryRepository
        self.is_initialized = False
        
        # Database components
        self.db_manager = None
        self.session_repo = None
        self.chat_history_repo = None
        self.user_repo = None
        self.subject_repo = None
        self.db_initialized = False
        
        # Pedagogical engine
        self.pedagogical_integration = None
        self.pedagogy_initialized = False
    
    def initialize_database(self):
        """Initialize database connection and repositories"""
        if not DB_AVAILABLE:
            logger.warning("Database components not available - skipping database initialization")
            return False
        
        try:
            # Get database URL from environment
            database_url = os.getenv('DATABASE_URL')
            
            if not database_url:
                logger.warning("DATABASE_URL not set - database features disabled")
                return False
            
            logger.info("Initializing database connection...")
            
            # Create database manager
            self.db_manager = DatabaseManager(database_url)
            
            # Test connection
            if not self.db_manager.health_check():
                logger.error("Database health check failed - PostgreSQL may be unavailable")
                logger.error("Please ensure PostgreSQL is running and DATABASE_URL is correct")
                return False
            
            # Initialize repositories
            self.session_repo = SessionRepository(self.db_manager)
            self.chat_history_repo = ChatHistoryRepository(self.db_manager)
            self.user_repo = UserRepository(self.db_manager)
            self.subject_repo = SubjectRepository(self.db_manager)
            
            self.db_initialized = True
            logger.info("Database initialized successfully")
            
            # Initialize pedagogical engine if available
            if PEDAGOGY_AVAILABLE:
                try:
                    self.pedagogical_integration = create_pedagogical_integration(self.db_manager)
                    self.pedagogy_initialized = True
                    logger.info("Pedagogical engine initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize pedagogical engine: {e}", exc_info=True)
                    self.pedagogy_initialized = False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            logger.error("Server will run without database persistence")
            logger.error("To enable database features, ensure PostgreSQL is running and DATABASE_URL is set")
            self.db_initialized = False
            return False
    
    def initialize(self):
        """Initialize complete pipeline"""
        # Initialize database first
        self.initialize_database()
        
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
        "database": state.db_initialized,
        "timestamp": datetime.now().isoformat()
    }

# ===========================
# Authentication Endpoints
# ===========================
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint - offline-first authentication with database persistence
    """
    username = request.username.lower()
    password = request.password
    role = request.role.lower()
    
    # Check if database is available
    if not state.db_initialized:
        logger.error("Login attempt failed - database unavailable")
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Authentication is disabled. Please try again later."
        )
    
    try:
        # Verify user exists (using demo users for now, will migrate to database later)
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
        
        # Get or create user in database
        db_user = state.user_repo.get_user_by_username(username)
        if not db_user:
            # Create user in database if not exists
            # Use the plain password from the demo users (we know the plain passwords)
            plain_passwords = {
                "siswa": "siswa123",
                "guru": "guru123",
                "admin": "admin123"
            }
            db_user = state.user_repo.create_user(
                username=username,
                password=plain_passwords.get(username, "default123"),
                role=role,
                full_name=user['name']
            )
        
        # Store token in database (expires in 24 hours)
        session = state.session_repo.create_session(
            user_id=db_user.id,
            token=token,
            expires_hours=24
        )
        
        logger.info(f"User logged in: {username} ({role})")
        
        return LoginResponse(
            success=True,
            token=token,
            message="Login berhasil",
            role=role
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Login failed due to database error: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
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
    Logout endpoint - invalidate token in database
    """
    if not state.db_initialized:
        logger.error("Logout attempt failed - database unavailable")
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )
    
    try:
        # Get the token from the request
        # We need to extract it from the authorization header
        # For now, delete all sessions for this user
        deleted_count = state.session_repo.delete_user_sessions(token_data['user_id'])
        
        logger.info(f"User logged out: {token_data['username']} ({deleted_count} sessions deleted)")
        
        return {"success": True, "message": "Logout berhasil"}
    
    except Exception as e:
        logger.error(f"Logout failed due to database error: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )

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
async def chat(request: ChatRequest, token_data: Dict = Depends(verify_token)):
    """
    Main chat endpoint untuk student mode with database persistence
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
        logger.info(f"Received question from user {token_data['username']}: {request.message[:50]}...")
        
        # Process with complete pipeline
        result = state.pipeline.process_query(
            query=request.message,
            subject_filter=request.subject_filter if request.subject_filter != "all" else None
        )
        
        # Save to database if available
        if state.db_initialized and state.chat_history_repo:
            try:
                # Get subject_id from subject_filter
                subject_id = None
                subject_name = 'informatika'  # Default subject
                
                if request.subject_filter and request.subject_filter != "all":
                    # Try to get subject from database
                    try:
                        subjects = state.subject_repo.get_all_subjects()
                        for subject in subjects:
                            if subject.name.lower() == request.subject_filter.lower():
                                subject_id = subject.id
                                subject_name = subject.name
                                break
                    except Exception as e:
                        logger.warning(f"Failed to get subject from database: {e}")
                
                # Save chat to database
                # Note: QueryResult doesn't have confidence, use 0.0 as default
                state.chat_history_repo.save_chat(
                    user_id=token_data['user_id'],
                    subject_id=subject_id,
                    question=request.message,
                    response=result.response,
                    confidence=0.0  # QueryResult doesn't have confidence attribute
                )
                logger.info(f"Chat saved to database for user_id={token_data['user_id']}")
                
                # Process with pedagogical engine if available
                if state.pedagogy_initialized and state.pedagogical_integration:
                    try:
                        pedagogical_result = state.pedagogical_integration.process_student_question(
                            user_id=token_data['user_id'],
                            subject_id=subject_id or 1,  # Use 1 as default if no subject
                            question=request.message,
                            subject_name=subject_name,
                            suggest_practice=False  # Don't suggest practice by default
                        )
                        
                        if pedagogical_result['success']:
                            logger.info(
                                f"Pedagogical tracking updated: "
                                f"topic={pedagogical_result['topic']}, "
                                f"mastery={pedagogical_result['mastery_level']:.2f}, "
                                f"weak_areas={pedagogical_result['weak_areas_count']}"
                            )
                        else:
                            logger.warning(f"Pedagogical tracking failed: {pedagogical_result.get('error')}")
                    
                    except Exception as e:
                        logger.error(f"Failed to process pedagogical tracking: {e}", exc_info=True)
                        # Continue even if pedagogical tracking fails
                
            except Exception as e:
                logger.error(f"Failed to save chat to database: {e}", exc_info=True)
                logger.warning("Continuing without saving chat history")
                # Continue even if database save fails - don't block user interaction
        else:
            logger.warning("Database not available - chat history not saved")
        
        # Extract source information
        source = None
        if result.sources:
            source = ", ".join([s.get("title", "Unknown") for s in result.sources[:2]])
        
        return ChatResponse(
            response=result.response,
            source=source,
            confidence=0.0  # QueryResult doesn't have confidence attribute
        )
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# Pedagogical Engine Endpoints
# ===========================
@app.get("/api/student/progress")
async def get_student_progress(token_data: Dict = Depends(verify_token)):
    """
    Get student progress summary (mastery levels, weak areas)
    """
    if not state.pedagogy_initialized or not state.pedagogical_integration:
        raise HTTPException(
            status_code=503,
            detail="Pedagogical engine not available"
        )
    
    try:
        # Get default subject (informatika kelas 10)
        subject_id = 1  # Default to first subject
        
        # Try to get actual subject from database
        if state.subject_repo:
            try:
                subjects = state.subject_repo.get_subjects_by_grade(10)
                if subjects:
                    subject_id = subjects[0].id
            except Exception as e:
                logger.warning(f"Failed to get subject: {e}")
        
        progress = state.pedagogical_integration.get_student_progress_summary(
            user_id=token_data['user_id'],
            subject_id=subject_id
        )
        
        return progress
    
    except Exception as e:
        logger.error(f"Error getting student progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/student/weak-areas")
async def get_weak_areas(token_data: Dict = Depends(verify_token)):
    """
    Get student weak areas with recommendations
    """
    if not state.pedagogy_initialized or not state.pedagogical_integration:
        raise HTTPException(
            status_code=503,
            detail="Pedagogical engine not available"
        )
    
    try:
        # Get default subject
        subject_id = 1
        
        if state.subject_repo:
            try:
                subjects = state.subject_repo.get_subjects_by_grade(10)
                if subjects:
                    subject_id = subjects[0].id
            except Exception as e:
                logger.warning(f"Failed to get subject: {e}")
        
        weak_areas = state.pedagogical_integration.weak_area_detector.detect_weak_areas(
            user_id=token_data['user_id'],
            subject_id=subject_id
        )
        
        return {
            'success': True,
            'weak_areas': [
                {
                    'topic': wa.topic,
                    'mastery_level': wa.mastery_level,
                    'weakness_score': wa.weakness_score,
                    'recommendation': wa.recommendation,
                }
                for wa in weak_areas
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting weak areas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/student/practice-questions")
async def get_practice_questions(count: int = 5, token_data: Dict = Depends(verify_token)):
    """
    Get adaptive practice questions based on weak areas
    """
    if not state.pedagogy_initialized or not state.pedagogical_integration:
        raise HTTPException(
            status_code=503,
            detail="Pedagogical engine not available"
        )
    
    try:
        # Get default subject
        subject_id = 1
        subject_name = 'informatika'
        
        if state.subject_repo:
            try:
                subjects = state.subject_repo.get_subjects_by_grade(10)
                if subjects:
                    subject_id = subjects[0].id
                    subject_name = subjects[0].name
            except Exception as e:
                logger.warning(f"Failed to get subject: {e}")
        
        practice_questions = state.pedagogical_integration.question_generator.get_practice_set(
            user_id=token_data['user_id'],
            subject_id=subject_id,
            count=count,
            subject_name=subject_name
        )
        
        return {
            'success': True,
            'questions': [
                {
                    'topic': q.topic,
                    'difficulty': q.difficulty,
                    'question': q.question_text,
                    'hint': q.answer_hint,
                }
                for q in practice_questions
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting practice questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/teacher/student/{student_id}/report")
async def get_student_report(student_id: int, token_data: Dict = Depends(require_role(['guru', 'admin']))):
    """
    Get weekly report for a specific student (teacher/admin only)
    """
    if not state.pedagogy_initialized or not state.pedagogical_integration:
        raise HTTPException(
            status_code=503,
            detail="Pedagogical engine not available"
        )
    
    try:
        # Get default subject
        subject_id = 1
        
        if state.subject_repo:
            try:
                subjects = state.subject_repo.get_subjects_by_grade(10)
                if subjects:
                    subject_id = subjects[0].id
            except Exception as e:
                logger.warning(f"Failed to get subject: {e}")
        
        progress = state.pedagogical_integration.get_student_progress_summary(
            user_id=student_id,
            subject_id=subject_id
        )
        
        return progress
    
    except Exception as e:
        logger.error(f"Error getting student report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ===========================
# Teacher Dashboard Endpoints
# ===========================
@app.get("/api/teacher/stats", response_model=TeacherStats)
async def get_teacher_stats(token_data: Dict = Depends(verify_token)):
    """
    Get statistics for teacher dashboard from database
    """
    try:
        if not state.db_initialized or not state.chat_history_repo:
            # Graceful degradation - return empty stats with user-friendly message
            logger.warning("Teacher stats requested but database unavailable")
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable. Statistics cannot be retrieved. Please try again later."
            )
        
        # Get recent chat history (last 1000 records)
        recent_chats = state.chat_history_repo.get_recent_chats(limit=1000)
        
        total_questions = len(recent_chats)
        
        # Count topics by subject_id
        topic_counts = {}
        unique_users = set()
        
        for chat in recent_chats:
            # Track unique users
            unique_users.add(chat.user_id)
            
            # Count by subject (use subject_id or "unknown")
            subject_key = f"Subject {chat.subject_id}" if chat.subject_id else "Umum"
            topic_counts[subject_key] = topic_counts.get(subject_key, 0) + 1
        
        # Get most popular topic
        popular_topic = max(topic_counts.items(), key=lambda x: x[1])[0] if topic_counts else "Belum ada data"
        
        # Format topics list
        topics = [
            {"name": subject, "count": count}
            for subject, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return TeacherStats(
            total_questions=total_questions,
            popular_topic=popular_topic,
            active_students=len(unique_users),
            topics=topics[:10]  # Top 10
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting teacher stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )

@app.get("/api/teacher/export")
async def export_report(format: str = "pdf", token_data: Dict = Depends(verify_token)):
    """
    Export teacher report in PDF or CSV format from database
    """
    try:
        if not state.db_initialized or not state.chat_history_repo:
            logger.warning("Export report requested but database unavailable")
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable. Report export is not available. Please try again later."
            )
        
        # Get recent chat history
        recent_chats = state.chat_history_repo.get_recent_chats(limit=1000)
        
        if format == "csv":
            # Generate CSV
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=["timestamp", "user_id", "question", "subject_id"])
            writer.writeheader()
            
            for chat in recent_chats:
                writer.writerow({
                    "timestamp": chat.created_at.isoformat() if chat.created_at else "",
                    "user_id": chat.user_id,
                    "question": chat.question,
                    "subject_id": chat.subject_id or "N/A"
                })
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=laporan_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        else:
            # For PDF, return JSON for now (can be enhanced with reportlab)
            chat_data = [chat.to_dict() for chat in recent_chats]
            return {"message": "PDF export coming soon", "data": chat_data}
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error exporting report: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )

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
async def create_backup(token_data: Dict = Depends(verify_token)):
    """
    Create system backup (database data)
    """
    try:
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        backup_file = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "database_available": state.db_initialized,
            "config": "placeholder"
        }
        
        # Add database stats if available
        if state.db_initialized and state.chat_history_repo:
            try:
                recent_chats = state.chat_history_repo.get_recent_chats(limit=100)
                backup_data["recent_chats_count"] = len(recent_chats)
            except Exception as e:
                logger.error(f"Failed to get chat stats for backup: {e}")
        
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
