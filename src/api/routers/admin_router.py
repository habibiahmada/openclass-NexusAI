"""
Admin Router
Handles admin panel and system management endpoints
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict

from ..models import AdminStatus
from ..state import AppState
from ..config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def create_admin_router(state: AppState, require_admin_dependency):
    """Create admin router with dependencies"""
    
    @router.get("/status", response_model=AdminStatus)
    async def get_admin_status():
        """Get system status for admin panel"""
        try:
            import psutil
            
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return AdminStatus(
                model_status="Aktif" if state.is_initialized else "Tidak Aktif",
                db_status="Terhubung" if state.db_initialized else "Terputus",
                version="1.0.0",
                ram_usage=f"{ram.used / (1024**3):.1f} GB / {ram.total / (1024**3):.1f} GB",
                storage_usage=f"{disk.used / (1024**3):.1f} GB / {disk.total / (1024**3):.1f} GB"
            )
            
        except Exception as e:
            logger.error(f"Error getting admin status: {e}")
            return AdminStatus(
                model_status="Aktif" if state.is_initialized else "Tidak Aktif",
                db_status="Terhubung" if state.db_initialized else "Terputus",
                version="1.0.0",
                ram_usage="N/A",
                storage_usage="N/A"
            )
    
    @router.post("/update-model")
    async def update_model(token_data: Dict = Depends(require_admin_dependency)):
        """Update AI model (placeholder)"""
        return {"message": "Fitur update model akan segera tersedia"}
    
    @router.post("/update-curriculum")
    async def update_curriculum(token_data: Dict = Depends(require_admin_dependency)):
        """Update curriculum data (placeholder)"""
        return {"message": "Fitur update kurikulum akan segera tersedia"}
    
    @router.post("/backup")
    async def create_backup(token_data: Dict = Depends(require_admin_dependency)):
        """Create system backup"""
        try:
            backup_dir = config.BACKUP_DIR
            backup_dir.mkdir(exist_ok=True)
            
            backup_file = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "database_available": state.db_initialized,
                "pipeline_status": state.is_initialized,
                "config": "placeholder"
            }
            
            # Add database stats if available
            if state.db_initialized and state.chat_history_repo:
                try:
                    recent_chats = state.chat_history_repo.get_recent_chats(limit=100)
                    backup_data["recent_chats_count"] = len(recent_chats)
                except Exception as e:
                    logger.error(f"Failed to get chat stats: {e}")
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            return {"message": f"Backup berhasil dibuat: {backup_file.name}"}
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router
