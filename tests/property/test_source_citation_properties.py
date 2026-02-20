"""Property-based tests for source citation formatting.

Feature: phase4-local-application
"""

import pytest
import re
from hypothesis import given, strategies as st, settings

from src.ui.models import SourceCitation


# Feature: phase4-local-application, Property 3: Source Citation Completeness
@settings(max_examples=100)
@given(
    filename=st.text(min_size=1, max_size=200, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='\n\r\t'
    )),
    subject=st.sampled_from(["Matematika", "IPA", "Bahasa Indonesia", "Informatika"]),
    relevance_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    chunk_index=st.integers(min_value=0, max_value=1000)
)
def test_property_source_citation_completeness(filename, subject, relevance_score, chunk_index):
    """Property 3: For any response generated with sources, each source citation should 
    include filename, subject, and relevance score in the format 
    "📚 [Subject] - [Filename] (Relevance: [Score])".
    
    **Validates: Requirements 1.4, 6.1, 6.2, 6.3, 6.5**
    """
    # Create a source citation with random valid data
    citation = SourceCitation(
        filename=filename,
        subject=subject,
        relevance_score=relevance_score,
        chunk_index=chunk_index
    )
    
    # Format the citation
    formatted = citation.format_citation()
    
    # Property 1: Citation must start with the book emoji
    assert formatted.startswith("📚 "), \
        f"Citation must start with '📚 ', got: {formatted}"
    
    # Property 2: Citation must contain the subject
    assert subject in formatted, \
        f"Citation must contain subject '{subject}', got: {formatted}"
    
    # Property 3: Citation must contain the filename
    assert filename in formatted, \
        f"Citation must contain filename '{filename}', got: {formatted}"
    
    # Property 4: Citation must contain relevance score formatted to 2 decimal places
    expected_score = f"{relevance_score:.2f}"
    assert expected_score in formatted, \
        f"Citation must contain relevance score '{expected_score}', got: {formatted}"
    
    # Property 5: Citation must follow the exact format pattern
    # Pattern: 📚 [Subject] - [Filename] (Relevance: [Score])
    # We'll verify the structure by checking key components are in the right order
    
    # Find positions of key components
    emoji_pos = formatted.find("📚")
    subject_pos = formatted.find(subject)
    dash_pos = formatted.find(" - ")
    filename_pos = formatted.find(filename)
    relevance_label_pos = formatted.find("(Relevance: ")
    score_pos = formatted.find(expected_score)
    closing_paren_pos = formatted.rfind(")")
    
    # Verify all components are present
    assert emoji_pos != -1, "Missing emoji"
    assert subject_pos != -1, "Missing subject"
    assert dash_pos != -1, "Missing dash separator"
    assert filename_pos != -1, "Missing filename"
    assert relevance_label_pos != -1, "Missing relevance label"
    assert score_pos != -1, "Missing score"
    assert closing_paren_pos != -1, "Missing closing parenthesis"
    
    # Verify components are in the correct order
    assert emoji_pos < subject_pos, "Emoji must come before subject"
    assert subject_pos < dash_pos, "Subject must come before dash"
    assert dash_pos < filename_pos, "Dash must come before filename"
    assert filename_pos < relevance_label_pos, "Filename must come before relevance label"
    assert relevance_label_pos < score_pos, "Relevance label must come before score"
    assert score_pos < closing_paren_pos, "Score must come before closing parenthesis"
    
    # Property 6: Citation must match the exact format using regex
    # Pattern: 📚 [Subject] - [Filename] (Relevance: [Score])
    pattern = r"^📚 .+ - .+ \(Relevance: \d+\.\d{2}\)$"
    assert re.match(pattern, formatted), \
        f"Citation doesn't match expected format pattern, got: {formatted}"


# Feature: phase4-local-application, Property 3: Source Citation Score Formatting
@settings(max_examples=100)
@given(
    relevance_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
)
def test_property_source_citation_score_formatting(relevance_score):
    """Property 3 (Score Formatting): For any relevance score, the formatted citation 
    should display the score with exactly 2 decimal places.
    
    **Validates: Requirements 6.3**
    """
    citation = SourceCitation(
        filename="test.pdf",
        subject="Matematika",
        relevance_score=relevance_score,
        chunk_index=0
    )
    
    formatted = citation.format_citation()
    
    # Extract the score from the formatted string
    score_match = re.search(r"Relevance: (\d+\.\d+)", formatted)
    assert score_match is not None, f"Could not find score in formatted citation: {formatted}"
    
    formatted_score = score_match.group(1)
    
    # Verify exactly 2 decimal places
    decimal_part = formatted_score.split('.')[1]
    assert len(decimal_part) == 2, \
        f"Score must have exactly 2 decimal places, got: {formatted_score}"
    
    # Verify the score value matches (within floating point precision)
    parsed_score = float(formatted_score)
    assert abs(parsed_score - relevance_score) < 0.01, \
        f"Formatted score {parsed_score} doesn't match original {relevance_score}"


# Feature: phase4-local-application, Property 3: Source Citation Immutability
@settings(max_examples=100)
@given(
    filename=st.text(min_size=1, max_size=100),
    subject=st.sampled_from(["Matematika", "IPA", "Bahasa Indonesia", "Informatika"]),
    relevance_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    chunk_index=st.integers(min_value=0, max_value=1000)
)
def test_property_source_citation_immutability(filename, subject, relevance_score, chunk_index):
    """Property 3 (Immutability): For any source citation, calling format_citation() 
    multiple times should produce the same result.
    
    **Validates: Requirements 6.5**
    """
    citation = SourceCitation(
        filename=filename,
        subject=subject,
        relevance_score=relevance_score,
        chunk_index=chunk_index
    )
    
    # Format multiple times
    formatted1 = citation.format_citation()
    formatted2 = citation.format_citation()
    formatted3 = citation.format_citation()
    
    # All results should be identical
    assert formatted1 == formatted2, \
        "Multiple calls to format_citation() should produce identical results"
    assert formatted2 == formatted3, \
        "Multiple calls to format_citation() should produce identical results"
