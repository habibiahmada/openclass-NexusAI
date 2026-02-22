#!/usr/bin/env python3
"""
Telemetry Upload Cron Job

Runs hourly to:
1. Aggregate metrics from collector
2. Verify no PII in telemetry data
3. Upload to DynamoDB if online
4. Queue locally if offline
"""

import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.telemetry.collector import get_collector
from src.telemetry.aggregator import MetricsAggregator
from src.telemetry.pii_verifier import PIIVerifier
from src.telemetry.uploader import TelemetryUploader, check_internet_connectivity
from src.telemetry.anonymizer import get_anonymizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telemetry_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main telemetry upload workflow"""
    logger.info("=" * 60)
    logger.info("Starting telemetry upload job")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    try:
        # 1. Get metrics snapshot from collector
        collector = get_collector()
        snapshot = collector.get_metrics_snapshot()
        
        logger.info(f"Collected metrics: {snapshot.total_queries} queries")
        
        # Skip if no queries recorded
        if snapshot.total_queries == 0:
            logger.info("No queries recorded, skipping upload")
            return
        
        # 2. Get school ID and anonymize it
        school_id = os.getenv('SCHOOL_ID', 'default-school')
        anonymizer = get_anonymizer()
        anonymized_school_id = anonymizer.anonymize_school_id(school_id)
        
        logger.info(f"School ID anonymized: {school_id} -> {anonymized_school_id}")
        
        # 3. Aggregate metrics
        aggregator = MetricsAggregator(anonymized_school_id)
        metrics = aggregator.aggregate_hourly(snapshot)
        
        logger.info(f"Aggregated metrics: avg_latency={metrics.average_latency_ms:.2f}ms, "
                   f"error_rate={metrics.error_rate:.2%}")
        
        # 4. Verify no PII
        verifier = PIIVerifier()
        metrics_dict = metrics.to_dict()
        
        if not verifier.verify_no_pii(metrics_dict):
            logger.error("PII VERIFICATION FAILED - ABORTING UPLOAD")
            logger.error("Telemetry data contains PII and will NOT be uploaded")
            return
        
        logger.info("PII verification passed")
        
        # 5. Validate schema
        is_valid, error_msg = verifier.validate_schema(metrics_dict)
        if not is_valid:
            logger.error(f"Schema validation failed: {error_msg}")
            return
        
        logger.info("Schema validation passed")
        
        # 6. Check internet connectivity
        uploader = TelemetryUploader()
        
        if not check_internet_connectivity():
            logger.info("Offline mode - queuing metrics locally")
            uploader.queue_offline_metrics(metrics)
            logger.info(f"Queue size: {uploader.get_queue_size()}")
            return
        
        logger.info("Online mode - uploading to DynamoDB")
        
        # 7. Upload to DynamoDB
        if uploader.upload_metrics(metrics):
            logger.info("Successfully uploaded metrics to DynamoDB")
            
            # Reset collector after successful upload
            collector.reset_metrics()
            logger.info("Collector metrics reset")
        else:
            logger.warning("Upload failed - queuing metrics locally")
            uploader.queue_offline_metrics(metrics)
        
        # 8. Retry queued metrics
        logger.info("Attempting to upload queued metrics...")
        uploaded_count = uploader.retry_failed_uploads()
        logger.info(f"Uploaded {uploaded_count} queued metrics")
        logger.info(f"Remaining queue size: {uploader.get_queue_size()}")
        
    except Exception as e:
        logger.error(f"Telemetry upload job failed: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Telemetry upload job completed successfully")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
