"""
Property Test: Weak Area Detection

**Property 6: Weak Area Detection**
**Validates: Requirements 4.2**

The weak area detection must correctly identify topics needing reinforcement based on:
1. Low mastery levels (< 0.4 threshold)
2. High question frequency (> 5 questions in 7 days)
3. Low complexity questions (avg < 0.5)
4. Short retention (< 3 days between questions)

This property ensures that:
1. Topics with mastery < threshold are always detected as weak
2. Weakness score is always between 0.0 and 1.0
3. Higher weakness scores indicate greater need for practice
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from src.pedagogy.weak_area_detector import WeakAreaDetector


# Strategy for generating test inputs
mastery_level_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
question_count_strategy = st.integers(min_value=0, max_value=100)
avg_complexity_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
retention_days_strategy = st.integers(min_value=0, max_value=30)


@given(
    mastery_level=mastery_level_strategy,
    question_count=question_count_strategy,
    avg_complexity=avg_complexity_strategy,
    retention_days=retention_days_strategy
)
@settings(max_examples=500, deadline=None)
def test_weakness_score_always_in_bounds(mastery_level, question_count, avg_complexity, retention_days):
    """
    Property: Weakness score must always be between 0.0 and 1.0
    
    For any valid inputs, the calculate_weakness_score function must return
    a value in [0.0, 1.0].
    """
    mock_db = None
    detector = WeakAreaDetector(mock_db)
    
    weakness_score = detector.calculate_weakness_score(
        mastery_level, question_count, avg_complexity, retention_days
    )
    
    # Property: weakness score must be in bounds [0.0, 1.0]
    assert 0.0 <= weakness_score <= 1.0, (
        f"Weakness score {weakness_score} out of bounds for inputs: "
        f"mastery_level={mastery_level}, question_count={question_count}, "
        f"avg_complexity={avg_complexity}, retention_days={retention_days}"
    )


@given(
    mastery_level=st.floats(min_value=0.0, max_value=0.39, allow_nan=False, allow_infinity=False),
    question_count=st.integers(min_value=0, max_value=50),
    avg_complexity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    retention_days=st.integers(min_value=0, max_value=30)
)
@settings(max_examples=300, deadline=None)
def test_low_mastery_always_detected_as_weak(mastery_level, question_count, avg_complexity, retention_days):
    """
    Property: Topics with mastery < 0.4 must always be detected as weak areas
    
    This is the primary criterion for weak area detection.
    """
    mock_db = None
    detector = WeakAreaDetector(mock_db, mastery_threshold=0.4)
    
    is_weak = detector.is_weak_area(mastery_level, question_count, avg_complexity, retention_days)
    
    # Property: low mastery must be detected as weak
    assert is_weak, (
        f"Low mastery {mastery_level} not detected as weak area "
        f"(question_count={question_count}, avg_complexity={avg_complexity}, "
        f"retention_days={retention_days})"
    )


@given(
    mastery_level=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    question_count=st.integers(min_value=6, max_value=50),
    avg_complexity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    retention_days=st.integers(min_value=0, max_value=2)
)
@settings(max_examples=300, deadline=None)
def test_high_frequency_short_retention_detected_as_weak(mastery_level, question_count, 
                                                         avg_complexity, retention_days):
    """
    Property: High question frequency (> 5) with short retention (< 3 days)
    should be detected as weak area
    
    This tests the secondary criterion for weak area detection.
    """
    mock_db = None
    detector = WeakAreaDetector(mock_db)
    
    is_weak = detector.is_weak_area(mastery_level, question_count, avg_complexity, retention_days)
    
    # Property: high frequency with short retention should be detected as weak
    assert is_weak, (
        f"High frequency ({question_count}) with short retention ({retention_days}) "
        f"not detected as weak area (mastery_level={mastery_level}, "
        f"avg_complexity={avg_complexity})"
    )


@given(
    mastery_level=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    question_count=st.integers(min_value=4, max_value=50),
    avg_complexity=st.floats(min_value=0.0, max_value=0.49, allow_nan=False, allow_infinity=False),
    retention_days=st.integers(min_value=0, max_value=30)
)
@settings(max_examples=300, deadline=None)
def test_low_complexity_high_frequency_detected_as_weak(mastery_level, question_count,
                                                        avg_complexity, retention_days):
    """
    Property: Low complexity (< 0.5) with high frequency (> 3) should be
    detected as weak area
    
    This tests the tertiary criterion for weak area detection.
    """
    mock_db = None
    detector = WeakAreaDetector(mock_db)
    
    is_weak = detector.is_weak_area(mastery_level, question_count, avg_complexity, retention_days)
    
    # Property: low complexity with high frequency should be detected as weak
    assert is_weak, (
        f"Low complexity ({avg_complexity}) with high frequency ({question_count}) "
        f"not detected as weak area (mastery_level={mastery_level}, "
        f"retention_days={retention_days})"
    )


@given(
    mastery1=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False),
    mastery2=st.floats(min_value=0.5, max_value=1.0, allow_nan=False, allow_infinity=False),
    question_count=st.integers(min_value=1, max_value=50),
    avg_complexity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    retention_days=st.integers(min_value=0, max_value=30)
)
@settings(max_examples=300, deadline=None)
def test_lower_mastery_higher_weakness_score(mastery1, mastery2, question_count,
                                             avg_complexity, retention_days):
    """
    Property: Lower mastery should result in higher weakness score
    
    This tests that the weakness score correctly reflects mastery level.
    """
    mock_db = None
    detector = WeakAreaDetector(mock_db)
    
    # Calculate weakness scores
    weakness1 = detector.calculate_weakness_score(mastery1, question_count, avg_complexity, retention_days)
    weakness2 = detector.calculate_weakness_score(mastery2, question_count, avg_complexity, retention_days)
    
    # Property: lower mastery should result in higher weakness score
    assert weakness1 >= weakness2, (
        f"Lower mastery ({mastery1}) resulted in lower weakness score ({weakness1}) "
        f"than higher mastery ({mastery2}) with score ({weakness2})"
    )


@given(
    mastery_level=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    count1=st.integers(min_value=1, max_value=20),
    count2=st.integers(min_value=21, max_value=50),
    avg_complexity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    retention_days=st.integers(min_value=0, max_value=30)
)
@settings(max_examples=300, deadline=None)
def test_higher_frequency_higher_weakness_score(mastery_level, count1, count2,
                                                avg_complexity, retention_days):
    """
    Property: Higher question frequency should result in higher weakness score
    
    This tests that the weakness score correctly reflects question frequency.
    """
    mock_db = None
    detector = WeakAreaDetector(mock_db)
    
    # Calculate weakness scores
    weakness1 = detector.calculate_weakness_score(mastery_level, count1, avg_complexity, retention_days)
    weakness2 = detector.calculate_weakness_score(mastery_level, count2, avg_complexity, retention_days)
    
    # Property: higher frequency should result in higher or equal weakness score
    assert weakness2 >= weakness1, (
        f"Higher frequency ({count2}) resulted in lower weakness score ({weakness2}) "
        f"than lower frequency ({count1}) with score ({weakness1})"
    )


def test_weak_area_detection_edge_cases():
    """
    Test edge cases for weak area detection
    """
    mock_db = None
    detector = WeakAreaDetector(mock_db, mastery_threshold=0.4)
    
    # Edge case: perfect mastery, no questions
    is_weak = detector.is_weak_area(1.0, 0, 1.0, 30)
    assert not is_weak, "Perfect mastery should not be weak"
    
    # Edge case: zero mastery (complete novice)
    is_weak = detector.is_weak_area(0.0, 1, 0.5, 5)
    assert is_weak, "Zero mastery should be weak"
    
    # Edge case: exactly at threshold
    is_weak = detector.is_weak_area(0.4, 1, 0.5, 5)
    assert not is_weak, "Mastery at threshold should not be weak (boundary)"
    
    # Edge case: just below threshold
    is_weak = detector.is_weak_area(0.39, 1, 0.5, 5)
    assert is_weak, "Mastery just below threshold should be weak"
    
    # Edge case: many questions, short retention
    is_weak = detector.is_weak_area(0.5, 10, 0.5, 1)
    assert is_weak, "Many questions with short retention should be weak"
    
    # Edge case: low complexity, moderate frequency
    is_weak = detector.is_weak_area(0.5, 5, 0.3, 5)
    assert is_weak, "Low complexity with moderate frequency should be weak"


def test_weakness_score_calculation():
    """
    Test weakness score calculation with known inputs
    """
    mock_db = None
    detector = WeakAreaDetector(mock_db)
    
    # Test case: struggling student (low mastery, high frequency, low complexity, short retention)
    weakness = detector.calculate_weakness_score(0.2, 20, 0.3, 1)
    assert weakness > 0.6, f"Struggling student should have high weakness score, got {weakness}"
    
    # Test case: mastering student (high mastery, low frequency, high complexity, long retention)
    weakness = detector.calculate_weakness_score(0.8, 2, 0.9, 20)
    assert weakness < 0.4, f"Mastering student should have low weakness score, got {weakness}"
    
    # Test case: moderate student
    weakness = detector.calculate_weakness_score(0.5, 5, 0.5, 5)
    assert 0.3 <= weakness <= 0.7, f"Moderate student should have moderate weakness score, got {weakness}"
