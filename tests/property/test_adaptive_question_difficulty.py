"""
Property Test: Adaptive Question Difficulty

**Property 7: Adaptive Question Difficulty**
**Validates: Requirements 4.6**

The adaptive question generator must adjust difficulty based on mastery level:
- 0.0 - 0.3: easy (foundational concepts)
- 0.3 - 0.6: medium (application problems)
- 0.6 - 1.0: hard (complex scenarios)

This property ensures that:
1. Difficulty adjustment is consistent with mastery level
2. Lower mastery results in easier questions
3. Higher mastery results in harder questions
4. Difficulty levels are always valid ('easy', 'medium', 'hard')
"""

import pytest
from hypothesis import given, strategies as st, settings

from src.pedagogy.question_generator import AdaptiveQuestionGenerator


# Strategy for generating mastery levels
mastery_level_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


@given(mastery_level=mastery_level_strategy)
@settings(max_examples=500, deadline=None)
def test_difficulty_always_valid(mastery_level):
    """
    Property: Difficulty level must always be one of: 'easy', 'medium', 'hard'
    
    For any mastery level in [0.0, 1.0], the adjust_difficulty function
    must return a valid difficulty level.
    """
    mock_db = None
    generator = AdaptiveQuestionGenerator(mock_db)
    
    difficulty = generator.adjust_difficulty(mastery_level)
    
    # Property: difficulty must be valid
    valid_difficulties = {'easy', 'medium', 'hard'}
    assert difficulty in valid_difficulties, (
        f"Invalid difficulty '{difficulty}' for mastery_level={mastery_level}"
    )


@given(mastery_level=st.floats(min_value=0.0, max_value=0.29, allow_nan=False, allow_infinity=False))
@settings(max_examples=300, deadline=None)
def test_low_mastery_gets_easy_difficulty(mastery_level):
    """
    Property: Mastery level < 0.3 must result in 'easy' difficulty
    
    Students with low mastery need foundational practice.
    """
    mock_db = None
    generator = AdaptiveQuestionGenerator(mock_db)
    
    difficulty = generator.adjust_difficulty(mastery_level)
    
    # Property: low mastery should get easy questions
    assert difficulty == 'easy', (
        f"Low mastery {mastery_level} should get 'easy' difficulty, got '{difficulty}'"
    )


@given(mastery_level=st.floats(min_value=0.3, max_value=0.59, allow_nan=False, allow_infinity=False))
@settings(max_examples=300, deadline=None)
def test_medium_mastery_gets_medium_difficulty(mastery_level):
    """
    Property: Mastery level 0.3 - 0.6 must result in 'medium' difficulty
    
    Students with medium mastery need application practice.
    """
    mock_db = None
    generator = AdaptiveQuestionGenerator(mock_db)
    
    difficulty = generator.adjust_difficulty(mastery_level)
    
    # Property: medium mastery should get medium questions
    assert difficulty == 'medium', (
        f"Medium mastery {mastery_level} should get 'medium' difficulty, got '{difficulty}'"
    )


@given(mastery_level=st.floats(min_value=0.6, max_value=1.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=300, deadline=None)
def test_high_mastery_gets_hard_difficulty(mastery_level):
    """
    Property: Mastery level >= 0.6 must result in 'hard' difficulty
    
    Students with high mastery need challenging practice.
    """
    mock_db = None
    generator = AdaptiveQuestionGenerator(mock_db)
    
    difficulty = generator.adjust_difficulty(mastery_level)
    
    # Property: high mastery should get hard questions
    assert difficulty == 'hard', (
        f"High mastery {mastery_level} should get 'hard' difficulty, got '{difficulty}'"
    )


@given(
    mastery1=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False),
    mastery2=st.floats(min_value=0.5, max_value=1.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=300, deadline=None)
def test_higher_mastery_harder_or_equal_difficulty(mastery1, mastery2):
    """
    Property: Higher mastery should result in harder or equal difficulty
    
    This tests the monotonic relationship between mastery and difficulty.
    """
    mock_db = None
    generator = AdaptiveQuestionGenerator(mock_db)
    
    difficulty1 = generator.adjust_difficulty(mastery1)
    difficulty2 = generator.adjust_difficulty(mastery2)
    
    # Define difficulty ordering
    difficulty_order = {'easy': 0, 'medium': 1, 'hard': 2}
    
    # Property: higher mastery should result in harder or equal difficulty
    assert difficulty_order[difficulty2] >= difficulty_order[difficulty1], (
        f"Higher mastery ({mastery2}) resulted in easier difficulty ('{difficulty2}') "
        f"than lower mastery ({mastery1}) with difficulty ('{difficulty1}')"
    )


def test_difficulty_boundary_cases():
    """
    Test boundary cases for difficulty adjustment
    """
    mock_db = None
    generator = AdaptiveQuestionGenerator(mock_db)
    
    # Boundary: exactly 0.0 (complete novice)
    difficulty = generator.adjust_difficulty(0.0)
    assert difficulty == 'easy', f"Mastery 0.0 should be 'easy', got '{difficulty}'"
    
    # Boundary: just below 0.3
    difficulty = generator.adjust_difficulty(0.29)
    assert difficulty == 'easy', f"Mastery 0.29 should be 'easy', got '{difficulty}'"
    
    # Boundary: exactly 0.3
    difficulty = generator.adjust_difficulty(0.3)
    assert difficulty == 'medium', f"Mastery 0.3 should be 'medium', got '{difficulty}'"
    
    # Boundary: just below 0.6
    difficulty = generator.adjust_difficulty(0.59)
    assert difficulty == 'medium', f"Mastery 0.59 should be 'medium', got '{difficulty}'"
    
    # Boundary: exactly 0.6
    difficulty = generator.adjust_difficulty(0.6)
    assert difficulty == 'hard', f"Mastery 0.6 should be 'hard', got '{difficulty}'"
    
    # Boundary: exactly 1.0 (complete mastery)
    difficulty = generator.adjust_difficulty(1.0)
    assert difficulty == 'hard', f"Mastery 1.0 should be 'hard', got '{difficulty}'"


def test_difficulty_consistency():
    """
    Test that difficulty adjustment is consistent (same input = same output)
    """
    mock_db = None
    generator = AdaptiveQuestionGenerator(mock_db)
    
    # Test consistency for various mastery levels
    test_levels = [0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0]
    
    for mastery in test_levels:
        difficulty1 = generator.adjust_difficulty(mastery)
        difficulty2 = generator.adjust_difficulty(mastery)
        
        assert difficulty1 == difficulty2, (
            f"Inconsistent difficulty for mastery {mastery}: "
            f"got '{difficulty1}' and '{difficulty2}'"
        )


def test_difficulty_progression():
    """
    Test that difficulty progresses logically as mastery increases
    """
    mock_db = None
    generator = AdaptiveQuestionGenerator(mock_db)
    
    # Test progression from novice to expert
    mastery_progression = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    previous_difficulty_level = -1
    difficulty_order = {'easy': 0, 'medium': 1, 'hard': 2}
    
    for mastery in mastery_progression:
        difficulty = generator.adjust_difficulty(mastery)
        current_difficulty_level = difficulty_order[difficulty]
        
        # Difficulty should never decrease as mastery increases
        assert current_difficulty_level >= previous_difficulty_level, (
            f"Difficulty decreased from level {previous_difficulty_level} to "
            f"{current_difficulty_level} at mastery {mastery}"
        )
        
        previous_difficulty_level = current_difficulty_level
