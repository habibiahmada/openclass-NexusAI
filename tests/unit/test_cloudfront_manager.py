import time
from unittest.mock import Mock, patch, MagicMock

import pytest
from botocore.exceptions import ClientError

from src.aws_control_plane.cloudfront_manager import (
    CloudFrontManager,
    DistributionInfo,
    InvalidationResult
)


@pytest.fixture
def mock_aws_config():
    """Mock AWS configuration."""
    with patch('src.aws_control_plane.cloudfront_manager.aws_config') as mock_config:
        mock_config.s3_bucket = "test-bucket"
        mock_config.region = "ap-southeast-2"
        mock_config.access_key = "test-key"
        mock_config.secret_key = "test-secret"
        mock_config.cloudfront_distribution_id = "E1234567890ABC"
        mock_config.get_s3_client.return_value = MagicMock()
        yield mock_config


@pytest.fixture
def mock_cloudfront_client():
    """Mock CloudFront client."""
    with patch('boto3.client') as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def cloudfront_manager(mock_aws_config, mock_cloudfront_client):
    """Create CloudFront manager with mocked AWS services."""
    manager = CloudFrontManager(bucket_name="test-bucket")
    manager.cloudfront = mock_cloudfront_client
    return manager


class TestDistributionCreation:
    """Test CloudFront distribution creation."""
    
    def test_create_distribution_success(self, cloudfront_manager, mock_cloudfront_client):
        """Test creating a CloudFront distribution successfully."""
        # Requirements: 6.1, 6.4
        # Mock S3 bucket location
        cloudfront_manager.s3.get_bucket_location.return_value = {
            'LocationConstraint': 'ap-southeast-2'
        }
        
        # Mock CloudFront create_distribution response
        mock_cloudfront_client.create_distribution.return_value = {
            'Distribution': {
                'Id': 'E1234567890ABC',
                'DomainName': 'd111111abcdef8.cloudfront.net',
                'Status': 'InProgress',
                'DistributionConfig': {
                    'Enabled': True
                }
            }
        }
        
        # Create distribution
        result = cloudfront_manager.create_distribution()
        
        # Verify result
        assert isinstance(result, DistributionInfo)
        assert result.distribution_id == 'E1234567890ABC'
        assert result.domain_name == 'd111111abcdef8.cloudfront.net'
        assert result.status == 'InProgress'
        assert result.enabled is True
        
        # Verify CloudFront client was called
        assert mock_cloudfront_client.create_distribution.called
    
    def test_create_distribution_https_requirement(self, cloudfront_manager, mock_cloudfront_client):
        """Test that distribution requires HTTPS for all requests."""
        # Requirement 6.3: HTTPS requirement
        cloudfront_manager.s3.get_bucket_location.return_value = {
            'LocationConstraint': 'ap-southeast-2'
        }
        
        mock_cloudfront_client.create_distribution.return_value = {
            'Distribution': {
                'Id': 'E1234567890ABC',
                'DomainName': 'd111111abcdef8.cloudfront.net',
                'Status': 'InProgress',
                'DistributionConfig': {'Enabled': True}
            }
        }
        
        cloudfront_manager.create_distribution()
        
        # Verify HTTPS configuration
        call_args = mock_cloudfront_client.create_distribution.call_args
        config = call_args[1]['DistributionConfig']
        
        # Check ViewerProtocolPolicy is set to redirect-to-https
        assert config['DefaultCacheBehavior']['ViewerProtocolPolicy'] == 'redirect-to-https'
    
    def test_create_distribution_cache_ttl_configuration(self, cloudfront_manager, mock_cloudfront_client):
        """Test that cache TTL is set to 24 hours."""
        # Requirement 6.2: Cache TTL to 24 hours (86400 seconds)
        cloudfront_manager.s3.get_bucket_location.return_value = {
            'LocationConstraint': 'ap-southeast-2'
        }
        
        mock_cloudfront_client.create_distribution.return_value = {
            'Distribution': {
                'Id': 'E1234567890ABC',
                'DomainName': 'd111111abcdef8.cloudfront.net',
                'Status': 'InProgress',
                'DistributionConfig': {'Enabled': True}
            }
        }
        
        cloudfront_manager.create_distribution()
        
        # Verify cache TTL configuration
        call_args = mock_cloudfront_client.create_distribution.call_args
        config = call_args[1]['DistributionConfig']
        
        # Check DefaultTTL is 86400 seconds (24 hours)
        assert config['DefaultCacheBehavior']['DefaultTTL'] == 86400
    
    def test_create_distribution_compression_enabled(self, cloudfront_manager, mock_cloudfront_client):
        """Test that gzip compression is enabled."""
        # Requirements: 6.1
        cloudfront_manager.s3.get_bucket_location.return_value = {
            'LocationConstraint': 'ap-southeast-2'
        }
        
        mock_cloudfront_client.create_distribution.return_value = {
            'Distribution': {
                'Id': 'E1234567890ABC',
                'DomainName': 'd111111abcdef8.cloudfront.net',
                'Status': 'InProgress',
                'DistributionConfig': {'Enabled': True}
            }
        }
        
        cloudfront_manager.create_distribution()
        
        # Verify compression is enabled
        call_args = mock_cloudfront_client.create_distribution.call_args
        config = call_args[1]['DistributionConfig']
        
        assert config['DefaultCacheBehavior']['Compress'] is True
    
    def test_create_distribution_s3_origin_configuration(self, cloudfront_manager, mock_cloudfront_client):
        """Test that distribution points to correct S3 bucket."""
        # Requirement 6.1: Distribution pointing to S3 bucket
        cloudfront_manager.s3.get_bucket_location.return_value = {
            'LocationConstraint': 'us-west-2'
        }
        
        mock_cloudfront_client.create_distribution.return_value = {
            'Distribution': {
                'Id': 'E1234567890ABC',
                'DomainName': 'd111111abcdef8.cloudfront.net',
                'Status': 'InProgress',
                'DistributionConfig': {'Enabled': True}
            }
        }
        
        cloudfront_manager.create_distribution()
        
        # Verify S3 origin configuration
        call_args = mock_cloudfront_client.create_distribution.call_args
        config = call_args[1]['DistributionConfig']
        
        origin = config['Origins']['Items'][0]
        assert 'test-bucket' in origin['DomainName']
        assert origin['Id'] == 'test-bucket-origin'
    
    def test_create_distribution_handles_s3_location_error(self, cloudfront_manager, mock_cloudfront_client):
        """Test distribution creation when S3 location lookup fails."""
        # Mock S3 error
        cloudfront_manager.s3.get_bucket_location.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
            'get_bucket_location'
        )
        
        mock_cloudfront_client.create_distribution.return_value = {
            'Distribution': {
                'Id': 'E1234567890ABC',
                'DomainName': 'd111111abcdef8.cloudfront.net',
                'Status': 'InProgress',
                'DistributionConfig': {'Enabled': True}
            }
        }
        
        # Should still create distribution with default region
        result = cloudfront_manager.create_distribution()
        
        assert result.distribution_id == 'E1234567890ABC'
    
    def test_create_distribution_cloudfront_error(self, cloudfront_manager, mock_cloudfront_client):
        """Test handling CloudFront API errors."""
        cloudfront_manager.s3.get_bucket_location.return_value = {
            'LocationConstraint': 'ap-southeast-2'
        }
        
        # Mock CloudFront error
        mock_cloudfront_client.create_distribution.side_effect = ClientError(
            {'Error': {'Code': 'TooManyDistributions', 'Message': 'Limit exceeded'}},
            'create_distribution'
        )
        
        # Should raise ClientError
        with pytest.raises(ClientError):
            cloudfront_manager.create_distribution()


