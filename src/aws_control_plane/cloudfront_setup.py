"""
CloudFront Distribution Setup Module

Manages CloudFront distribution for VKP delivery with signed URLs.
"""

import json
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CloudFrontManager:
    """Manages CloudFront distribution for VKP delivery"""

    def __init__(self, region: str):
        self.cloudfront_client = boto3.client('cloudfront', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.region = region

    def create_distribution_idempotent(
        self,
        distribution_name: str,
        s3_bucket_name: str,
        s3_origin_path: str = "/vkp"
    ) -> Optional[str]:
        """
        Create CloudFront distribution idempotently.
        Returns distribution ID if successful.
        """
        try:
            # Check if distribution already exists
            existing_dist = self._find_distribution_by_name(distribution_name)
            if existing_dist:
                logger.info(f"CloudFront distribution '{distribution_name}' already exists")
                return existing_dist['Id']

            # Create new distribution
            s3_domain = f"{s3_bucket_name}.s3.{self.region}.amazonaws.com"

            distribution_config = {
                'CallerReference': distribution_name,
                'Comment': f"VKP distribution for {distribution_name}",
                'Enabled': True,
                'Origins': {
                    'Quantity': 1,
                    'Items': [
                        {
                            'Id': 'S3Origin',
                            'DomainName': s3_domain,
                            'S3OriginConfig': {
                                'OriginAccessIdentity': ''
                            },
                            'OriginPath': s3_origin_path
                        }
                    ]
                },
                'DefaultCacheBehavior': {
                    'TargetOriginId': 'S3Origin',
                    'ViewerProtocolPolicy': 'https-only',
                    'TrustedSigners': {
                        'Enabled': True,
                        'Quantity': 0
                    },
                    'ForwardedValues': {
                        'QueryString': False,
                        'Cookies': {'Forward': 'none'},
                        'Headers': {
                            'Quantity': 0
                        }
                    },
                    'MinTTL': 0,
                    'DefaultTTL': 86400,
                    'MaxTTL': 31536000
                },
                'CacheBehaviors': {
                    'Quantity': 0
                }
            }

            response = self.cloudfront_client.create_distribution(
                DistributionConfig=distribution_config
            )

            dist_id = response['Distribution']['Id']
            logger.info(f"Created CloudFront distribution '{distribution_name}' with ID '{dist_id}'")
            return dist_id
        except ClientError as e:
            logger.error(f"Failed to create CloudFront distribution: {e}")
            return None

    def _find_distribution_by_name(self, name: str) -> Optional[dict]:
        """Find distribution by name/comment"""
        try:
            response = self.cloudfront_client.list_distributions()
            
            for dist in response.get('DistributionList', {}).get('Items', []):
                if dist.get('Comment') == f"VKP distribution for {name}":
                    return dist
            
            return None
        except ClientError as e:
            logger.error(f"Failed to list distributions: {e}")
            return None

    def get_distribution_domain(self, distribution_id: str) -> Optional[str]:
        """Get domain name for distribution"""
        try:
            response = self.cloudfront_client.get_distribution(Id=distribution_id)
            domain = response['Distribution']['DomainName']
            logger.info(f"Distribution domain: {domain}")
            return domain
        except ClientError as e:
            logger.error(f"Failed to get distribution domain: {e}")
            return None

    def create_signed_url(
        self,
        distribution_domain: str,
        file_path: str,
        key_pair_id: str,
        private_key: str,
        expiration_seconds: int = 3600
    ) -> Optional[str]:
        """
        Create signed URL for CloudFront distribution.
        
        Args:
            distribution_domain: CloudFront domain name
            file_path: Path to file in distribution
            key_pair_id: CloudFront key pair ID
            private_key: Private key for signing
            expiration_seconds: URL expiration time in seconds
        """
        try:
            from datetime import datetime, timedelta
            import base64
            import hashlib
            import hmac

            # Create URL
            url = f"https://{distribution_domain}/{file_path}"

            # Create policy
            expiration = datetime.utcnow() + timedelta(seconds=expiration_seconds)
            expiration_timestamp = int(expiration.timestamp())

            policy = {
                "Statement": [
                    {
                        "Resource": url,
                        "Condition": {
                            "DateLessThan": {
                                "AWS:EpochTime": expiration_timestamp
                            }
                        }
                    }
                ]
            }

            policy_json = json.dumps(policy, separators=(',', ':'))
            policy_b64 = base64.b64encode(policy_json.encode()).decode()

            # Sign policy
            signature = base64.b64encode(
                hmac.new(
                    private_key.encode(),
                    policy_b64.encode(),
                    hashlib.sha1
                ).digest()
            ).decode()

            # Create signed URL
            signed_url = (
                f"{url}?"
                f"Policy={policy_b64}&"
                f"Signature={signature}&"
                f"Key-Pair-Id={key_pair_id}"
            )

            logger.info(f"Created signed URL for {file_path}")
            return signed_url
        except Exception as e:
            logger.error(f"Failed to create signed URL: {e}")
            return None

    def enable_signed_urls(self, distribution_id: str, key_pair_id: str) -> bool:
        """Enable signed URLs for distribution"""
        try:
            # Get current distribution config
            response = self.cloudfront_client.get_distribution_config(Id=distribution_id)
            config = response['DistributionConfig']
            etag = response['ETag']

            # Update to require signed URLs
            config['DefaultCacheBehavior']['TrustedSigners'] = {
                'Enabled': True,
                'Quantity': 1,
                'Items': [key_pair_id]
            }

            # Update distribution
            self.cloudfront_client.update_distribution(
                Id=distribution_id,
                DistributionConfig=config,
                IfMatch=etag
            )

            logger.info(f"Enabled signed URLs for distribution {distribution_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to enable signed URLs: {e}")
            return False
