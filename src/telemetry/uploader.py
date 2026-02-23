"""
Telemetry Uploader Module

Uploads aggregated metrics to AWS DynamoDB with offline queuing
and exponential backoff retry logic.
"""

import json
import os
import time
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class TelemetryUploader:
    """
    Uploads telemetry metrics to DynamoDB.
    
    Features:
    - Batch upload to DynamoDB
    - Offline queue for failed uploads
    - Exponential backoff retry logic
    """
    
    def __init__(
        self,
        table_name: str = 'nexusai-metrics',
        queue_file: str = 'data/telemetry_queue.json',
        region: str = 'ap-southeast-1'
    ):
        """
        Initialize telemetry uploader.
        
        Args:
            table_name: DynamoDB table name
            queue_file: Path to offline queue file
            region: AWS region
        """
        self.table_name = table_name
        self.queue_file = queue_file
        self.region = region
        
        # Initialize DynamoDB client (lazy)
        self._dynamodb = None
        self._table = None
        
        # Ensure queue directory exists
        os.makedirs(os.path.dirname(queue_file), exist_ok=True)
    
    @property
    def dynamodb(self):
        """Lazy initialization of DynamoDB client"""
        if self._dynamodb is None:
            self._dynamodb = boto3.resource('dynamodb', region_name=self.region)
        return self._dynamodb
    
    @property
    def table(self):
        """Lazy initialization of DynamoDB table"""
        if self._table is None:
            self._table = self.dynamodb.Table(self.table_name)
        return self._table
    
    def upload_metrics(self, metrics: 'AggregatedMetrics') -> bool:
        """
        Upload metrics to DynamoDB.
        
        Args:
            metrics: AggregatedMetrics to upload
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            # Convert to DynamoDB item
            item = metrics.to_dict()
            
            # Add TTL (90 days from now)
            from datetime import timezone
            ttl = int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())
            item['ttl'] = ttl
            
            # Upload to DynamoDB
            self.table.put_item(Item=item)
            
            logger.info(f"Successfully uploaded metrics for school {metrics.school_id}")
            return True
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to upload metrics: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading metrics: {e}")
            return False
    
    def queue_offline_metrics(self, metrics: 'AggregatedMetrics') -> None:
        """
        Queue metrics locally when offline.
        
        Args:
            metrics: AggregatedMetrics to queue
        """
        try:
            # Load existing queue
            queue = self._load_queue()
            
            # Add new metrics
            queue.append(metrics.to_dict())
            
            # Save queue
            self._save_queue(queue)
            
            logger.info(f"Queued metrics offline for school {metrics.school_id}")
            
        except Exception as e:
            logger.error(f"Failed to queue metrics: {e}")
    
    def retry_failed_uploads(self, max_retries: int = 3) -> int:
        """
        Retry uploading queued metrics with exponential backoff.
        
        Args:
            max_retries: Maximum retry attempts per metric
            
        Returns:
            Number of successfully uploaded metrics
        """
        queue = self._load_queue()
        if not queue:
            return 0
        
        successful = 0
        failed = []
        
        for metrics_dict in queue:
            # Reconstruct AggregatedMetrics
            from src.telemetry.aggregator import AggregatedMetrics
            metrics = AggregatedMetrics(**metrics_dict)
            
            # Try upload with exponential backoff
            uploaded = False
            for attempt in range(max_retries):
                if self.upload_metrics(metrics):
                    successful += 1
                    uploaded = True
                    break
                
                # Exponential backoff: 2^attempt seconds
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retry attempt {attempt + 1} failed, waiting {wait_time}s")
                    time.sleep(wait_time)
            
            # Keep in queue if all retries failed
            if not uploaded:
                failed.append(metrics_dict)
        
        # Update queue with failed items
        self._save_queue(failed)
        
        logger.info(f"Retry complete: {successful} uploaded, {len(failed)} still queued")
        return successful
    
    def _load_queue(self) -> List[dict]:
        """Load offline queue from file"""
        if not os.path.exists(self.queue_file):
            return []
        
        try:
            with open(self.queue_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load queue: {e}")
            return []
    
    def _save_queue(self, queue: List[dict]) -> None:
        """Save offline queue to file"""
        try:
            with open(self.queue_file, 'w') as f:
                json.dump(queue, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save queue: {e}")
    
    def get_queue_size(self) -> int:
        """Get number of queued metrics"""
        return len(self._load_queue())
    
    def clear_queue(self) -> None:
        """Clear offline queue"""
        self._save_queue([])


def check_internet_connectivity() -> bool:
    """
    Check if internet is available.
    
    Returns:
        True if internet is available
    """
    try:
        import socket
        # Try to connect to AWS DynamoDB endpoint
        socket.create_connection(("dynamodb.ap-southeast-1.amazonaws.com", 443), timeout=5)
        return True
    except (socket.error, socket.timeout):
        return False
