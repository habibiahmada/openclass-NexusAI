"""
Property Test: Version Comparison Correctness

**Property 18: Version Comparison Correctness**
**Validates: Requirements 7.2**

This test verifies that semantic version comparison is correct and consistent.

Test Strategy:
- Generate random semantic versions (MAJOR.MINOR.PATCH)
- Verify comparison is transitive (if A > B and B > C, then A > C)
- Verify comparison is consistent with string ordering
- Verify reflexivity (A == A)
- Verify antisymmetry (if A > B, then B < A)
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.vkp.puller import VKPPuller
from src.vkp.version_manager import VKPVersionManager


# Strategy for generating semantic versions
@st.composite
def semantic_version(draw):
    """Generate a valid semantic version string."""
    major = draw(st.integers(min_value=0, max_value=100))
    minor = draw(st.integers(min_value=0, max_value=100))
    patch = draw(st.integers(min_value=0, max_value=100))
    return f"{major}.{minor}.{patch}"


class TestVersionComparisonCorrectness:
    """Property tests for version comparison correctness."""
    
    @given(version=semantic_version())
    def test_version_reflexivity(self, version):
        """
        Property: A version is always equal to itself.
        
        For any version V, compare_versions(V, V) should return "up_to_date".
        """
        # Create a mock puller (we only need the compare_versions method)
        puller = VKPPuller(
            bucket_name='test-bucket',
            version_manager=None,
            chroma_manager=None,
            book_repository=None
        )
        
        result = puller.compare_versions(version, version)
        
        assert result == "up_to_date", \
            f"Version {version} should be equal to itself"
    
    @given(v1=semantic_version(), v2=semantic_version())
    def test_version_antisymmetry(self, v1, v2):
        """
        Property: If v1 > v2, then v2 < v1 (antisymmetry).
        
        If compare_versions(v1, v2) returns "local_newer",
        then compare_versions(v2, v1) should return "update_available".
        """
        assume(v1 != v2)  # Skip if versions are equal
        
        puller = VKPPuller(
            bucket_name='test-bucket',
            version_manager=None,
            chroma_manager=None,
            book_repository=None
        )
        
        result1 = puller.compare_versions(v1, v2)
        result2 = puller.compare_versions(v2, v1)
        
        # Antisymmetry check
        if result1 == "update_available":
            assert result2 == "local_newer", \
                f"If {v1} < {v2}, then {v2} > {v1}"
        elif result1 == "local_newer":
            assert result2 == "update_available", \
                f"If {v1} > {v2}, then {v2} < {v1}"
    
    @given(
        v1=semantic_version(),
        v2=semantic_version(),
        v3=semantic_version()
    )
    def test_version_transitivity(self, v1, v2, v3):
        """
        Property: Version comparison is transitive.
        
        If v1 < v2 and v2 < v3, then v1 < v3.
        """
        puller = VKPPuller(
            bucket_name='test-bucket',
            version_manager=None,
            chroma_manager=None,
            book_repository=None
        )
        
        result_12 = puller.compare_versions(v1, v2)
        result_23 = puller.compare_versions(v2, v3)
        result_13 = puller.compare_versions(v1, v3)
        
        # Transitivity check: if v1 < v2 and v2 < v3, then v1 < v3
        if result_12 == "update_available" and result_23 == "update_available":
            assert result_13 == "update_available", \
                f"Transitivity violated: {v1} < {v2} < {v3} but {v1} >= {v3}"
        
        # Transitivity check: if v1 > v2 and v2 > v3, then v1 > v3
        if result_12 == "local_newer" and result_23 == "local_newer":
            assert result_13 == "local_newer", \
                f"Transitivity violated: {v1} > {v2} > {v3} but {v1} <= {v3}"
    
    @given(v1=semantic_version(), v2=semantic_version())
    def test_version_comparison_consistency(self, v1, v2):
        """
        Property: Version comparison is consistent with numeric ordering.
        
        Parse versions as tuples and verify comparison matches numeric ordering.
        """
        puller = VKPPuller(
            bucket_name='test-bucket',
            version_manager=None,
            chroma_manager=None,
            book_repository=None
        )
        
        result = puller.compare_versions(v1, v2)
        
        # Parse versions
        v1_parts = tuple(int(x) for x in v1.split('.'))
        v2_parts = tuple(int(x) for x in v2.split('.'))
        
        # Verify consistency
        if v1_parts < v2_parts:
            assert result == "update_available", \
                f"Expected update_available for {v1} < {v2}, got {result}"
        elif v1_parts > v2_parts:
            assert result == "local_newer", \
                f"Expected local_newer for {v1} > {v2}, got {result}"
        else:
            assert result == "up_to_date", \
                f"Expected up_to_date for {v1} == {v2}, got {result}"
    
    @given(major=st.integers(min_value=0, max_value=10))
    def test_major_version_dominates(self, major):
        """
        Property: Major version changes dominate minor and patch changes.
        
        v(N+1).0.0 > v(N).99.99 for any N.
        """
        v1 = f"{major}.99.99"
        v2 = f"{major + 1}.0.0"
        
        puller = VKPPuller(
            bucket_name='test-bucket',
            version_manager=None,
            chroma_manager=None,
            book_repository=None
        )
        
        result = puller.compare_versions(v1, v2)
        
        assert result == "update_available", \
            f"Major version should dominate: {v1} < {v2}"
    
    @given(
        major=st.integers(min_value=0, max_value=10),
        minor=st.integers(min_value=0, max_value=10)
    )
    def test_minor_version_dominates_patch(self, major, minor):
        """
        Property: Minor version changes dominate patch changes.
        
        v(M).(N+1).0 > v(M).(N).99 for any M, N.
        """
        v1 = f"{major}.{minor}.99"
        v2 = f"{major}.{minor + 1}.0"
        
        puller = VKPPuller(
            bucket_name='test-bucket',
            version_manager=None,
            chroma_manager=None,
            book_repository=None
        )
        
        result = puller.compare_versions(v1, v2)
        
        assert result == "update_available", \
            f"Minor version should dominate patch: {v1} < {v2}"
    
    def test_version_manager_compare_consistency(self):
        """
        Property: VKPVersionManager.compare_versions is consistent with VKPPuller.
        
        Both should return the same comparison result.
        """
        from unittest.mock import Mock
        
        # Create mock database manager
        mock_db = Mock()
        version_manager = VKPVersionManager(mock_db)
        
        puller = VKPPuller(
            bucket_name='test-bucket',
            version_manager=version_manager,
            chroma_manager=None,
            book_repository=None
        )
        
        test_cases = [
            ("1.0.0", "1.0.0", 0),
            ("1.0.0", "1.0.1", -1),
            ("1.0.1", "1.0.0", 1),
            ("1.0.0", "2.0.0", -1),
            ("2.0.0", "1.0.0", 1),
            ("1.2.3", "1.2.4", -1),
        ]
        
        for v1, v2, expected_vm_result in test_cases:
            # VKPVersionManager result
            vm_result = version_manager.compare_versions(v1, v2)
            
            # VKPPuller result
            puller_result = puller.compare_versions(v1, v2)
            
            # Map VKPPuller result to numeric
            puller_numeric = {
                "update_available": -1,
                "up_to_date": 0,
                "local_newer": 1
            }[puller_result]
            
            assert vm_result == expected_vm_result, \
                f"VKPVersionManager.compare_versions({v1}, {v2}) = {vm_result}, expected {expected_vm_result}"
            
            assert puller_numeric == expected_vm_result, \
                f"VKPPuller.compare_versions({v1}, {v2}) = {puller_result} ({puller_numeric}), expected {expected_vm_result}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
