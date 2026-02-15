#!/usr/bin/env python3
"""
Example script demonstrating the complete model packaging and distribution workflow.

This example shows how to:
1. Package a model with metadata
2. Upload to S3 (if configured)
3. Create delta updates between model versions
4. Apply delta updates

Usage:
    python examples/model_packaging_example.py
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, 'src')

try:
    # Try direct imports first
    from local_inference.model_packager import (
        ModelPackager, 
        ModelPackageMetadata,
        create_model_package
    )
    from local_inference.delta_updater import (
        DeltaUpdater,
        create_delta_update,
        apply_delta_update
    )
except ImportError:
    try:
        # Try with src prefix
        from src.local_inference.model_packager import (
            ModelPackager, 
            ModelPackageMetadata,
            create_model_package
        )
        from src.local_inference.delta_updater import (
            DeltaUpdater,
            create_delta_update,
            apply_delta_update
        )
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running this from the project root directory.")
        print("And that all dependencies are installed.")
        sys.exit(1)


def create_example_model(path: Path, version: str, size_mb: int = 2) -> Path:
    """Create an example model file for demonstration."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create content that varies by version
    base_content = f"GGUF_MODEL_VERSION_{version}_".encode()
    content = base_content * (size_mb * 1024 * 256)  # Approximate size
    
    with open(path, 'wb') as f:
        f.write(content)
    
    return path


