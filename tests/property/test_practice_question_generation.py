"""
Property Test: Adaptive Practice Question Generation

**Property 9: Adaptive Practice Question Generation**
**Validates: Requirements 4.3**

The adaptive question generator must generate practice questions targeting weak areas
with appropriate difficulty levels.

This property ensures that:
1. Generated questions have valid difficulty levels
2. Difficulty matches the mastery level
3. Questions are properly formatted
4. Question text is non-empty
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, MagicMock

from src.pedagogy.question_generator import AdaptiveQuestionGenerator, Question


# Strategy for generating test inputs
subject_id_strategy = st.integers(min_value=1, max_value=100)
mastery_level_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
topic_strategy = st.sampled_from(['aljabar', 'geometri', 'trigonometri', 'kalkulus', 
                                  'pemrograman', 'struktur_data', 'database'])
difficulty_strategy = st.sampled_from(['easy', 'medium', 'hard'])
subject_name_strategy = st.sampled_from(['matematika', 'informatika'])


@given(
    subject_id=subject_id_strategy,
    topic=topic_strategy,
    difficulty=difficulty_strategy,
    mastery_level=mastery_level_strategy,
    subject_name=subject_name_strategy
)
@settings(max_examples=300, deadline=None)
def test_generated_question_has_valid_structure(subject_id, topic, difficulty, 
                                                mastery_level, subject_name):
    """
    Property: Generated questions must have valid structure
    
    Every generated question must have:
    - Valid subject_id
    - Valid topic
    - Valid difficulty
    - Non-empty question_text
    - Valid created_at timestamp
    """
    # Create mock database that returns a question ID
    mock_db = Mock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1,)  # Return question ID
    mock_conn.cursor.return_value = mock_cursor
    mock_db.get_connection.return_value = mock_conn
    
    generator = AdaptiveQuestionGenerator(mock_db)
    
    question = generator.generate_question(
        subject_id, topic, difficulty, mastery_level, subject_name
    )
    
    # Property: question must have valid structure
    assert isinstance(question, Question), f"Result is not a Question object: {type(question)}"
    assert question.subject_id == subject_id, f"Subject ID mismatch"
    assert question.topic == topic, f"Topic mismatch"
    assert question.difficulty == difficulty, f"Difficulty mismatch"
    assert isinstance(question.question_text, str), f"Question text is not a string"
    assert len(question.question_text) > 0, f"Question text is empty"
    assert question.created_at is not None, f"Created timestamp is None"


@given(
    subject_id=subject_id_strategy,
    topic=topic_strategy,
    mastery_level=mastery_level_strategy,
    subject_name=subject_name_strategy
)
@settings(max_examples=300, deadline=None)
def test_difficulty_matches_mastery_level(subject_id, topic, mastery_level, subject_name):
    """
    Property: Generated question difficulty must match mastery level
    
    The difficulty should be adjusted based on mastery level:
    - Low mastery (< 0.3) -> easy
    - Medium mastery (0.3 - 0.6) -> medium
    - High mastery (>= 0.6) -> hard
    """
    mock_db = Mock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1,)
    mock_conn.cursor.return_value = mock_cursor
    mock_db.get_connection.return_value = mock_conn
    
    generator = AdaptiveQuestionGenerator(mock_db)
    
    # Adjust difficulty based on mastery
    expected_difficulty = generator.adjust_difficulty(mastery_level)
    
    # Generate question
    question = generator.generate_question(
        subject_id, topic, expected_difficulty, mastery_level, subject_name
    )
    
    # Property: difficulty must match expected difficulty
    assert question.difficulty == expected_difficulty, (
        f"Question difficulty '{question.difficulty}' does not match expected "
        f"'{expected_difficulty}' for mastery level {mastery_level}"
    )


@given(mastery_level=mastery_level_strategy)
@settings(max_examples=300, deadline=None)
def test_difficulty_adjustment_is_deterministic(mastery_level):
    """
    Property: Difficulty adjustment must be deterministic
    
    The same mastery level should always produce the same difficulty.
    """
    mock_db = None
    generator = AdaptiveQuestionGenerator(mock_db)
    
    difficulty1 = generator.adjust_difficulty(mastery_level)
    difficulty2 = generator.adjust_difficulty(mastery_level)
    
    # Property: difficulty adjustment must be deterministic
    assert difficulty1 == difficulty2, (
        f"Difficulty adjustment is not deterministic for mastery {mastery_level}: "
        f"got '{difficulty1}' and '{difficulty2}'"
    )


def test_question_generation_for_all_difficulties():
    """
    Test that questions can be generated for all difficulty levels
    """
    mock_db = Mock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1,)
    mock_conn.cursor.return_value = mock_cursor
    mock_db.get_connection.return_value = mock_conn
    
    generator = AdaptiveQuestionGenerator(mock_db)
    
    difficulties = ['easy', 'medium', 'hard']
    
    for difficulty in difficulties:
        question = generator.generate_question(
            subject_id=1,
            topic='aljabar',
            difficulty=difficulty,
            mastery_level=0.5,
            subject_name='matematika'
        )
        
        assert question.difficulty == difficulty, (
            f"Failed to generate {difficulty} question"
        )
        assert len(question.question_text) > 0, (
            f"Empty question text for {difficulty} difficulty"
        )


def test_question_generation_for_all_topics():
    """
    Test that questions can be generated for various topics
    """
    mock_db = Mock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1,)
    mock_conn.cursor.return_value = mock_cursor
    mock_db.get_connection.return_value = mock_conn
    
    generator = AdaptiveQuestionGenerator(mock_db)
    
    # Test matematika topics
    matematika_topics = ['aljabar', 'geometri', 'trigonometri']
    
    for topic in matematika_topics:
        question = generator.generate_question(
            subject_id=1,
            topic=topic,
            difficulty='medium',
            mastery_level=0.5,
            subject_name='matematika'
        )
        
        assert question.topic == topic, f"Topic mismatch for {topic}"
        assert len(question.question_text) > 0, f"Empty question for topic {topic}"
    
    # Test informatika topics
    informatika_topics = ['pemrograman', 'struktur_data', 'database']
    
    for topic in informatika_topics:
        question = generator.generate_question(
            subject_id=2,
            topic=topic,
            difficulty='medium',
            mastery_level=0.5,
            subject_name='informatika'
        )
        
        assert question.topic == topic, f"Topic mismatch for {topic}"
        assert len(question.question_text) > 0, f"Empty question for topic {topic}"


def test_question_has_hint():
    """
    Test that generated questions include answer hints
    """
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
    
    assert question.answer_hint is not None, "Question has no hint"
    assert isinstance(question.answer_hint, str), "Hint is not a string"
    assert len(question.answer_hint) > 0, "Hint is empty"


def test_fallback_for_unknown_topic():
    """
    Test that generator handles unknown topics gracefully
    """
    mock_db = Mock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1,)
    mock_conn.cursor.return_value = mock_cursor
    mock_db.get_connection.return_value = mock_conn
    
    generator = AdaptiveQuestionGenerator(mock_db)
    
    # Generate question for unknown topic
    question = generator.generate_question(
        subject_id=1,
        topic='unknown_topic',
        difficulty='medium',
        mastery_level=0.5,
        subject_name='matematika'
    )
    
    # Should still generate a valid question (fallback)
    assert isinstance(question, Question), "Failed to generate fallback question"
    assert len(question.question_text) > 0, "Fallback question is empty"
    assert question.topic == 'unknown_topic', "Topic was changed"


def test_difficulty_progression():
    """
    Test that difficulty progresses appropriately with mastery
    """
    mock_db = None
    generator = AdaptiveQuestionGenerator(mock_db)
    
    # Test mastery progression
    mastery_levels = [0.0, 0.2, 0.4, 0.7, 1.0]
    expected_difficulties = ['easy', 'easy', 'medium', 'hard', 'hard']
    
    for mastery, expected in zip(mastery_levels, expected_difficulties):
        difficulty = generator.adjust_difficulty(mastery)
        assert difficulty == expected, (
            f"Mastery {mastery} should produce '{expected}' difficulty, got '{difficulty}'"
        )
