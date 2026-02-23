"""Property-based tests for text chunking parameters.

Feature: architecture-alignment-refactoring
Property 22: Text Chunking Parameters
Validates: Requirements 8.3
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import List

from src.aws_control_plane.pdf_processor import TextChunker, TextChunk


def count_tokens(text: str) -> int:
    """
    Count tokens in text using simple word-based tokenization.
    This matches the TextChunker's tokenization approach.
    """
    return len(text.split())


def calculate_overlap(chunk1: TextChunk, chunk2: TextChunk) -> int:
    """
    Calculate the number of overlapping tokens between two consecutive chunks.
    """
    # Get the text from both chunks
    text1 = chunk1.text
    text2 = chunk2.text
    
    # Find the longest common substring at the boundary
    # We look for overlap at the end of chunk1 and start of chunk2
    words1 = text1.split()
    words2 = text2.split()
    
    # Find maximum overlap by checking progressively smaller suffixes of chunk1
    # against prefixes of chunk2
    max_overlap = 0
    for overlap_size in range(min(len(words1), len(words2)), 0, -1):
        suffix = words1[-overlap_size:]
        prefix = words2[:overlap_size]
        if suffix == prefix:
            max_overlap = overlap_size
            break
    
    return max_overlap


# Property 22: Text Chunking Parameters - Chunk Size
@settings(max_examples=100, deadline=None)
@given(text=st.text(
    min_size=2000, 
    max_size=20000,
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
))
def test_property_22_chunk_size_approximately_800_tokens(text):
    """
    Property 22a: For any text processed by the chunker, all chunks (except possibly 
    the last) should have approximately 800 tokens.
    
    **Validates: Requirements 8.3**
    
    The Lambda_Function SHALL chunk text with 800 token chunks and 100 token overlap.
    """
    chunker = TextChunker(chunk_size=800, chunk_overlap=100)
    chunks = chunker.chunk_text(text)
    
    # Skip if no chunks generated
    if not chunks:
        return
    
    # Check all chunks except the last one
    for i, chunk in enumerate(chunks[:-1]):
        token_count = count_tokens(chunk.text)
        
        # All chunks except the last should have approximately 800 tokens
        # We allow a tolerance since the chunker uses word boundaries
        # The chunk should be close to 800 tokens (within reasonable bounds)
        assert 700 <= token_count <= 900, \
            f"Chunk {i} has {token_count} tokens, expected approximately 800 (700-900 range)"
    
    # The last chunk may be smaller
    if len(chunks) > 0:
        last_chunk_tokens = count_tokens(chunks[-1].text)
        assert last_chunk_tokens > 0, "Last chunk should not be empty"
        assert last_chunk_tokens <= 900, \
            f"Last chunk has {last_chunk_tokens} tokens, should not exceed 900"


# Property 22: Text Chunking Parameters - Overlap
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
@given(text=st.text(
    min_size=3000,
    max_size=20000,
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
))
def test_property_22_chunk_overlap_approximately_100_tokens(text):
    """
    Property 22b: For any text processed by the chunker, consecutive chunks should 
    have approximately 100 tokens of overlap.
    
    **Validates: Requirements 8.3**
    
    The Lambda_Function SHALL chunk text with 800 token chunks and 100 token overlap.
    """
    chunker = TextChunker(chunk_size=800, chunk_overlap=100)
    chunks = chunker.chunk_text(text)
    
    # Need at least 2 chunks to test overlap
    if len(chunks) < 2:
        return
    
    # Check overlap between consecutive chunks
    for i in range(len(chunks) - 1):
        chunk_n = chunks[i]
        chunk_n1 = chunks[i + 1]
        
        overlap_tokens = calculate_overlap(chunk_n, chunk_n1)
        
        # Consecutive chunks should have approximately 100 tokens of overlap
        # We allow some tolerance for word boundary alignment
        assert 80 <= overlap_tokens <= 120, \
            f"Chunks {i} and {i+1} have {overlap_tokens} tokens overlap, " \
            f"expected approximately 100 (80-120 range)"


# Property 22: Text Chunking Parameters - Determinism
@settings(max_examples=100, deadline=None)
@given(text=st.text(
    min_size=1000,
    max_size=10000,
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
))
def test_property_22_chunking_is_deterministic(text):
    """
    Property 22c: For any text, chunking should be deterministic - the same input 
    should always produce the same chunks.
    
    **Validates: Requirements 8.3**
    
    Ensures consistent and reproducible chunking behavior.
    """
    chunker = TextChunker(chunk_size=800, chunk_overlap=100)
    
    # Chunk the same text twice
    chunks1 = chunker.chunk_text(text)
    chunks2 = chunker.chunk_text(text)
    
    # Should produce the same number of chunks
    assert len(chunks1) == len(chunks2), \
        f"Chunking produced different number of chunks: {len(chunks1)} vs {len(chunks2)}"
    
    # Each corresponding chunk should be identical
    for i, (chunk1, chunk2) in enumerate(zip(chunks1, chunks2)):
        assert chunk1.text == chunk2.text, \
            f"Chunk {i} differs between runs"
        assert chunk1.start_position == chunk2.start_position, \
            f"Chunk {i} start_position differs: {chunk1.start_position} vs {chunk2.start_position}"
        assert chunk1.end_position == chunk2.end_position, \
            f"Chunk {i} end_position differs: {chunk1.end_position} vs {chunk2.end_position}"


# Property 22: Text Chunking Parameters - Completeness
@settings(max_examples=100, deadline=None)
@given(text=st.text(
    min_size=1000,
    max_size=10000,
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
))
def test_property_22_no_text_lost_during_chunking(text):
    """
    Property 22d: For any text, no text should be lost during chunking - all 
    original text should appear in the chunks (accounting for overlap).
    
    **Validates: Requirements 8.3**
    
    Ensures that the chunking process preserves all content.
    """
    chunker = TextChunker(chunk_size=800, chunk_overlap=100)
    chunks = chunker.chunk_text(text)
    
    # Skip if no chunks or empty text
    if not chunks or not text.strip():
        return
    
    # Get all words from original text
    original_words = text.split()
    
    # Skip if no words
    if not original_words:
        return
    
    # Reconstruct text from chunks (removing overlap)
    # The first chunk contains words 0 to chunk_size
    # The second chunk contains words (chunk_size - overlap) to (2*chunk_size - overlap)
    # etc.
    
    # Verify that the first chunk starts with the first words of the original text
    first_chunk_words = chunks[0].text.split()
    assert first_chunk_words == original_words[:len(first_chunk_words)], \
        "First chunk should start with the beginning of the original text"
    
    # Verify that the last chunk ends with the last words of the original text
    last_chunk_words = chunks[-1].text.split()
    assert last_chunk_words == original_words[-len(last_chunk_words):], \
        "Last chunk should end with the end of the original text"
    
    # Verify coverage: collect all unique word positions covered by chunks
    covered_positions = set()
    for chunk in chunks:
        for pos in range(chunk.start_position, chunk.end_position):
            covered_positions.add(pos)
    
    # All word positions should be covered
    expected_positions = set(range(len(original_words)))
    assert covered_positions == expected_positions, \
        f"Not all text positions covered. Missing: {expected_positions - covered_positions}"


# Property 22: Text Chunking Parameters - Configuration Validation
@settings(max_examples=50, deadline=None)
@given(
    chunk_size=st.integers(min_value=1, max_value=2000),
    chunk_overlap=st.integers(min_value=0, max_value=1999)
)
def test_property_22_chunker_validates_configuration(chunk_size, chunk_overlap):
    """
    Property 22e: The chunker should validate its configuration parameters and 
    reject invalid combinations.
    
    **Validates: Requirements 8.3**
    
    Ensures that the chunker enforces valid configuration constraints.
    """
    if chunk_overlap >= chunk_size:
        # Invalid configuration: overlap must be less than chunk size
        with pytest.raises(ValueError, match="chunk_overlap must be < chunk_size"):
            TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    else:
        # Valid configuration: should not raise
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        assert chunker.chunk_size == chunk_size
        assert chunker.chunk_overlap == chunk_overlap
