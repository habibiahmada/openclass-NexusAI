#!/usr/bin/env python3
"""
Main ETL Pipeline Script

This script orchestrates the complete ETL pipeline from PDF extraction
to ChromaDB storage and S3 upload. It provides a command-line interface
for running the pipeline with various configuration options.

Requirements:
- 8.1: Process all PDF files in the raw_dataset directory
- 8.4: Generate summary report with success/failure counts
- 9.5: Generate quality report with pass/fail status
- 10.5: Track costs and send alerts when budget threshold exceeded
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from src.data_processing.etl_pipeline import ETLPipeline, PipelineConfig, PipelineResult
from src.data_processing.validator import Validator
from src.data_processing.cost_tracker import CostTracker
from src.aws_control_plane.s3_storage_manager import S3StorageManager
from src.aws_control_plane.cloudfront_manager import CloudFrontManager
from src.aws_control_plane.job_tracker import JobTracker
from config.app_config import app_config


# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )


def parse_arguments():
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Run ETL pipeline to process PDFs into vector database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python scripts/run_etl_pipeline.py
  
  # Run with custom input directory
  python scripts/run_etl_pipeline.py --input-dir data/raw_dataset/kelas_10/informatika
  
  # Run without S3 upload
  python scripts/run_etl_pipeline.py --no-upload
  
  # Run with debug logging
  python scripts/run_etl_pipeline.py --log-level DEBUG
  
  # Run with custom budget limit
  python scripts/run_etl_pipeline.py --budget 0.50
        """
    )
    
    # Input/Output directories
    parser.add_argument(
        '--input-dir',
        type=str,
        default='data/raw_dataset/kelas_10/informatika',
        help='Input directory containing PDF files (default: data/raw_dataset/kelas_10/informatika)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/processed',
        help='Output directory for processed files (default: data/processed)'
    )
    
    parser.add_argument(
        '--vector-db-dir',
        type=str,
        default='data/vector_db',
        help='ChromaDB persistence directory (default: data/vector_db)'
    )
    
    # Processing parameters
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=800,
        help='Text chunk size in characters (default: 800)'
    )
    
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=100,
        help='Overlap between chunks in characters (default: 100)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=25,
        help='Batch size for embedding generation (default: 25)'
    )
    
    # Budget and cost tracking
    parser.add_argument(
        '--budget',
        type=float,
        default=1.0,
        help='Budget limit in USD (default: 1.00)'
    )
    
    # S3 upload options
    parser.add_argument(
        '--upload-to-s3',
        action='store_true',
        default=True,
        help='Upload processed files to S3 (enabled by default, use --no-upload to skip)'
    )
    
    parser.add_argument(
        '--no-upload',
        action='store_true',
        help='Skip S3 upload phase (overrides --upload-to-s3)'
    )
    
    parser.add_argument(
        '--subject',
        type=str,
        default='informatika',
        help='Subject area for S3 path structure (default: informatika)'
    )
    
    parser.add_argument(
        '--grade',
        type=str,
        default='kelas_10',
        help='Grade level for S3 path structure (default: kelas_10)'
    )
    
    # CloudFront cache invalidation
    parser.add_argument(
        '--invalidate-cache',
        action='store_true',
        help='Invalidate CloudFront cache after upload'
    )
    
    # Validation options
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip quality validation phase'
    )
    
    # Logging options
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Optional log file path'
    )
    
    return parser.parse_args()


def run_validation(
    pipeline_result: PipelineResult,
    config: PipelineConfig,
    validator: Validator
):
    """Run quality validation on pipeline results.
    
    Args:
        pipeline_result: Result from pipeline execution
        config: Pipeline configuration
        validator: Validator instance
    """
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 60)
    logger.info("Running Quality Validation")
    logger.info("=" * 60)
    
    # Get list of PDF files that were processed
    input_path = Path(config.input_dir)
    pdf_files = list(input_path.glob("*.pdf"))
    
    # Validate extraction
    validator.validate_extraction(
        pdf_files=pdf_files,
        processed_dir=f"{config.output_dir}/text"
    )
    
    # Validate chunks (if we have access to them)
    # Note: In production, we'd need to load chunks from storage
    # For now, we validate based on counts
    if pipeline_result.total_chunks > 0:
        # Estimate expected chunk range based on file count
        # Assuming ~200 chunks per file on average
        expected_min = pipeline_result.successful_files * 50
        expected_max = pipeline_result.successful_files * 500
        
        logger.info(
            f"Chunk count validation: {pipeline_result.total_chunks} chunks "
            f"(expected range: {expected_min}-{expected_max})"
        )
    
    # Validate embeddings
    if pipeline_result.total_embeddings > 0:
        logger.info(
            f"Embedding validation: {pipeline_result.total_embeddings} embeddings "
            f"(expected: {pipeline_result.total_chunks})"
        )
        
        # Check if embedding count matches chunk count
        if pipeline_result.total_embeddings == pipeline_result.total_chunks:
            logger.info("✓ Embedding count matches chunk count")
        else:
            logger.warning(
                f"✗ Embedding count mismatch: {pipeline_result.total_embeddings} != {pipeline_result.total_chunks}"
            )
    
    # Generate quality report
    quality_report = validator.generate_quality_report(
        output_path=f"{config.output_dir}/metadata/quality_report.json"
    )
    
    return quality_report


