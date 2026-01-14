# Test Fixtures

This directory contains test fixtures for the Phase 2 ETL pipeline tests.

## Structure

- `sample_pdfs/` - Sample PDF files for testing extraction and chunking
- `expected_outputs/` - Expected outputs for regression testing
- `mock_data/` - Mock data for testing without external dependencies

## Usage

Test fixtures should be small and focused on specific test scenarios:
- Normal educational PDF (1-2 pages)
- PDF with images/diagrams
- PDF with complex formatting
- Empty or corrupted PDFs for error handling tests
