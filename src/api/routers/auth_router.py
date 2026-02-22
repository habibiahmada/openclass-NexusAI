"""
Authentication Router
Handles login, logout, and token verification endpoints
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict

from ..models import LoginRequest, LoginResponse, TokenVerifyResponse
from ..auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def create_auth_router(auth_service: AuthService, verify_token_dependency):
    """Create authentication router with dependencies"""
    
    @router.post("/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        """Login endpoint - offline-first authentication with database persistence"""
        if not auth_service.session_repo or not auth_service.user_repo:
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable. Authentication is disabled."
            )
        
        try:
            # Verify credentials
            result = auth_service.verify_credentials(
                request.username,
                request.password,
                request.role.lower()
            )
            
            if not result['success']:
                return LoginResponse(
                    success=False,
                    token="",
                    message=result['message'],
                    role=""
                )
            
            # Create session
            session_data = auth_service.create_session(
                result['username'],
                request.role.lower()
            )
            
            return LoginResponse(
                success=True,
                token=session_data['token'],
                message="Login berhasil",
                role=request.role.lower()
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable"
            )
    
    @router.post("/verify", response_model=TokenVerifyResponse)
    async def verify_token(token_data: Dict = Depends(verify_token_dependency)):
        """Verify token validity"""
        return TokenVerifyResponse(
            valid=True,
            role=token_data['role'],
            username=token_data['username']
        )
    
    @router.post("/logout")
    async def logout(token_data: Dict = Depends(verify_token_dependency)):
        """Logout endpoint - invalidate token in database"""
        if not auth_service.session_repo:
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable"
            )
        
        try:
            deleted_count = auth_service.logout(token_data['user_id'])
            return {
                "success": True,
                "message": "Logout berhasil",
                "sessions_deleted": deleted_count
            }
        except Exception as e:
            logger.error(f"Logout failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable"
            )
    
    return router
