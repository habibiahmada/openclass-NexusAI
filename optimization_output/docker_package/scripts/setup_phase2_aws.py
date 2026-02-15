"""
Phase 2 AWS Infrastructure Setup
Master script to setup all AWS components for Phase 2:
- CloudFront distribution
- S3 lifecycle policies
- Storage optimization
- Encryption and security
"""

import sys
import time
from setup_cloudfront import CloudFrontSetup
from optimize_s3_storage import S3StorageOptimizer

def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def print_step(step_num, total_steps, description):
    """Print step progress."""
    print(f"\n[Step {step_num}/{total_steps}] {description}")
    print("-" * 70)

def confirm_action(message):
    """Ask user for confirmation."""
    response = input(f"\n{message} (y/n): ").strip().lower()
    return response == 'y'

def main():
    """Main setup orchestrator."""
    print_header("🚀 OpenClass Nexus AI - Phase 2 AWS Infrastructure Setup")
    
    print("This script will configure the following AWS services:")
    print("  1. ☁️  CloudFront Distribution (CDN for fast content delivery)")
    print("  2. 💾 S3 Lifecycle Policies (automatic cost optimization)")
    print("  3. 🔒 S3 Encryption (AES-256 server-side encryption)")
    print("  4. 📦 S3 Versioning (data protection)")
    print("  5. 🤖 S3 Intelligent-Tiering (optional)")
    
    print("\n💰 Expected Benefits:")
    print("  - 60-80% reduction in storage costs")
    print("  - Faster content delivery via CloudFront")
    print("  - Enhanced security with encryption")
    print("  - Data protection with versioning")
    
    print("\n⏱️  Estimated Time: 5-10 minutes (+ 15-20 min for CloudFront deployment)")
    print("💵 Estimated Cost: ~$0.01-0.05/month (well within $1.00 budget)")
    
    if not confirm_action("\n🤔 Do you want to proceed with the setup?"):
        print("\n❌ Setup cancelled by user")
        return
    
    # Track results
    results = {
        'cloudfront': False,
        's3_lifecycle': False,
        's3_encryption': False,
        's3_versioning': False,
        's3_intelligent_tiering': False
    }
    
    try:
        # Step 1: S3 Storage Optimization
        print_step(1, 2, "S3 Storage Optimization")
        print("Configuring S3 bucket for cost efficiency and security...")
        
        optimizer = S3StorageOptimizer()
        
        # Get current status
        print("\n📊 Current Bucket Status:")
        optimizer.get_bucket_size_and_cost()
        
        # Apply optimizations
        print("\n🔧 Applying optimizations...")
        results['s3_lifecycle'] = optimizer.setup_lifecycle_policies()
        time.sleep(1)
        
        results['s3_encryption'] = optimizer.enable_encryption()
        time.sleep(1)
        
        results['s3_versioning'] = optimizer.enable_versioning()
        time.sleep(1)
        
        results['s3_intelligent_tiering'] = optimizer.configure_intelligent_tiering()
        
        # Step 2: CloudFront Distribution
        print_step(2, 2, "CloudFront Distribution Setup")
        print("Creating CloudFront distribution for global content delivery...")
        
        cloudfront = CloudFrontSetup()
        
        # Check for existing distribution
        existing = cloudfront._get_existing_distribution()
        
        if existing:
            print("\n✅ CloudFront distribution already exists!")
            results['cloudfront'] = True
        else:
            # Create new distribution
            print("\n🚀 Creating new CloudFront distribution...")
            dist_result = cloudfront.create_distribution()
            results['cloudfront'] = dist_result is not None
        
        # Final Summary
        print_header("✅ Phase 2 AWS Infrastructure Setup Complete!")
        
        print("📊 Setup Results:")
        print("-" * 70)
        
        status_emoji = {True: "✅", False: "❌"}
        
        print(f"\n  S3 Storage Optimization:")
        print(f"    {status_emoji[results['s3_lifecycle']]} Lifecycle Policies")
        print(f"    {status_emoji[results['s3_encryption']]} Server-Side Encryption (AES-256)")
        print(f"    {status_emoji[results['s3_versioning']]} Versioning")
        print(f"    {status_emoji[results['s3_intelligent_tiering']]} Intelligent-Tiering (optional)")
        
        print(f"\n  CloudFront Distribution:")
        print(f"    {status_emoji[results['cloudfront']]} Distribution Created/Configured")
        
        # Next Steps
        print("\n" + "=" * 70)
        print("📝 Next Steps:")
        print("=" * 70)
        
        print("\n1. ⏳ Wait for CloudFront deployment (15-20 minutes)")
        print("   Check status: python scripts/setup_cloudfront.py --status")
        
        print("\n2. 🧪 Test CloudFront access:")
        print("   python scripts/setup_cloudfront.py --status")
        
        print("\n3. 📊 Monitor costs:")
        print("   python scripts/optimize_s3_storage.py --status")
        
        print("\n4. 🚀 Start Phase 2 implementation:")
        print("   - PDF extraction and processing")
        print("   - Vector embeddings generation")
        print("   - ChromaDB knowledge base creation")
        
        print("\n💡 Tips:")
        print("   - CloudFront caches content for 24 hours")
        print("   - Use --invalidate to force cache refresh")
        print("   - Lifecycle policies apply automatically")
        print("   - All new S3 objects are encrypted by default")
        
        print("\n💰 Cost Monitoring:")
        print("   - Current setup: ~$0.01-0.05/month")
        print("   - Budget limit: $1.00/month")
        print("   - Remaining: ~$0.95-0.99/month")
        
        print("\n✅ AWS infrastructure is ready for Phase 2 development!")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        print("You can re-run this script to complete the setup")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n\n❌ Error during setup: {e}")
        print("\nPartial setup may have completed. Check individual components:")
        print("  - S3: python scripts/optimize_s3_storage.py --status")
        print("  - CloudFront: python scripts/setup_cloudfront.py --status")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Usage:")
            print("  python scripts/setup_phase2_aws.py        # Run full setup")
            print("  python scripts/setup_phase2_aws.py --help # Show this help")
            print("\nIndividual Components:")
            print("  python scripts/setup_cloudfront.py        # CloudFront only")
            print("  python scripts/optimize_s3_storage.py     # S3 optimization only")
        else:
            print("Unknown option. Use --help for usage information")
    else:
        main()
