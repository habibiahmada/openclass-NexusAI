#!/usr/bin/env python3
"""
Download Educational PDFs from S3
Downloads PDF files from S3 bucket to local directory for development
"""

import boto3
import json
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.aws_config import aws_config

def load_dataset_inventory():
    """Load dataset inventory to get file list"""
    inventory_path = Path(__file__).parent.parent / "dataset_inventory.json"
    
    try:
        with open(inventory_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading dataset inventory: {e}")
        return None

def download_pdf_from_s3(s3_key, local_path, s3_client, bucket_name):
    """Download a single PDF file from S3"""
    try:
        # Create local directory if it doesn't exist
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file already exists locally
        if local_path.exists():
            print(f"ℹ️  File already exists locally: {local_path.name}")
            return True
        
        # Get file size from S3
        try:
            response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            file_size = response['ContentLength']
            print(f"📥 Downloading {local_path.name} ({file_size / 1024 / 1024:.1f} MB)...")
        except Exception as e:
            print(f"❌ File not found in S3: {s3_key}")
            return False
        
        # Download file
        s3_client.download_file(bucket_name, s3_key, str(local_path))
        print(f"✅ Downloaded: {local_path.name}")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading {s3_key}: {e}")
        return False

def download_all_pdfs(local_base_path=None, subject_filter=None, grade_filter=None):
    """Download all PDFs from S3 to local directory"""
    
    # Load inventory
    inventory = load_dataset_inventory()
    if not inventory:
        return False
    
    # Get S3 client
    s3_client = aws_config.get_s3_client()
    bucket_name = aws_config.s3_bucket
    
    # Validate S3 access
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Connected to S3 bucket: {bucket_name}")
    except Exception as e:
        print(f"❌ Cannot access S3 bucket {bucket_name}: {e}")
        return False
    
    # Set default local base path if not provided
    if local_base_path is None:
        local_base_path = Path(__file__).parent.parent / "raw_dataset"
    else:
        local_base_path = Path(local_base_path)
    
    print(f"📁 Local base path: {local_base_path}")
    
    # Filter files if needed
    files_to_download = inventory['files']
    if subject_filter:
        files_to_download = [f for f in files_to_download if f['subject'] == subject_filter]
    if grade_filter:
        files_to_download = [f for f in files_to_download if f['grade'] == grade_filter]
    
    # Download each file
    success_count = 0
    total_files = len(files_to_download)
    
    print(f"\n🚀 Starting download of {total_files} files...")
    
    for i, file_info in enumerate(files_to_download, 1):
        print(f"[{i}/{total_files}] Processing {file_info['filename']}...")
        
        # Construct local path
        local_path = local_base_path / file_info['grade'] / file_info['subject'] / file_info['filename']
        
        # Get S3 key from inventory
        s3_key = file_info['s3_key']
        
        # Download file
        if download_pdf_from_s3(s3_key, str(local_path), s3_client, bucket_name):
            success_count += 1
    
    # Summary
    print(f"\n📊 Download Summary:")
    print(f"   Total files: {total_files}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {total_files - success_count}")
    
    if success_count == total_files:
        print("🎉 All files downloaded successfully!")
        return True
    else:
        print("⚠️  Some files failed to download. Check the logs above.")
        return False

def list_s3_files():
    """List all PDF files in S3"""
    s3_client = aws_config.get_s3_client()
    bucket_name = aws_config.s3_bucket
    
    print("📚 PDF files in S3:")
    print("=" * 50)
    
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='raw-pdf/kelas_10/informatika/'
        )
        
        if 'Contents' in response:
            total_size = 0
            for obj in response['Contents']:
                size_mb = obj['Size'] / 1024 / 1024
                total_size += obj['Size']
                print(f"📄 {obj['Key'].split('/')[-1]} ({size_mb:.1f} MB)")
            
            print(f"\n📊 Total: {len(response['Contents'])} files, {total_size / 1024 / 1024:.1f} MB")
        else:
            print("No PDF files found in S3")
            
    except Exception as e:
        print(f"❌ Error listing S3 files: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download educational PDFs from S3')
    parser.add_argument('--local-path', help='Local directory to download PDFs to')
    parser.add_argument('--subject', help='Filter by subject (e.g., informatika)')
    parser.add_argument('--grade', help='Filter by grade (e.g., kelas_10)')
    parser.add_argument('--list-only', action='store_true', help='Only list files in S3')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be downloaded without downloading')
    
    args = parser.parse_args()
    
    print("📥 OpenClass Nexus AI - S3 Download Tool")
    print("=" * 50)
    
    # Verify AWS credentials
    is_valid, result = aws_config.validate_credentials()
    if not is_valid:
        print(f"❌ AWS credentials invalid: {result}")
        sys.exit(1)
    
    print(f"✅ Connected to AWS account: {result.get('Account')}")
    
    if args.list_only:
        list_s3_files()
        return
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be downloaded")
        inventory = load_dataset_inventory()
        if inventory:
            files_to_show = inventory['files']
            if args.subject:
                files_to_show = [f for f in files_to_show if f['subject'] == args.subject]
            if args.grade:
                files_to_show = [f for f in files_to_show if f['grade'] == args.grade]
            
            print(f"Would download {len(files_to_show)} files:")
            for file_info in files_to_show:
                print(f"   📄 {file_info['filename']} <- {file_info['s3_key']}")
        return
    
    # Download files
    success = download_all_pdfs(args.local_path, args.subject, args.grade)
    
    if success:
        print("\n🎉 Download completed successfully!")
    else:
        print("\n❌ Download completed with errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()