class TestCacheInvalidation:
    """Test CloudFront cache invalidation."""
    
    def test_invalidate_cache_success(self, cloudfront_manager, mock_cloudfront_client):
        """Test invalidating cache successfully."""
        # Requirement 6.5: Invalidate cache for updated files
        mock_cloudfront_client.create_invalidation.return_value = {
            'Invalidation': {
                'Id': 'I1234567890ABC',
                'Status': 'InProgress'
            }
        }
        
        paths = ['/processed/*', '/vector_db/*']
        result = cloudfront_manager.invalidate_cache(paths)
        
        # Verify result
        assert isinstance(result, InvalidationResult)
        assert result.invalidation_id == 'I1234567890ABC'
        assert result.status == 'InProgress'
        assert result.paths == paths
        
        # Verify CloudFront client was called
        assert mock_cloudfront_client.create_invalidation.called
    
    def test_invalidate_cache_with_distribution_id(self, cloudfront_manager, mock_cloudfront_client):
        """Test cache invalidation with explicit distribution ID."""
        # Requirement 6.5
        mock_cloudfront_client.create_invalidation.return_value = {
            'Invalidation': {
                'Id': 'I1234567890ABC',
                'Status': 'InProgress'
            }
        }
        
        custom_dist_id = 'ECUSTOMDIST123'
        paths = ['/*']
        
        result = cloudfront_manager.invalidate_cache(paths, distribution_id=custom_dist_id)
        
        # Verify correct distribution ID was used
        call_args = mock_cloudfront_client.create_invalidation.call_args
        assert call_args[1]['DistributionId'] == custom_dist_id
    
    def test_invalidate_cache_no_distribution_id(self, cloudfront_manager, mock_aws_config):
        """Test cache invalidation fails without distribution ID."""
        # Remove distribution ID from config
        mock_aws_config.cloudfront_distribution_id = None
        
        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            cloudfront_manager.invalidate_cache(['/*'])
        
        assert 'No CloudFront distribution ID' in str(exc_info.value)
    
    def test_invalidate_cache_multiple_paths(self, cloudfront_manager, mock_cloudfront_client):
        """Test invalidating multiple paths."""
        # Requirement 6.5
        mock_cloudfront_client.create_invalidation.return_value = {
            'Invalidation': {
                'Id': 'I1234567890ABC',
                'Status': 'InProgress'
            }
        }
        
        paths = [
            '/processed/informatika/*',
            '/processed/matematika/*',
            '/vector_db/*'
        ]
        
        result = cloudfront_manager.invalidate_cache(paths)
        
        # Verify all paths were included
        call_args = mock_cloudfront_client.create_invalidation.call_args
        batch = call_args[1]['InvalidationBatch']
        
        assert batch['Paths']['Quantity'] == 3
        assert batch['Paths']['Items'] == paths
    
    def test_invalidate_cache_api_error(self, cloudfront_manager, mock_cloudfront_client):
        """Test handling cache invalidation API errors."""
        # Requirement 6.5
        mock_cloudfront_client.create_invalidation.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchDistribution', 'Message': 'Distribution not found'}},
            'create_invalidation'
        )
        
        # Should raise ClientError
        with pytest.raises(ClientError):
            cloudfront_manager.invalidate_cache(['/*'])


