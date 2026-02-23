"""
PDF Processing Components for Lambda Curriculum Processor

This module provides the core components for processing PDF curriculum files:
- PDFTextExtractor: Extracts text from PDF files using pypdf
- TextChunker: Splits text into chunks with configurable size and overlap
- BedrockEmbeddingGenerator: Generates embeddings using AWS Bedrock Titan

Requirements: 8.1-8.7
"""

import logging
import re
from typing import List, Dict, Tuple, Optional
from io import BytesIO
from dataclasses import dataclass

try:
    from pypdf import PdfReader
except ImportError:
    # Fallback for different pypdf versions
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

logger = logging.getLogger(__name__)


@dataclass
class PageText:
    """Represents text extracted from a single PDF page"""
    page_number: int
    text: str
    
    def __post_init__(self):
        if self.page_number < 1:
            raise ValueError("Page number must be >= 1")


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    chunk_id: str
    text: str
    page_number: int
    start_position: int = 0
    end_position: int = 0
    
    def __post_init__(self):
        if not self.text.strip():
            raise ValueError("Chunk text cannot be empty")
        if self.page_number < 1:
            raise ValueError("Page number must be >= 1")


class PDFTextExtractor:
    """
    Extracts text from PDF files using pypdf library.
    
    Requirements: 8.2
    """
    
    def __init__(self):
        if PdfReader is None:
            raise ImportError("pypdf or PyPDF2 library is required. Install with: pip install pypdf")
        self.logger = logging.getLogger(f"{__name__}.PDFTextExtractor")
    
    def extract_from_bytes(self, pdf_content: bytes) -> Tuple[str, List[PageText]]:
        """
        Extract text from PDF content bytes.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Tuple of (full_text, list of PageText objects)
            
        Raises:
            ValueError: If PDF content is invalid
            RuntimeError: If text extraction fails
        """
        if not pdf_content:
            raise ValueError("PDF content cannot be empty")
        
        try:
            pdf_file = BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            if len(reader.pages) == 0:
                raise ValueError("PDF has no pages")
            
            full_text = ""
            page_texts = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    # Always add page, even if empty (for completeness)
                    page_texts.append(PageText(
                        page_number=page_num,
                        text=page_text if page_text else ""
                    ))
                    if page_text:
                        full_text += page_text + "\n\n"
                    else:
                        self.logger.warning(f"Page {page_num} has no extractable text")
                except Exception as e:
                    self.logger.error(f"Failed to extract text from page {page_num}: {e}")
                    # Add empty page to maintain page count
                    page_texts.append(PageText(
                        page_number=page_num,
                        text=""
                    ))
            
            # Allow empty text for blank PDFs (structure is still valid)
            # This is important for testing and handling scanned PDFs without OCR
            
            self.logger.info(f"Extracted {len(full_text)} characters from {len(page_texts)} pages")
            return full_text, page_texts
            
        except Exception as e:
            self.logger.error(f"Failed to extract text from PDF: {e}")
            raise RuntimeError(f"PDF text extraction failed: {e}")
    
    def extract_from_file(self, file_path: str) -> Tuple[str, List[PageText]]:
        """
        Extract text from PDF file path.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (full_text, list of PageText objects)
        """
        try:
            with open(file_path, 'rb') as f:
                pdf_content = f.read()
            return self.extract_from_bytes(pdf_content)
        except FileNotFoundError:
            raise ValueError(f"PDF file not found: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to read PDF file: {e}")


