"""
S3 Event Trigger Configuration Module

Manages S3 event notifications that trigger Lambda functions for PDF processing.
"""

import json
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3EventTriggerManager:
    """Manages S3 event notifications for Lambda triggers"""

    def __init__(self, region: str):
        self.s3_client = boto3.client('s3', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.region = region

    def configure_s3_event_trigger(
        self,
        bucket_name: str,
        lambda_function_arn: str,
        prefix: str = "raw/",
        suffix: str = ".pdf"
    ) -> bool:
        """
        Configure S3 event notification to trigger Lambda function.
        Filters for .pdf uploads with prefix:raw/
        """
        try:
            # First, add Lambda permission to be invoked by S3
            if not self._add_lambda_permission(bucket_name, lambda_function_arn):
                return False

            # Configure S3 event notification
            notification_config = {
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': lambda_function_arn,
                        'Events': ['s3:ObjectCreated:*'],
                        'Filter': {
                            'Key': {
                                'FilterRules': [
                                    {'Name': 'prefix', 'Value': prefix},
                                    {'Name': 'suffix', 'Value': suffix}
                                ]
                            }
                        }
                    }
                ]
            }

            self.s3_client.put_bucket_notification_configuration(
                Bucket=bucket_name,
                NotificationConfiguration=notification_config
            )
            logger.info(
                f"Configured S3 event trigger for bucket '{bucket_name}' "
                f"with prefix '{prefix}' and suffix '{suffix}'"
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to configure S3 event trigger: {e}")
            return False

    def _add_lambda_permission(self, bucket_name: str, lambda_function_arn: str) -> bool:
        """Add permission for S3 to invoke Lambda function"""
        try:
            # Extract function name from ARN
            function_name = lambda_function_arn.split(':')[-1]

            # Check if permission already exists
            try:
                self.lambda_client.get_policy(FunctionName=function_name)
                logger.info(f"Lambda permission already configured for '{function_name}'")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise

            # Add permission
            self.lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=f"AllowS3Invoke-{bucket_name}",
                Action='lambda:InvokeFunction',
                Principal='s3.amazonaws.com',
                SourceArn=f"arn:aws:s3:::{bucket_name}"
            )
            logger.info(f"Added Lambda permission for S3 bucket '{bucket_name}'")
            return True
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                logger.info("Lambda permission already exists")
                return True
            logger.error(f"Failed to add Lambda permission: {e}")
            return False

    def test_trigger(self, bucket_name: str, test_key: str = "raw/test.pdf") -> bool:
        """
        Test S3 event trigger by uploading a test file.
        """
        try:
            # Upload test file
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=b"Test PDF content"
            )
            logger.info(f"Uploaded test file to s3://{bucket_name}/{test_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload test file: {e}")
            return False

    def get_event_configuration(self, bucket_name: str) -> Optional[dict]:
        """Get current event notification configuration"""
        try:
            response = self.s3_client.get_bucket_notification_configuration(
                Bucket=bucket_name
            )
            return response
        except ClientError as e:
            logger.error(f"Failed to get event configuration: {e}")
            return None
