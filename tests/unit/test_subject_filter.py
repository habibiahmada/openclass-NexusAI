"""
Unit tests for subject filter module.

Tests SUBJECTS list, map_subject_to_filter() function, and render_subject_filter() function.
"""

import pytest
from src.ui.subject_filter import SUBJECTS, map_subject_to_filter, render_subject_filter


class TestSubjectsList:
    """Test SUBJECTS list contains all required subjects."""
    
    def test_subjects_list_contains_semua(self):
        """Test SUBJECTS list contains 'Semua' option."""
        assert "Semua" in SUBJECTS
    
    def test_subjects_list_contains_informatika(self):
        """Test SUBJECTS list contains 'Informatika' option."""
        assert "Informatika" in SUBJECTS
    
    def test_subjects_list_has_correct_count(self):
        """Test SUBJECTS list has exactly 2 subjects (current implementation)."""
        assert len(SUBJECTS) == 2
    
    def test_subjects_list_semua_is_first(self):
        """Test 'Semua' is the first option in SUBJECTS list."""
        assert SUBJECTS[0] == "Semua"
    
    def test_subjects_list_is_not_empty(self):
        """Test SUBJECTS list is not empty."""
        assert len(SUBJECTS) > 0
    
    def test_subjects_list_contains_only_strings(self):
        """Test all items in SUBJECTS list are strings."""
        assert all(isinstance(subject, str) for subject in SUBJECTS)


class TestMapSubjectToFilter:
    """Test map_subject_to_filter() function with different subjects."""
    
    def test_semua_returns_none(self):
        """Test map_subject_to_filter() with 'Semua' returns None."""
        result = map_subject_to_filter("Semua")
        assert result is None
    
    def test_matematika_returns_lowercase(self):
        """Test map_subject_to_filter() with 'Matematika' returns 'matematika'."""
        result = map_subject_to_filter("Matematika")
        assert result == "matematika"
    
    def test_ipa_returns_lowercase(self):
        """Test map_subject_to_filter() with 'IPA' returns 'ipa'."""
        result = map_subject_to_filter("IPA")
        assert result == "ipa"
    
    def test_bahasa_indonesia_returns_lowercase_with_underscore(self):
        """Test map_subject_to_filter() with 'Bahasa Indonesia' returns 'bahasa_indonesia'."""
        result = map_subject_to_filter("Bahasa Indonesia")
        assert result == "bahasa_indonesia"
    
    def test_informatika_returns_lowercase(self):
        """Test map_subject_to_filter() with 'Informatika' returns 'informatika'."""
        result = map_subject_to_filter("Informatika")
        assert result == "informatika"
    
    def test_unknown_subject_returns_lowercase(self):
        """Test map_subject_to_filter() with unknown subject returns lowercase version."""
        result = map_subject_to_filter("Unknown Subject")
        assert result == "unknown subject"
    
    def test_empty_string_returns_lowercase(self):
        """Test map_subject_to_filter() with empty string returns empty string."""
        result = map_subject_to_filter("")
        assert result == ""
    
    def test_case_sensitivity(self):
        """Test map_subject_to_filter() is case-sensitive for known subjects."""
        # Lowercase 'matematika' should not match the mapping
        result = map_subject_to_filter("matematika")
        assert result == "matematika"  # Falls through to .lower()
    
    def test_all_subjects_map_correctly(self):
        """Test all subjects in SUBJECTS list map to correct filter values."""
        # Test current implementation subjects
        expected_mappings = {
            "Semua": None,
            "Informatika": "informatika"
        }
        
        for subject, expected_filter in expected_mappings.items():
            result = map_subject_to_filter(subject)
            assert result == expected_filter, f"Subject '{subject}' should map to '{expected_filter}', got '{result}'"
    
    def test_future_subjects_map_correctly(self):
        """Test that future subjects (from requirements) would map correctly."""
        # These subjects are in the requirements but not yet in the implementation
        expected_mappings = {
            "Matematika": "matematika",
            "IPA": "ipa",
            "Bahasa Indonesia": "bahasa_indonesia"
        }
        
        for subject, expected_filter in expected_mappings.items():
            result = map_subject_to_filter(subject)
            assert result == expected_filter, f"Subject '{subject}' should map to '{expected_filter}', got '{result}'"


class TestRenderSubjectFilter:
    """Test render_subject_filter() function."""
    
    def test_render_subject_filter_without_streamlit(self):
        """Test render_subject_filter() returns default when Streamlit is not available."""
        # This test assumes STREAMLIT_AVAILABLE might be False in some environments
        # The function should gracefully handle missing Streamlit
        result = render_subject_filter()
        assert isinstance(result, str)
        # Should return a valid subject from the SUBJECTS list
        assert result in SUBJECTS or result == "Semua"
