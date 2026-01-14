"""Property-based tests for metadata management.

Feature: phase2-backend-knowledge-engineering
"""

import pytest
from hypothesis import given, strategies as st, settings

from src.data_processing.text_chunker import TextChunk
from src.data_processing.metadata_manager import MetadataManager, FileMetadata


# Feature: phase2-backend-knowledge-engineering, Property 7: Metadata Field Completeness
@settings(max_examples=100)
@given(
    text=st.text(min_size=1, max_size=1000),
    start_pos=st.integers(min_value=0, max_value=10000),
    chunk_index=st.integers(min_value=0, max_value=100),
    subject=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    grade=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    filename=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P')))
)
def test_property_metadata_field_completeness(text, start_pos, chunk_index, subject, grade, filename):
    """Property 7: For any enriched chunk, all required fields should be present and non-empty.
    
    Required fields: chunk_id, source_file, subject, grade, chunk_text (text), chunk_position (chunk_index)
    
    Validates: Requirements 3.5
    """
    # Create a text chunk
    end_pos = start_pos + len(text)
    chunk = TextChunk(
        text=text,
        start_pos=start_pos,
        end_pos=end_pos,
        chunk_index=chunk_index
    )
    
    # Create file metadata
    file_metadata = FileMetadata(
        subject=subject,
        grade=grade,
        filename=filename
    )
    
    # Enrich the chunk
    metadata_manager = MetadataManager()
    enriched = metadata_manager.enrich_chunk(chunk, file_metadata)
    
    # Verify all required fields are present and non-empty
    assert enriched.chunk_id, "chunk_id should be present and non-empty"
    assert enriched.text, "text should be present and non-empty"
    assert enriched.source_file, "source_file should be present and non-empty"
    assert enriched.subject, "subject should be present and non-empty"
    assert enriched.grade, "grade should be present and non-empty"
    
    # Verify chunk_index is present (can be 0, so check for None)
    assert enriched.chunk_index is not None, "chunk_index should be present"
    
    # Verify positions are present
    assert enriched.char_start is not None, "char_start should be present"
    assert enriched.char_end is not None, "char_end should be present"
    
    # Verify the values match what was provided
    assert enriched.text == text
    assert enriched.source_file == filename
    assert enriched.subject == subject
    assert enriched.grade == grade
    assert enriched.chunk_index == chunk_index
    assert enriched.char_start == start_pos
    assert enriched.char_end == end_pos


# Feature: phase2-backend-knowledge-engineering, Property 8: Chunk ID Uniqueness
@settings(max_examples=100)
@given(
    num_chunks=st.integers(min_value=10, max_value=100)
)
def test_property_chunk_id_uniqueness(num_chunks):
    """Property 8: For any set of enriched chunks, all chunk_id values should be unique.
    
    Validates: Requirements 3.4
    """
    metadata_manager = MetadataManager()
    file_metadata = FileMetadata(
        subject="informatika",
        grade="kelas_10",
        filename="test.pdf"
    )
    
    # Create multiple chunks
    chunks = [
        TextChunk(
            text=f"chunk {i}",
            start_pos=i * 100,
            end_pos=(i + 1) * 100,
            chunk_index=i
        )
        for i in range(num_chunks)
    ]
    
    # Enrich all chunks
    enriched_chunks = [
        metadata_manager.enrich_chunk(chunk, file_metadata)
        for chunk in chunks
    ]
    
    # Extract all chunk IDs
    chunk_ids = [enriched.chunk_id for enriched in enriched_chunks]
    
    # Verify all IDs are unique
    assert len(chunk_ids) == len(set(chunk_ids)), \
        f"Chunk IDs are not unique: {len(chunk_ids)} total, {len(set(chunk_ids))} unique"
    
    # Verify all IDs are non-empty
    assert all(chunk_id for chunk_id in chunk_ids), \
        "All chunk IDs should be non-empty"
