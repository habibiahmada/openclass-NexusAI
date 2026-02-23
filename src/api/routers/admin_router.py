"""
Admin Router
Handles admin panel and system management endpoints
"""

import logging
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import psutil

from ..models import AdminStatus
from ..state import AppState
from ..config import config

# Import AWS services
try:
    from src.aws_control_plane.s3_storage_manager import S3StorageManager
    from src.aws_control_plane.cloudfront_manager import CloudFrontManager
    from src.aws_control_plane.job_tracker import JobTracker
    from src.embeddings.strategy_manager import EmbeddingStrategyManager
    from src.vkp.puller import VKPPuller
    from src.vkp.version_manager import VKPVersionManager
    from src.resilience.backup_manager import BackupManager
    AWS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AWS services not available: {e}")
    AWS_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()


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
            backup_dir = config.backup_dir
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
    
    # ===========================
    # AWS Services Status
    # ===========================
    @router.get("/aws-status")  
    async def get_aws_status():
        """Get AWS services status"""
        try:
            status = {
                "s3": {
                    "connected": False,
                    "bucket": None,
                    "last_upload": None,
                    "total_files": 0,
                    "storage_bytes": 0
                },
                "bedrock": {
                    "connected": False,
                    "strategy": "unknown",
                    "model_id": None,
                    "fallback_enabled": False,
                    "region": None
                },
                "cloudfront": {
                    "configured": False,
                    "distribution_id": None,
                    "domain": None,
                    "last_invalidation": None
                },
                "lambda": {
                    "deployed": False,
                    "function_name": None,
                    "last_execution": None,
                    "success_rate": None,
                    "avg_duration": None
                }
            }
            
            if not AWS_AVAILABLE:
                return status
            
            # Check S3
            try:
                s3_manager = S3StorageManager()
                status["s3"]["connected"] = True
                status["s3"]["bucket"] = s3_manager.bucket_name
                # Get S3 stats (simplified)
                status["s3"]["total_files"] = 0
                status["s3"]["storage_bytes"] = 0
            except Exception as e:
                logger.debug(f"S3 not available: {e}")
            
            # Check Bedrock
            try:
                strategy_manager = EmbeddingStrategyManager()
                current_strategy = strategy_manager.get_strategy()
                status["bedrock"]["connected"] = True
                status["bedrock"]["strategy"] = current_strategy.__class__.__name__
                status["bedrock"]["model_id"] = os.getenv('BEDROCK_MODEL_ID', 'amazon.titan-embed-text-v2:0')
                status["bedrock"]["fallback_enabled"] = True
                status["bedrock"]["region"] = os.getenv('BEDROCK_REGION', 'ap-southeast-2')
            except Exception as e:
                logger.debug(f"Bedrock not available: {e}")
            
            # Check CloudFront
            try:
                cloudfront_manager = CloudFrontManager()
                dist_id = os.getenv('CLOUDFRONT_DISTRIBUTION_ID')
                if dist_id:
                    status["cloudfront"]["configured"] = True
                    status["cloudfront"]["distribution_id"] = dist_id
                    status["cloudfront"]["domain"] = os.getenv('CLOUDFRONT_DISTRIBUTION_URL')
            except Exception as e:
                logger.debug(f"CloudFront not available: {e}")
            
            # Check Lambda (simplified - just check if configured)
            lambda_function = os.getenv('LAMBDA_FUNCTION_NAME')
            if lambda_function:
                status["lambda"]["deployed"] = True
                status["lambda"]["function_name"] = lambda_function
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting AWS status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===========================
    # System Health
    # ===========================
    @router.get("/system-health")
    async def get_system_health():
        """Get system health status"""
        try:
            # Get system resources
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get uptime
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.now().timestamp() - boot_time
            
            health = {
                "postgresql": {
                    "connected": state.db_initialized,
                    "latency": 0,
                    "active_connections": 0,
                    "database_size": 0
                },
                "chromadb": {
                    "connected": state.is_initialized,
                    "collections": 0,
                    "total_documents": 0,
                    "storage_size": 0,
                    "last_update": None
                },
                "llm": {
                    "loaded": state.is_initialized,
                    "model_name": config.local_model_path.split('/')[-1] if hasattr(config, 'local_model_path') else "Not loaded",
                    "memory_usage": 0,
                    "avg_inference_time": 0
                },
                "resources": {
                    "cpu_usage": round(cpu_percent, 1),
                    "ram_usage": round(ram.percent, 1),
                    "disk_usage": round(disk.percent, 1),
                    "disk_free": disk.free,
                    "uptime_seconds": int(uptime_seconds)
                }
            }
            
            # Get PostgreSQL stats
            if state.db_initialized and state.database_manager:
                try:
                    # Simple health check
                    health["postgresql"]["connected"] = True
                    health["postgresql"]["latency"] = 10  # Placeholder
                except Exception as e:
                    logger.debug(f"PostgreSQL health check failed: {e}")
            
            # Get ChromaDB stats
            if state.is_initialized and state.chroma_manager:
                try:
                    collections = state.chroma_manager.list_collections()
                    health["chromadb"]["collections"] = len(collections)
                    health["chromadb"]["total_documents"] = state.chroma_manager.count_documents()
                except Exception as e:
                    logger.debug(f"ChromaDB health check failed: {e}")
            
            return health
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===========================
    # Recent Activity
    # ===========================
    @router.get("/recent-activity")
    async def get_recent_activity():
        """Get recent activity logs"""
        try:
            activity = {
                "etl_runs": [],
                "vkp_updates": [],
                "telemetry_uploads": [],
                "backups": []
            }
            
            if not AWS_AVAILABLE:
                return activity
            
            # Get recent ETL runs from DynamoDB
            try:
                job_tracker = JobTracker()
                jobs = job_tracker.list_recent_jobs(limit=5)
                activity["etl_runs"] = [
                    {
                        "job_id": job.get("job_id"),
                        "status": job.get("status"),
                        "started_at": job.get("started_at")
                    }
                    for job in jobs
                ]
            except Exception as e:
                logger.debug(f"Failed to get ETL runs: {e}")
            
            # Get recent VKP updates
            try:
                version_manager = VKPVersionManager()
                updates = version_manager.get_recent_updates(limit=5)
                activity["vkp_updates"] = updates
            except Exception as e:
                logger.debug(f"Failed to get VKP updates: {e}")
            
            # Get recent telemetry uploads (placeholder)
            activity["telemetry_uploads"] = []
            
            # Get recent backups
            try:
                backup_dir = config.backup_dir
                if backup_dir.exists():
                    backups = sorted(backup_dir.glob("backup_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
                    activity["backups"] = [
                        {
                            "type": "full",
                            "size": backup.stat().st_size,
                            "created_at": datetime.fromtimestamp(backup.stat().st_mtime).isoformat()
                        }
                        for backup in backups
                    ]
            except Exception as e:
                logger.debug(f"Failed to get backups: {e}")
            
            return activity
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===========================
    # Quick Actions
    # ===========================
    @router.post("/check-vkp-updates")
    async def check_vkp_updates():
        """Check for VKP updates"""
        try:
            if not AWS_AVAILABLE:
                raise HTTPException(status_code=503, detail="AWS services not available")
            
            puller = VKPPuller()
            updates = puller.check_updates()
            
            # Broadcast notification
            await manager.broadcast({
                "type": "vkp_update",
                "message": f"{len(updates)} VKP updates available"
            })
            
            return {"updates_available": updates}
            
        except Exception as e:
            logger.error(f"Error checking VKP updates: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/invalidate-cache")
    async def invalidate_cloudfront_cache():
        """Invalidate CloudFront cache"""
        try:
            if not AWS_AVAILABLE:
                raise HTTPException(status_code=503, detail="AWS services not available")
            
            cloudfront_manager = CloudFrontManager()
            result = cloudfront_manager.invalidate_cache(paths=['/processed/*'])
            
            return {
                "invalidation_id": result.invalidation_id,
                "status": result.status
            }
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/run-etl")
    async def run_etl_pipeline():
        """Run ETL pipeline"""
        try:
            # This would trigger ETL pipeline
            # For now, return placeholder
            return {
                "success": False,
                "message": "ETL pipeline trigger not implemented yet. Use CLI: python scripts/data/run_etl_pipeline.py"
            }
            
        except Exception as e:
            logger.error(f"Error running ETL pipeline: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/run-backup")
    async def run_manual_backup():
        """Run manual backup"""
        try:
            if not AWS_AVAILABLE:
                # Use simple backup
                backup_dir = config.backup_dir
                backup_dir.mkdir(exist_ok=True)
                
                backup_file = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                backup_data = {
                    "timestamp": datetime.now().isoformat(),
                    "database_available": state.db_initialized,
                    "pipeline_status": state.is_initialized
                }
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
                return {"success": True, "backup_file": backup_file.name}
            
            # Use BackupManager
            backup_manager = BackupManager()
            backup_path = backup_manager.create_full_backup()
            
            return {"success": True, "backup_file": str(backup_path)}
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===========================
    # WebSocket Endpoint
    # ===========================
    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates"""
        await manager.connect(websocket)
        try:
            while True:
                # Keep connection alive
                data = await websocket.receive_text()
                # Echo back for testing
                await websocket.send_json({"type": "echo", "data": data})
        except WebSocketDisconnect:
            manager.disconnect(websocket)
    
    return router
