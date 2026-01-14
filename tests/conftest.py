"""Pytest configuration and fixtures for Phase 2 tests"""
import pytest
from hypothesis import settings, Verbosity

# Configure Hypothesis profile for property-based testing
# This ensures all property tests run with 100 iterations
settings.register_profile("ci", max_examples=100, deadline=None)
settings.register_profile("dev", max_examples=10, deadline=None)
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose, deadline=None)

# Load the CI profile by default
settings.load_profile("ci")


@pytest.fixture
def sample_text():
    """Fixture providing sample text for testing."""
    return """
    Informatika adalah ilmu yang mempelajari tentang komputasi, informasi, dan automasi.
    Dalam kurikulum merdeka, informatika diajarkan mulai dari kelas 10.
    Materi yang dipelajari meliputi berpikir komputasional, teknologi informasi dan komunikasi,
    sistem komputer, jaringan komputer dan internet, analisis data, algoritma dan pemrograman,
    dampak sosial informatika, dan praktik lintas bidang.
    """


@pytest.fixture
def sample_metadata():
    """Fixture providing sample metadata for testing."""
    return {
        "subject": "informatika",
        "grade": "kelas_10",
        "filename": "test_file.pdf"
    }


@pytest.fixture
def fixtures_dir():
    """Fixture providing path to test fixtures directory."""
    import pathlib
    return pathlib.Path(__file__).parent / "fixtures"
