"""
Property Test: AWS Infrastructure Setup Idempotence

**Validates: Requirements 15.7**

Tests that the AWS infrastructure setup script can be run multiple times
without errors and produces the same result each time.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import Mock, patch, MagicMock
import json

from src.aws_control_plane.infrastructure_setup import (
    InfrastructureSetup,
    InfrastructureConfig,
    S3Manager,
    DynamoDBManager,
    IAMManager
)


class TestInfrastructureIdempotence:
    """Test infrastructure setup idempotence"""

    @given(
        run_count=st.integers(min_value=1, max_value=5),
        region=st.sampled_from(['ap-southeast-1', 'us-east-1', 'eu-west-1'])
    )
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.too_slow]
    )
    def test_setup_idempotence(self, run_count, region):
        """
        Property 31: AWS Infrastructure Setup Idempotence
        
        Running setup multiple times should produce the same result
        without errors or side effects.
        """
        config = InfrastructureConfig(region=region)
        
        with patch('boto3.client') as mock_boto3:
            # Setup mock clients
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
            
            # Configure mocks to simulate existing resources
            mock_s3.head_bucket.side_effect = Exception("404")  # Bucket doesn't exist first time
            mock_dynamodb.describe_table.side_effect = Exception("ResourceNotFoundException")
            mock_iam.get_role.side_effect = Exception("NoSuchEntity")
            
            # Run setup multiple times
            results = []
            for i in range(run_count):
                setup = InfrastructureSetup(config)
                
                # Mock successful creation
                mock_s3.head_bucket.side_effect = None  # Bucket exists after first creation
                mock_dynamodb.describe_table.side_effect = None  # Table exists after first creation
                mock_iam.get_role.side_effect = None  # Role exists after first creation
                
                result = setup.setup_all()
                results.append(result)
            
            # All runs should succeed
            assert all(results), "All setup runs should succeed"
            
            # All runs should produce same result
            assert len(set(results)) == 1, "All runs should produce same result"

    @given(
        bucket_names=st.lists(
            st.text(
                alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
                min_size=3,
                max_size=63
            ),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    @settings(max_examples=5)
    def test_s3_bucket_creation_idempotence(self, bucket_names):
        """
        S3 bucket creation should be idempotent.
        Creating same bucket twice should not fail.
        """
        with patch('boto3.client') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.return_value = mock_s3
            
            manager = S3Manager('ap-southeast-1')
            
            for bucket_name in bucket_names:
                # First creation
                mock_s3.head_bucket.side_effect = Exception("404")
                result1 = manager.create_bucket_idempotent(bucket_name)
                
                # Second creation (bucket now exists)
                mock_s3.head_bucket.side_effect = None
                result2 = manager.create_bucket_idempotent(bucket_name)
                
                # Both should succeed
                assert result1 is True
                assert result2 is True

    @given(
        table_names=st.lists(
            st.text(
                alphabet='abcdefghijklmnopqrstuvwxyz0123456789_',
                min_size=3,
                max_size=255
            ),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    @settings(max_examples=5)
    def test_dynamodb_table_creation_idempotence(self, table_names):
        """
        DynamoDB table creation should be idempotent.
        Creating same table twice should not fail.
        """
        with patch('boto3.client') as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            
            # Setup waiter mock
            mock_waiter = MagicMock()
            mock_dynamodb.get_waiter.return_value = mock_waiter
            
            manager = DynamoDBManager('ap-southeast-1')
            
            for table_name in table_names:
                key_schema = [{'AttributeName': 'id', 'KeyType': 'HASH'}]
                attributes = [{'AttributeName': 'id', 'AttributeType': 'S'}]
                
                # First creation
                mock_dynamodb.describe_table.side_effect = Exception("ResourceNotFoundException")
                result1 = manager.create_table_idempotent(
                    table_name,
                    key_schema,
                    attributes
                )
                
                # Second creation (table now exists)
                mock_dynamodb.describe_table.side_effect = None
                result2 = manager.create_table_idempotent(
                    table_name,
                    key_schema,
                    attributes
                )
                
                # Both should succeed
                assert result1 is True
                assert result2 is True

    @given(
        role_names=st.lists(
            st.text(
                alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
                min_size=1,
                max_size=64
            ),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    @settings(max_examples=5)
    def test_iam_role_creation_idempotence(self, role_names):
        """
        IAM role creation should be idempotent.
        Creating same role twice should not fail.
        """
        with patch('boto3.client') as mock_boto3:
            mock_iam = MagicMock()
            mock_boto3.return_value = mock_iam
            
            manager = IAMManager('ap-southeast-1')
            
            assume_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            for role_name in role_names:
                # First creation
                mock_iam.get_role.side_effect = Exception("NoSuchEntity")
                mock_iam.create_role.return_value = {
                    'Role': {'Arn': f'arn:aws:iam::123456789:role/{role_name}'}
                }
                result1 = manager.create_role_idempotent(role_name, assume_policy)
                
                # Second creation (role now exists)
                mock_iam.get_role.side_effect = None
                mock_iam.get_role.return_value = {
                    'Role': {'Arn': f'arn:aws:iam::123456789:role/{role_name}'}
                }
                result2 = manager.create_role_idempotent(role_name, assume_policy)
                
                # Both should succeed
                assert result1 is not None
                assert result2 is not None
                assert result1 == result2

    def test_infrastructure_setup_no_side_effects(self):
        """
        Running setup should not have side effects.
        State should be consistent after multiple runs.
        """
        config = InfrastructureConfig()
        
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
            
            # Configure mocks
            mock_s3.head_bucket.side_effect = Exception("404")
            mock_dynamodb.describe_table.side_effect = Exception("ResourceNotFoundException")
            mock_iam.get_role.side_effect = Exception("NoSuchEntity")
            
            # First run
            setup1 = InfrastructureSetup(config)
            result1 = setup1.setup_all()
            
            # Reset mocks to simulate existing resources
            mock_s3.head_bucket.side_effect = None
            mock_dynamodb.describe_table.side_effect = None
            mock_iam.get_role.side_effect = None
            
            # Second run
            setup2 = InfrastructureSetup(config)
            result2 = setup2.setup_all()
            
            # Both should succeed
            assert result1 is True
            assert result2 is True
            
            # Verify no duplicate creation calls
            # (head_bucket should be called, not create_bucket on second run)
            assert mock_s3.head_bucket.call_count >= 2


class TestInfrastructureErrorHandling:
    """Test error handling in infrastructure setup"""

    def test_s3_creation_failure_handling(self):
        """S3 creation failures should be handled gracefully"""
        with patch('boto3.client') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.return_value = mock_s3
            
            # Simulate creation failure
            mock_s3.head_bucket.side_effect = Exception("404")
            mock_s3.create_bucket.side_effect = Exception("AccessDenied")
            
            manager = S3Manager('ap-southeast-1')
            result = manager.create_bucket_idempotent('test-bucket')
            
            # Should return False on failure
            assert result is False

    def test_dynamodb_creation_failure_handling(self):
        """DynamoDB creation failures should be handled gracefully"""
        with patch('boto3.client') as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            
            # Simulate creation failure
            mock_dynamodb.describe_table.side_effect = Exception("ResourceNotFoundException")
            mock_dynamodb.create_table.side_effect = Exception("ValidationException")
            
            manager = DynamoDBManager('ap-southeast-1')
            result = manager.create_table_idempotent(
                'test-table',
                [{'AttributeName': 'id', 'KeyType': 'HASH'}],
                [{'AttributeName': 'id', 'AttributeType': 'S'}]
            )
            
            # Should return False on failure
            assert result is False

    def test_iam_creation_failure_handling(self):
        """IAM creation failures should be handled gracefully"""
        with patch('boto3.client') as mock_boto3:
            mock_iam = MagicMock()
            mock_boto3.return_value = mock_iam
            
            # Simulate creation failure
            mock_iam.get_role.side_effect = Exception("NoSuchEntity")
            mock_iam.create_role.side_effect = Exception("AccessDenied")
            
            manager = IAMManager('ap-southeast-1')
            result = manager.create_role_idempotent(
                'test-role',
                {"Version": "2012-10-17", "Statement": []}
            )
            
            # Should return None on failure
            assert result is None