def run_s3_upload(
    config: PipelineConfig,
    subject: str,
    grade: str,
    cost_tracker: CostTracker
):
    """Upload processed files to S3.
    
    Args:
        config: Pipeline configuration
        subject: Subject area for S3 path
        grade: Grade level for S3 path
        cost_tracker: Cost tracker instance
    """
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 60)
    logger.info("Uploading to S3")
    logger.info("=" * 60)
    
    try:
        s3_manager = S3StorageManager()
        
        total_bytes = 0
        
        # Upload ChromaDB files
        logger.info("Uploading ChromaDB files...")
        chromadb_result = s3_manager.upload_chromadb_files(
            chromadb_dir=config.vector_db_dir,
            subject=subject,
            grade=grade
        )
        
        logger.info(
            f"ChromaDB upload: {chromadb_result.successful_uploads} successful, "
            f"{chromadb_result.failed_uploads} failed"
        )
        total_bytes += chromadb_result.total_bytes_uploaded
        
        # Upload processed text files
        logger.info("Uploading processed text files...")
        text_result = s3_manager.upload_processed_text(
            text_dir=f"{config.output_dir}/text",
            subject=subject,
            grade=grade
        )
        
        logger.info(
            f"Text upload: {text_result.successful_uploads} successful, "
            f"{text_result.failed_uploads} failed"
        )
        total_bytes += text_result.total_bytes_uploaded
        
        # Upload metadata files
        logger.info("Uploading metadata files...")
        metadata_result = s3_manager.upload_metadata(
            metadata_dir=f"{config.output_dir}/metadata",
            subject=subject,
            grade=grade
        )
        
        logger.info(
            f"Metadata upload: {metadata_result.successful_uploads} successful, "
            f"{metadata_result.failed_uploads} failed"
        )
        total_bytes += metadata_result.total_bytes_uploaded
        
        # Track S3 costs
        total_mb = total_bytes / (1024 * 1024)
        cost_tracker.track_s3_transfer(total_mb)
        
        logger.info(f"\nTotal uploaded: {total_mb:.2f} MB")
        logger.info(f"S3 cost: ${cost_tracker.calculate_s3_cost():.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"S3 upload failed: {e}", exc_info=True)
        return False


def run_cloudfront_invalidation(paths: Optional[list] = None):
    """Invalidate CloudFront cache for updated files.
    
    Args:
        paths: Optional list of paths to invalidate (defaults to all processed files)
    """
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 60)
    logger.info("Invalidating CloudFront Cache")
    logger.info("=" * 60)
    
    try:
        cloudfront_manager = CloudFrontManager()
        
        # Default paths to invalidate
        if paths is None:
            paths = [
                '/processed/*',  # All processed files
            ]
        
        logger.info(f"Invalidating paths: {paths}")
        
        result = cloudfront_manager.invalidate_cache(paths=paths)
        
        logger.info(f"✓ Cache invalidation created: {result.invalidation_id}")
        logger.info(f"  Status: {result.status}")
        
        return True
        
    except ValueError as e:
        logger.warning(f"CloudFront invalidation skipped: {e}")
        return False
    except Exception as e:
        logger.error(f"CloudFront invalidation failed: {e}", exc_info=True)
        return False


def print_final_summary(
    pipeline_result: PipelineResult,
    quality_report,
    s3_uploaded: bool,
    cache_invalidated: bool
):
    """Print final summary of pipeline execution.
    
    Args:
        pipeline_result: Pipeline execution result
        quality_report: Quality validation report
        s3_uploaded: Whether S3 upload succeeded
        cache_invalidated: Whether cache invalidation succeeded
    """
    print("\n" + "=" * 60)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 60)
    
    # Pipeline results
    print("\nProcessing Results:")
    print(f"  Total files: {pipeline_result.total_files}")
    print(f"  Successful: {pipeline_result.successful_files}")
    print(f"  Failed: {pipeline_result.failed_files}")
    print(f"  Total chunks: {pipeline_result.total_chunks}")
    print(f"  Total embeddings: {pipeline_result.total_embeddings}")
    print(f"  Processing time: {pipeline_result.processing_time:.2f}s")
    print(f"  Estimated cost: ${pipeline_result.estimated_cost:.4f}")
    
    # Quality validation
    if quality_report:
        print(f"\nQuality Validation:")
        print(f"  Overall status: {quality_report.overall_status}")
        print(f"  Checks passed: {quality_report.passed_checks}/{quality_report.total_checks}")
    
    # S3 upload
    print(f"\nS3 Upload: {'✓ Success' if s3_uploaded else '✗ Skipped/Failed'}")
    
    # CloudFront
    print(f"CloudFront Cache: {'✓ Invalidated' if cache_invalidated else '✗ Skipped/Failed'}")
    
    # Errors
    if pipeline_result.errors:
        print(f"\nErrors encountered: {len(pipeline_result.errors)}")
        print("  (See logs for details)")
    
    print("=" * 60)
    
    # Exit status
    if pipeline_result.failed_files > 0 or (quality_report and quality_report.overall_status == "FAIL"):
        print("\n⚠️  Pipeline completed with errors")
        return 1
    else:
        print("\n✓ Pipeline completed successfully!")
        return 0


