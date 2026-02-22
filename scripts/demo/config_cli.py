#!/usr/bin/env python3
"""
Configuration CLI Utility for OpenClass Nexus AI Phase 3.

This script provides command-line interface for managing system configuration:
- Generate default configuration with hardware auto-detection
- Validate existing configuration files
- Update hardware settings
- Convert between YAML and JSON formats

Usage:
    python scripts/config_cli.py generate [--format yaml|json] [--output filename]
    python scripts/config_cli.py validate [--config filename]
    python scripts/config_cli.py update-hardware [--config filename]
    python scripts/config_cli.py convert [--input filename] [--output filename] [--format yaml|json]
    python scripts/config_cli.py info [--config filename]
"""

import argparse
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edge_runtime.config_manager import (
    ConfigurationManager, ConfigFormat, SystemConfiguration
)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def generate_config(args):
    """Generate default configuration with hardware auto-detection."""
    config_manager = ConfigurationManager(args.config_dir)
    
    print("🔍 Detecting hardware configuration...")
    config = config_manager.create_default_configuration()
    
    # Determine format
    format_type = ConfigFormat.YAML if args.format == 'yaml' else ConfigFormat.JSON
    
    # Save configuration
    output_path = config_manager.save_configuration(
        config, 
        filename=args.output,
        format_type=format_type
    )
    
    print(f"✅ Configuration generated successfully!")
    print(f"📁 Saved to: {output_path}")
    print(f"🖥️  Hardware Profile: {config.hardware_profile.profile_name}")
    print(f"💾 Memory: {config.hardware_profile.total_memory_gb:.1f}GB")
    print(f"🔧 CPU Threads: {config.hardware_profile.cpu_threads}")
    print(f"⚡ Performance Tier: {config.hardware_profile.performance_tier}")


def validate_config(args):
    """Validate existing configuration file."""
    config_manager = ConfigurationManager(args.config_dir)
    
    try:
        print(f"🔍 Validating configuration...")
        if args.config:
            config = config_manager.load_configuration(filename=args.config)
        else:
            config = config_manager.load_configuration()
        
        print("✅ Configuration is valid!")
        print(f"📱 App: {config.app_name} v{config.version}")
        print(f"🖥️  Hardware Profile: {config.hardware_profile.profile_name}")
        print(f"🤖 Model: {config.model_config.model_id}")
        print(f"🧠 Context Size: {config.inference_config.n_ctx}")
        print(f"💾 Memory Limit: {config.inference_config.memory_limit_mb}MB")
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {str(e)}")
        sys.exit(1)


def update_hardware(args):
    """Update configuration with current hardware settings."""
    config_manager = ConfigurationManager(args.config_dir)
    
    try:
        print("🔍 Loading existing configuration...")
        if args.config:
            config = config_manager.load_configuration(filename=args.config)
        else:
            config = config_manager.load_configuration()
        
        print("🔧 Detecting current hardware...")
        updated_config = config_manager.update_hardware_settings(config)
        
        # Save updated configuration
        output_path = config_manager.save_configuration(updated_config)
        
        print("✅ Hardware settings updated successfully!")
        print(f"📁 Updated: {output_path}")
        print(f"🖥️  New Profile: {updated_config.hardware_profile.profile_name}")
        print(f"💾 Memory: {updated_config.hardware_profile.total_memory_gb:.1f}GB")
        print(f"🔧 CPU Threads: {updated_config.hardware_profile.cpu_threads}")
        print(f"⚡ Performance Tier: {updated_config.hardware_profile.performance_tier}")
        
    except Exception as e:
        print(f"❌ Hardware update failed: {str(e)}")
        sys.exit(1)


def convert_config(args):
    """Convert configuration between YAML and JSON formats."""
    config_manager = ConfigurationManager(args.config_dir)
    
    try:
        print(f"🔄 Converting configuration format...")
        
        # Load from input file
        config = config_manager.load_configuration(filename=args.input)
        
        # Determine output format
        format_type = ConfigFormat.YAML if args.format == 'yaml' else ConfigFormat.JSON
        
        # Save in new format
        output_path = config_manager.save_configuration(
            config,
            filename=args.output,
            format_type=format_type
        )
        
        print(f"✅ Configuration converted successfully!")
        print(f"📁 Input: {args.input}")
        print(f"📁 Output: {output_path}")
        print(f"📄 Format: {format_type.value.upper()}")
        
    except Exception as e:
        print(f"❌ Configuration conversion failed: {str(e)}")
        sys.exit(1)


