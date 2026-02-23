"""
Pedagogical Intelligence Engine

This module provides learning support infrastructure including:
- Mastery tracking per student/topic
- Weak area detection
- Adaptive question generation
- Weekly progress reports
"""

from src.pedagogy.mastery_tracker import MasteryTracker
from src.pedagogy.weak_area_detector import WeakAreaDetector
from src.pedagogy.question_generator import AdaptiveQuestionGenerator
from src.pedagogy.report_generator import WeeklyReportGenerator

__all__ = [
    'MasteryTracker',
    'WeakAreaDetector',
    'AdaptiveQuestionGenerator',
    'WeeklyReportGenerator',
]