def demonstrate_model_packaging():
    """Demonstrate model packaging functionality."""
    print("=== Model Packaging Demonstration ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create example model
        model_file = temp_path / "llama-3.2-3b-instruct-q4_k_m.gguf"
        create_example_model(model_file, "1.0.0", size_mb=3)
        
        print(f"Created example model: {model_file}")
        print(f"Model size: {model_file.stat().st_size / (1024**2):.2f} MB")
        
        # Create package metadata
        metadata = ModelPackageMetadata(
            package_name="llama-3.2-3b-instruct",
            version="1.0.0",
            model_id="meta-llama/Llama-3.2-3B-Instruct",
            description="Llama 3.2 3B Instruct model optimized for Indonesian educational content",
            quantization="Q4_K_M",
            supports_indonesian=True,
            educational_optimized=True,
            curriculum_subjects=[
                "Informatika", "Matematika", "Fisika", "Kimia",
                "Biologi", "Bahasa Indonesia", "Bahasa Inggris"
            ]
        )
        
        # Create packager
        packages_dir = temp_path / "packages"
        packager = ModelPackager(output_dir=str(packages_dir))
        
        # Create package
        print("\nCreating model package...")
        package_path = packager.create_package(model_file, metadata)
        
        print(f"Package created: {package_path}")
        print(f"Package size: {package_path.stat().st_size / (1024**2):.2f} MB")
        
        # Verify package
        print("\nVerifying package...")
        verification = packager.verify_package(package_path)
        
        print(f"Package valid: {verification['valid']}")
        if verification['errors']:
            print(f"Errors: {verification['errors']}")
        if verification['warnings']:
            print(f"Warnings: {verification['warnings']}")
        
        # Extract and display metadata
        print("\nExtracting metadata...")
        extracted_metadata = packager.extract_metadata(package_path)
        if extracted_metadata:
            print(f"Package: {extracted_metadata.package_name} v{extracted_metadata.version}")
            print(f"Model ID: {extracted_metadata.model_id}")
            print(f"SHA256: {extracted_metadata.sha256_checksum}")
            print(f"Educational subjects: {', '.join(extracted_metadata.curriculum_subjects)}")
        
        # List packages
        packages = packager.list_packages()
        print(f"\nFound {len(packages)} packages in directory:")
        for pkg in packages:
            print(f"  - {pkg['filename']} ({pkg['size_mb']:.2f} MB)")
        
        return package_path, extracted_metadata


def demonstrate_s3_upload():
    """Demonstrate S3 upload functionality (if configured)."""
    print("\n=== S3 Upload Demonstration ===\n")
    
    # Check if AWS credentials are available
    try:
        import boto3
        # Try to create S3 client to check credentials
        s3_client = boto3.client('s3')
        print("AWS credentials found - S3 upload is available")
        
        # Note: This is just a demonstration - actual upload would require
        # a real S3 bucket and proper configuration
        print("To upload to S3, configure your bucket name and run:")
        print("  packager = ModelPackager(s3_bucket='your-bucket-name')")
        print("  upload_info = packager.upload_to_s3(package_path)")
        
    except Exception as e:
        print(f"S3 upload not available: {e}")
        print("To enable S3 upload:")
        print("  1. Configure AWS credentials (aws configure)")
        print("  2. Set up an S3 bucket")
        print("  3. Update the packager with your bucket name")


def demonstrate_delta_updates():
    """Demonstrate delta update functionality."""
    print("\n=== Delta Updates Demonstration ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create multiple model versions
        print("Creating model versions...")
        models = {}
        versions = ["1.0.0", "1.1.0", "1.2.0"]
        
        for version in versions:
            model_file = temp_path / f"model_v{version.replace('.', '_')}.gguf"
            create_example_model(model_file, version, size_mb=2)
            models[version] = model_file
            print(f"  Created model v{version}: {model_file.stat().st_size / (1024**2):.2f} MB")
        
        # Create delta updater
        updates_dir = temp_path / "updates"
        updater = DeltaUpdater(updates_dir=str(updates_dir))
        
        # Create delta updates
        print("\nCreating delta updates...")
        delta_updates = []
        
        # Create incremental updates
        for i in range(len(versions) - 1):
            from_version = versions[i]
            to_version = versions[i + 1]
            
            print(f"  Creating delta: {from_version} -> {to_version}")
            delta_dir = updater.create_delta_update(
                old_model_path=models[from_version],
                new_model_path=models[to_version],
                from_version=from_version,
                to_version=to_version,
                model_id="meta-llama/Llama-3.2-3B-Instruct",
                package_name="llama-3.2-3b-instruct"
            )
            delta_updates.append(delta_dir)
        
        # Create direct update (skip version)
        print(f"  Creating direct delta: 1.0.0 -> 1.2.0")
        direct_delta = updater.create_delta_update(
            old_model_path=models["1.0.0"],
            new_model_path=models["1.2.0"],
            from_version="1.0.0",
            to_version="1.2.0",
            model_id="meta-llama/Llama-3.2-3B-Instruct",
            package_name="llama-3.2-3b-instruct"
        )
        delta_updates.append(direct_delta)
        
        # List available updates
        print("\nAvailable delta updates:")
        available_updates = updater.list_available_updates()
        
        for update in available_updates:
            print(f"  {update['from_version']} -> {update['to_version']}")
            print(f"    Size: {update['delta_size_mb']:.2f} MB")
            print(f"    Savings: {update['bandwidth_savings_percent']:.1f}%")
            print(f"    Created: {update['created_at']}")
        
        # Demonstrate applying an update
        print("\nApplying delta update (1.0.0 -> 1.1.0)...")
        
        # Find the 1.0.0 -> 1.1.0 update
        target_update = None
        for update in available_updates:
            if update['from_version'] == '1.0.0' and update['to_version'] == '1.1.0':
                target_update = update
                break
        
        if target_update:
            updated_model = temp_path / "updated_model.gguf"
            result_path = updater.apply_delta_update(
                current_model_path=models["1.0.0"],
                delta_update_dir=Path(target_update['path']),
                output_path=updated_model
            )
            
            print(f"Update applied successfully: {result_path}")
            print(f"Updated model size: {result_path.stat().st_size / (1024**2):.2f} MB")
            
            # Verify the update worked
            with open(models["1.1.0"], 'rb') as f1, open(updated_model, 'rb') as f2:
                original_content = f1.read()
                updated_content = f2.read()
                
                if original_content == updated_content:
                    print("✓ Update verification successful - files match!")
                else:
                    print("✗ Update verification failed - files don't match")
        
        # Demonstrate update verification
        print("\nVerifying delta updates...")
        for i, delta_dir in enumerate(delta_updates):
            verification = updater.verify_update(delta_dir)
            print(f"  Update {i+1}: {'Valid' if verification['valid'] else 'Invalid'}")
            if verification['errors']:
                print(f"    Errors: {verification['errors']}")


def demonstrate_convenience_functions():
    """Demonstrate convenience functions."""
    print("\n=== Convenience Functions Demonstration ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create example models
        old_model = temp_path / "old_model.gguf"
        new_model = temp_path / "new_model.gguf"
        
        create_example_model(old_model, "1.0.0", size_mb=2)
        create_example_model(new_model, "2.0.0", size_mb=2)
        
        print("Using convenience functions...")
        
        # Create package using convenience function
        print("  Creating package with create_model_package()...")
        package_path = create_model_package(
            model_path=str(new_model),
            package_name="convenience-example",
            version="2.0.0",
            model_id="example/convenience-model",
            output_dir=str(temp_path / "packages"),
            description="Example package created with convenience function"
        )
        
        print(f"    Package created: {package_path}")
        
        # Create delta update using convenience function
        print("  Creating delta update with create_delta_update()...")
        delta_dir = create_delta_update(
            old_model_path=str(old_model),
            new_model_path=str(new_model),
            from_version="1.0.0",
            to_version="2.0.0",
            model_id="example/convenience-model",
            package_name="convenience-example",
            updates_dir=str(temp_path / "updates")
        )
        
        print(f"    Delta update created: {delta_dir}")
        
        # Apply delta update using convenience function
        print("  Applying delta update with apply_delta_update()...")
        updated_model = temp_path / "convenience_updated.gguf"
        result_path = apply_delta_update(
            current_model_path=str(old_model),
            delta_update_dir=str(delta_dir),
            output_path=str(updated_model)
        )
        
        print(f"    Update applied: {result_path}")


def main():
    """Run the complete demonstration."""
    print("OpenClass Nexus AI - Model Packaging and Distribution Demo")
    print("=" * 60)
    
    try:
        # Demonstrate model packaging
        package_path, metadata = demonstrate_model_packaging()
        
        # Demonstrate S3 upload (informational)
        demonstrate_s3_upload()
        
        # Demonstrate delta updates
        demonstrate_delta_updates()
        
        # Demonstrate convenience functions
        demonstrate_convenience_functions()
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("\nKey features demonstrated:")
        print("  ✓ Model packaging with metadata")
        print("  ✓ Package verification and validation")
        print("  ✓ Delta update creation and application")
        print("  ✓ Bandwidth optimization through delta updates")
        print("  ✓ Convenience functions for easy usage")
        print("  ✓ S3 upload capability (when configured)")
        
        print("\nNext steps:")
        print("  1. Configure AWS credentials for S3 upload")
        print("  2. Install bsdiff4 for better binary diff support:")
        print("     pip install bsdiff4")
        print("  3. Integrate with your model management workflow")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())