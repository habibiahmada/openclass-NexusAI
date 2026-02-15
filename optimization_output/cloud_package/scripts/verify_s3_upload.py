#!/usr/bin/env python3
"""Verify S3 upload for final checkpoint."""

import boto3
from botocore.exceptions import ClientError

def verify_s3_upload():
    """Verify that files were uploaded to S3."""
    try:
        s3 = boto3.client('s3')
        bucket = 'openclass-nexus-data'
        prefix = 'processed/informatika/kelas_10/'
        
        print("=" * 60)
        print("S3 Upload Verification")
        print("=" * 60)
        print(f"Bucket: {bucket}")
        print(f"Prefix: {prefix}")
        print()
        
        # List objects
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=100
        )
        
        if 'Contents' not in response:
            print("✗ No files found in S3")
            return False
        
        files = response['Contents']
        total_size = sum(obj['Size'] for obj in files)
        
        print(f"Total files uploaded: {len(files)}")
        print(f"Total size: {total_size / (1024*1024):.2f} MB")
        print()
        
        # Group by type
        chromadb_files = [f for f in files if 'chromadb/' in f['Key']]
        text_files = [f for f in files if 'text/' in f['Key']]
        metadata_files = [f for f in files if 'metadata/' in f['Key']]
        
        print(f"ChromaDB files: {len(chromadb_files)}")
        print(f"Text files: {len(text_files)}")
        print(f"Metadata files: {len(metadata_files)}")
        print()
        
        # Show sample files
        print("Sample files:")
        for obj in files[:10]:
            size_kb = obj['Size'] / 1024
            print(f"  - {obj['Key']} ({size_kb:.1f} KB)")
        
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more files")
        
        print()
        print("✓ S3 upload verified successfully!")
        return True
        
    except ClientError as e:
        print(f"✗ S3 error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    verify_s3_upload()
