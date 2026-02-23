"""
Property Test: Mastery Level Bounds

**Property 5: Mastery Level Bounds**
**Validates: Requirements 4.1**

The mastery level calculation must ALWAYS return a value between 0.0 and 1.0,
regardless of input values for question_count, avg_complexity, and retention_days.

This property ensures that:
1. Mastery level is never negative
2. Mastery level never exceeds 1.0
3. The scoring algorithm properly bounds all intermediate calculations
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from src.pedagogy.mastery_tracker import MasteryTracker


# Strategy for generating test inputs
question_count_strategy = st.integers(min_value=0, max_value=1000)
avg_complexity_strategy = st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False)
retention_days_strategy = st.integers(min_value=0, max_value=365)


@given(
    question_count=question_count_strategy,
    avg_complexity=avg_complexity_strategy,
    retention_days=retention_days_strategy
)
@settings(max_examples=500, deadline=None)
def test_mastery_level_always_in_bounds(question_count, avg_complexity, retention_days):
    """
    Property: Mastery level must always be between 0.0 and 1.0
    
    For any valid inputs (question_count >= 0, avg_complexity >= 0, retention_days >= 0),
    the calculate_mastery function must return a value in [0.0, 1.0].
    """
    # Create a mock database manager (not needed for this calculation)
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Calculate mastery level
    mastery = tracker.calculate_mastery(question_count, avg_complexity, retention_days)
    
    # Property: mastery level must be in bounds [0.0, 1.0]
    assert 0.0 <= mastery <= 1.0, (
        f"Mastery level {mastery} out of bounds for inputs: "
        f"question_count={question_count}, avg_complexity={avg_complexity}, "
        f"retention_days={retention_days}"
    )


@given(
    question_count=question_count_strategy,
    avg_complexity=avg_complexity_strategy,
    retention_days=retention_days_strategy
)
@settings(max_examples=500, deadline=None)
def test_mastery_level_is_float(question_count, avg_complexity, retention_days):
    """
    Property: Mastery level must be a valid float (not NaN or infinity)
    """
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    mastery = tracker.calculate_mastery(question_count, avg_complexity, retention_days)
    
    # Property: mastery must be a valid float
    assert isinstance(mastery, float), f"Mastery level {mastery} is not a float"
    assert not (mastery != mastery), f"Mastery level is NaN"  # NaN check
    assert mastery != float('inf') and mastery != float('-inf'), f"Mastery level is infinity"


@given(
    question_count=st.integers(min_value=0, max_value=100),
    avg_complexity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    retention_days=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=300, deadline=None)
def test_mastery_decreases_with_more_questions(question_count, avg_complexity, retention_days):
    """
    Property: More questions (higher frequency) should generally decrease mastery
    
    This tests the frequency_factor component of the algorithm.
    """
    # Skip if question_count is 0 (edge case)
    assume(question_count > 0)
    
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Calculate mastery with current question count
    mastery1 = tracker.calculate_mastery(question_count, avg_complexity, retention_days)
    
    # Calculate mastery with more questions (indicating struggle)
    mastery2 = tracker.calculate_mastery(question_count + 10, avg_complexity, retention_days)
    
    # Property: more questions should result in lower or equal mastery
    # (equal is possible due to other factors dominating)
    assert mastery2 <= mastery1, (
        f"Mastery increased with more questions: {mastery1} -> {mastery2} "
        f"for question_count={question_count}, avg_complexity={avg_complexity}, "
        f"retention_days={retention_days}"
    )


@given(
    question_count=st.integers(min_value=1, max_value=50),
    complexity1=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False),
    complexity2=st.floats(min_value=0.5, max_value=1.0, allow_nan=False, allow_infinity=False),
    retention_days=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=300, deadline=None)
def test_mastery_increases_with_complexity(question_count, complexity1, complexity2, retention_days):
    """
    Property: Higher complexity questions should increase mastery
    
    This tests the complexity_factor component of the algorithm.
    """
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Calculate mastery with lower complexity
    mastery1 = tracker.calculate_mastery(question_count, complexity1, retention_days)
    
    # Calculate mastery with higher complexity
    mastery2 = tracker.calculate_mastery(question_count, complexity2, retention_days)
    
    # Property: higher complexity should result in higher or equal mastery
    assert mastery2 >= mastery1, (
        f"Mastery decreased with higher complexity: {mastery1} -> {mastery2} "
        f"for question_count={question_count}, complexity1={complexity1}, "
        f"complexity2={complexity2}, retention_days={retention_days}"
    )


@given(
    question_count=st.integers(min_value=1, max_value=50),
    avg_complexity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    retention_days=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=300, deadline=None)
def test_mastery_increases_with_retention(question_count, avg_complexity, retention_days):
    """
    Property: Longer retention (more days between questions) should increase mastery
    
    This tests the retention_factor component of the algorithm.
    """
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Calculate mastery with current retention
    mastery1 = tracker.calculate_mastery(question_count, avg_complexity, retention_days)
    
    # Calculate mastery with longer retention (better understanding)
    mastery2 = tracker.calculate_mastery(question_count, avg_complexity, retention_days + 10)
    
    # Property: longer retention should result in higher or equal mastery
    assert mastery2 >= mastery1, (
        f"Mastery decreased with longer retention: {mastery1} -> {mastery2} "
        f"for question_count={question_count}, avg_complexity={avg_complexity}, "
        f"retention_days={retention_days}"
    )


def test_mastery_edge_cases():
    """
    Test edge cases for mastery calculation
    """
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Edge case: zero questions (novice)
    mastery = tracker.calculate_mastery(0, 0.0, 0)
    assert 0.0 <= mastery <= 1.0
    
    # Edge case: perfect inputs (expert)
    mastery = tracker.calculate_mastery(1, 1.0, 30)
    assert 0.0 <= mastery <= 1.0
    assert mastery > 0.5, "Perfect inputs should result in high mastery"
    
    # Edge case: many questions, low complexity (struggling)
    mastery = tracker.calculate_mastery(100, 0.1, 1)
    assert 0.0 <= mastery <= 1.0
    assert mastery < 0.5, "Many low-complexity questions should result in low mastery"
    
    # Edge case: few questions, high complexity, good retention (mastering)
    mastery = tracker.calculate_mastery(2, 0.9, 25)
    assert 0.0 <= mastery <= 1.0
    assert mastery > 0.5, "Few high-complexity questions with good retention should result in high mastery"
