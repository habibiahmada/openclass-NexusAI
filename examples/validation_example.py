"""Example demonstrating validation and quality control usage.

This example shows how to use the Validator class to validate
data at each stage of the ETL pipeline.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processing.validator import Validator
from src.data_processing.metadata_manager import EnrichedChunk


def main():
    """Demonstrate validation functionality."""
    
    print("=" * 60)
    print("Validation and Quality Control Example")
    print("=" * 60)
    print()
    
    # Create validator
    validator = Validator()
    
    # Example 1: Validate extraction
    print("1. Validating PDF extraction...")
    print("-" * 60)
    
    # Simulate PDF files
    pdf_files = [
        Path("data/raw_dataset/kelas_10/informatika/file1.pdf"),
        Path("data/raw_dataset/kelas_10/informatika/file2.pdf"),
        Path("data/raw_dataset/kelas_10/informatika/file3.pdf")
    ]
    
    # Note: This will fail if files don't exist, which is expected for this example
    result = validator.validate_extraction(
        pdf_files=pdf_files,
        processed_dir="data/processed/text"
    )
    
    print(f"Status: {'PASS' if result.passed else 'FAIL'}")
    print(f"Message: {result.message}")
    print(f"Details: {result.details}")
    print()
    
    # Example 2: Validate chunks
    print("2. Validating text chunks...")
    print("-" * 60)
    
    # Create sample chunks
    chunks = [
        EnrichedChunk(
            chunk_id=f"chunk_{i}",
            text=f"This is sample chunk {i} with some educational content.",
            source_file="test.pdf",
            subject="informatika",
            grade="kelas_10",
            chunk_index=i,
            char_start=i * 100,
            char_end=(i + 1) * 100
        )
        for i in range(10)
    ]
    
    result = validator.validate_chunks(
        chunks=chunks,
        expected_min_chunks=5,
        expected_max_chunks=20
    )
    
    print(f"Status: {'PASS' if result.passed else 'FAIL'}")
    print(f"Message: {result.message}")
    print(f"Details: {result.details}")
    print()
    
    # Example 3: Validate embeddings
    print("3. Validating embeddings...")
    print("-" * 60)
    
    # Create sample embeddings (1024-dimensional)
    embeddings = [
        [0.1] * 1024
        for _ in range(10)
    ]
    
    result = validator.validate_embeddings(
        embeddings=embeddings,
        expected_dimension=1024,
        expected_count=10
    )
    
    print(f"Status: {'PASS' if result.passed else 'FAIL'}")
    print(f"Message: {result.message}")
    print(f"Details: {result.details}")
    print()
    
    # Example 4: Validate metadata
    print("4. Validating metadata completeness...")
    print("-" * 60)
    
    result = validator.validate_metadata(chunks=chunks)
    
    print(f"Status: {'PASS' if result.passed else 'FAIL'}")
    print(f"Message: {result.message}")
    print(f"Details: {result.details}")
    print()
    
    # Example 5: Generate quality report
    print("5. Generating quality report...")
    print("-" * 60)
    
    report = validator.generate_quality_report(
        output_path="data/processed/metadata/quality_report.json"
    )
    
    print(f"\nQuality Report Summary:")
    print(f"  Overall Status: {report.overall_status}")
    print(f"  Total Checks: {report.total_checks}")
    print(f"  Passed: {report.passed_checks}")
    print(f"  Failed: {report.failed_checks}")
    print()
    
    print("=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
