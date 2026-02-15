import logging
import re
from pathlib import Path
from typing import Dict, List

import pypdf

logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Exception raised when PDF extraction fails."""
    pass


class PDFExtractor:
    """Extract clean text from PDF files with header/footer removal."""
    
    def __init__(self, output_dir: str = "data/processed/text"):
        """Initialize PDFExtractor.
        
        Args:
            output_dir: Directory to save extracted text files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract clean text from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Clean text content with headers/footers removed
            
        Raises:
            PDFExtractionError: If extraction fails
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise PDFExtractionError(f"PDF file not found: {pdf_path}")
        
        try:
            # First attempt: Use pypdf for basic extraction
            text = self._extract_with_pypdf(pdf_path)
            
            # Clean the text: remove headers, footers, page numbers
            text = self._clean_text(text)
            
            # Save extracted text
            self._save_text(pdf_path, text)
            
            return text
            
        except Exception as e:
            error_msg = f"Failed to extract text from {pdf_path}: {str(e)}"
            logger.error(error_msg)
            raise PDFExtractionError(error_msg) from e
    
    def _extract_with_pypdf(self, pdf_path: Path) -> str:
        """Extract text using pypdf library.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Raw extracted text
        """
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            
            if len(reader.pages) == 0:
                raise PDFExtractionError("PDF has no pages")
            
            # Extract text from all pages
            pages_text = []
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num} from {pdf_path}: {e}")
                    continue
            
            if not pages_text:
                raise PDFExtractionError("No text could be extracted from any page")
            
            # Join pages with double newline to preserve structure
            return "\n\n".join(pages_text)
            
        except pypdf.errors.PdfReadError as e:
            raise PDFExtractionError(f"Corrupted or invalid PDF: {e}") from e
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing headers, footers, and page numbers.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove common page number patterns
        # Pattern: "Page N", "N", "- N -", etc. on their own line
        text = re.sub(r'^\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'^\s*-?\s*\d+\s*-?\s*$', '', text, flags=re.MULTILINE)
        
        # Remove repeated header/footer patterns
        # Find lines that appear multiple times (likely headers/footers)
        lines = text.split('\n')
        line_counts = {}
        for line in lines:
            stripped = line.strip()
            if stripped and len(stripped) > 5:  # Ignore very short lines
                line_counts[stripped] = line_counts.get(stripped, 0) + 1
        
        # Remove lines that appear more than 3 times (likely headers/footers)
        repeated_lines = {line for line, count in line_counts.items() if count > 3}
        cleaned_lines = [
            line for line in lines 
            if line.strip() not in repeated_lines or len(line.strip()) <= 5
        ]
        
        text = '\n'.join(cleaned_lines)
        
        # Remove excessive whitespace while preserving paragraph structure
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Normalize spaces
        
        return text.strip()
    
    def _save_text(self, pdf_path: Path, text: str) -> None:
        """Save extracted text to file.
        
        Args:
            pdf_path: Original PDF path
            text: Extracted text
        """
        # Create output filename based on PDF name
        output_filename = pdf_path.stem + ".txt"
        output_path = self.output_dir / output_filename
        
        # Save with UTF-8 encoding
        output_path.write_text(text, encoding='utf-8')
        logger.info(f"Saved extracted text to {output_path}")
    
    def extract_batch(self, pdf_paths: List[str]) -> Dict[str, str]:
        """Extract text from multiple PDFs.
        
        Args:
            pdf_paths: List of PDF file paths
            
        Returns:
            Dictionary mapping pdf_path -> extracted_text
        """
        results = {}
        
        for pdf_path in pdf_paths:
            try:
                text = self.extract_text(pdf_path)
                results[pdf_path] = text
            except PDFExtractionError as e:
                logger.error(f"Skipping {pdf_path}: {e}")
                results[pdf_path] = None
        
        return results