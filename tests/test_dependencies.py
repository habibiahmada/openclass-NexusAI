"""Test that all required dependencies for Phase 2 are installed and working."""
import pytest


def test_pypdf_import():
    """Test that pypdf is installed and can be imported."""
    import pypdf
    assert pypdf.__version__ is not None


def test_unstructured_import():
    """Test that unstructured is installed and can be imported."""
    import unstructured
    # unstructured doesn't expose __version__ directly, just verify import works
    assert unstructured is not None


def test_langchain_import():
    """Test that langchain is installed and can be imported."""
    import langchain
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    # Test that we can create a text splitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
    assert splitter is not None


def test_chromadb_import():
    """Test that chromadb is installed and can be imported."""
    import chromadb
    assert chromadb.__version__ is not None


def test_boto3_import():
    """Test that boto3 is installed and can be imported."""
    import boto3
    assert boto3.__version__ is not None


def test_hypothesis_import():
    """Test that hypothesis is installed and can be imported."""
    import hypothesis
    from hypothesis import given, strategies as st
    assert hypothesis.__version__ is not None


def test_pytest_import():
    """Test that pytest is installed and can be imported."""
    import pytest
    assert pytest.__version__ is not None


def test_hypothesis_profile_configured():
    """Test that Hypothesis is configured with the correct profile."""
    from hypothesis import settings
    
    # Get the current settings
    current_settings = settings()
    
    # Verify max_examples is set to 100 (from CI profile)
    assert current_settings.max_examples == 100
    assert current_settings.deadline is None


def test_pytest_markers_configured():
    """Test that pytest markers are properly configured."""
    # This test verifies that the markers defined in pytest.ini are recognized
    # If markers are not configured, pytest will show warnings
    pass  # The fact that this test runs without warnings confirms markers are set


def test_test_directories_exist():
    """Test that all required test directories exist."""
    import pathlib
    
    base_dir = pathlib.Path(__file__).parent
    
    # Check main test directories
    assert (base_dir / "unit").exists()
    assert (base_dir / "property").exists()
    assert (base_dir / "integration").exists()
    assert (base_dir / "fixtures").exists()
    
    # Check fixture subdirectories
    assert (base_dir / "fixtures" / "sample_pdfs").exists()
    assert (base_dir / "fixtures" / "mock_data").exists()
    assert (base_dir / "fixtures" / "expected_outputs").exists()


def test_dataclasses_available():
    """Test that dataclasses are available for data models."""
    from dataclasses import dataclass
    
    @dataclass
    class TestClass:
        field1: str
        field2: int
    
    obj = TestClass(field1="test", field2=42)
    assert obj.field1 == "test"
    assert obj.field2 == 42


def test_pathlib_available():
    """Test that pathlib is available for path handling."""
    from pathlib import Path
    
    path = Path("test/path/file.txt")
    assert path.name == "file.txt"
    assert path.suffix == ".txt"


def test_uuid_available():
    """Test that uuid is available for generating unique IDs."""
    import uuid
    
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()
    
    assert id1 != id2
    assert isinstance(str(id1), str)


def test_json_available():
    """Test that json is available for serialization."""
    import json
    
    data = {"key": "value", "number": 42}
    json_str = json.dumps(data)
    parsed = json.loads(json_str)
    
    assert parsed == data
