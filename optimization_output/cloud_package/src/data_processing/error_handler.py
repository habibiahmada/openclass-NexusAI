"""Error handling and reporting for ETL pipeline.

This module provides error handling utilities and report generation
for the ETL pipeline.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class ErrorRecord:
    """Record of a single error."""
    timestamp: str
    phase: str  # extraction, chunking, embedding, storage
    file_path: str
    error_message: str
    error_type: str


@dataclass
class SummaryReport:
    """Summary report for pipeline execution."""
    pipeline_run_id: str
    start_time: str
    end_time: str
    processing_time_seconds: float
    
    # File processing stats
    total_files: int
    successful_files: int
    failed_files: int
    
    # Chunk and embedding stats
    total_chunks: int
    total_embeddings: int
    
    # Cost tracking
    tokens_processed: int
    estimated_cost_usd: float
    
    # Error tracking
    total_errors: int
    errors_by_phase: Dict[str, int] = field(default_factory=dict)
    error_details: List[ErrorRecord] = field(default_factory=list)
    
    # Status
    status: str = "completed"  # completed, partial, failed


class ErrorHandler:
    """Handles errors and generates reports for ETL pipeline."""
    
    def __init__(self, max_retries: int = 3):
        """Initialize error handler.
        
        Args:
            max_retries: Maximum number of retries for recoverable errors
        """
        self.max_retries = max_retries
        self.errors: List[ErrorRecord] = []
        self.failed_files: List[str] = []
        self.start_time: datetime = datetime.now()
    
    def record_error(
        self,
        phase: str,
        file_path: str,
        error: Exception,
        error_type: str = None
    ):
        """Record an error that occurred during pipeline execution.
        
        Args:
            phase: Pipeline phase where error occurred
            file_path: Path to file being processed
            error: Exception that was raised
            error_type: Optional error type classification
        """
        error_record = ErrorRecord(
            timestamp=datetime.now().isoformat(),
            phase=phase,
            file_path=file_path,
            error_message=str(error),
            error_type=error_type or type(error).__name__
        )
        
        self.errors.append(error_record)
        
        # Track failed files
        if file_path not in self.failed_files:
            self.failed_files.append(file_path)
        
        logger.error(
            f"Error in {phase} phase for {file_path}: {error_type or type(error).__name__} - {error}"
        )
    
    def should_retry(self, attempt: int) -> bool:
        """Determine if operation should be retried.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            True if should retry, False otherwise
        """
        return attempt < self.max_retries
    
    def get_backoff_time(self, attempt: int) -> float:
        """Calculate exponential backoff time.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Wait time in seconds
        """
        return 2 ** attempt  # 1, 2, 4, 8 seconds
    
    def generate_summary_report(
        self,
        pipeline_result: Any,
        output_path: str = None
    ) -> SummaryReport:
        """Generate summary report for pipeline execution.
        
        Args:
            pipeline_result: PipelineResult object from pipeline execution
            output_path: Optional path to save report JSON
            
        Returns:
            SummaryReport object
        """
        end_time = datetime.now()
        
        # Count errors by phase
        errors_by_phase = {}
        for error in self.errors:
            phase = error.phase
            errors_by_phase[phase] = errors_by_phase.get(phase, 0) + 1
        
        # Determine overall status
        if pipeline_result.failed_files == pipeline_result.total_files:
            status = "failed"
        elif pipeline_result.failed_files > 0:
            status = "partial"
        else:
            status = "completed"
        
        report = SummaryReport(
            pipeline_run_id=self.start_time.strftime("%Y%m%d_%H%M%S"),
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            processing_time_seconds=pipeline_result.processing_time,
            total_files=pipeline_result.total_files,
            successful_files=pipeline_result.successful_files,
            failed_files=pipeline_result.failed_files,
            total_chunks=pipeline_result.total_chunks,
            total_embeddings=pipeline_result.total_embeddings,
            tokens_processed=0,  # Will be set from embedding result
            estimated_cost_usd=pipeline_result.estimated_cost,
            total_errors=len(self.errors),
            errors_by_phase=errors_by_phase,
            error_details=self.errors,
            status=status
        )
        
        # Save report if output path provided
        if output_path:
            self._save_report(report, output_path)
        
        return report
    
    def _save_report(self, report: SummaryReport, output_path: str):
        """Save report to JSON file.
        
        Args:
            report: SummaryReport to save
            output_path: Path to save JSON file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict for JSON serialization
        report_dict = asdict(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Summary report saved to {output_file}")
    
    def print_summary(self, report: SummaryReport):
        """Print human-readable summary to console.
        
        Args:
            report: SummaryReport to print
        """
        print("\n" + "=" * 70)
        print("ETL PIPELINE EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Run ID: {report.pipeline_run_id}")
        print(f"Status: {report.status.upper()}")
        print(f"Duration: {report.processing_time_seconds:.2f} seconds")
        print()
        
        print("FILE PROCESSING:")
        print(f"  Total files: {report.total_files}")
        print(f"  Successful: {report.successful_files}")
        print(f"  Failed: {report.failed_files}")
        print()
        
        print("DATA PROCESSING:")
        print(f"  Total chunks: {report.total_chunks}")
        print(f"  Total embeddings: {report.total_embeddings}")
        print()
        
        print("COST TRACKING:")
        print(f"  Estimated cost: ${report.estimated_cost_usd:.4f}")
        print()
        
        if report.total_errors > 0:
            print("ERRORS:")
            print(f"  Total errors: {report.total_errors}")
            for phase, count in report.errors_by_phase.items():
                print(f"    {phase}: {count}")
            print()
            
            if report.error_details:
                print("ERROR DETAILS:")
                for i, error in enumerate(report.error_details[:5], 1):  # Show first 5
                    print(f"  {i}. [{error.phase}] {Path(error.file_path).name}")
                    print(f"     {error.error_type}: {error.error_message}")
                
                if len(report.error_details) > 5:
                    print(f"  ... and {len(report.error_details) - 5} more errors")
                print()
        
        print("=" * 70)
    
    def get_failed_files(self) -> List[str]:
        """Get list of files that failed processing.
        
        Returns:
            List of file paths that failed
        """
        return self.failed_files.copy()
    
    def get_error_count(self) -> int:
        """Get total number of errors recorded.
        
        Returns:
            Total error count
        """
        return len(self.errors)
    
    def reset(self):
        """Reset error handler state."""
        self.errors.clear()
        self.failed_files.clear()
        self.start_time = datetime.now()