class TextChunker:
    """
    Splits text into chunks with configurable size and overlap.
    
    Default configuration: 800 token chunks with 100 token overlap.
    
    Requirements: 8.3
    """
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        """
        Initialize TextChunker.
        
        Args:
            chunk_size: Number of tokens per chunk (default: 800)
            chunk_overlap: Number of tokens to overlap between chunks (default: 100)
            
        Raises:
            ValueError: If chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.logger = logging.getLogger(f"{__name__}.TextChunker")
    
    def chunk_text(self, text: str, page_number: int = 1) -> List[TextChunk]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Text to chunk
            page_number: Page number for metadata (default: 1)
            
        Returns:
            List of TextChunk objects
        """
        if not text.strip():
            return []
        
        # Simple word-based tokenization (approximation)
        words = text.split()
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if chunk_text.strip():
                chunks.append(TextChunk(
                    chunk_id=f"chunk_{chunk_id:04d}",
                    text=chunk_text,
                    page_number=page_number,
                    start_position=i,
                    end_position=i + len(chunk_words)
                ))
                chunk_id += 1
        
        self.logger.info(f"Created {len(chunks)} chunks from {len(words)} words")
        return chunks
    
    def chunk_pages(self, page_texts: List[PageText]) -> List[TextChunk]:
        """
        Split multiple pages into chunks, preserving page metadata.
        
        Args:
            page_texts: List of PageText objects
            
        Returns:
            List of TextChunk objects
        """
        all_chunks = []
        chunk_id = 0
        
        for page_text in page_texts:
            words = page_text.text.split()
            
            for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
                chunk_words = words[i:i + self.chunk_size]
                chunk_text = ' '.join(chunk_words)
                
                if chunk_text.strip():
                    all_chunks.append(TextChunk(
                        chunk_id=f"chunk_{chunk_id:04d}",
                        text=chunk_text,
                        page_number=page_text.page_number,
                        start_position=i,
                        end_position=i + len(chunk_words)
                    ))
                    chunk_id += 1
        
        self.logger.info(f"Created {len(all_chunks)} chunks from {len(page_texts)} pages")
        return all_chunks


class BedrockEmbeddingGenerator:
    """
    Generates embeddings using AWS Bedrock Titan model.
    
    Requirements: 8.4
    """
    
    def __init__(self, model_id: str = "amazon.titan-embed-text-v1", region: str = "us-east-1"):
        """
        Initialize Bedrock embedding generator.
        
        Args:
            model_id: Bedrock model ID (default: amazon.titan-embed-text-v1)
            region: AWS region (default: us-east-1)
        """
        try:
            import boto3
            self.bedrock_client = boto3.client('bedrock-runtime', region_name=region)
        except ImportError:
            raise ImportError("boto3 library is required. Install with: pip install boto3")
        
        self.model_id = model_id
        self.region = region
        self.logger = logging.getLogger(f"{__name__}.BedrockEmbeddingGenerator")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            ValueError: If text is empty
            RuntimeError: If embedding generation fails
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            import json
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({"inputText": text})
            )
            
            result = json.loads(response['body'].read())
            embedding = result.get('embedding', [])
            
            if not embedding:
                raise RuntimeError("No embedding returned from Bedrock")
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            RuntimeError: If any embedding generation fails
        """
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Generated {i + 1}/{len(texts)} embeddings")
                    
            except Exception as e:
                self.logger.error(f"Failed to generate embedding for text {i}: {e}")
                raise RuntimeError(f"Batch embedding generation failed at index {i}: {e}")
        
        self.logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def generate_embeddings_for_chunks(self, chunks: List[TextChunk]) -> List[List[float]]:
        """
        Generate embeddings for text chunks.
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            List of embedding vectors
        """
        texts = [chunk.text for chunk in chunks]
        return self.generate_embeddings_batch(texts)


def extract_metadata_from_filename(filename: str) -> Dict[str, any]:
    """
    Extract metadata from PDF filename.
    
    Expected format: {Subject}_Kelas_{Grade}_Semester_{Semester}_v{Version}.pdf
    Example: Matematika_Kelas_10_Semester_1_v1.0.0.pdf
    
    Args:
        filename: PDF filename
        
    Returns:
        Dict with subject, grade, semester, version
    """
    try:
        # Remove .pdf extension
        name = filename.replace('.pdf', '').replace('.PDF', '')
        
        # Try to extract using regex pattern
        pattern = r'([A-Za-z]+)_Kelas_(\d+)_Semester_(\d+)_v(\d+\.\d+\.\d+)'
        match = re.match(pattern, name)
        
        if match:
            subject = match.group(1).lower()
            grade = int(match.group(2))
            semester = int(match.group(3))
            version = match.group(4)
            
            return {
                'subject': subject,
                'grade': grade,
                'semester': semester,
                'version': version
            }
        else:
            # Fallback to defaults if pattern doesn't match
            logger.warning(f"Could not parse filename: {filename}, using defaults")
            return {
                'subject': 'unknown',
                'grade': 10,
                'semester': 1,
                'version': '1.0.0'
            }
    except Exception as e:
        logger.error(f"Error extracting metadata from filename: {e}")
        return {
            'subject': 'unknown',
            'grade': 10,
            'semester': 1,
            'version': '1.0.0'
        }