def main():
    """Main entry point for ETL pipeline script."""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(log_level=args.log_level, log_file=args.log_file)
    logger = logging.getLogger(__name__)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize job tracker
    job_tracker = None
    job_id = None
    try:
        job_tracker = JobTracker()
        logger.info("✓ DynamoDB job tracker initialized")
    except Exception as e:
        logger.warning(f"Could not initialize job tracker: {e}")
        logger.warning("Continuing without job tracking...")
    
    logger.info("=" * 60)
    logger.info("OpenClass Nexus AI - ETL Pipeline")
    logger.info("=" * 60)
    logger.info(f"Input directory: {args.input_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Vector DB directory: {args.vector_db_dir}")
    logger.info(f"Budget limit: ${args.budget:.2f}")
    logger.info(f"S3 upload: {'Disabled' if args.no_upload else 'Enabled'}")
    logger.info(f"CloudFront invalidation: {'Enabled' if args.invalidate_cache else 'Disabled'}")
    logger.info("=" * 60)
    
    # Create pipeline configuration
    config = PipelineConfig(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        vector_db_dir=args.vector_db_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size,
        budget_limit=args.budget
    )
    
    # Start job tracking
    if job_tracker:
        try:
            job_id = job_tracker.start_job(
                job_type="etl_pipeline",
                input_dir=args.input_dir,
                config={
                    'chunk_size': args.chunk_size,
                    'chunk_overlap': args.chunk_overlap,
                    'batch_size': args.batch_size,
                    'budget_limit': args.budget
                }
            )
            logger.info(f"✓ Job tracking started: {job_id}")
        except Exception as e:
            logger.warning(f"Could not start job tracking: {e}")
    
    # Initialize pipeline
    pipeline = ETLPipeline(config)
    
    # Run pipeline
    try:
        logger.info("\nStarting ETL pipeline execution...")
        pipeline_result = pipeline.run()
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        print(f"\n✗ Pipeline failed: {e}")
        return 1
    
    # Run validation (unless skipped)
    quality_report = None
    if not args.skip_validation:
        try:
            validator = Validator()
            quality_report = run_validation(pipeline_result, config, validator)
        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
    
    # Upload to S3 (enabled by default, unless --no-upload specified)
    s3_uploaded = False
    if not args.no_upload:
        try:
            logger.info("\n📤 Uploading to S3 (use --no-upload to skip)...")
            s3_uploaded = run_s3_upload(
                config=config,
                subject=args.subject,
                grade=args.grade,
                cost_tracker=pipeline.cost_tracker
            )
        except Exception as e:
            logger.error(f"S3 upload failed: {e}", exc_info=True)
    else:
        logger.info("\n⏭️  S3 upload skipped (--no-upload flag)")
    
    # Invalidate CloudFront cache (if requested and upload succeeded)
    cache_invalidated = False
    if args.invalidate_cache and s3_uploaded:
        try:
            cache_invalidated = run_cloudfront_invalidation()
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}", exc_info=True)
    
    # Complete job tracking
    if job_tracker and job_id:
        try:
            status = "completed" if pipeline_result.failed_files == 0 else "partial"
            if pipeline_result.successful_files == 0:
                status = "failed"
            
            job_tracker.complete_job(
                job_id=job_id,
                status=status,
                total_files=pipeline_result.total_files,
                successful_files=pipeline_result.successful_files,
                failed_files=pipeline_result.failed_files,
                total_chunks=pipeline_result.total_chunks,
                total_embeddings=pipeline_result.total_embeddings,
                processing_time=pipeline_result.processing_time,
                estimated_cost=pipeline_result.estimated_cost,
                errors=pipeline_result.errors
            )
            logger.info(f"✓ Job tracking completed: {job_id}")
            
            # Print cost summary
            cost_summary = job_tracker.get_cost_summary(days=7)
            logger.info("\n" + "=" * 60)
            logger.info("Cost Summary (Last 7 Days)")
            logger.info("=" * 60)
            logger.info(f"Total jobs: {cost_summary['total_jobs']}")
            logger.info(f"Total cost: ${cost_summary['total_cost']:.4f}")
            logger.info(f"Average cost per job: ${cost_summary['average_cost_per_job']:.4f}")
            logger.info(f"Cost per file: ${cost_summary['cost_per_file']:.6f}")
            logger.info(f"Cost per embedding: ${cost_summary['cost_per_embedding']:.8f}")
            logger.info("=" * 60)
        except Exception as e:
            logger.warning(f"Could not complete job tracking: {e}")
    
    # Print final summary
    exit_code = print_final_summary(
        pipeline_result=pipeline_result,
        quality_report=quality_report,
        s3_uploaded=s3_uploaded,
        cache_invalidated=cache_invalidated
    )
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
