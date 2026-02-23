"""
Property-based test for PDF Text Extraction Completeness

Property 21: PDF Text Extraction Completeness
Validates: Requirements 8.2

This test verifies that the PDFTextExtractor class correctly extracts
all text content from PDF files without loss.
"""

import tempfile
from pathlib import Path
from io import BytesIO

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck

try:
    from pypdf import PdfWriter, PageObject
    PYPDF_AVAILABLE = True
except ImportError:
    try:
        from PyPDF2 import PdfWriter, PageObject
        PYPDF_AVAILABLE = True
    except ImportError:
        PYPDF_AVAILABLE = False

from src.aws_control_plane.pdf_processor import PDFTextExtractor, PageText


# Skip tests if pypdf is not available
pytestmark = pytest.mark.skipif(not PYPDF_AVAILABLE, reason="pypdf library not available")


def create_test_pdf_bytes(num_pages: int) -> bytes:
    """
    Create a simple PDF with specified number of pages.
    
    Note: pypdf doesn't easily support adding text to pages programmatically,
    so we create blank pages for structure testing.
    """
    writer = PdfWriter()
    
    for i in range(num_pages):
        # Create blank page
        page = PageObject.create_blank_page(width=612, height=792)
        writer.add_page(page)
    
    # Write to bytes
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(
    num_pages=st.integers(min_value=1, max_value=20)
)
def test_property_21_pdf_text_extraction_completeness(num_pages):
    """
    **Property 21: PDF Text Extraction Completeness**
    
    **Validates: Requirements 8.2**
    
    For any valid PDF with N pages, the PDFTextExtractor SHALL:
    1. Extract text from all N pages without error
    2. Return a PageText object for each page
    3. Preserve page number ordering (1 to N)
    4. Not lose any pages during extraction
    5. Handle empty pages gracefully
    
    This property ensures that the extraction process is complete and
    doesn't skip or lose pages during processing.
    """
    # Create test PDF
    pdf_bytes = create_test_pdf_bytes(num_pages)
    
    # Verify PDF was created
    assume(len(pdf_bytes) > 0)
    
    # Initialize extractor
    extractor = PDFTextExtractor()
    
    # Extract text
    try:
        full_text, page_texts = extractor.extract_from_bytes(pdf_bytes)
        
        # Property 1: Should return results without error
        assert full_text is not None
        assert page_texts is not None
        
        # Property 2: Should have PageText for each page
        assert len(page_texts) == num_pages, \
            f"Expected {num_pages} pages, got {len(page_texts)}"
        
        # Property 3: Page numbers should be ordered 1 to N
        page_numbers = [pt.page_number for pt in page_texts]
        expected_numbers = list(range(1, num_pages + 1))
        assert page_numbers == expected_numbers, \
            f"Page numbers not in order: {page_numbers} != {expected_numbers}"
        
        # Property 4: All PageText objects should be valid
        for i, page_text in enumerate(page_texts, start=1):
            assert isinstance(page_text, PageText)
            assert page_text.page_number == i
            assert isinstance(page_text.text, str)
            # Text can be empty for blank pages, but should be a string
        
        # Property 5: Full text should be concatenation of non-empty pages
        # (with newlines between pages)
        non_empty_texts = [pt.text for pt in page_texts if pt.text.strip()]
        if non_empty_texts:
            reconstructed = "\n\n".join(non_empty_texts)
            # Allow for trailing newlines
            assert full_text.strip() == reconstructed.strip()
        else:
            # All pages are blank - full_text should be empty
            assert full_text.strip() == ""
        
    except Exception as e:
        # Extraction should not fail for valid PDFs
        pytest.fail(f"PDF extraction failed unexpectedly: {e}")


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(
    num_pages=st.integers(min_value=1, max_value=10)
)
def test_property_21_page_ordering_preserved(num_pages):
    """
    **Property 21 (Variant): Page Ordering Preservation**
    
    **Validates: Requirements 8.2**
    
    The PDFTextExtractor SHALL preserve the original page ordering
    from the PDF file. Pages should be extracted in sequence from
    first to last.
    """
    pdf_bytes = create_test_pdf_bytes(num_pages)
    assume(len(pdf_bytes) > 0)
    
    extractor = PDFTextExtractor()
    
    try:
        _, page_texts = extractor.extract_from_bytes(pdf_bytes)
        
        # Verify strict ordering
        for i in range(len(page_texts) - 1):
            current_page = page_texts[i].page_number
            next_page = page_texts[i + 1].page_number
            
            assert next_page == current_page + 1, \
                f"Page ordering broken: page {current_page} followed by {next_page}"
        
        # Verify no duplicate pages
        page_numbers = [pt.page_number for pt in page_texts]
        assert len(page_numbers) == len(set(page_numbers)), \
            f"Duplicate page numbers found: {page_numbers}"
        
    except Exception as e:
        pytest.fail(f"Page ordering test failed: {e}")


def test_property_21_empty_pdf_handling():
    """
    **Property 21 (Edge Case): Empty PDF Handling**
    
    **Validates: Requirements 8.2**
    
    The PDFTextExtractor SHALL handle edge cases gracefully:
    - Empty PDF content should raise ValueError
    - Invalid PDF bytes should raise RuntimeError
    """
    extractor = PDFTextExtractor()
    
    # Test 1: Empty bytes should raise ValueError
    with pytest.raises(ValueError, match="PDF content cannot be empty"):
        extractor.extract_from_bytes(b"")
    
    # Test 2: Invalid PDF bytes should raise RuntimeError
    with pytest.raises(RuntimeError, match="PDF text extraction failed"):
        extractor.extract_from_bytes(b"not a valid pdf")
    
    # Test 3: None should raise appropriate error
    with pytest.raises((ValueError, TypeError)):
        extractor.extract_from_bytes(None)


@settings(max_examples=50, deadline=None)
@given(
    num_pages=st.integers(min_value=1, max_value=10)
)
def test_property_21_no_data_loss(num_pages):
    """
    **Property 21 (Invariant): No Data Loss**
    
    **Validates: Requirements 8.2**
    
    The PDFTextExtractor SHALL not lose any pages during extraction.
    The number of PageText objects returned SHALL equal the number
    of pages in the input PDF.
    """
    pdf_bytes = create_test_pdf_bytes(num_pages)
    assume(len(pdf_bytes) > 0)
    
    extractor = PDFTextExtractor()
    
    try:
        _, page_texts = extractor.extract_from_bytes(pdf_bytes)
        
        # Invariant: No pages lost
        assert len(page_texts) == num_pages, \
            f"Data loss detected: expected {num_pages} pages, got {len(page_texts)}"
        
        # Invariant: All page numbers present
        page_numbers = {pt.page_number for pt in page_texts}
        expected_numbers = set(range(1, num_pages + 1))
        
        assert page_numbers == expected_numbers, \
            f"Missing pages: expected {expected_numbers}, got {page_numbers}"
        
    except Exception as e:
        pytest.fail(f"Data loss test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
