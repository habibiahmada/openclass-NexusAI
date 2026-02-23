"""
Pedagogical Engine Integration

Integrates the pedagogical engine with the chat pipeline to:
- Track mastery after each question
- Detect weak areas
- Optionally suggest practice questions
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from src.pedagogy.mastery_tracker import MasteryTracker
from src.pedagogy.weak_area_detector import WeakAreaDetector
from src.pedagogy.question_generator import AdaptiveQuestionGenerator

logger = logging.getLogger(__name__)


class PedagogicalIntegration:
    """
    Integrates pedagogical engine with chat pipeline
    
    After each student query:
    1. Extract topic from question
    2. Calculate question complexity
    3. Update mastery tracker
    4. Check for weak areas
    5. Optionally suggest practice questions
    """
    
    def __init__(self, db_manager):
        """
        Initialize pedagogical integration
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
        self.mastery_tracker = MasteryTracker(db_manager)
        self.weak_area_detector = WeakAreaDetector(db_manager)
        self.question_generator = AdaptiveQuestionGenerator(db_manager)
    
    def process_student_question(self, user_id: int, subject_id: int,
                                question: str, subject_name: str = 'matematika',
                                suggest_practice: bool = False) -> Dict[str, Any]:
        """
        Process student question and update pedagogical tracking
        
        Args:
            user_id: Student user ID
            subject_id: Subject ID
            question: Student's question text
            subject_name: Subject name (default: 'matematika')
            suggest_practice: Whether to suggest practice questions (default: False)
        
        Returns:
            Dictionary with tracking results and optional practice suggestions
        """
        try:
            # 1. Classify topic
            topic = self.mastery_tracker.classify_topic(question, subject_name)
            logger.info(f"Classified question into topic: {topic}")
            
            # 2. Calculate question complexity
            complexity = self.mastery_tracker.calculate_question_complexity(question)
            logger.info(f"Question complexity: {complexity:.2f}")
            
            # 3. Update mastery tracker
            mastery_level = self.mastery_tracker.update_mastery(
                user_id, subject_id, topic, complexity
            )
            logger.info(f"Updated mastery level for {topic}: {mastery_level:.2f}")
            
            # 4. Detect weak areas
            weak_areas = self.weak_area_detector.detect_weak_areas(user_id, subject_id)
            logger.info(f"Detected {len(weak_areas)} weak areas")
            
            # 5. Optionally suggest practice questions
            practice_suggestions = []
            if suggest_practice and weak_areas:
                # Get practice questions for top weak areas
                practice_questions = self.question_generator.get_practice_set(
                    user_id, subject_id, count=3, subject_name=subject_name
                )
                
                practice_suggestions = [
                    {
                        'topic': q.topic,
                        'difficulty': q.difficulty,
                        'question': q.question_text,
                        'hint': q.answer_hint,
                    }
                    for q in practice_questions
                ]
                
                logger.info(f"Generated {len(practice_suggestions)} practice suggestions")
            
            return {
                'success': True,
                'topic': topic,
                'complexity': complexity,
                'mastery_level': mastery_level,
                'weak_areas_count': len(weak_areas),
                'weak_areas': [
                    {
                        'topic': wa.topic,
                        'mastery_level': wa.mastery_level,
                        'weakness_score': wa.weakness_score,
                        'recommendation': wa.recommendation,
                    }
                    for wa in weak_areas[:3]  # Top 3 weak areas
                ],
                'practice_suggestions': practice_suggestions,
            }
            
        except Exception as e:
            logger.error(f"Error processing student question: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_student_progress_summary(self, user_id: int, subject_id: int) -> Dict[str, Any]:
        """
        Get summary of student progress
        
        Args:
            user_id: Student user ID
            subject_id: Subject ID
        
        Returns:
            Dictionary with progress summary
        """
        try:
            # Get all mastery levels
            mastery_levels = self.mastery_tracker.get_all_mastery(user_id, subject_id)
            
            # Get weak areas
            weak_areas = self.weak_area_detector.detect_weak_areas(user_id, subject_id)
            
            # Calculate average mastery
            avg_mastery = (
                sum(mastery_levels.values()) / len(mastery_levels)
                if mastery_levels else 0.0
            )
            
            return {
                'success': True,
                'total_topics': len(mastery_levels),
                'average_mastery': avg_mastery,
                'weak_areas_count': len(weak_areas),
                'topics': mastery_levels,
                'weak_areas': [
                    {
                        'topic': wa.topic,
                        'mastery_level': wa.mastery_level,
                        'weakness_score': wa.weakness_score,
                    }
                    for wa in weak_areas
                ],
            }
            
        except Exception as e:
            logger.error(f"Error getting progress summary: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
            }


def create_pedagogical_integration(db_manager) -> PedagogicalIntegration:
    """
    Factory function to create pedagogical integration
    
    Args:
        db_manager: DatabaseManager instance
    
    Returns:
        PedagogicalIntegration instance
    """
    return PedagogicalIntegration(db_manager)
