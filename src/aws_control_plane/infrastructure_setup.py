"""
AWS Infrastructure Setup Module

Provides idempotent setup for AWS resources including S3 buckets, DynamoDB tables,
Lambda functions, and IAM roles. Can be run multiple times safely.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from src.aws_control_plane.cloudfront_setup import CloudFrontManager
from src.aws_control_plane.s3_event_trigger import S3EventTriggerManager
from src.aws_control_plane.lambda_processor import LambdaProcessorPackager
from config.aws_config import aws_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class InfrastructureConfig:
    """Configuration for AWS infrastructure setup"""
    region: str = aws_config.region
    curriculum_raw_bucket: str = aws_config.curriculum_raw_bucket
    vkp_packages_bucket: str = aws_config.vkp_packages_bucket
    model_distribution_bucket: str = aws_config.model_distribution_bucket
    schools_table: str = os.getenv("AWS_SCHOOLS_TABLE", "nexusai-schools")
    metrics_table: str = os.getenv("AWS_METRICS_TABLE", "nexusai-metrics")
    lambda_function_name: str = os.getenv("AWS_LAMBDA_FUNCTION_NAME", "nexusai-curriculum-processor")
    lambda_role_name: str = os.getenv("AWS_LAMBDA_ROLE_NAME", "nexusai-lambda-execution-role")
    school_server_role_name: str = os.getenv("AWS_SCHOOL_SERVER_ROLE_NAME", "nexusai-school-server-role")
    cloudfront_distribution_name: str = os.getenv("AWS_CLOUDFRONT_DISTRIBUTION_NAME", "nexusai-vkp-distribution")


class S3Manager:
    """Manages S3 bucket creation and configuration"""

    def __init__(self, region: str):
        self.s3_client = boto3.client('s3', region_name=region)
        self.region = region

    def create_bucket_idempotent(self, bucket_name: str, versioning: bool = False) -> bool:
        """
        Create S3 bucket idempotently. Returns True if created or already exists.
        """
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"S3 bucket '{bucket_name}' already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                try:
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    logger.info(f"Created S3 bucket '{bucket_name}'")
                    
                    # Enable versioning if requested
                    if versioning:
                        self.s3_client.put_bucket_versioning(
                            Bucket=bucket_name,
                            VersioningConfiguration={'Status': 'Enabled'}
                        )
                        logger.info(f"Enabled versioning on bucket '{bucket_name}'")
                    
                    return True
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket '{bucket_name}': {create_error}")
                    return False
            else:
                logger.error(f"Error checking bucket '{bucket_name}': {e}")
                return False

    def configure_cors(self, bucket_name: str) -> bool:
        """Configure CORS for bucket"""
        try:
            cors_config = {
                'CORSRules': [
                    {
                        'AllowedHeaders': ['*'],
                        'AllowedMethods': ['GET', 'PUT', 'POST'],
                        'AllowedOrigins': ['*'],
                        'ExposeHeaders': ['ETag'],
                        'MaxAgeSeconds': 3000
                    }
                ]
            }
            self.s3_client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_config)
            logger.info(f"Configured CORS for bucket '{bucket_name}'")
            return True
        except ClientError as e:
            logger.error(f"Failed to configure CORS for '{bucket_name}': {e}")
            return False

    def configure_bucket_policy(self, bucket_name: str, policy: Dict) -> bool:
        """Configure bucket policy"""
        try:
            self.s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
            logger.info(f"Configured policy for bucket '{bucket_name}'")
            return True
        except ClientError as e:
            logger.error(f"Failed to configure policy for '{bucket_name}': {e}")
            return False


class DynamoDBManager:
    """Manages DynamoDB table creation and configuration"""

    def __init__(self, region: str):
        self.dynamodb_client = boto3.client('dynamodb', region_name=region)
        self.region = region

    def create_table_idempotent(
        self,
        table_name: str,
        key_schema: List[Dict],
        attribute_definitions: List[Dict],
        billing_mode: str = 'PAY_PER_REQUEST',
        ttl_attribute: Optional[str] = None
    ) -> bool:
        """
        Create DynamoDB table idempotently. Returns True if created or already exists.
        """
        try:
            # Check if table exists
            self.dynamodb_client.describe_table(TableName=table_name)
            logger.info(f"DynamoDB table '{table_name}' already exists")
            
            # Configure TTL if specified
            if ttl_attribute:
                self._configure_ttl(table_name, ttl_attribute)
            
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, create it
                try:
                    params = {
                        'TableName': table_name,
                        'KeySchema': key_schema,
                        'AttributeDefinitions': attribute_definitions,
                        'BillingMode': billing_mode
                    }
                    
                    self.dynamodb_client.create_table(**params)
                    logger.info(f"Created DynamoDB table '{table_name}'")
                    
                    # Wait for table to be active
                    waiter = self.dynamodb_client.get_waiter('table_exists')
                    waiter.wait(TableName=table_name)
                    logger.info(f"Table '{table_name}' is now active")
                    
                    # Configure TTL if specified
                    if ttl_attribute:
                        self._configure_ttl(table_name, ttl_attribute)
                    
                    return True
                except ClientError as create_error:
                    logger.error(f"Failed to create table '{table_name}': {create_error}")
                    return False
            else:
                logger.error(f"Error checking table '{table_name}': {e}")
                return False

    def _configure_ttl(self, table_name: str, attribute_name: str) -> bool:
        """Configure TTL for table"""
        try:
            self.dynamodb_client.update_time_to_live(
                TableName=table_name,
                TimeToLiveSpecification={
                    'AttributeName': attribute_name,
                    'Enabled': True
                }
            )
            logger.info(f"Configured TTL for table '{table_name}' on attribute '{attribute_name}'")
            return True
        except ClientError as e:
            if 'ValidationException' in str(e):
                logger.info(f"TTL already configured for table '{table_name}'")
                return True
            logger.error(f"Failed to configure TTL for '{table_name}': {e}")
            return False


class IAMManager:
    """Manages IAM roles and policies"""

    def __init__(self, region: str):
        self.iam_client = boto3.client('iam', region_name=region)
        self.region = region

    def create_role_idempotent(self, role_name: str, assume_role_policy: Dict) -> Optional[str]:
        """
        Create IAM role idempotently. Returns role ARN if successful.
        """
        try:
            # Check if role exists
            response = self.iam_client.get_role(RoleName=role_name)
            logger.info(f"IAM role '{role_name}' already exists")
            return response['Role']['Arn']
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                # Role doesn't exist, create it
                try:
                    response = self.iam_client.create_role(
                        RoleName=role_name,
                        AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                        Description=f"Role for {role_name}"
                    )
                    logger.info(f"Created IAM role '{role_name}'")
                    return response['Role']['Arn']
                except ClientError as create_error:
                    logger.error(f"Failed to create role '{role_name}': {create_error}")
                    return None
            else:
                logger.error(f"Error checking role '{role_name}': {e}")
                return None

    def attach_policy_idempotent(self, role_name: str, policy_name: str, policy_document: Dict) -> bool:
        """
        Attach inline policy to role idempotently.
        """
        try:
            # Check if policy already attached
            self.iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
            logger.info(f"Policy '{policy_name}' already attached to role '{role_name}'")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                # Policy doesn't exist, create it
                try:
                    self.iam_client.put_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name,
                        PolicyDocument=json.dumps(policy_document)
                    )
                    logger.info(f"Attached policy '{policy_name}' to role '{role_name}'")
                    return True
                except ClientError as attach_error:
                    logger.error(f"Failed to attach policy '{policy_name}': {attach_error}")
                    return False
            else:
                logger.error(f"Error checking policy '{policy_name}': {e}")
                return False


class LambdaManager:
    """Manages Lambda function deployment"""

    def __init__(self, region: str):
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.region = region

    def function_exists(self, function_name: str) -> bool:
        """Check if Lambda function exists"""
        try:
            self.lambda_client.get_function(FunctionName=function_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            logger.error(f"Error checking function '{function_name}': {e}")
            return False

    def create_function_idempotent(
        self,
        function_name: str,
        role_arn: str,
        zip_file_path: str,
        handler: str = "lambda_function.lambda_handler",
        runtime: str = "python3.11",
        timeout: int = 300,
        memory_size: int = 1024,
        environment_variables: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Create Lambda function idempotently.
        """
        if self.function_exists(function_name):
            logger.info(f"Lambda function '{function_name}' already exists")
            return True

        try:
            # Read zip file
            if not os.path.exists(zip_file_path):
                logger.error(f"Zip file not found: {zip_file_path}")
                return False

            with open(zip_file_path, 'rb') as f:
                zip_content = f.read()

            params = {
                'FunctionName': function_name,
                'Runtime': runtime,
                'Role': role_arn,
                'Handler': handler,
                'Code': {'ZipFile': zip_content},
                'Timeout': timeout,
                'MemorySize': memory_size,
                'Description': f"Curriculum processor for {function_name}"
            }

            if environment_variables:
                params['Environment'] = {'Variables': environment_variables}

            self.lambda_client.create_function(**params)
            logger.info(f"Created Lambda function '{function_name}'")
            return True
        except ClientError as e:
            logger.error(f"Failed to create Lambda function '{function_name}': {e}")
            return False


