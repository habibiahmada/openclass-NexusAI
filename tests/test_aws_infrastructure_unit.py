"""
Unit Tests for AWS Infrastructure Setup

Tests S3, DynamoDB, Lambda deployment, and IAM configuration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
from botocore.exceptions import ClientError

from src.aws_control_plane.infrastructure_setup import (
    InfrastructureSetup,
    InfrastructureConfig,
    S3Manager,
    DynamoDBManager,
    IAMManager,
    LambdaManager
)
from src.aws_control_plane.s3_event_trigger import S3EventTriggerManager
from src.aws_control_plane.cloudfront_setup import CloudFrontManager


def create_client_error(code, message):
    """Helper to create ClientError"""
    error_response = {'Error': {'Code': code, 'Message': message}}
    return ClientError(error_response, 'operation')


class TestS3Manager:
    """Test S3 bucket management"""

    def test_create_bucket_new_bucket(self):
        """Test creating a new S3 bucket"""
        with patch('boto3.client') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.return_value = mock_s3
            
            # Simulate bucket doesn't exist
            mock_s3.head_bucket.side_effect = create_client_error('404', 'Not Found')
            
            manager = S3Manager('ap-southeast-1')
            result = manager.create_bucket_idempotent('test-bucket')
            
            assert result is True
            mock_s3.create_bucket.assert_called_once()

    def test_create_bucket_already_exists(self):
        """Test creating bucket that already exists"""
        with patch('boto3.client') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.return_value = mock_s3
            
            # Simulate bucket exists
            mock_s3.head_bucket.return_value = {}
            
            manager = S3Manager('ap-southeast-1')
            result = manager.create_bucket_idempotent('test-bucket')
            
            assert result is True
            mock_s3.create_bucket.assert_not_called()

    def test_create_bucket_with_versioning(self):
        """Test creating bucket with versioning enabled"""
        with patch('boto3.client') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.return_value = mock_s3
            
            mock_s3.head_bucket.side_effect = Exception("404")
            
            manager = S3Manager('ap-southeast-1')
            result = manager.create_bucket_idempotent('test-bucket', versioning=True)
            
            assert result is True
            mock_s3.put_bucket_versioning.assert_called_once()

    def test_configure_cors(self):
        """Test CORS configuration"""
        with patch('boto3.client') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.return_value = mock_s3
            
            manager = S3Manager('ap-southeast-1')
            result = manager.configure_cors('test-bucket')
            
            assert result is True
            mock_s3.put_bucket_cors.assert_called_once()

    def test_configure_bucket_policy(self):
        """Test bucket policy configuration"""
        with patch('boto3.client') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.return_value = mock_s3
            
            policy = {
                "Version": "2012-10-17",
                "Statement": []
            }
            
            manager = S3Manager('ap-southeast-1')
            result = manager.configure_bucket_policy('test-bucket', policy)
            
            assert result is True
            mock_s3.put_bucket_policy.assert_called_once()


class TestDynamoDBManager:
    """Test DynamoDB table management"""

    def test_create_table_new_table(self):
        """Test creating a new DynamoDB table"""
        with patch('boto3.client') as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            
            # Setup waiter
            mock_waiter = MagicMock()
            mock_dynamodb.get_waiter.return_value = mock_waiter
            
            # Simulate table doesn't exist
            mock_dynamodb.describe_table.side_effect = create_client_error('ResourceNotFoundException', 'Not Found')
            
            manager = DynamoDBManager('ap-southeast-1')
            result = manager.create_table_idempotent(
                'test-table',
                [{'AttributeName': 'id', 'KeyType': 'HASH'}],
                [{'AttributeName': 'id', 'AttributeType': 'S'}]
            )
            
            assert result is True
            mock_dynamodb.create_table.assert_called_once()

    def test_create_table_already_exists(self):
        """Test creating table that already exists"""
        with patch('boto3.client') as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            
            # Simulate table exists
            mock_dynamodb.describe_table.return_value = {'Table': {}}
            
            manager = DynamoDBManager('ap-southeast-1')
            result = manager.create_table_idempotent(
                'test-table',
                [{'AttributeName': 'id', 'KeyType': 'HASH'}],
                [{'AttributeName': 'id', 'AttributeType': 'S'}]
            )
            
            assert result is True
            mock_dynamodb.create_table.assert_not_called()

    def test_create_table_with_ttl(self):
        """Test creating table with TTL configuration"""
        with patch('boto3.client') as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            
            mock_waiter = MagicMock()
            mock_dynamodb.get_waiter.return_value = mock_waiter
            mock_dynamodb.describe_table.side_effect = create_client_error('ResourceNotFoundException', 'Not Found')
            
            manager = DynamoDBManager('ap-southeast-1')
            result = manager.create_table_idempotent(
                'test-table',
                [{'AttributeName': 'id', 'KeyType': 'HASH'}],
                [{'AttributeName': 'id', 'AttributeType': 'S'}],
                ttl_attribute='expiration_time'
            )
            
            assert result is True
            mock_dynamodb.update_time_to_live.assert_called_once()

    def test_configure_ttl(self):
        """Test TTL configuration"""
        with patch('boto3.client') as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            
            manager = DynamoDBManager('ap-southeast-1')
            result = manager._configure_ttl('test-table', 'expiration_time')
            
            assert result is True
            mock_dynamodb.update_time_to_live.assert_called_once()


class TestIAMManager:
    """Test IAM role management"""

    def test_create_role_new_role(self):
        """Test creating a new IAM role"""
        with patch('boto3.client') as mock_boto3:
            mock_iam = MagicMock()
            mock_boto3.return_value = mock_iam
            
            # Simulate role doesn't exist
            mock_iam.get_role.side_effect = create_client_error('NoSuchEntity', 'Not Found')
            mock_iam.create_role.return_value = {
                'Role': {'Arn': 'arn:aws:iam::123456789:role/test-role'}
            }
            
            manager = IAMManager('ap-southeast-1')
            policy = {"Version": "2012-10-17", "Statement": []}
            result = manager.create_role_idempotent('test-role', policy)
            
            assert result == 'arn:aws:iam::123456789:role/test-role'
            mock_iam.create_role.assert_called_once()

    def test_create_role_already_exists(self):
        """Test creating role that already exists"""
        with patch('boto3.client') as mock_boto3:
            mock_iam = MagicMock()
            mock_boto3.return_value = mock_iam
            
            # Simulate role exists
            mock_iam.get_role.return_value = {
                'Role': {'Arn': 'arn:aws:iam::123456789:role/test-role'}
            }
            
            manager = IAMManager('ap-southeast-1')
            policy = {"Version": "2012-10-17", "Statement": []}
            result = manager.create_role_idempotent('test-role', policy)
            
            assert result == 'arn:aws:iam::123456789:role/test-role'
            mock_iam.create_role.assert_not_called()

    def test_attach_policy_new_policy(self):
        """Test attaching a new policy"""
        with patch('boto3.client') as mock_boto3:
            mock_iam = MagicMock()
            mock_boto3.return_value = mock_iam
            
            # Simulate policy doesn't exist
            mock_iam.get_role_policy.side_effect = create_client_error('NoSuchEntity', 'Not Found')
            
            manager = IAMManager('ap-southeast-1')
            policy = {"Version": "2012-10-17", "Statement": []}
            result = manager.attach_policy_idempotent('test-role', 'test-policy', policy)
            
            assert result is True
            mock_iam.put_role_policy.assert_called_once()

    def test_attach_policy_already_exists(self):
        """Test attaching policy that already exists"""
        with patch('boto3.client') as mock_boto3:
            mock_iam = MagicMock()
            mock_boto3.return_value = mock_iam
            
            # Simulate policy exists
            mock_iam.get_role_policy.return_value = {'PolicyDocument': {}}
            
            manager = IAMManager('ap-southeast-1')
            policy = {"Version": "2012-10-17", "Statement": []}
            result = manager.attach_policy_idempotent('test-role', 'test-policy', policy)
            
            assert result is True
            mock_iam.put_role_policy.assert_not_called()


class TestLambdaManager:
    """Test Lambda function management"""

    def test_function_exists_true(self):
        """Test checking if function exists (true case)"""
        with patch('boto3.client') as mock_boto3:
            mock_lambda = MagicMock()
            mock_boto3.return_value = mock_lambda
            
            mock_lambda.get_function.return_value = {'Configuration': {}}
            
            manager = LambdaManager('ap-southeast-1')
            result = manager.function_exists('test-function')
            
            assert result is True

    def test_function_exists_false(self):
        """Test checking if function exists (false case)"""
        with patch('boto3.client') as mock_boto3:
            mock_lambda = MagicMock()
            mock_boto3.return_value = mock_lambda
            
            mock_lambda.get_function.side_effect = create_client_error('ResourceNotFoundException', 'Not Found')
            
            manager = LambdaManager('ap-southeast-1')
            result = manager.function_exists('test-function')
            
            assert result is False

    def test_create_function_new_function(self):
        """Test creating a new Lambda function"""
        with patch('boto3.client') as mock_boto3:
            mock_lambda = MagicMock()
            mock_boto3.return_value = mock_lambda
            
            mock_lambda.get_function.side_effect = create_client_error('ResourceNotFoundException', 'Not Found')
            
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b'zip content'
                
                manager = LambdaManager('ap-southeast-1')
                result = manager.create_function_idempotent(
                    'test-function',
                    'arn:aws:iam::123456789:role/test-role',
                    '/tmp/test.zip'
                )
                
                assert result is True
                mock_lambda.create_function.assert_called_once()


class TestS3EventTrigger:
    """Test S3 event trigger configuration"""

    def test_configure_s3_event_trigger(self):
        """Test configuring S3 event trigger"""
        with patch('boto3.client') as mock_boto3:
            mock_s3 = MagicMock()
            mock_lambda = MagicMock()
            
            def client_factory(service, region_name=None):
                if service == 's3':
                    return mock_s3
                elif service == 'lambda':
                    return mock_lambda
                return MagicMock()
            
            mock_boto3.side_effect = client_factory
            
            manager = S3EventTriggerManager('ap-southeast-1')
            result = manager.configure_s3_event_trigger(
                'test-bucket',
                'arn:aws:lambda:ap-southeast-1:123456789:function:test'
            )
            
            assert result is True
            mock_s3.put_bucket_notification_configuration.assert_called_once()

    def test_add_lambda_permission(self):
        """Test adding Lambda permission for S3"""
        with patch('boto3.client') as mock_boto3:
            mock_lambda = MagicMock()
            mock_boto3.return_value = mock_lambda
            
            manager = S3EventTriggerManager('ap-southeast-1')
            result = manager._add_lambda_permission(
                'test-bucket',
                'arn:aws:lambda:ap-southeast-1:123456789:function:test'
            )
            
            assert result is True
            mock_lambda.add_permission.assert_called_once()


class TestCloudFrontManager:
    """Test CloudFront distribution management"""

    def test_create_distribution_new(self):
        """Test creating a new CloudFront distribution"""
        with patch('boto3.client') as mock_boto3:
            mock_cf = MagicMock()
            mock_boto3.return_value = mock_cf
            
            mock_cf.list_distributions.return_value = {'DistributionList': {'Items': []}}
            mock_cf.create_distribution.return_value = {
                'Distribution': {'Id': 'DIST123'}
            }
            
            manager = CloudFrontManager('ap-southeast-1')
            result = manager.create_distribution_idempotent(
                'test-dist',
                'test-bucket'
            )
            
            assert result == 'DIST123'
            mock_cf.create_distribution.assert_called_once()

    def test_create_distribution_already_exists(self):
        """Test creating distribution that already exists"""
        with patch('boto3.client') as mock_boto3:
            mock_cf = MagicMock()
            mock_boto3.return_value = mock_cf
            
            mock_cf.list_distributions.return_value = {
                'DistributionList': {
                    'Items': [
                        {
                            'Id': 'DIST123',
                            'Comment': 'VKP distribution for test-dist'
                        }
                    ]
                }
            }
            
            manager = CloudFrontManager('ap-southeast-1')
            result = manager.create_distribution_idempotent(
                'test-dist',
                'test-bucket'
            )
            
            assert result == 'DIST123'
            mock_cf.create_distribution.assert_not_called()

    def test_get_distribution_domain(self):
        """Test getting distribution domain"""
        with patch('boto3.client') as mock_boto3:
            mock_cf = MagicMock()
            mock_boto3.return_value = mock_cf
            
            mock_cf.get_distribution.return_value = {
                'Distribution': {'DomainName': 'd123.cloudfront.net'}
            }
            
            manager = CloudFrontManager('ap-southeast-1')
            result = manager.get_distribution_domain('DIST123')
            
            assert result == 'd123.cloudfront.net'


class TestInfrastructureSetup:
    """Test complete infrastructure setup"""

    def test_setup_all_success(self):
        """Test complete infrastructure setup"""
        with patch('boto3.client') as mock_boto3:
            mock_s3 = MagicMock()
            mock_dynamodb = MagicMock()
            mock_iam = MagicMock()
            
            def client_factory(service, region_name=None):
                if service == 's3':
                    return mock_s3
                elif service == 'dynamodb':
                    return mock_dynamodb
                elif service == 'iam':
                    return mock_iam
                return MagicMock()
            
            mock_boto3.side_effect = client_factory
            
            # Setup mocks
            mock_s3.head_bucket.side_effect = create_client_error('404', 'Not Found')
            mock_dynamodb.describe_table.side_effect = create_client_error('ResourceNotFoundException', 'Not Found')
            mock_iam.get_role.side_effect = create_client_error('NoSuchEntity', 'Not Found')
            
            mock_waiter = MagicMock()
            mock_dynamodb.get_waiter.return_value = mock_waiter
            
            mock_iam.create_role.return_value = {
                'Role': {'Arn': 'arn:aws:iam::123456789:role/test'}
            }
            
            setup = InfrastructureSetup()
            result = setup.setup_all()
            
            assert result is True
            mock_s3.create_bucket.assert_called()
            mock_dynamodb.create_table.assert_called()
            mock_iam.create_role.assert_called()
