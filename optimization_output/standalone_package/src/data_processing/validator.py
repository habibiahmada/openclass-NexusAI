"""Validation and quality control for ETL pipeline.

This module provides functionality to validate processed data quality
at each stage of the pipeline and generate quality reports.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.data_processing.metadata_manager import EnrichedChunk

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result from a validation check."""
    check_name: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityReport:
    """Complete quality report for pipeline execution."""
    timestamp: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    validation_results: List[ValidationResult] = field(default_factory=list)
    overall_status: str = "PASS"  # PASS or FAIL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "overall_status": self.overall_status,
            "validation_results": [
                {
                    "check_name": vr.check_name,
                    "passed": vr.passed,
                    "message": vr.message,
                    "details": vr.details
                }
                for vr in self.validation_results
            ]
        }


class Validator:
    """Validates data quality at each stage of the ETL pipeline."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize validator with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.validation_results: List[ValidationResult] = []
    
    def validate_extraction(
        self, 
        pdf_files: List[Path], 
        processed_dir: str
    ) -> ValidationResult:
        """Validate that all PDF files have corresponding processed text files.
        
        Args:
            pdf_files: List of PDF file paths that were processed
            processed_dir: Directory containing processed text files
            
        Returns:
            ValidationResult indicating pass/fail status
        """
        logger.info("Validating extraction phase...")
        
        processed_path = Path(processed_dir)
        if not processed_path.exists():
            return ValidationResult(
                check_name="extraction_completeness",
                passed=False,
                message=f"Processed directory does not exist: {processed_dir}",
                details={"processed_dir": processed_dir}
            )
        
        missing_files = []
        found_files = []
        
        for pdf_file in pdf_files:
            # Expected text file name (replace .pdf with .txt)
            text_filename = pdf_file.stem + ".txt"
            text_file_path = processed_path / text_filename
            
            if text_file_path.exists():
                found_files.append(text_filename)
            else:
                missing_files.append(text_filename)
        
        passed = len(missing_files) == 0
        
        result = ValidationResult(
            check_name="extraction_completeness",
            passed=passed,
            message=(
                f"All {len(pdf_files)} PDF files have corresponding text files"
                if passed
                else f"{len(missing_files)} text files missing out of {len(pdf_files)}"
            ),
            details={
                "total_pdfs": len(pdf_files),
                "found_text_files": len(found_files),
                "missing_text_files": missing_files
            }
        )
        
        self.validation_results.append(result)
        logger.info(f"  {result.message}")
        
        return result
    
    def validate_chunks(
        self, 
        chunks: List[EnrichedChunk],
        expected_min_chunks: Optional[int] = None,
        expected_max_chunks: Optional[int] = None
    ) -> ValidationResult:
        """Validate chunk counts and properties.
        
        Args:
            chunks: List of enriched chunks to validate
            expected_min_chunks: Optional minimum expected chunk count
            expected_max_chunks: Optional maximum expected chunk count
            
        Returns:
            ValidationResult indicating pass/fail status
        """
        logger.info("Validating chunks...")
        
        if not chunks:
            return ValidationResult(
                check_name="chunk_validation",
                passed=False,
                message="No chunks found",
                details={"chunk_count": 0}
            )
        
        chunk_count = len(chunks)
        
        # Check if chunk count is within expected range
        passed = True
        messages = []
        
        if expected_min_chunks is not None and chunk_count < expected_min_chunks:
            passed = False
            messages.append(
                f"Chunk count {chunk_count} is below minimum {expected_min_chunks}"
            )
        
        if expected_max_chunks is not None and chunk_count > expected_max_chunks:
            passed = False
            messages.append(
                f"Chunk count {chunk_count} exceeds maximum {expected_max_chunks}"
            )
        
        # Validate chunk properties
        invalid_chunks = []
        for i, chunk in enumerate(chunks):
            if chunk.char_start >= chunk.char_end:
                invalid_chunks.append(f"Chunk {i}: invalid position (start >= end)")
            if not chunk.text or not chunk.text.strip():
                invalid_chunks.append(f"Chunk {i}: empty text")
        
        if invalid_chunks:
            passed = False
            messages.extend(invalid_chunks[:5])  # Limit to first 5 errors
        
        if passed:
            message = f"All {chunk_count} chunks are valid"
        else:
            message = "; ".join(messages)
        
        result = ValidationResult(
            check_name="chunk_validation",
            passed=passed,
            message=message,
            details={
                "chunk_count": chunk_count,
                "expected_min": expected_min_chunks,
                "expected_max": expected_max_chunks,
                "invalid_chunks": len(invalid_chunks)
            }
        )
        
        self.validation_results.append(result)
        logger.info(f"  {result.message}")
        
        return result
    
    def validate_embeddings(
        self, 
        embeddings: List[List[float]],
        expected_dimension: int = 1024,
        expected_count: Optional[int] = None
    ) -> ValidationResult:
        """Validate embedding dimensions and counts.
        
        Args:
            embeddings: List of embedding vectors to validate
            expected_dimension: Expected dimension of each embedding (default 1024)
            expected_count: Optional expected number of embeddings
            
        Returns:
            ValidationResult indicating pass/fail status
        """
        logger.info("Validating embeddings...")
        
        if not embeddings:
            return ValidationResult(
                check_name="embedding_validation",
                passed=False,
                message="No embeddings found",
                details={"embedding_count": 0}
            )
        
        embedding_count = len(embeddings)
        
        # Check dimension of each embedding
        invalid_dimensions = []
        for i, embedding in enumerate(embeddings):
            if len(embedding) != expected_dimension:
                invalid_dimensions.append(
                    f"Embedding {i}: dimension {len(embedding)} != {expected_dimension}"
                )
        
        # Check if count matches expected
        count_mismatch = False
        if expected_count is not None and embedding_count != expected_count:
            count_mismatch = True
        
        passed = len(invalid_dimensions) == 0 and not count_mismatch
        
        messages = []
        if invalid_dimensions:
            messages.append(
                f"{len(invalid_dimensions)} embeddings have invalid dimensions"
            )
        if count_mismatch:
            messages.append(
                f"Embedding count {embedding_count} != expected {expected_count}"
            )
        
        if passed:
            message = (
                f"All {embedding_count} embeddings have correct dimension "
                f"({expected_dimension})"
            )
        else:
            message = "; ".join(messages)
        
        result = ValidationResult(
            check_name="embedding_validation",
            passed=passed,
            message=message,
            details={
                "embedding_count": embedding_count,
                "expected_dimension": expected_dimension,
                "expected_count": expected_count,
                "invalid_dimensions": len(invalid_dimensions)
            }
        )
        
        self.validation_results.append(result)
        logger.info(f"  {result.message}")
        
        return result
    
    def validate_metadata(
        self, 
        chunks: List[EnrichedChunk]
    ) -> ValidationResult:
        """Validate that all required metadata fields are present and non-empty.
        
        Args:
            chunks: List of enriched chunks to validate
            
        Returns:
            ValidationResult indicating pass/fail status
        """
        logger.info("Validating metadata...")
        
        if not chunks:
            return ValidationResult(
                check_name="metadata_validation",
                passed=False,
                message="No chunks to validate",
                details={"chunk_count": 0}
            )
        
        required_fields = [
            "chunk_id", "text", "source_file", "subject", 
            "grade", "chunk_index", "char_start", "char_end"
        ]
        
        missing_fields = []
        empty_fields = []
        
        for i, chunk in enumerate(chunks):
            # Check all required fields exist
            for field in required_fields:
                if not hasattr(chunk, field):
                    missing_fields.append(f"Chunk {i}: missing field '{field}'")
                else:
                    value = getattr(chunk, field)
                    # Check non-empty for string fields
                    if field in ["chunk_id", "text", "source_file", "subject", "grade"]:
                        if not value or (isinstance(value, str) and not value.strip()):
                            empty_fields.append(f"Chunk {i}: empty field '{field}'")
        
        passed = len(missing_fields) == 0 and len(empty_fields) == 0
        
        messages = []
        if missing_fields:
            messages.append(f"{len(missing_fields)} missing field errors")
        if empty_fields:
            messages.append(f"{len(empty_fields)} empty field errors")
        
        if passed:
            message = f"All {len(chunks)} chunks have complete metadata"
        else:
            message = "; ".join(messages)
        
        result = ValidationResult(
            check_name="metadata_validation",
            passed=passed,
            message=message,
            details={
                "chunk_count": len(chunks),
                "required_fields": required_fields,
                "missing_fields": missing_fields[:5],  # Limit to first 5
                "empty_fields": empty_fields[:5]  # Limit to first 5
            }
        )
        
        self.validation_results.append(result)
        logger.info(f"  {result.message}")
        
        return result
    
    def generate_quality_report(
        self, 
        output_path: Optional[str] = None
    ) -> QualityReport:
        """Generate quality report with pass/fail status for each validation.
        
        Args:
            output_path: Optional path to save report as JSON
            
        Returns:
            QualityReport with all validation results
        """
        logger.info("Generating quality report...")
        
        total_checks = len(self.validation_results)
        passed_checks = sum(1 for vr in self.validation_results if vr.passed)
        failed_checks = total_checks - passed_checks
        
        overall_status = "PASS" if failed_checks == 0 else "FAIL"
        
        report = QualityReport(
            timestamp=datetime.now().isoformat(),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            validation_results=self.validation_results,
            overall_status=overall_status
        )
        
        # Save to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2)
            
            logger.info(f"Quality report saved to {output_path}")
        
        # Log summary
        logger.info("=" * 60)
        logger.info("QUALITY REPORT")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {overall_status}")
        logger.info(f"Total Checks: {total_checks}")
        logger.info(f"Passed: {passed_checks}")
        logger.info(f"Failed: {failed_checks}")
        logger.info("")
        
        for vr in self.validation_results:
            status_icon = "✓" if vr.passed else "✗"
            logger.info(f"{status_icon} {vr.check_name}: {vr.message}")
        
        logger.info("=" * 60)
        
        return report
    
    def reset(self):
        """Reset validation results."""
        self.validation_results = []
