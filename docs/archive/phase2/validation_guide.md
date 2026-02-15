# Validation and Quality Control Guide

## Overview

The validation module (`src/data_processing/validator.py`) provides comprehensive quality control for the ETL pipeline. It validates data at each stage and generates detailed quality reports.

## Features

- **Extraction Validation**: Verify all PDF files have corresponding text files
- **Chunk Validation**: Check chunk counts, positions, and text content
- **Embedding Validation**: Verify embedding dimensions and counts
- **Metadata Validation**: Ensure all required metadata fields are present
- **Quality Reports**: Generate comprehensive reports with pass/fail status

## Usage

### Basic Usage

```python
from src.data_processing.validator import Validator
from pathlib import Path

# Create validator
validator = Validator()

# Validate extraction
pdf_files = [Path("file1.pdf"), Path("file2.pdf")]
result = validator.validate_extraction(pdf_files, "data/processed/text")

if result.passed:
    print("✓ All text files exist")
else:
    print(f"✗ Validation failed: {result.message}")
```

### Validating Chunks

```python
from src.data_processing.metadata_manager import EnrichedChunk

# Create or load chunks
chunks = [...]  # List of EnrichedChunk objects

# Validate chunks
result = validator.validate_chunks(
    chunks=chunks,
    expected_min_chunks=10,
    expected_max_chunks=1000
)

print(f"Chunk validation: {result.message}")
```

### Validating Embeddings

```python
# Validate embeddings
embeddings = [...]  # List of embedding vectors

result = validator.validate_embeddings(
    embeddings=embeddings,
    expected_dimension=1024,
    expected_count=len(chunks)
)

if not result.passed:
    print(f"Invalid embeddings: {result.details}")
```

### Validating Metadata

```python
# Validate metadata completeness
result = validator.validate_metadata(chunks)

if result.passed:
    print("✓ All metadata fields are complete")
else:
    print(f"Missing fields: {result.details['missing_fields']}")
    print(f"Empty fields: {result.details['empty_fields']}")
```

### Generating Quality Reports

```python
# Generate comprehensive quality report
report = validator.generate_quality_report(
    output_path="data/processed/metadata/quality_report.json"
)

print(f"Overall Status: {report.overall_status}")
print(f"Passed: {report.passed_checks}/{report.total_checks}")

# Access individual validation results
for vr in report.validation_results:
    status = "✓" if vr.passed else "✗"
    print(f"{status} {vr.check_name}: {vr.message}")
```

## Integration with ETL Pipeline

The validator can be integrated into the ETL pipeline to validate data at each stage:

```python
from src.data_processing.etl_pipeline import ETLPipeline, PipelineConfig
from src.data_processing.validator import Validator

# Run pipeline
config = PipelineConfig()
pipeline = ETLPipeline(config)
result = pipeline.run()

# Validate results
validator = Validator()

# Validate extraction
pdf_files = list(Path(config.input_dir).glob("*.pdf"))
validator.validate_extraction(pdf_files, f"{config.output_dir}/text")

# Validate chunks
if pipeline.chunking_result:
    validator.validate_chunks(pipeline.chunking_result.enriched_chunks)

# Validate embeddings
if pipeline.embedding_result and pipeline.chunking_result:
    validator.validate_embeddings(
        embeddings=pipeline.embedding_result.embeddings,
        expected_dimension=1024,
        expected_count=len(pipeline.chunking_result.enriched_chunks)
    )

# Validate metadata
if pipeline.chunking_result:
    validator.validate_metadata(pipeline.chunking_result.enriched_chunks)

# Generate report
report = validator.generate_quality_report(
    output_path=f"{config.output_dir}/metadata/quality_report.json"
)
```

## Validation Results

Each validation method returns a `ValidationResult` object with:

- `check_name`: Name of the validation check
- `passed`: Boolean indicating pass/fail
- `message`: Human-readable message
- `details`: Dictionary with detailed information

### Example Result

```python
ValidationResult(
    check_name="extraction_completeness",
    passed=True,
    message="All 15 PDF files have corresponding text files",
    details={
        "total_pdfs": 15,
        "found_text_files": 15,
        "missing_text_files": []
    }
)
```

## Quality Report Format

Quality reports are saved as JSON files with the following structure:

