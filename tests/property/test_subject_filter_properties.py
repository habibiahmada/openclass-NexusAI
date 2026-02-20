"""
Property-based tests for subject filter propagation.

Feature: phase4-local-application
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.ui.subject_filter import map_subject_to_filter, SUBJECTS


class TestSubjectFilterPropagationProperty:
    """
    Property 4: Subject Filter Propagation
    
    **Validates: Requirements 1.5, 8.3**
    
    For any subject filter selection (including "Semua"), the system should correctly 
    map the UI selection to the pipeline filter parameter (None for "Semua", lowercase 
    subject name for specific subjects).
    """
    
    @given(
        # Generate random number of "Semua" selections
        num_selections=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_semua_maps_to_none(self, num_selections):
        """
        Property: "Semua" should always map to None filter.
        
        For any number of times "Semua" is selected, the filter should always be None,
        indicating no subject filtering should be applied.
        """
        for _ in range(num_selections):
            result = map_subject_to_filter("Semua")
            assert result is None, \
                "Subject filter 'Semua' should map to None for querying all subjects"
    
    @given(
        # Generate random specific subject selections from available subjects
        # Use only subjects that are actually in the SUBJECTS list (excluding "Semua")
        subject=st.sampled_from([s for s in SUBJECTS if s != "Semua"]) if len([s for s in SUBJECTS if s != "Semua"]) > 0 
                else st.just("Informatika")  # Fallback if only "Semua" exists
    )
    @settings(max_examples=100, deadline=None)
    def test_specific_subject_maps_to_lowercase(self, subject):
        """
        Property: Specific subjects should map to lowercase filter values.
        
        For any specific subject selection, the filter should be the lowercase
        version of the subject name (with special handling for multi-word subjects).
        """
        result = map_subject_to_filter(subject)
        
        # Verify result is not None
        assert result is not None, \
            f"Specific subject '{subject}' should not map to None"
        
        # Verify result is lowercase
        assert result.islower() or "_" in result, \
            f"Filter for '{subject}' should be lowercase or contain underscore"
        
        # Verify expected mappings for known subjects
        expected_mappings = {
            "Matematika": "matematika",
            "IPA": "ipa",
            "Bahasa Indonesia": "bahasa_indonesia",
            "Informatika": "informatika"
        }
        
        if subject in expected_mappings:
            assert result == expected_mappings[subject], \
                f"Subject '{subject}' should map to '{expected_mappings[subject]}', got '{result}'"
    
    @given(
        # Generate random sequences of subject selections
        subject_sequence=st.lists(
            st.sampled_from(SUBJECTS),
            min_size=1,
            max_size=30
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_filter_mapping_consistency(self, subject_sequence):
        """
        Property: Filter mapping should be consistent across multiple calls.
        
        For any sequence of subject selections, the same subject should always
        map to the same filter value (idempotent mapping).
        """
        # Track mappings
        mappings = {}
        
        for subject in subject_sequence:
            result = map_subject_to_filter(subject)
            
            if subject in mappings:
                # Verify consistency
                assert result == mappings[subject], \
                    f"Subject '{subject}' mapped to different values: '{mappings[subject]}' vs '{result}'"
            else:
                # Store first mapping
                mappings[subject] = result
        
        # Verify "Semua" always maps to None
        if "Semua" in mappings:
            assert mappings["Semua"] is None, \
                "'Semua' should consistently map to None"
    
    @given(
        # Generate random subject with different cases from available subjects
        subject=st.sampled_from([s for s in SUBJECTS if s != "Semua"]) if len([s for s in SUBJECTS if s != "Semua"]) > 0 
                else st.just("Informatika")  # Fallback
    )
    @settings(max_examples=100, deadline=None)
    def test_filter_propagation_to_pipeline_format(self, subject):
        """
        Property: Filter should be in correct format for pipeline consumption.
        
        For any specific subject, the filter should be a string in lowercase format
        that can be passed to the RAG pipeline for context retrieval.
        """
        result = map_subject_to_filter(subject)
        
        # Verify result is a string (not None for specific subjects)
        assert isinstance(result, str), \
            f"Filter for specific subject '{subject}' should be a string"
        
        # Verify no uppercase characters
        assert result == result.lower(), \
            f"Filter '{result}' should be all lowercase for pipeline compatibility"
        
        # Verify no spaces (should use underscores)
        assert " " not in result, \
            f"Filter '{result}' should not contain spaces (use underscores instead)"
    
    @given(
        # Generate all possible subject selections
        subject=st.sampled_from(SUBJECTS)
    )
    @settings(max_examples=100, deadline=None)
    def test_all_subjects_have_valid_mapping(self, subject):
        """
        Property: All subjects in SUBJECTS list should have valid mappings.
        
        For any subject in the SUBJECTS list, map_subject_to_filter should return
        either None (for "Semua") or a valid lowercase string.
        """
        result = map_subject_to_filter(subject)
        
        # Verify result is either None or a non-empty string
        assert result is None or (isinstance(result, str) and len(result) > 0), \
            f"Subject '{subject}' should map to None or a non-empty string"
        
        # If not "Semua", should be a string
        if subject != "Semua":
            assert isinstance(result, str), \
                f"Non-'Semua' subject '{subject}' should map to a string"
            assert len(result) > 0, \
                f"Filter for '{subject}' should not be empty"
    
    def test_semua_is_first_in_subjects_list(self):
        """
        Property: "Semua" should be the first option in SUBJECTS list.
        
        This ensures the default selection (index 0) is "Semua", which means
        no filtering by default.
        """
        assert len(SUBJECTS) > 0, "SUBJECTS list should not be empty"
        assert SUBJECTS[0] == "Semua", \
            "'Semua' should be the first option for default no-filter behavior"
    
    @given(
        # Generate random pairs of (subject, filter) to verify bidirectional consistency
        # Use only subjects that are actually in the SUBJECTS list
        subject=st.sampled_from([s for s in SUBJECTS if s != "Semua"])
    )
    @settings(max_examples=100, deadline=None)
    def test_filter_value_uniqueness(self, subject):
        """
        Property: Each subject should map to a unique filter value.
        
        For any specific subject, the filter value should be unique (no two subjects
        should map to the same filter value).
        """
        # Get all specific subjects (excluding "Semua")
        specific_subjects = [s for s in SUBJECTS if s != "Semua"]
        
        # Skip test if no specific subjects available
        if not specific_subjects:
            return
        
        # Map all subjects to filters
        filter_mappings = {s: map_subject_to_filter(s) for s in specific_subjects}
        
        # Get the filter for the current subject
        current_filter = filter_mappings[subject]
        
        # Count how many subjects map to this filter
        subjects_with_same_filter = [
            s for s, f in filter_mappings.items() 
            if f == current_filter
        ]
        
        # Should be exactly one subject with this filter
        assert len(subjects_with_same_filter) == 1, \
            f"Filter '{current_filter}' is used by multiple subjects: {subjects_with_same_filter}"
        assert subjects_with_same_filter[0] == subject, \
            f"Filter '{current_filter}' should uniquely identify '{subject}'"
    
    @given(
        # Generate random sequences alternating between "Semua" and specific subjects
        num_alternations=st.integers(min_value=1, max_value=15)
    )
    @settings(max_examples=100, deadline=None)
    def test_filter_alternation_between_all_and_specific(self, num_alternations):
        """
        Property: Alternating between "Semua" and specific subjects should work correctly.
        
        For any sequence of alternations between "Semua" (None filter) and specific
        subjects (lowercase filter), the mapping should be correct each time.
        """
        # Get specific subjects from SUBJECTS list
        specific_subjects = [s for s in SUBJECTS if s != "Semua"]
        
        # Skip test if no specific subjects available
        if not specific_subjects:
            return
        
        for i in range(num_alternations):
            if i % 2 == 0:
                # Test "Semua"
                result = map_subject_to_filter("Semua")
                assert result is None, \
                    f"Alternation {i}: 'Semua' should map to None"
            else:
                # Test a specific subject
                subject = specific_subjects[i % len(specific_subjects)]
                result = map_subject_to_filter(subject)
                assert result is not None, \
                    f"Alternation {i}: '{subject}' should not map to None"
                assert isinstance(result, str), \
                    f"Alternation {i}: '{subject}' should map to a string"
