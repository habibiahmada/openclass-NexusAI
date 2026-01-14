"""Unit tests for PDF extraction edge cases.

Requirements: 1.3, 1.4
"""

import tempfile
from pathlib import Path

import pypdf
import pytest

from src.data_processing.pdf_extractor import PDFExtractor, PDFExtractionError


class TestPDFExtractorEdgeCases:
    """Test edge cases for PDF extraction."""
    
    def test_empty_pdf(self):
        """Test extraction from a PDF with no pages.
        
        Requirements: 1.3, 1.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "empty.pdf"
            
            # Create an empty PDF (no pages)
            writer = pypdf.PdfWriter()
            with open(pdf_path, 'wb') as f:
                writer.write(f)
            
            extractor = PDFExtractor(output_dir=tmpdir)
            
            # Should raise PDFExtractionError for empty PDF
            with pytest.raises(PDFExtractionError, match="PDF has no pages"):
                extractor.extract_text(str(pdf_path))
    
    def test_blank_pages_pdf(self):
        """Test extraction from a PDF with blank pages (no text).
        
        Requirements: 1.3, 1.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "blank.pdf"
            
            # Create a PDF with blank pages
            writer = pypdf.PdfWriter()
            for _ in range(3):
                page = pypdf.PageObject.create_blank_page(width=612, height=792)
                writer.add_page(page)
            
            with open(pdf_path, 'wb') as f:
                writer.write(f)
            
            extractor = PDFExtractor(output_dir=tmpdir)
            
            # Should raise PDFExtractionError when no text can be extracted
            with pytest.raises(PDFExtractionError, match="No text could be extracted"):
                extractor.extract_text(str(pdf_path))
    
    def test_corrupted_pdf(self):
        """Test extraction from a corrupted PDF file.
        
        Requirements: 1.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "corrupted.pdf"
            
            # Create a corrupted PDF (invalid content)
            pdf_path.write_bytes(b"This is not a valid PDF file")
            
            extractor = PDFExtractor(output_dir=tmpdir)
            
            # Should raise PDFExtractionError for corrupted PDF
            with pytest.raises(PDFExtractionError):
                extractor.extract_text(str(pdf_path))
    
    def test_nonexistent_pdf(self):
        """Test extraction from a non-existent PDF file.
        
        Requirements: 1.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "nonexistent.pdf"
            
            extractor = PDFExtractor(output_dir=tmpdir)
            
            # Should raise PDFExtractionError for missing file
            with pytest.raises(PDFExtractionError, match="PDF file not found"):
                extractor.extract_text(str(pdf_path))
    
    def test_extract_batch_with_failures(self):
        """Test batch extraction continues after individual failures.
        
        Requirements: 1.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create one valid PDF and one corrupted
            valid_pdf = Path(tmpdir) / "valid.pdf"
            corrupted_pdf = Path(tmpdir) / "corrupted.pdf"
            
            # Valid PDF with blank page
            writer = pypdf.PdfWriter()
            page = pypdf.PageObject.create_blank_page(width=612, height=792)
            writer.add_page(page)
            with open(valid_pdf, 'wb') as f:
                writer.write(f)
            
            # Corrupted PDF
            corrupted_pdf.write_bytes(b"Not a PDF")
            
            extractor = PDFExtractor(output_dir=tmpdir)
            results = extractor.extract_batch([str(valid_pdf), str(corrupted_pdf)])
            
            # Should have results for both (one success, one failure)
            assert len(results) == 2
            assert str(corrupted_pdf) in results
            assert results[str(corrupted_pdf)] is None  # Failed extraction
    
    def test_save_text_creates_output_file(self):
        """Test that extracted text is saved to the output directory.
        
        Requirements: 1.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            output_dir = Path(tmpdir) / "output"
            
            # Create a simple PDF (we'll use the internal method directly)
            extractor = PDFExtractor(output_dir=str(output_dir))
            
            # Test the save method
            test_text = "This is test content"
            extractor._save_text(pdf_path, test_text)
            
            # Verify output file exists
            output_file = output_dir / "test.txt"
            assert output_file.exists()
            
            # Verify content is correct and UTF-8 encoded
            saved_text = output_file.read_text(encoding='utf-8')
            assert saved_text == test_text
    
    def test_clean_text_removes_page_numbers(self):
        """Test that page numbers are removed from text.
        
        Requirements: 1.2
        """
        extractor = PDFExtractor()
        
        text_with_page_numbers = """
        This is content on page 1.
        Page 1
        More content here.
        - 2 -
        Even more content.
        Page 3
        Final content.
        """
        
        cleaned = extractor._clean_text(text_with_page_numbers)
        
        # Page number patterns should be removed
        assert "Page 1" not in cleaned
        assert "Page 3" not in cleaned
        # Content should remain
        assert "This is content" in cleaned
        assert "More content" in cleaned
