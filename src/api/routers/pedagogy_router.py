"""
Pedagogy Router
Handles pedagogical engine endpoints (student progress, weak areas, practice questions)
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict

from ..state import AppState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/student", tags=["pedagogy"])


def create_pedagogy_router(state: AppState, verify_token_dependency, require_teacher_dependency):
    """Create pedagogy router with dependencies"""
    
    @router.get("/progress")
    async def get_student_progress(token_data: Dict = Depends(verify_token_dependency)):
        """Get student progress summary"""
        if not state.pedagogy_initialized or not state.pedagogical_integration:
            raise HTTPException(
                status_code=503,
                detail="Pedagogical engine not available"
            )
        
        try:
            subject_id = _get_default_subject_id(state)
            
            progress = state.pedagogical_integration.get_student_progress_summary(
                user_id=token_data['user_id'],
                subject_id=subject_id
            )
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting student progress: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/weak-areas")
    async def get_weak_areas(token_data: Dict = Depends(verify_token_dependency)):
        """Get student weak areas with recommendations"""
        if not state.pedagogy_initialized or not state.pedagogical_integration:
            raise HTTPException(
                status_code=503,
                detail="Pedagogical engine not available"
            )
        
        try:
            subject_id = _get_default_subject_id(state)
            
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
    
    @router.get("/practice-questions")
    async def get_practice_questions(
        count: int = 5,
        token_data: Dict = Depends(verify_token_dependency)
    ):
        """Get adaptive practice questions based on weak areas"""
        if not state.pedagogy_initialized or not state.pedagogical_integration:
            raise HTTPException(
                status_code=503,
                detail="Pedagogical engine not available"
            )
        
        try:
            subject_id = _get_default_subject_id(state)
            subject_name = _get_subject_name(subject_id, state)
            
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
    
    @router.get("/{student_id}/report")
    async def get_student_report(
        student_id: int,
        token_data: Dict = Depends(require_teacher_dependency)
    ):
        """Get weekly report for a specific student (teacher/admin only)"""
        if not state.pedagogy_initialized or not state.pedagogical_integration:
            raise HTTPException(
                status_code=503,
                detail="Pedagogical engine not available"
            )
        
        try:
            subject_id = _get_default_subject_id(state)
            
            progress = state.pedagogical_integration.get_student_progress_summary(
                user_id=student_id,
                subject_id=subject_id
            )
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting student report: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    return router


def _get_default_subject_id(state: AppState) -> int:
    """Get default subject ID (informatika kelas 10)"""
    subject_id = 1
    
    if state.subject_repo:
        try:
            subjects = state.subject_repo.get_subjects_by_grade(10)
            if subjects:
                subject_id = subjects[0].id
        except Exception as e:
            logger.warning(f"Failed to get subject: {e}")
    
    return subject_id


def _get_subject_name(subject_id: int, state: AppState) -> str:
    """Get subject name by ID"""
    if state.subject_repo:
        try:
            subjects = state.subject_repo.get_all_subjects()
            for subject in subjects:
                if subject.id == subject_id:
                    return subject.name
        except Exception as e:
            logger.warning(f"Failed to get subject name: {e}")
    
    return 'informatika'
