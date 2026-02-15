# Models Directory Structure

This directory contains the model management infrastructure for OpenClass Nexus AI Phase 3 local inference.

## Directory Structure

```
models/
├── cache/          # Downloaded GGUF model files
├── configs/        # Model configuration files
├── metadata/       # Model metadata and checksums
└── README.md       # This documentation file
```

## Directory Purposes

### `cache/`
- Stores downloaded GGUF model files
- Primary location for Llama-3.2-3B-Instruct-Q4_K_M.gguf
- Organized by model name and version
- Automatically managed by ModelDownloader

### `configs/`
- Contains model configuration JSON/YAML files
- Stores inference parameters and optimization settings
- Environment-specific configurations (performance, quality, memory-optimized)
- User customization files

### `metadata/`
- Model metadata files (checksums, version info, download timestamps)
- Model validation results and performance benchmarks
- License information and usage tracking
- Model compatibility information

## Usage

The model management system automatically creates and manages these directories.
Models are downloaded to `cache/`, with corresponding metadata stored in `metadata/`
and configurations in `configs/`.

## Storage Requirements

- Llama-3.2-3B-Instruct (Q4_K_M): ~2.5GB
- Additional space for metadata and temporary files: ~100MB
- Total recommended space: 3GB minimum

## Security Notes

- Model files are validated using checksums stored in `metadata/`
- Only models from trusted sources (HuggingFace Hub) are downloaded
- All downloads are verified for integrity before use