def show_info(args):
    """Show detailed information about configuration."""
    config_manager = ConfigurationManager(args.config_dir)
    
    try:
        print("🔍 Loading configuration information...")
        if args.config:
            config = config_manager.load_configuration(filename=args.config)
        else:
            config = config_manager.load_configuration()
        
        print("\n" + "="*60)
        print("📋 OPENCLASS NEXUS AI - CONFIGURATION INFO")
        print("="*60)
        
        print(f"\n📱 APPLICATION:")
        print(f"   Name: {config.app_name}")
        print(f"   Version: {config.version}")
        print(f"   Debug Mode: {config.debug_mode}")
        print(f"   Log Level: {config.log_level}")
        
        print(f"\n🤖 MODEL CONFIGURATION:")
        print(f"   Model ID: {config.model_config.model_id}")
        print(f"   GGUF File: {config.model_config.gguf_filename}")
        print(f"   Repository: {config.model_config.gguf_repo}")
        print(f"   File Size: {config.model_config.file_size_mb}MB")
        print(f"   Quantization: {config.model_config.quantization_format}")
        print(f"   Context Window: {config.model_config.context_window}")
        print(f"   Indonesian Support: {config.model_config.supports_indonesian}")
        
        print(f"\n🧠 INFERENCE CONFIGURATION:")
        print(f"   Context Size: {config.inference_config.n_ctx}")
        print(f"   Max Tokens: {config.inference_config.max_tokens}")
        print(f"   CPU Threads: {config.inference_config.n_threads}")
        print(f"   GPU Layers: {config.inference_config.n_gpu_layers}")
        print(f"   Temperature: {config.inference_config.temperature}")
        print(f"   Memory Limit: {config.inference_config.memory_limit_mb}MB")
        print(f"   Streaming: {config.inference_config.streaming}")
        
        print(f"\n🖥️  HARDWARE PROFILE:")
        print(f"   Profile Name: {config.hardware_profile.profile_name}")
        print(f"   Performance Tier: {config.hardware_profile.performance_tier}")
        print(f"   Total Memory: {config.hardware_profile.total_memory_gb:.1f}GB")
        print(f"   CPU Cores: {config.hardware_profile.cpu_cores}")
        print(f"   CPU Threads: {config.hardware_profile.cpu_threads}")
        print(f"   CPU Frequency: {config.hardware_profile.cpu_frequency_ghz:.1f}GHz")
        print(f"   Architecture: {config.hardware_profile.architecture}")
        
        print(f"\n📚 EDUCATIONAL SETTINGS:")
        print(f"   Response Language: {config.response_language}")
        print(f"   Supported Languages: {', '.join(config.supported_languages)}")
        print(f"   Subjects: {', '.join(config.educational_subjects[:3])}...")
        
        print(f"\n📁 DIRECTORIES:")
        print(f"   Models: {config.models_dir}")
        print(f"   Cache: {config.cache_dir}")
        print(f"   Logs: {config.logs_dir}")
        print(f"   Config: {config.config_dir}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"❌ Failed to load configuration info: {str(e)}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OpenClass Nexus AI Configuration Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate default configuration
  python scripts/config_cli.py generate
  
  # Generate JSON configuration
  python scripts/config_cli.py generate --format json --output my_config.json
  
  # Validate configuration
  python scripts/config_cli.py validate
  
  # Update hardware settings
  python scripts/config_cli.py update-hardware
  
  # Convert YAML to JSON
  python scripts/config_cli.py convert --input config.yaml --output config.json --format json
  
  # Show configuration info
  python scripts/config_cli.py info
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--config-dir', default='./config',
                       help='Configuration directory (default: ./config)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', 
                                          help='Generate default configuration')
    generate_parser.add_argument('--format', choices=['yaml', 'json'], 
                               default='yaml', help='Output format')
    generate_parser.add_argument('--output', help='Output filename')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate',
                                          help='Validate configuration file')
    validate_parser.add_argument('--config', help='Configuration filename')
    
    # Update hardware command
    update_parser = subparsers.add_parser('update-hardware',
                                        help='Update hardware settings')
    update_parser.add_argument('--config', help='Configuration filename')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert',
                                         help='Convert configuration format')
    convert_parser.add_argument('--input', required=True, help='Input filename')
    convert_parser.add_argument('--output', help='Output filename')
    convert_parser.add_argument('--format', choices=['yaml', 'json'],
                              required=True, help='Output format')
    
    # Info command
    info_parser = subparsers.add_parser('info',
                                      help='Show configuration information')
    info_parser.add_argument('--config', help='Configuration filename')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    setup_logging(args.verbose)
    
    # Execute command
    if args.command == 'generate':
        generate_config(args)
    elif args.command == 'validate':
        validate_config(args)
    elif args.command == 'update-hardware':
        update_hardware(args)
    elif args.command == 'convert':
        convert_config(args)
    elif args.command == 'info':
        show_info(args)


if __name__ == '__main__':
    main()