class TestGetDistribution:
    """Test getting distribution information."""
    
    def test_get_distribution_success(self, cloudfront_manager, mock_cloudfront_client):
        """Test getting distribution information successfully."""
        # Requirements: 6.1, 6.4
        mock_cloudfront_client.get_distribution.return_value = {
            'Distribution': {
                'Id': 'E1234567890ABC',
                'DomainName': 'd111111abcdef8.cloudfront.net',
                'Status': 'Deployed',
                'DistributionConfig': {
                    'Enabled': True
                }
            }
        }
        
        result = cloudfront_manager.get_distribution()
        
        assert isinstance(result, DistributionInfo)
        assert result.distribution_id == 'E1234567890ABC'
        assert result.domain_name == 'd111111abcdef8.cloudfront.net'
        assert result.status == 'Deployed'
        assert result.enabled is True
    
    def test_get_distribution_with_custom_id(self, cloudfront_manager, mock_cloudfront_client):
        """Test getting distribution with custom ID."""
        mock_cloudfront_client.get_distribution.return_value = {
            'Distribution': {
                'Id': 'ECUSTOM123',
                'DomainName': 'd222222abcdef8.cloudfront.net',
                'Status': 'Deployed',
                'DistributionConfig': {'Enabled': True}
            }
        }
        
        result = cloudfront_manager.get_distribution(distribution_id='ECUSTOM123')
        
        # Verify correct distribution ID was used
        call_args = mock_cloudfront_client.get_distribution.call_args
        assert call_args[1]['Id'] == 'ECUSTOM123'
    
    def test_get_distribution_no_id(self, cloudfront_manager, mock_aws_config):
        """Test getting distribution fails without ID."""
        mock_aws_config.cloudfront_distribution_id = None
        
        with pytest.raises(ValueError) as exc_info:
            cloudfront_manager.get_distribution()
        
        assert 'No CloudFront distribution ID' in str(exc_info.value)
    
    def test_get_distribution_not_found(self, cloudfront_manager, mock_cloudfront_client):
        """Test handling distribution not found error."""
        mock_cloudfront_client.get_distribution.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchDistribution', 'Message': 'Distribution not found'}},
            'get_distribution'
        )
        
        with pytest.raises(ClientError):
            cloudfront_manager.get_distribution()


class TestListDistributions:
    """Test listing CloudFront distributions."""
    
    def test_list_distributions_success(self, cloudfront_manager, mock_cloudfront_client):
        """Test listing distributions successfully."""
        mock_cloudfront_client.list_distributions.return_value = {
            'DistributionList': {
                'Items': [
                    {
                        'Id': 'E1111111111111',
                        'DomainName': 'd111111abcdef8.cloudfront.net',
                        'Status': 'Deployed',
                        'Enabled': True
                    },
                    {
                        'Id': 'E2222222222222',
                        'DomainName': 'd222222abcdef8.cloudfront.net',
                        'Status': 'InProgress',
                        'Enabled': True
                    }
                ]
            }
        }
        
        distributions = cloudfront_manager.list_distributions()
        
        assert len(distributions) == 2
        assert distributions[0].distribution_id == 'E1111111111111'
        assert distributions[1].distribution_id == 'E2222222222222'
    
    def test_list_distributions_empty(self, cloudfront_manager, mock_cloudfront_client):
        """Test listing when no distributions exist."""
        mock_cloudfront_client.list_distributions.return_value = {
            'DistributionList': {}
        }
        
        distributions = cloudfront_manager.list_distributions()
        
        assert len(distributions) == 0
    
    def test_list_distributions_api_error(self, cloudfront_manager, mock_cloudfront_client):
        """Test handling list distributions API error."""
        mock_cloudfront_client.list_distributions.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'list_distributions'
        )
        
        # Should return empty list on error
        distributions = cloudfront_manager.list_distributions()
        
        assert len(distributions) == 0


