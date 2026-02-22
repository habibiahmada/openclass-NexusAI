"""
Property Test: Topic Classification and Mastery Update

**Property 8: Topic Classification and Mastery Update**
**Validates: Requirements 4.5**

The mastery tracker must classify questions into topics and update mastery tracking.

This property ensures that:
1. Topic classification always returns a valid topic string
2. Topic classification is consistent for similar questions
3. Questions containing topic keywords are classified correctly
4. Question complexity calculation is always in bounds [0.0, 1.0]
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from src.pedagogy.mastery_tracker import MasteryTracker


# Strategy for generating questions
question_strategy = st.text(min_size=5, max_size=200, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),  # Letters, numbers, spaces
    whitelist_characters='?.,!áéíóúÁÉÍÓÚ'
))


@given(question=question_strategy)
@settings(max_examples=300, deadline=None)
def test_topic_classification_always_returns_string(question):
    """
    Property: Topic classification must always return a non-empty string
    
    For any question text, classify_topic must return a valid topic name.
    """
    # Skip empty or whitespace-only questions
    assume(question.strip())
    
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    topic = tracker.classify_topic(question, 'matematika')
    
    # Property: topic must be a non-empty string
    assert isinstance(topic, str), f"Topic is not a string: {type(topic)}"
    assert len(topic) > 0, "Topic is empty string"


@given(question=question_strategy)
@settings(max_examples=300, deadline=None)
def test_topic_classification_is_consistent(question):
    """
    Property: Topic classification must be consistent (same input = same output)
    
    Classifying the same question multiple times should return the same topic.
    """
    assume(question.strip())
    
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    topic1 = tracker.classify_topic(question, 'matematika')
    topic2 = tracker.classify_topic(question, 'matematika')
    
    # Property: classification must be consistent
    assert topic1 == topic2, (
        f"Inconsistent classification for question '{question}': "
        f"got '{topic1}' and '{topic2}'"
    )


@given(question=question_strategy)
@settings(max_examples=300, deadline=None)
def test_complexity_always_in_bounds(question):
    """
    Property: Question complexity must always be between 0.0 and 1.0
    
    For any question text, calculate_question_complexity must return
    a value in [0.0, 1.0].
    """
    assume(question.strip())
    
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    complexity = tracker.calculate_question_complexity(question)
    
    # Property: complexity must be in bounds [0.0, 1.0]
    assert 0.0 <= complexity <= 1.0, (
        f"Complexity {complexity} out of bounds for question: '{question}'"
    )


def test_topic_classification_with_keywords():
    """
    Test that questions containing topic keywords are classified correctly
    """
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Test matematika topics
    test_cases = [
        ("Bagaimana cara menyelesaikan persamaan linear?", "aljabar"),
        ("Hitung luas segitiga dengan alas 5 cm", "geometri"),
        ("Apa itu teorema Pythagoras?", "geometri"),
        ("Jelaskan tentang sinus dan cosinus", "trigonometri"),
        ("Bagaimana cara menghitung integral dan turunan?", "kalkulus"),
        ("Apa itu mean dan median?", "statistika"),
        ("Bagaimana cara menghitung determinan matriks?", "matriks"),
    ]
    
    for question, expected_topic in test_cases:
        topic = tracker.classify_topic(question, 'matematika')
        assert topic == expected_topic, (
            f"Question '{question}' classified as '{topic}', expected '{expected_topic}'"
        )


def test_topic_classification_informatika():
    """
    Test topic classification for informatika subject
    """
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Test informatika topics
    test_cases = [
        ("Bagaimana cara menulis program Python?", "pemrograman"),
        ("Apa itu linked list?", "struktur_data"),
        ("Jelaskan tentang SQL query", "database"),
        ("Apa itu protokol TCP/IP?", "jaringan"),
        ("Bagaimana cara enkripsi password?", "keamanan"),
    ]
    
    for question, expected_topic in test_cases:
        topic = tracker.classify_topic(question, 'informatika')
        assert topic == expected_topic, (
            f"Question '{question}' classified as '{topic}', expected '{expected_topic}'"
        )


def test_topic_classification_fallback():
    """
    Test that questions without clear keywords fall back to 'general'
    """
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Questions without specific topic keywords
    generic_questions = [
        "Apa itu matematika?",
        "Saya tidak mengerti",
        "Tolong jelaskan lebih detail",
        "Bagaimana cara belajar?",
    ]
    
    for question in generic_questions:
        topic = tracker.classify_topic(question, 'matematika')
        assert topic == 'general', (
            f"Generic question '{question}' should be classified as 'general', got '{topic}'"
        )


def test_complexity_increases_with_length():
    """
    Test that longer questions generally have higher complexity
    """
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Short simple question
    short_question = "Apa itu x?"
    short_complexity = tracker.calculate_question_complexity(short_question)
    
    # Long complex question
    long_question = (
        "Bagaimana cara menganalisis dan membandingkan berbagai metode "
        "untuk menyelesaikan persamaan diferensial parsial dengan kondisi "
        "batas yang kompleks dan jelaskan mengapa metode tertentu lebih "
        "efektif dalam situasi tertentu?"
    )
    long_complexity = tracker.calculate_question_complexity(long_question)
    
    # Property: longer questions should have higher or equal complexity
    assert long_complexity >= short_complexity, (
        f"Long question has lower complexity ({long_complexity}) than "
        f"short question ({short_complexity})"
    )


def test_complexity_increases_with_keywords():
    """
    Test that questions with complexity keywords have higher complexity
    """
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Simple question without complexity keywords
    simple_question = "Hitung nilai x"
    simple_complexity = tracker.calculate_question_complexity(simple_question)
    
    # Complex question with complexity keywords
    complex_question = "Jelaskan mengapa dan bagaimana cara membuktikan teorema ini"
    complex_complexity = tracker.calculate_question_complexity(complex_question)
    
    # Property: questions with complexity keywords should have higher complexity
    assert complex_complexity > simple_complexity, (
        f"Complex question has lower complexity ({complex_complexity}) than "
        f"simple question ({simple_complexity})"
    )


def test_complexity_edge_cases():
    """
    Test edge cases for complexity calculation
    """
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Edge case: very short question
    complexity = tracker.calculate_question_complexity("x?")
    assert 0.0 <= complexity <= 1.0
    assert complexity < 0.3, "Very short question should have low complexity"
    
    # Edge case: very long question (> 50 words)
    long_question = " ".join(["word"] * 100)
    complexity = tracker.calculate_question_complexity(long_question)
    assert 0.0 <= complexity <= 1.0
    
    # Edge case: question with many complexity keywords
    complex_question = "Mengapa bagaimana jelaskan buktikan analisis bandingkan evaluasi"
    complexity = tracker.calculate_question_complexity(complex_question)
    assert 0.0 <= complexity <= 1.0
    assert complexity > 0.5, "Question with many complexity keywords should have high complexity"


def test_case_insensitive_classification():
    """
    Test that topic classification is case-insensitive
    """
    mock_db = None
    tracker = MasteryTracker(mock_db)
    
    # Test with different cases
    questions = [
        "Bagaimana cara menyelesaikan PERSAMAAN linear?",
        "bagaimana cara menyelesaikan persamaan linear?",
        "BAGAIMANA CARA MENYELESAIKAN PERSAMAAN LINEAR?",
    ]
    
    topics = [tracker.classify_topic(q, 'matematika') for q in questions]
    
    # All should classify to the same topic
    assert len(set(topics)) == 1, (
        f"Case-insensitive classification failed: got topics {topics}"
    )
    assert topics[0] == 'aljabar', f"Expected 'aljabar', got '{topics[0]}'"
