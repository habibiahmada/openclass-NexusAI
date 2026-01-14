"""Test to verify pytest and Hypothesis configuration"""
import pytest
from hypothesis import given, strategies as st, settings


def test_pytest_works():
    """Verify pytest is working correctly."""
    assert True


@pytest.mark.property
@given(x=st.integers())
def test_hypothesis_configured(x):
    """Verify Hypothesis is configured with 100 iterations."""
    # This test will run 100 times with different integer values
    assert isinstance(x, int)


def test_fixtures_available(sample_text, sample_metadata, fixtures_dir):
    """Verify that conftest fixtures are available."""
    assert sample_text is not None
    assert "Informatika" in sample_text
    assert sample_metadata["subject"] == "informatika"
    assert sample_metadata["grade"] == "kelas_10"
    assert fixtures_dir.exists()