```json
{
  "timestamp": "2026-01-14T10:30:00",
  "total_checks": 4,
  "passed_checks": 3,
  "failed_checks": 1,
  "overall_status": "FAIL",
  "validation_results": [
    {
      "check_name": "extraction_completeness",
      "passed": true,
      "message": "All 15 PDF files have corresponding text files",
      "details": {
        "total_pdfs": 15,
        "found_text_files": 15,
        "missing_text_files": []
      }
    },
    {
      "check_name": "chunk_validation",
      "passed": true,
      "message": "All 3000 chunks are valid",
      "details": {
        "chunk_count": 3000,
        "invalid_chunks": 0
      }
    },
    {
      "check_name": "embedding_validation",
      "passed": true,
      "message": "All 3000 embeddings have correct dimension (1024)",
      "details": {
        "embedding_count": 3000,
        "expected_dimension": 1024,
        "invalid_dimensions": 0
      }
    },
    {
      "check_name": "metadata_validation",
      "passed": false,
      "message": "5 empty field errors",
      "details": {
        "chunk_count": 3000,
        "empty_fields": ["Chunk 10: empty field 'subject'", ...]
      }
    }
  ]
}
```

## Best Practices

1. **Validate Early**: Run validation after each pipeline stage to catch errors early
2. **Check Reports**: Always review quality reports before deploying to production
3. **Set Thresholds**: Use `expected_min_chunks` and `expected_max_chunks` to detect anomalies
4. **Save Reports**: Store quality reports for audit trails and debugging
5. **Monitor Trends**: Track validation metrics over time to identify quality degradation

## Requirements Validation

The validator implements the following requirements:

- **Requirement 9.1**: Validates all PDF files have corresponding text files
- **Requirement 9.2**: Validates chunk counts match expected ranges
- **Requirement 9.3**: Validates all chunks have corresponding 1024-dimensional embeddings
- **Requirement 9.4**: Validates all required metadata fields are present
- **Requirement 9.5**: Generates quality reports with pass/fail status

## Testing

The validation module is thoroughly tested with:

- **Unit Tests**: 20 tests covering all validation methods (`tests/unit/test_validator.py`)
- **Property Tests**: 5 property-based tests with 100 iterations each (`tests/property/test_validation_properties.py`)

Run tests with:

```bash
# Run all validation tests
pytest tests/unit/test_validator.py tests/property/test_validation_properties.py -v

# Run only unit tests
pytest tests/unit/test_validator.py -v

# Run only property tests
pytest tests/property/test_validation_properties.py -v
```

## Example

See `examples/validation_example.py` for a complete working example demonstrating all validation features.

Run the example:

```bash
python examples/validation_example.py
```

## API Reference

### Validator Class

#### `__init__(config: Optional[Dict[str, Any]] = None)`

Initialize validator with optional configuration.

#### `validate_extraction(pdf_files: List[Path], processed_dir: str) -> ValidationResult`

Validate that all PDF files have corresponding processed text files.

#### `validate_chunks(chunks: List[EnrichedChunk], expected_min_chunks: Optional[int] = None, expected_max_chunks: Optional[int] = None) -> ValidationResult`

Validate chunk counts and properties.

#### `validate_embeddings(embeddings: List[List[float]], expected_dimension: int = 1024, expected_count: Optional[int] = None) -> ValidationResult`

Validate embedding dimensions and counts.

#### `validate_metadata(chunks: List[EnrichedChunk]) -> ValidationResult`

Validate that all required metadata fields are present and non-empty.

#### `generate_quality_report(output_path: Optional[str] = None) -> QualityReport`

Generate quality report with pass/fail status for each validation.

#### `reset()`

Reset validation results.

### ValidationResult Class

- `check_name: str` - Name of the validation check
- `passed: bool` - Whether the check passed
- `message: str` - Human-readable message
- `details: Dict[str, Any]` - Detailed information

### QualityReport Class

- `timestamp: str` - ISO format timestamp
- `total_checks: int` - Total number of checks
- `passed_checks: int` - Number of passed checks
- `failed_checks: int` - Number of failed checks
- `overall_status: str` - "PASS" or "FAIL"
- `validation_results: List[ValidationResult]` - All validation results

## Troubleshooting

### Common Issues

**Issue**: Validation fails with "Processed directory does not exist"

**Solution**: Ensure the processed directory exists before running validation:
```python
Path("data/processed/text").mkdir(parents=True, exist_ok=True)
```

**Issue**: Chunk validation fails with "invalid position"

**Solution**: Check that `char_start < char_end` for all chunks.

**Issue**: Embedding validation fails with "invalid dimensions"

**Solution**: Verify all embeddings are 1024-dimensional vectors from Bedrock Titan model.

**Issue**: Metadata validation fails with "empty field"

**Solution**: Ensure all required fields (chunk_id, text, source_file, subject, grade) are non-empty strings.