class TestFindDistributionForBucket:
    """Test finding distribution for specific bucket."""
    
    def test_find_distribution_for_bucket_success(self, cloudfront_manager, mock_cloudfront_client):
        """Test finding distribution for bucket successfully."""
        # Mock list_distributions
        mock_cloudfront_client.list_distributions.return_value = {
            'DistributionList': {
                'Items': [
                    {
                        'Id': 'E1111111111111',
                        'DomainName': 'd111111abcdef8.cloudfront.net',
                        'Status': 'Deployed',
                        'Enabled': True
                    }
                ]
            }
        }
        
        # Mock get_distribution
        mock_cloudfront_client.get_distribution.return_value = {
            'Distribution': {
                'Id': 'E1111111111111',
                'DomainName': 'd111111abcdef8.cloudfront.net',
                'Status': 'Deployed',
                'DistributionConfig': {
                    'Enabled': True,
                    'Origins': {
                        'Items': [
                            {
                                'Id': 'test-bucket-origin',
                                'DomainName': 'test-bucket.s3.amazonaws.com'
                            }
                        ]
                    }
                }
            }
        }
        
        result = cloudfront_manager.find_distribution_for_bucket()
        
        assert result is not None
        assert result.distribution_id == 'E1111111111111'
    
    def test_find_distribution_for_bucket_not_found(self, cloudfront_manager, mock_cloudfront_client):
        """Test when no distribution exists for bucket."""
        # Mock list_distributions
        mock_cloudfront_client.list_distributions.return_value = {
            'DistributionList': {
                'Items': [
                    {
                        'Id': 'E1111111111111',
                        'DomainName': 'd111111abcdef8.cloudfront.net',
                        'Status': 'Deployed',
                        'Enabled': True
                    }
                ]
            }
        }
        
        # Mock get_distribution with different bucket
        mock_cloudfront_client.get_distribution.return_value = {
            'Distribution': {
                'Id': 'E1111111111111',
                'DomainName': 'd111111abcdef8.cloudfront.net',
                'Status': 'Deployed',
                'DistributionConfig': {
                    'Enabled': True,
                    'Origins': {
                        'Items': [
                            {
                                'Id': 'other-bucket-origin',
                                'DomainName': 'other-bucket.s3.amazonaws.com'
                            }
                        ]
                    }
                }
            }
        }
        
        result = cloudfront_manager.find_distribution_for_bucket()
        
        assert result is None


class TestWaitForDeployment:
    """Test waiting for distribution deployment."""
    
    def test_wait_for_deployment_success(self, cloudfront_manager, mock_cloudfront_client):
        """Test waiting for deployment to complete."""
        # Mock get_distribution to return Deployed status
        mock_cloudfront_client.get_distribution.return_value = {
            'Distribution': {
                'Id': 'E1234567890ABC',
                'DomainName': 'd111111abcdef8.cloudfront.net',
                'Status': 'Deployed',
                'DistributionConfig': {'Enabled': True}
            }
        }
        
        result = cloudfront_manager.wait_for_deployment('E1234567890ABC', max_wait_seconds=5)
        
        assert result is True
    
    def test_wait_for_deployment_timeout(self, cloudfront_manager, mock_cloudfront_client):
        """Test timeout when deployment takes too long."""
        # Mock get_distribution to always return InProgress
        mock_cloudfront_client.get_distribution.return_value = {
            'Distribution': {
                'Id': 'E1234567890ABC',
                'DomainName': 'd111111abcdef8.cloudfront.net',
                'Status': 'InProgress',
                'DistributionConfig': {'Enabled': True}
            }
        }
        
        result = cloudfront_manager.wait_for_deployment('E1234567890ABC', max_wait_seconds=2)
        
        assert result is False
    
    def test_wait_for_deployment_api_error(self, cloudfront_manager, mock_cloudfront_client):
        """Test handling API error during wait."""
        mock_cloudfront_client.get_distribution.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchDistribution', 'Message': 'Distribution not found'}},
            'get_distribution'
        )
        
        result = cloudfront_manager.wait_for_deployment('E1234567890ABC', max_wait_seconds=5)
        
        assert result is False
