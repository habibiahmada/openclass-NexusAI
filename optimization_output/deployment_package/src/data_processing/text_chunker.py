from dataclasses import dataclass
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class TextChunk:
    """Represents a chunk of text with position metadata."""
    text: str
    start_pos: int
    end_pos: int
    chunk_index: int


class TextChunker:
    """Splits text into overlapping chunks for embedding generation."""
    
    def __init__(self, chunk_size: int = 800, overlap: int = 100):
        """Initialize chunker with size parameters.
        
        Args:
            chunk_size: Target chunk size in characters (500-1000)
            overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
    
    def chunk_text(self, text: str) -> List[TextChunk]:
        """Split text into overlapping chunks.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of TextChunk objects with text and position metadata
        """
        if not text:
            return []
        
        # Split text into chunks
        chunks = self.splitter.split_text(text)
        
        # Create TextChunk objects with position metadata
        result = []
        current_pos = 0
        
        for idx, chunk in enumerate(chunks):
            # Find the actual position of this chunk in the original text
            # For the first chunk, start at 0
            if idx == 0:
                start_pos = 0
            else:
                # For subsequent chunks, account for overlap
                # Search for the chunk text starting from expected position
                # Ensure search position is non-negative
                search_start = max(0, current_pos - self.overlap)
                start_pos = text.find(chunk, search_start)
                if start_pos == -1:
                    # Fallback: if exact match not found, use current position
                    # This can happen with complex Unicode or when chunks don't overlap exactly
                    start_pos = current_pos
            
            end_pos = start_pos + len(chunk)
            
            result.append(TextChunk(
                text=chunk,
                start_pos=start_pos,
                end_pos=end_pos,
                chunk_index=idx
            ))
            
            # Update current position for next iteration
            current_pos = end_pos
        
        return result