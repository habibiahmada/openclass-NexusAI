"""
DynamoDB Job Tracker

Tracks ETL pipeline runs, costs, and metadata in DynamoDB for monitoring and analytics.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

from config.aws_config import aws_config

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class JobTracker:
    """Tracks ETL pipeline jobs in DynamoDB"""
    
    def __init__(self, table_name: Optional[str] = None):
        """Initialize job tracker.
        
        Args:
            table_name: DynamoDB table name (defaults to config)
        """
        self.table_name = table_name or aws_config.dynamodb_table or "ETLPipelineJobs"
        self.dynamodb = aws_config.get_dynamodb_client()
        
        # Ensure table exists
        self._ensure_table_exists()
        
        logger.info(f"Initialized JobTracker with table: {self.table_name}")
    
    def _ensure_table_exists(self):
        """Create DynamoDB table if it doesn't exist"""
        try:
            # Check if table exists
            self.dynamodb.describe_table(TableName=self.table_name)
            logger.debug(f"Table {self.table_name} exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create table
                logger.info(f"Creating DynamoDB table: {self.table_name}")
                self._create_table()
            else:
                raise
    
    def _create_table(self):
        """Create DynamoDB table for job tracking"""
        try:
            self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'job_id', 'KeyType': 'HASH'},  # Partition key
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'job_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'StatusIndex',
                        'KeySchema': [
                            {'AttributeName': 'status', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Wait for table to be created
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=self.table_name)
            
            logger.info(f"Created table {self.table_name}")
        except ClientError as e:
            logger.error(f"Failed to create table: {e}")
            raise
    
    def start_job(
        self,
        job_type: str = "etl_pipeline",
        input_dir: str = "",
        config: Dict[str, Any] = None
    ) -> str:
        """Record job start.
        
        Args:
            job_type: Type of job (e.g., "etl_pipeline", "embedding_generation")
            input_dir: Input directory path
            config: Job configuration dict
            
        Returns:
            job_id: Unique job identifier
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        job_id = f"{job_type}_{timestamp.replace(':', '-').replace('.', '-')}"
        
        item = {
            'job_id': {'S': job_id},
            'timestamp': {'S': timestamp},
            'job_type': {'S': job_type},
            'status': {'S': 'running'},
            'input_dir': {'S': input_dir},
            'started_at': {'S': timestamp}
        }
        
        if config:
            item['config'] = {'S': json.dumps(config)}
        
        try:
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item
            )
            logger.info(f"Started job tracking: {job_id}")
            return job_id
        except ClientError as e:
            logger.error(f"Failed to record job start: {e}")
            raise
    
    def update_job_progress(
        self,
        job_id: str,
        files_processed: int = 0,
        chunks_created: int = 0,
        embeddings_generated: int = 0
    ):
        """Update job progress metrics.
        
        Args:
            job_id: Job identifier
            files_processed: Number of files processed
            chunks_created: Number of chunks created
            embeddings_generated: Number of embeddings generated
        """
        try:
            self.dynamodb.update_item(
                TableName=self.table_name,
                Key={
                    'job_id': {'S': job_id},
                    'timestamp': {'S': job_id.split('_', 1)[1].replace('-', ':')}
                },
                UpdateExpression='SET files_processed = :f, chunks_created = :c, embeddings_generated = :e',
                ExpressionAttributeValues={
                    ':f': {'N': str(files_processed)},
                    ':c': {'N': str(chunks_created)},
                    ':e': {'N': str(embeddings_generated)}
                }
            )
            logger.debug(f"Updated job progress: {job_id}")
        except ClientError as e:
            logger.error(f"Failed to update job progress: {e}")
    
    def complete_job(
        self,
        job_id: str,
        status: str = "completed",
        total_files: int = 0,
        successful_files: int = 0,
        failed_files: int = 0,
        total_chunks: int = 0,
        total_embeddings: int = 0,
        processing_time: float = 0.0,
        estimated_cost: float = 0.0,
        errors: List[str] = None
    ):
        """Record job completion.
        
        Args:
            job_id: Job identifier
            status: Final status ("completed", "failed", "partial")
            total_files: Total files processed
            successful_files: Successfully processed files
            failed_files: Failed files
            total_chunks: Total chunks created
            total_embeddings: Total embeddings generated
            processing_time: Total processing time in seconds
            estimated_cost: Estimated cost in USD
            errors: List of error messages
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        update_expr = 'SET #status = :s, completed_at = :t, total_files = :tf, ' \
                     'successful_files = :sf, failed_files = :ff, total_chunks = :tc, ' \
                     'total_embeddings = :te, processing_time = :pt, estimated_cost = :ec'
        
        expr_values = {
            ':s': {'S': status},
            ':t': {'S': timestamp},
            ':tf': {'N': str(total_files)},
            ':sf': {'N': str(successful_files)},
            ':ff': {'N': str(failed_files)},
            ':tc': {'N': str(total_chunks)},
            ':te': {'N': str(total_embeddings)},
            ':pt': {'N': str(processing_time)},
            ':ec': {'N': str(estimated_cost)}
        }
        
        if errors:
            update_expr += ', errors = :err'
            expr_values[':err'] = {'S': json.dumps(errors[:10])}  # Store first 10 errors
        
        try:
            # Get original timestamp from job_id
            original_timestamp = job_id.split('_', 1)[1].replace('-', ':').replace('Z', '') + 'Z'
            
            self.dynamodb.update_item(
                TableName=self.table_name,
                Key={
                    'job_id': {'S': job_id},
                    'timestamp': {'S': original_timestamp}
                },
                UpdateExpression=update_expr,
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues=expr_values
            )
            logger.info(f"Completed job tracking: {job_id} with status: {status}")
        except ClientError as e:
            logger.error(f"Failed to record job completion: {e}")
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job details dict or None if not found
        """
        try:
            # Extract timestamp from job_id
            original_timestamp = job_id.split('_', 1)[1].replace('-', ':').replace('Z', '') + 'Z'
            
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={
                    'job_id': {'S': job_id},
                    'timestamp': {'S': original_timestamp}
                }
            )
            
            if 'Item' not in response:
                return None
            
            # Convert DynamoDB format to dict
            item = self._deserialize_item(response['Item'])
            return item
        except ClientError as e:
            logger.error(f"Failed to get job: {e}")
            return None
    
    def list_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent jobs.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of job dicts
        """
        try:
            response = self.dynamodb.scan(
                TableName=self.table_name,
                Limit=limit
            )
            
            items = []
            for item in response.get('Items', []):
                items.append(self._deserialize_item(item))
            
            # Sort by timestamp descending
            items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return items[:limit]
        except ClientError as e:
            logger.error(f"Failed to list jobs: {e}")
            return []
    
    def get_jobs_by_status(self, status: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get jobs by status.
        
        Args:
            status: Job status ("running", "completed", "failed", "partial")
            limit: Maximum number of jobs to return
            
        Returns:
            List of job dicts
        """
        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                IndexName='StatusIndex',
                KeyConditionExpression='#status = :s',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':s': {'S': status}
                },
                Limit=limit
            )
            
            items = []
            for item in response.get('Items', []):
                items.append(self._deserialize_item(item))
            
            return items
        except ClientError as e:
            logger.error(f"Failed to get jobs by status: {e}")
            return []
    
    def _deserialize_item(self, item: Dict) -> Dict[str, Any]:
        """Convert DynamoDB item format to regular dict.
        
        Args:
            item: DynamoDB item with type descriptors
            
        Returns:
            Regular Python dict
        """
        result = {}
        for key, value in item.items():
            if 'S' in value:
                result[key] = value['S']
            elif 'N' in value:
                result[key] = float(value['N'])
            elif 'BOOL' in value:
                result[key] = value['BOOL']
            elif 'NULL' in value:
                result[key] = None
            else:
                result[key] = value
        
        return result
    
    def get_cost_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get cost summary for recent jobs.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Cost summary dict with total, average, and breakdown
        """
        jobs = self.list_recent_jobs(limit=100)
        
        # Filter jobs from last N days
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        recent_jobs = [
            job for job in jobs
            if datetime.fromisoformat(job.get('timestamp', '').replace('Z', ''))
            >= cutoff
        ]
        
        total_cost = sum(job.get('estimated_cost', 0) for job in recent_jobs)
        total_files = sum(job.get('total_files', 0) for job in recent_jobs)
        total_embeddings = sum(job.get('total_embeddings', 0) for job in recent_jobs)
        
        return {
            'period_days': days,
            'total_jobs': len(recent_jobs),
            'total_cost': total_cost,
            'average_cost_per_job': total_cost / len(recent_jobs) if recent_jobs else 0,
            'total_files_processed': total_files,
            'total_embeddings_generated': total_embeddings,
            'cost_per_file': total_cost / total_files if total_files > 0 else 0,
            'cost_per_embedding': total_cost / total_embeddings if total_embeddings > 0 else 0
        }
