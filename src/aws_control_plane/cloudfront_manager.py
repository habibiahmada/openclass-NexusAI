"""
CloudFront Distribution Manager

Manages CloudFront distributions for efficient content delivery of knowledge base updates.
Implements Requirements 6.1-6.5 for CloudFront distribution setup and cache management.
"""

import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError

from config.aws_config import aws_config


@dataclass
class DistributionInfo:
    """Information about a CloudFront distribution."""
    distribution_id: str
    domain_name: str
    status: str
    enabled: bool


@dataclass
class InvalidationResult:
    """Result of a cache invalidation operation."""
    invalidation_id: str
    status: str
    paths: List[str]


class CloudFrontManager:
    """
    Manages CloudFront distributions for S3 bucket content delivery.
    
    This class handles:
    - Creating CloudFront distributions with proper caching and security settings
    - Invalidating cache when content is updated
    - Configuring HTTPS-only access
    - Setting cache TTL to 24 hours
    
    Requirements:
    - 6.1: Create distribution pointing to S3 bucket
    - 6.2: Set cache TTL to 24 hours
    - 6.3: Require HTTPS for all requests
    - 6.4: Output CloudFront domain URL
    - 6.5: Invalidate cache for updated files
    """
    
    def __init__(self, bucket_name: Optional[str] = None):
        """
        Initialize CloudFront manager.
        
        Args:
            bucket_name: S3 bucket name (defaults to aws_config.s3_bucket)
        """
        self.cloudfront = boto3.client(
            'cloudfront',
            region_name=aws_config.region,
            aws_access_key_id=aws_config.access_key,
            aws_secret_access_key=aws_config.secret_key
        )
        self.s3 = aws_config.get_s3_client()
        self.bucket_name = bucket_name or aws_config.s3_bucket
    
    def create_distribution(self) -> DistributionInfo:
        """
        Create CloudFront distribution for S3 bucket.
        
        Creates a distribution with:
        - HTTPS-only access (redirect-to-https)
        - 24-hour cache TTL (86400 seconds)
        - Gzip compression enabled
        - Cost-optimized price class
        
        Requirements:
        - 6.1: Create distribution pointing to S3 bucket
        - 6.2: Set cache TTL to 24 hours (86400 seconds)
        - 6.3: Require HTTPS for all requests (redirect-to-https)
        - 6.4: Output CloudFront domain URL
        
        Returns:
            DistributionInfo with distribution ID, domain name, status, and enabled flag
            
        Raises:
            ClientError: If distribution creation fails
        """
        # Get S3 bucket region for origin domain
        try:
            bucket_location = self.s3.get_bucket_location(Bucket=self.bucket_name)
            region = bucket_location.get('LocationConstraint') or 'ap-southeast-2'
        except ClientError:
            # Default to ap-southeast-2 if we can't get location
            region = 'ap-southeast-2'
        
        # Build S3 origin domain name
        if region == 'ap-southeast-2':
            origin_domain = f"{self.bucket_name}.s3.amazonaws.com"
        else:
            origin_domain = f"{self.bucket_name}.s3.{region}.amazonaws.com"
        
        # CloudFront distribution configuration
        distribution_config = {
            'CallerReference': f'openclass-nexus-{int(time.time())}',
            'Comment': 'OpenClass Nexus AI - Knowledge Base Distribution',
            'Enabled': True,
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': f'{self.bucket_name}-origin',
                        'DomainName': origin_domain,
                        'S3OriginConfig': {
                            'OriginAccessIdentity': ''
                        }
                    }
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': f'{self.bucket_name}-origin',
                'ViewerProtocolPolicy': 'redirect-to-https',  # Requirement 6.3: HTTPS only
                'AllowedMethods': {
                    'Quantity': 2,
                    'Items': ['GET', 'HEAD'],
                    'CachedMethods': {
                        'Quantity': 2,
                        'Items': ['GET', 'HEAD']
                    }
                },
                'Compress': True,  # Enable gzip compression
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'},
                    'Headers': {
                        'Quantity': 0
                    }
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,  # Requirement 6.2: 24 hours cache (86400 seconds)
                'MaxTTL': 31536000,
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                }
            },
            'PriceClass': 'PriceClass_100',  # Cost optimization: North America and Europe only
            'ViewerCertificate': {
                'CloudFrontDefaultCertificate': True,
                'MinimumProtocolVersion': 'TLSv1.2_2021'
            }
        }
        
        # Create distribution
        response = self.cloudfront.create_distribution(
            DistributionConfig=distribution_config
        )
        
        distribution = response['Distribution']
        
        # Requirement 6.4: Return distribution info with domain URL
        return DistributionInfo(
            distribution_id=distribution['Id'],
            domain_name=distribution['DomainName'],
            status=distribution['Status'],
            enabled=distribution['DistributionConfig']['Enabled']
        )
    
    def invalidate_cache(self, paths: List[str], distribution_id: Optional[str] = None) -> InvalidationResult:
        """
        Invalidate CloudFront cache for specified paths.
        
        This forces CloudFront to fetch fresh content from S3 for the specified paths.
        Useful when knowledge base is updated and users need immediate access to new content.
        
        Requirement 6.5: Invalidate cache for updated files
        
        Args:
            paths: List of paths to invalidate (e.g., ['/processed/*', '/vector_db/*'])
            distribution_id: CloudFront distribution ID (defaults to aws_config value)
            
        Returns:
            InvalidationResult with invalidation ID, status, and paths
            
        Raises:
            ValueError: If no distribution ID is provided or found in config
            ClientError: If invalidation creation fails
        """
        # Get distribution ID from parameter or config
        dist_id = distribution_id or aws_config.cloudfront_distribution_id
        
        if not dist_id:
            raise ValueError(
                "No CloudFront distribution ID provided. "
                "Either pass distribution_id parameter or set CLOUDFRONT_DISTRIBUTION_ID in config."
            )
        
        # Create invalidation batch
        response = self.cloudfront.create_invalidation(
            DistributionId=dist_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': f'invalidation-{int(time.time())}'
            }
        )
        
        invalidation = response['Invalidation']
        
        return InvalidationResult(
            invalidation_id=invalidation['Id'],
            status=invalidation['Status'],
            paths=paths
        )
    
    def get_distribution(self, distribution_id: Optional[str] = None) -> DistributionInfo:
        """
        Get information about a CloudFront distribution.
        
        Args:
            distribution_id: CloudFront distribution ID (defaults to aws_config value)
            
        Returns:
            DistributionInfo with current distribution details
            
        Raises:
            ValueError: If no distribution ID is provided or found in config
            ClientError: If distribution retrieval fails
        """
        dist_id = distribution_id or aws_config.cloudfront_distribution_id
        
        if not dist_id:
            raise ValueError(
                "No CloudFront distribution ID provided. "
                "Either pass distribution_id parameter or set CLOUDFRONT_DISTRIBUTION_ID in config."
            )
        
        response = self.cloudfront.get_distribution(Id=dist_id)
        distribution = response['Distribution']
        
        return DistributionInfo(
            distribution_id=distribution['Id'],
            domain_name=distribution['DomainName'],
            status=distribution['Status'],
            enabled=distribution['DistributionConfig']['Enabled']
        )
    
    def list_distributions(self) -> List[DistributionInfo]:
        """
        List all CloudFront distributions in the account.
        
        Returns:
            List of DistributionInfo objects for all distributions
        """
        distributions = []
        
        try:
            response = self.cloudfront.list_distributions()
            
            if 'DistributionList' in response and 'Items' in response['DistributionList']:
                for dist in response['DistributionList']['Items']:
                    distributions.append(DistributionInfo(
                        distribution_id=dist['Id'],
                        domain_name=dist['DomainName'],
                        status=dist['Status'],
                        enabled=dist['Enabled']
                    ))
        except ClientError:
            # Return empty list if listing fails
            pass
        
        return distributions
    
    def find_distribution_for_bucket(self) -> Optional[DistributionInfo]:
        """
        Find existing CloudFront distribution for the configured S3 bucket.
        
        Returns:
            DistributionInfo if found, None otherwise
        """
        distributions = self.list_distributions()
        
        for dist_info in distributions:
            try:
                # Get full distribution details
                response = self.cloudfront.get_distribution(Id=dist_info.distribution_id)
                distribution = response['Distribution']
                
                # Check if any origin matches our bucket
                for origin in distribution['DistributionConfig']['Origins']['Items']:
                    if self.bucket_name in origin['DomainName']:
                        return dist_info
            except ClientError:
                continue
        
        return None
    
    def wait_for_deployment(self, distribution_id: str, max_wait_seconds: int = 1200) -> bool:
        """
        Wait for CloudFront distribution to be fully deployed.
        
        Args:
            distribution_id: CloudFront distribution ID
            max_wait_seconds: Maximum time to wait in seconds (default: 20 minutes)
            
        Returns:
            True if deployed successfully, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            try:
                dist_info = self.get_distribution(distribution_id)
                
                if dist_info.status == 'Deployed':
                    return True
                
                # Wait 30 seconds before checking again
                time.sleep(30)
            except ClientError:
                return False
        
        return False
