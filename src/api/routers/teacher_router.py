"""
Teacher Router
Handles teacher dashboard and reporting endpoints
"""

import logging
import csv
from io import StringIO
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Dict

from ..models import TeacherStats
from ..state import AppState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


def create_teacher_router(state: AppState, verify_token_dependency):
    """Create teacher router with dependencies"""
    
    @router.get("/stats", response_model=TeacherStats)
    async def get_teacher_stats(token_data: Dict = Depends(verify_token_dependency)):
        """Get statistics for teacher dashboard"""
        if not state.db_initialized or not state.chat_history_repo:
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable"
            )
        
        try:
            # Get recent chat history
            recent_chats = state.chat_history_repo.get_recent_chats(limit=1000)
            
            total_questions = len(recent_chats)
            
            # Count topics and unique users
            topic_counts = {}
            unique_users = set()
            
            for chat in recent_chats:
                unique_users.add(chat.user_id)
                subject_key = f"Subject {chat.subject_id}" if chat.subject_id else "Umum"
                topic_counts[subject_key] = topic_counts.get(subject_key, 0) + 1
            
            # Get most popular topic
            popular_topic = max(
                topic_counts.items(),
                key=lambda x: x[1]
            )[0] if topic_counts else "Belum ada data"
            
            # Format topics list
            topics = [
                {"name": subject, "count": count}
                for subject, count in sorted(
                    topic_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ]
            
            return TeacherStats(
                total_questions=total_questions,
                popular_topic=popular_topic,
                active_students=len(unique_users),
                topics=topics[:10]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting teacher stats: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable"
            )
    
    @router.get("/export")
    async def export_report(
        format: str = "csv",
        token_data: Dict = Depends(verify_token_dependency)
    ):
        """Export teacher report in CSV or JSON format"""
        if not state.db_initialized or not state.chat_history_repo:
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable"
            )
        
        try:
            recent_chats = state.chat_history_repo.get_recent_chats(limit=1000)
            
            if format == "csv":
                output = StringIO()
                writer = csv.DictWriter(
                    output,
                    fieldnames=["timestamp", "user_id", "question", "subject_id"]
                )
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
                    headers={
                        "Content-Disposition": f"attachment; filename=laporan_{datetime.now().strftime('%Y%m%d')}.csv"
                    }
                )
            else:
                chat_data = [chat.to_dict() for chat in recent_chats]
                return {
                    "message": "PDF export coming soon",
                    "data": chat_data
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error exporting report: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable"
            )
    
    return router