class InfrastructureSetup:
    """Main orchestrator for AWS infrastructure setup"""

    def __init__(self, config: Optional[InfrastructureConfig] = None):
        self.config = config or InfrastructureConfig()
        self.s3_manager = S3Manager(self.config.region)
        self.dynamodb_manager = DynamoDBManager(self.config.region)
        self.iam_manager = IAMManager(self.config.region)
        self.lambda_manager = LambdaManager(self.config.region)
        self.setup_results = {}

    def setup_all(self) -> bool:
        """Execute complete infrastructure setup"""
        logger.info("Starting AWS infrastructure setup...")
        
        try:
            # Setup S3 buckets
            if not self._setup_s3_buckets():
                logger.error("S3 bucket setup failed")
                return False

            # Setup DynamoDB tables
            if not self._setup_dynamodb_tables():
                logger.error("DynamoDB table setup failed")
                return False

            # Setup IAM roles
            if not self._setup_iam_roles():
                logger.error("IAM role setup failed")
                return False

            logger.info("AWS infrastructure setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Unexpected error during infrastructure setup: {e}")
            return False

    def _setup_s3_buckets(self) -> bool:
        """Setup S3 buckets"""
        logger.info("Setting up S3 buckets...")
        
        # Create curriculum raw bucket
        if not self.s3_manager.create_bucket_idempotent(self.config.curriculum_raw_bucket):
            return False
        self.s3_manager.configure_cors(self.config.curriculum_raw_bucket)

        # Create VKP packages bucket with versioning
        if not self.s3_manager.create_bucket_idempotent(
            self.config.vkp_packages_bucket,
            versioning=True
        ):
            return False
        self.s3_manager.configure_cors(self.config.vkp_packages_bucket)

        # Create model distribution bucket
        if not self.s3_manager.create_bucket_idempotent(self.config.model_distribution_bucket):
            return False
        self.s3_manager.configure_cors(self.config.model_distribution_bucket)

        logger.info("S3 buckets setup completed")
        return True

    def _setup_dynamodb_tables(self) -> bool:
        """Setup DynamoDB tables"""
        logger.info("Setting up DynamoDB tables...")

        # Create schools table
        schools_key_schema = [
            {'AttributeName': 'school_id', 'KeyType': 'HASH'}
        ]
        schools_attributes = [
            {'AttributeName': 'school_id', 'AttributeType': 'S'}
        ]
        if not self.dynamodb_manager.create_table_idempotent(
            self.config.schools_table,
            schools_key_schema,
            schools_attributes
        ):
            return False

        # Create metrics table with TTL
        metrics_key_schema = [
            {'AttributeName': 'school_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ]
        metrics_attributes = [
            {'AttributeName': 'school_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'N'}
        ]
        if not self.dynamodb_manager.create_table_idempotent(
            self.config.metrics_table,
            metrics_key_schema,
            metrics_attributes,
            ttl_attribute='expiration_time'
        ):
            return False

        logger.info("DynamoDB tables setup completed")
        return True

    def _setup_iam_roles(self) -> bool:
        """Verify IAM roles exist (created manually in AWS Console)"""
        logger.info("Verifying IAM roles...")
        
        try:
            resp = self.iam_manager.iam_client.get_role(RoleName=self.config.lambda_role_name)
            logger.info(f"Lambda role exists: {resp['Role']['Arn']}")
        except Exception as e:
            logger.error(f"Lambda role NOT FOUND: {e}")
            return False
        
        try:
            resp = self.iam_manager.iam_client.get_role(RoleName=self.config.school_server_role_name)
            logger.info(f"School server role exists: {resp['Role']['Arn']}")
        except Exception as e:
            logger.error(f"School server role NOT FOUND: {e}")
            return False
        
        logger.info("IAM roles verification completed")
        return True


def main():
    """Main entry point for infrastructure setup"""
    try:
        setup = InfrastructureSetup()
        success = setup.setup_all()
        
        if success:
            logger.info("Infrastructure setup completed successfully")
            return 0
        else:
            logger.error("Infrastructure setup failed")
            return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
