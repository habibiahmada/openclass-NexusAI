#!/usr/bin/env python3
"""
Upload Educational PDFs to S3
Uploads PDF files from local directory to S3 bucket with proper organization
"""

import boto3
import json
import os
import sys
from pathlib import Path
from datetime import datetime

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

def upload_pdf_to_s3(local_path, s3_key, s3_client, bucket_name):
    """Upload a single PDF file to S3"""
    try:
        # Check if file exists locally
        if not os.path.exists(local_path):
            print(f"⚠️  Local file not found: {local_path}")
            return False
        
        # Check if file already exists in S3
        try:
            s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            print(f"ℹ️  File already exists in S3: {s3_key}")
            return True
        except:
            pass  # File doesn't exist, proceed with upload
        
        # Get file size for progress
        file_size = os.path.getsize(local_path)
        
        # Upload with progress
        print(f"📤 Uploading {os.path.basename(local_path)} ({file_size / 1024 / 1024:.1f} MB)...")
        
        s3_client.upload_file(
            local_path, 
            bucket_name, 
            s3_key,
            ExtraArgs={
                'ContentType': 'application/pdf',
                'Metadata': {
                    'project': 'OpenClassNexusAI',
                    'content-type': 'educational-pdf',
                    'source': 'BSE-Kemdikbud'
                }
            }
        )
        
        print(f"✅ Uploaded: {s3_key}")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading {local_path}: {e}")
        return False

def upload_all_pdfs(local_base_path=None):
    """Upload all PDFs from inventory to S3"""
    
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
    
    # Upload each file
    success_count = 0
    total_files = len(inventory['files'])
    
    print(f"\n🚀 Starting upload of {total_files} files...")
    
    for i, file_info in enumerate(inventory['files'], 1):
        print(f"[{i}/{total_files}] Processing {file_info['filename']}...")
        
        # Construct local path
        local_path = local_base_path / file_info['grade'] / file_info['subject'] / file_info['filename']
        
        # Get S3 key from inventory
        s3_key = file_info['s3_key']
        
        # Upload file
        if upload_pdf_to_s3(str(local_path), s3_key, s3_client, bucket_name):
            success_count += 1
    
    # Summary
    print(f"\n📊 Upload Summary:")
    print(f"   Total files: {total_files}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {total_files - success_count}")
    
    if success_count == total_files:
        print("🎉 All files uploaded successfully!")
        
        # Update inventory status
        inventory['processing_status']['s3_upload_status'] = 'completed'
        inventory['processing_status']['last_upload_date'] = str(datetime.now().isoformat())
        
        # Save updated inventory
        inventory_path = Path(__file__).parent.parent / "dataset_inventory.json"
        with open(inventory_path, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        
        return True
    else:
        print("⚠️  Some files failed to upload. Check the logs above.")
        return False

def verify_s3_structure():
    """Verify S3 bucket structure matches expected layout"""
    s3_client = aws_config.get_s3_client()
    bucket_name = aws_config.s3_bucket
    
    print("🔍 Verifying S3 bucket structure...")
    
    expected_prefixes = [
        'raw-pdf/',
        'processed-text/',
        'vector-db/',
        'model-weights/'
    ]
    
    for prefix in expected_prefixes:
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=1
            )
            
            if 'Contents' in response or prefix == 'raw-pdf/':
                print(f"✅ Prefix exists: {prefix}")
            else:
                print(f"ℹ️  Prefix empty (expected): {prefix}")
                
        except Exception as e:
            print(f"❌ Error checking prefix {prefix}: {e}")
    
    # List files in raw-pdf directory
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='raw-pdf/kelas_10/informatika/',
            MaxKeys=20
        )
        
        if 'Contents' in response:
            file_count = len(response['Contents'])
            print(f"📚 Found {file_count} PDF files in S3")
            
            # Show first few files
            for obj in response['Contents'][:5]:
                size_mb = obj['Size'] / 1024 / 1024
                print(f"   📄 {obj['Key']} ({size_mb:.1f} MB)")
            
            if file_count > 5:
                print(f"   ... and {file_count - 5} more files")
        else:
            print("📚 No PDF files found in S3")
            
    except Exception as e:
        print(f"❌ Error listing PDF files: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload educational PDFs to S3')
    parser.add_argument('--local-path', help='Local directory containing PDFs')
    parser.add_argument('--verify-only', action='store_true', help='Only verify S3 structure')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be uploaded without uploading')
    
    args = parser.parse_args()
    
    print("📤 OpenClass Nexus AI - S3 Upload Tool")
    print("=" * 50)
    
    # Verify AWS credentials
    is_valid, result = aws_config.validate_credentials()
    if not is_valid:
        print(f"❌ AWS credentials invalid: {result}")
        sys.exit(1)
    
    print(f"✅ Connected to AWS account: {result.get('Account')}")
    
    if args.verify_only:
        verify_s3_structure()
        return
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be uploaded")
        inventory = load_dataset_inventory()
        if inventory:
            print(f"Would upload {len(inventory['files'])} files:")
            for file_info in inventory['files']:
                print(f"   📄 {file_info['filename']} -> {file_info['s3_key']}")
        return
    
    # Upload files
    success = upload_all_pdfs(args.local_path)
    
    if success:
        print("\n🔍 Verifying upload...")
        verify_s3_structure()
        print("\n🎉 Upload completed successfully!")
    else:
        print("\n❌ Upload completed with errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()