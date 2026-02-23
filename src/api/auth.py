"""
Authentication Module
Handles user authentication, token generation, and authorization
"""

import secrets
import hashlib
import logging
from typing import Dict, List
from datetime import datetime
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)
security = HTTPBearer()


# Demo users - In production, this should be in database
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

# Plain passwords for user creation
DEMO_PLAIN_PASSWORDS = {
    "siswa": "siswa123",
    "guru": "guru123",
    "admin": "admin123"
}


def generate_token() -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


class AuthService:
    """Authentication Service"""
    
    def __init__(self, session_repo=None, user_repo=None):
        self.session_repo = session_repo
        self.user_repo = user_repo
        # In-memory sessions for demo mode (when database is not available)
        self._memory_sessions = {}
        self._memory_users = {}
    
    def verify_credentials(self, username: str, password: str, role: str) -> Dict:
        """Verify user credentials"""
        username = username.lower()
        
        # Check if user exists in demo users
        if username not in DEMO_USERS:
            return {
                'success': False,
                'message': 'Username tidak ditemukan'
            }
        
        user = DEMO_USERS[username]
        
        # Verify password
        if hash_password(password) != user['password']:
            return {
                'success': False,
                'message': 'Password salah'
            }
        
        # Verify role
        if user['role'] != role:
            return {
                'success': False,
                'message': f"Role tidak sesuai. User ini adalah {user['role']}"
            }
        
        return {
            'success': True,
            'user': user,
            'username': username
        }
    
    def create_session(self, username: str, role: str) -> Dict:
        """Create new session with token"""
        # Generate token
        token = generate_token()
        
        # If database is available, use it
        if self.session_repo and self.user_repo:
            try:
                # Get or create user in database
                db_user = self.user_repo.get_user_by_username(username)
                if not db_user:
                    plain_password = DEMO_PLAIN_PASSWORDS.get(username, "default123")
                    db_user = self.user_repo.create_user(
                        username=username,
                        password=plain_password,
                        role=role,
                        full_name=DEMO_USERS[username]['name']
                    )
                
                # Create session in database
                session = self.session_repo.create_session(
                    user_id=db_user.id,
                    token=token,
                    expires_hours=24
                )
                
                logger.info(f"User logged in (database): {username} ({role})")
                
                return {
                    'token': token,
                    'user_id': db_user.id,
                    'session': session
                }
            except Exception as e:
                logger.warning(f"Database session creation failed, using in-memory: {e}")
        
        # Fallback to in-memory sessions (demo mode)
        # Use small positive integer for in-memory user IDs (compatible with PostgreSQL)
        user_id = abs(hash(username)) % 1000000  # Keep it under 1 million
        
        # Store user in memory
        self._memory_users[user_id] = {
            'id': user_id,
            'username': username,
            'role': role,
            'full_name': DEMO_USERS[username]['name']
        }
        
        # Store session in memory
        self._memory_sessions[token] = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'created_at': datetime.now(),
            'expires_at': datetime.now()
        }
        
        logger.info(f"User logged in (in-memory): {username} ({role})")
        
        return {
            'token': token,
            'user_id': user_id,
            'session': self._memory_sessions[token]
        }
    
    def verify_token(self, token: str) -> Dict:
        """Verify token and return user info"""
        # Try database first
        if self.session_repo and self.user_repo:
            try:
                # Get session from database
                session = self.session_repo.get_session_by_token(token)
                
                if session:
                    # Get user info
                    user = self.user_repo.get_user_by_id(session.user_id)
                    
                    if user:
                        return {
                            'username': user.username,
                            'role': user.role,
                            'name': user.full_name,
                            'user_id': user.id,
                            'created': session.created_at,
                            'expires': session.expires_at
                        }
            except Exception as e:
                logger.warning(f"Database token verification failed, trying in-memory: {e}")
        
        # Fallback to in-memory sessions
        if token in self._memory_sessions:
            session = self._memory_sessions[token]
            user = self._memory_users.get(session['user_id'])
            
            if user:
                return {
                    'username': user['username'],
                    'role': user['role'],
                    'name': user['full_name'],
                    'user_id': user['id'],
                    'created': session['created_at'],
                    'expires': session['expires_at']
                }
        
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    def logout(self, user_id: int) -> int:
        """Logout user and delete sessions"""
        deleted_count = 0
        
        # Try database first
        if self.session_repo:
            try:
                deleted_count = self.session_repo.delete_user_sessions(user_id)
                logger.info(f"User logged out (database): user_id={user_id} ({deleted_count} sessions deleted)")
                return deleted_count
            except Exception as e:
                logger.warning(f"Database logout failed, trying in-memory: {e}")
        
        # Fallback to in-memory sessions
        tokens_to_delete = [
            token for token, session in self._memory_sessions.items()
            if session['user_id'] == user_id
        ]
        
        for token in tokens_to_delete:
            del self._memory_sessions[token]
            deleted_count += 1
        
        logger.info(f"User logged out (in-memory): user_id={user_id} ({deleted_count} sessions deleted)")
        
        return deleted_count


def create_auth_dependency(auth_service: AuthService):
    """Create authentication dependency"""
    
    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
        """Verify JWT token and return user info"""
        token = credentials.credentials
        
        try:
            return auth_service.verify_token(token)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification error: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable"
            )
    
    return verify_token


def create_role_dependency(allowed_roles: List[str], auth_service: AuthService):
    """Create role-based authorization dependency"""
    
    verify_token = create_auth_dependency(auth_service)
    
    def require_role(token_data: Dict = Depends(verify_token)) -> Dict:
        """Check if user has required role"""
        if token_data['role'] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return token_data
    
    return require_role
