"""
Unit Tests for Pedagogical Intelligence Engine

Tests all components of the pedagogical engine:
- MasteryTracker
- WeakAreaDetector
- AdaptiveQuestionGenerator
- WeeklyReportGenerator
- PedagogicalIntegration
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date, timedelta

from src.pedagogy.mastery_tracker import MasteryTracker
from src.pedagogy.weak_area_detector import WeakAreaDetector, WeakArea
from src.pedagogy.question_generator import AdaptiveQuestionGenerator, Question
from src.pedagogy.report_generator import WeeklyReportGenerator, Report, ClassSummary
from src.pedagogy.integration import PedagogicalIntegration


class TestMasteryTracker:
    """Unit tests for MasteryTracker"""
    
    def test_classify_topic_matematika(self):
        """Test topic classification for matematika"""
        tracker = MasteryTracker(None)
        
        assert tracker.classify_topic("Selesaikan persamaan x + 5 = 10", "matematika") == "aljabar"
        assert tracker.classify_topic("Hitung luas segitiga", "matematika") == "geometri"
        assert tracker.classify_topic("Apa itu sinus?", "matematika") == "trigonometri"
    
    def test_classify_topic_informatika(self):
        """Test topic classification for informatika"""
        tracker = MasteryTracker(None)
        
        assert tracker.classify_topic("Tulis program Python", "informatika") == "pemrograman"
        assert tracker.classify_topic("Apa itu linked list?", "informatika") == "struktur_data"
        assert tracker.classify_topic("Jelaskan SQL query", "informatika") == "database"
    
    def test_classify_topic_fallback(self):
        """Test topic classification fallback to 'general'"""
        tracker = MasteryTracker(None)
        
        assert tracker.classify_topic("Apa itu matematika?", "matematika") == "general"
        assert tracker.classify_topic("Saya tidak mengerti", "matematika") == "general"
    
    def test_calculate_question_complexity(self):
        """Test question complexity calculation"""
        tracker = MasteryTracker(None)
        
        # Short simple question
        complexity = tracker.calculate_question_complexity("Apa itu x?")
        assert 0.0 <= complexity <= 1.0
        assert complexity < 0.3
        
        # Long complex question with keywords
        complexity = tracker.calculate_question_complexity(
            "Jelaskan mengapa dan bagaimana cara membuktikan teorema Pythagoras "
            "dengan menggunakan analisis geometri dan bandingkan dengan metode aljabar"
        )
        assert 0.0 <= complexity <= 1.0
        assert complexity > 0.5
    
    def test_calculate_mastery(self):
        """Test mastery calculation"""
        tracker = MasteryTracker(None)
        
        # Low mastery: many questions, low complexity, short retention
        mastery = tracker.calculate_mastery(20, 0.2, 1)
        assert 0.0 <= mastery <= 1.0
        assert mastery < 0.4
        
        # High mastery: few questions, high complexity, long retention
        mastery = tracker.calculate_mastery(2, 0.9, 25)
        assert 0.0 <= mastery <= 1.0
        assert mastery > 0.5


class TestWeakAreaDetector:
    """Unit tests for WeakAreaDetector"""
    
    def test_calculate_weakness_score(self):
        """Test weakness score calculation"""
        detector = WeakAreaDetector(None)
        
        # High weakness: low mastery, high frequency, low complexity, short retention
        weakness = detector.calculate_weakness_score(0.2, 20, 0.3, 1)
        assert 0.0 <= weakness <= 1.0
        assert weakness > 0.6
        
        # Low weakness: high mastery, low frequency, high complexity, long retention
        weakness = detector.calculate_weakness_score(0.8, 2, 0.9, 20)
        assert 0.0 <= weakness <= 1.0
        assert weakness < 0.4
    
    def test_is_weak_area_low_mastery(self):
        """Test weak area detection for low mastery"""
        detector = WeakAreaDetector(None, mastery_threshold=0.4)
        
        # Below threshold
        assert detector.is_weak_area(0.3, 5, 0.5, 5) == True
        
        # At threshold
        assert detector.is_weak_area(0.4, 5, 0.5, 5) == False
        
        # Above threshold
        assert detector.is_weak_area(0.5, 5, 0.5, 5) == False
    
    def test_is_weak_area_high_frequency(self):
        """Test weak area detection for high frequency"""
        detector = WeakAreaDetector(None)
        
        # High frequency with short retention
        assert detector.is_weak_area(0.5, 10, 0.5, 1) == True
        
        # High frequency with long retention
        assert detector.is_weak_area(0.5, 10, 0.5, 10) == False
    
    def test_is_weak_area_low_complexity(self):
        """Test weak area detection for low complexity"""
        detector = WeakAreaDetector(None)
        
        # Low complexity with high frequency
        assert detector.is_weak_area(0.5, 5, 0.3, 5) == True
        
        # Low complexity with low frequency
        assert detector.is_weak_area(0.5, 2, 0.3, 5) == False
    
    def test_recommend_practice(self):
        """Test practice recommendation generation"""
        detector = WeakAreaDetector(None)
        
        # Very low mastery
        recommendation = detector.recommend_practice("aljabar", 0.1, 5, 0.5)
        assert "fundamental" in recommendation.lower()
        
        # Low mastery with low complexity
        recommendation = detector.recommend_practice("geometri", 0.3, 5, 0.3)
        assert "harder" in recommendation.lower() or "complex" in recommendation.lower()
        
        # High frequency
        recommendation = detector.recommend_practice("trigonometri", 0.5, 10, 0.5)
        assert "many questions" in recommendation.lower()


class TestAdaptiveQuestionGenerator:
    """Unit tests for AdaptiveQuestionGenerator"""
    
    def test_adjust_difficulty(self):
        """Test difficulty adjustment based on mastery"""
        generator = AdaptiveQuestionGenerator(None)
        
        assert generator.adjust_difficulty(0.0) == 'easy'
        assert generator.adjust_difficulty(0.2) == 'easy'
        assert generator.adjust_difficulty(0.3) == 'medium'
        assert generator.adjust_difficulty(0.5) == 'medium'
        assert generator.adjust_difficulty(0.6) == 'hard'
        assert generator.adjust_difficulty(1.0) == 'hard'
    
    def test_generate_question_structure(self):
        """Test that generated questions have correct structure"""
        mock_db = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_conn
        
        generator = AdaptiveQuestionGenerator(mock_db)
        
        question = generator.generate_question(
            subject_id=1,
            topic='aljabar',
            difficulty='medium',
            mastery_level=0.5,
            subject_name='matematika'
        )
        
        assert isinstance(question, Question)
        assert question.subject_id == 1
        assert question.topic == 'aljabar'
        assert question.difficulty == 'medium'
        assert len(question.question_text) > 0
        assert question.answer_hint is not None
    
    def test_generate_question_for_all_difficulties(self):
        """Test question generation for all difficulty levels"""
        mock_db = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_conn
        
        generator = AdaptiveQuestionGenerator(mock_db)
        
        for difficulty in ['easy', 'medium', 'hard']:
            question = generator.generate_question(
                subject_id=1,
                topic='geometri',
                difficulty=difficulty,
                mastery_level=0.5,
                subject_name='matematika'
            )
            assert question.difficulty == difficulty


class TestWeeklyReportGenerator:
    """Unit tests for WeeklyReportGenerator"""
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        generator = WeeklyReportGenerator(None)
        
        weak_areas = ['aljabar', 'geometri', 'trigonometri']
        topics_covered = {
            'aljabar': 0.2,
            'geometri': 0.3,
            'trigonometri': 0.5
        }
        
        recommendations = generator._generate_recommendations(weak_areas, topics_covered)
        
        assert len(recommendations) > 0
        assert any('aljabar' in rec for rec in recommendations)
    
    def test_calculate_progress_trend(self):
        """Test progress trend calculation"""
        mock_db = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock improving trend - fetchone returns tuple
        mock_cursor.fetchone.side_effect = [(0.3,), (0.5,)]  # start_avg, end_avg
        mock_conn.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_conn
        
        generator = WeeklyReportGenerator(mock_db)
        
        trend = generator._calculate_progress_trend(
            user_id=1,
            subject_id=1,
            start_date=date.today() - timedelta(days=7),
            end_date=date.today()
        )
        
        assert trend == 'improving'
    
    def test_export_report_json(self):
        """Test JSON report export"""
        generator = WeeklyReportGenerator(None)
        
        report = Report(
            user_id=1,
            username='student1',
            full_name='Student One',
            subject_id=1,
            subject_name='Matematika',
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            total_questions=10,
            topics_covered={'aljabar': 0.5, 'geometri': 0.6},
            weak_areas=['trigonometri'],
            recommended_practice=['Practice trigonometry'],
            progress_trend='improving',
            generated_at=datetime.now()
        )
        
        json_bytes = generator.export_report(report, 'json')
        
        assert isinstance(json_bytes, bytes)
        assert len(json_bytes) > 0
        assert b'student1' in json_bytes
    
    def test_export_report_text(self):
        """Test text report export"""
        generator = WeeklyReportGenerator(None)
        
        report = Report(
            user_id=1,
            username='student1',
            full_name='Student One',
            subject_id=1,
            subject_name='Matematika',
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            total_questions=10,
            topics_covered={'aljabar': 0.5, 'geometri': 0.6},
            weak_areas=['trigonometri'],
            recommended_practice=['Practice trigonometry'],
            progress_trend='improving',
            generated_at=datetime.now()
        )
        
        text_bytes = generator.export_report(report, 'text')
        
        assert isinstance(text_bytes, bytes)
        assert len(text_bytes) > 0
        assert b'WEEKLY PROGRESS REPORT' in text_bytes
        assert b'Student One' in text_bytes


class TestPedagogicalIntegration:
    """Unit tests for PedagogicalIntegration"""
    
    def test_process_student_question_success(self):
        """Test successful question processing"""
        mock_db = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 0.5, datetime.now())
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_conn
        
        integration = PedagogicalIntegration(mock_db)
        
        result = integration.process_student_question(
            user_id=1,
            subject_id=1,
            question="Bagaimana cara menyelesaikan persamaan linear?",
            subject_name='matematika',
            suggest_practice=False
        )
        
        assert result['success'] == True
        assert 'topic' in result
        assert 'complexity' in result
        assert 'mastery_level' in result
        assert 0.0 <= result['mastery_level'] <= 1.0
    
    def test_get_student_progress_summary(self):
        """Test progress summary retrieval"""
        mock_db = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [('aljabar', 0.5), ('geometri', 0.6)],  # mastery levels
            []  # weak areas
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_db.get_connection.return_value = mock_conn
        
        integration = PedagogicalIntegration(mock_db)
        
        result = integration.get_student_progress_summary(
            user_id=1,
            subject_id=1
        )
        
        assert result['success'] == True
        assert result['total_topics'] == 2
        assert 0.0 <= result['average_mastery'] <= 1.0
        assert 'topics' in result
        assert 'weak_areas' in result


def test_integration_factory():
    """Test pedagogical integration factory function"""
    from src.pedagogy.integration import create_pedagogical_integration
    
    mock_db = Mock()
    integration = create_pedagogical_integration(mock_db)
    
    assert isinstance(integration, PedagogicalIntegration)
    assert integration.db == mock_db
