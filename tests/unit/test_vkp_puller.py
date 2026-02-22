"""
Unit Tests for VKP Puller

Tests for VKPPuller class covering:
- S3 listing and version comparison
- Download and verification
- ChromaDB extraction
- Offline mode behavior

Requirements: 7.1-7.7
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from botocore.exceptions import ClientError, NoCredentialsError
import json

from src.vkp.puller import VKPPuller, VKPUpdate
from src.vkp.models import VKP, VKPChunk, ChunkMetadata
from src.vkp.packager import VKPPackager


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    client = Mock()
    return client


@pytest.fixture
def mock_version_manager():
    """Create a mock VKPVersionManager."""
    manager = Mock()
    manager.get_installed_version = Mock(return_value=None)
    manager.register_version = Mock(return_value=True)
    manager.compare_versions = Mock(return_value=-1)
    return manager


@pytest.fixture
def mock_chroma_manager():
    """Create a mock ChromaDBManager."""
    manager = Mock()
    collection = Mock()
    collection.upsert = Mock()
    manager.create_collection = Mock(return_value=collection)
    return manager


@pytest.fixture
def mock_book_repository():
    """Create a mock BookRepository."""
    repo = Mock()
    return repo


@pytest.fixture
def vkp_puller(mock_version_manager, mock_chroma_manager, mock_book_repository):
    """Create a VKPPuller instance with mocked dependencies."""
    puller = VKPPuller(
        bucket_name='test-bucket',
        version_manager=mock_version_manager,
        chroma_manager=mock_chroma_manager,
        book_repository=mock_book_repository,
        region_name='ap-southeast-1',
        max_retries=3,
        retry_delay=0  # No delay for tests
    )
    return puller


@pytest.fixture
def sample_vkp():
    """Create a sample VKP for testing."""
    chunks = [
        VKPChunk(
            chunk_id="chunk_0",
            text="Test text 0",
            embedding=[0.1] * 128,
            metadata=ChunkMetadata(page=1, section="Test", topic="Testing")
        ),
        VKPChunk(
            chunk_id="chunk_1",
            text="Test text 1",
            embedding=[0.2] * 128,
            metadata=ChunkMetadata(page=2, section="Test", topic="Testing")
        )
    ]
    
    packager = VKPPackager()
    vkp = packager.create_package(
        version="1.0.0",
        subject="matematika",
        grade=10,
        semester=1,
        embedding_model="test-model",
        chunk_size=800,
        chunk_overlap=100,
        chunks=chunks,
        source_files=["test.pdf"]
    )
    
    return vkp


class TestVKPPullerInitialization:
    """Test VKPPuller initialization."""
    
    def test_initialization_success(self, mock_version_manager, mock_chroma_manager, mock_book_repository):
        """Test successful initialization."""
        puller = VKPPuller(
            bucket_name='test-bucket',
            version_manager=mock_version_manager,
            chroma_manager=mock_chroma_manager,
            book_repository=mock_book_repository
        )
        
        assert puller.bucket_name == 'test-bucket'
        assert puller.version_manager == mock_version_manager
        assert puller.chroma_manager == mock_chroma_manager
        assert puller.book_repository == mock_book_repository
        assert puller.max_retries == 3
        assert puller.retry_delay == 5


class TestVersionComparison:
    """Test version comparison methods."""
    
    def test_compare_versions_update_available(self, vkp_puller):
        """Test version comparison when update is available."""
        result = vkp_puller.compare_versions("1.0.0", "1.2.0")
        assert result == "update_available"
    
    def test_compare_versions_up_to_date(self, vkp_puller):
        """Test version comparison when versions are equal."""
        result = vkp_puller.compare_versions("1.2.0", "1.2.0")
        assert result == "up_to_date"
    
    def test_compare_versions_local_newer(self, vkp_puller):
        """Test version comparison when local is newer."""
        result = vkp_puller.compare_versions("2.0.0", "1.0.0")
        assert result == "local_newer"
    
    def test_compare_versions_major_dominates(self, vkp_puller):
        """Test that major version dominates minor and patch."""
        result = vkp_puller.compare_versions("1.99.99", "2.0.0")
        assert result == "update_available"
    
    def test_compare_versions_minor_dominates_patch(self, vkp_puller):
        """Test that minor version dominates patch."""
        result = vkp_puller.compare_versions("1.0.99", "1.1.0")
        assert result == "update_available"


class TestCheckUpdates:
    """Test check_updates method."""
    
    @patch('src.vkp.puller.boto3.client')
    def test_check_updates_success(self, mock_boto_client, vkp_puller, mock_version_manager):
        """Test successful update check."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        # Mock head_bucket (for connection test)
        mock_s3.head_bucket = Mock()
        
        # Mock paginator
        mock_paginator = Mock()
        mock_s3.get_paginator = Mock(return_value=mock_paginator)
        
        # Mock S3 list response
        mock_paginator.paginate = Mock(return_value=[
            {
                'Contents': [
                    {
                        'Key': 'matematika/kelas_10/v1.0.0.vkp',
                        'Size': 1024
                    },
                    {
                        'Key': 'matematika/kelas_10/v1.2.0.vkp',
                        'Size': 2048
                    }
                ]
            }
        ])
        
        # Mock version manager
        mock_version_manager.get_installed_version = Mock(return_value="1.0.0")
        
        # Check updates
        updates = vkp_puller.check_updates()
        
        # Verify results - should return all VKPs found
        # Note: check_updates returns all VKPs, not just newer ones
        # The filtering happens via is_update_available() method
        assert len(updates) >= 1  # At least the newer version
        
        # Find the updates
        v1_0_0 = next((u for u in updates if u.cloud_version == '1.0.0'), None)
        v1_2_0 = next((u for u in updates if u.cloud_version == '1.2.0'), None)
        
        # Verify v1.2.0 exists and is marked as update available
        assert v1_2_0 is not None
        assert v1_2_0.subject == 'matematika'
        assert v1_2_0.grade == 10
        assert v1_2_0.is_update_available()  # Newer version
    
    @patch('src.vkp.puller.boto3.client')
    def test_check_updates_no_credentials(self, mock_boto_client, vkp_puller):
        """Test update check with no AWS credentials."""
        mock_boto_client.side_effect = NoCredentialsError()
        
        with pytest.raises(RuntimeError, match="AWS credentials not configured"):
            vkp_puller.check_updates()
    
    @patch('src.vkp.puller.boto3.client')
    def test_check_updates_bucket_not_found(self, mock_boto_client, vkp_puller):
        """Test update check with non-existent bucket."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        # Mock bucket not found error
        error_response = {'Error': {'Code': '404'}}
        mock_s3.head_bucket = Mock(side_effect=ClientError(error_response, 'HeadBucket'))
        
        with pytest.raises(RuntimeError, match="S3 bucket not found"):
            vkp_puller.check_updates()


class TestDownloadVKP:
    """Test download_vkp method."""
    
    @patch('src.vkp.puller.boto3.client')
    def test_download_vkp_success(self, mock_boto_client, vkp_puller, sample_vkp):
        """Test successful VKP download."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket = Mock()
        
        # Serialize VKP
        packager = VKPPackager()
        vkp_data = packager.serialize(sample_vkp)
        
        # Mock S3 get_object response
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read = Mock(return_value=vkp_data)
        mock_s3.get_object = Mock(return_value=mock_response)
        
        # Download VKP
        vkp = vkp_puller.download_vkp('matematika/kelas_10/v1.0.0.vkp')
        
        # Verify
        assert vkp.subject == sample_vkp.subject
        assert vkp.version == sample_vkp.version
        assert len(vkp.chunks) == len(sample_vkp.chunks)
    
    @patch('src.vkp.puller.boto3.client')
    def test_download_vkp_not_found(self, mock_boto_client, vkp_puller):
        """Test download with non-existent VKP."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket = Mock()
        
        # Mock not found error
        error_response = {'Error': {'Code': 'NoSuchKey'}}
        mock_s3.get_object = Mock(side_effect=ClientError(error_response, 'GetObject'))
        
        with pytest.raises(RuntimeError, match="VKP not found in S3"):
            vkp_puller.download_vkp('matematika/kelas_10/v1.0.0.vkp')
    
    @patch('src.vkp.puller.boto3.client')
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_download_vkp_retry_success(self, mock_sleep, mock_boto_client, vkp_puller, sample_vkp):
        """Test download with retry on transient error."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket = Mock()
        
        # Serialize VKP
        packager = VKPPackager()
        vkp_data = packager.serialize(sample_vkp)
        
        # Mock S3 get_object - fail twice, then succeed
        error_response = {'Error': {'Code': '500'}}
        mock_response = {'Body': Mock()}
        mock_response['Body'].read = Mock(return_value=vkp_data)
        
        mock_s3.get_object = Mock(side_effect=[
            ClientError(error_response, 'GetObject'),
            ClientError(error_response, 'GetObject'),
            mock_response
        ])
        
        # Download VKP (should succeed on 3rd attempt)
        vkp = vkp_puller.download_vkp('matematika/kelas_10/v1.0.0.vkp')
        
        # Verify
        assert vkp.subject == sample_vkp.subject
        assert mock_s3.get_object.call_count == 3


class TestVerifyIntegrity:
    """Test verify_integrity method."""
    
    def test_verify_integrity_valid(self, vkp_puller, sample_vkp):
        """Test integrity verification with valid VKP."""
        is_valid = vkp_puller.verify_integrity(sample_vkp)
        assert is_valid
    
    def test_verify_integrity_invalid(self, vkp_puller, sample_vkp):
        """Test integrity verification with corrupted VKP."""
        # Corrupt VKP
        sample_vkp.chunks[0].text = "CORRUPTED"
        # Don't recalculate checksum
        
        is_valid = vkp_puller.verify_integrity(sample_vkp)
        assert not is_valid


class TestExtractToChromaDB:
    """Test extract_to_chromadb method."""
    
    def test_extract_to_chromadb_success(self, vkp_puller, sample_vkp, mock_chroma_manager):
        """Test successful extraction to ChromaDB."""
        # Extract
        success = vkp_puller.extract_to_chromadb(sample_vkp)
        
        # Verify
        assert success
        mock_chroma_manager.create_collection.assert_called_once()
        
        # Verify upsert was called with correct data
        collection = mock_chroma_manager.create_collection.return_value
        collection.upsert.assert_called_once()
        
        call_args = collection.upsert.call_args
        assert len(call_args.kwargs['ids']) == 2
        assert len(call_args.kwargs['documents']) == 2
        assert len(call_args.kwargs['embeddings']) == 2
        assert len(call_args.kwargs['metadatas']) == 2
    
    def test_extract_to_chromadb_custom_collection(self, vkp_puller, sample_vkp, mock_chroma_manager):
        """Test extraction with custom collection name."""
        success = vkp_puller.extract_to_chromadb(sample_vkp, collection_name="custom_collection")
        
        assert success
        mock_chroma_manager.create_collection.assert_called_once_with(name="custom_collection")
    
    def test_extract_to_chromadb_failure(self, vkp_puller, sample_vkp, mock_chroma_manager):
        """Test extraction failure."""
        # Mock ChromaDB error
        mock_chroma_manager.create_collection = Mock(side_effect=Exception("ChromaDB error"))
        
        with pytest.raises(RuntimeError, match="ChromaDB extraction failed"):
            vkp_puller.extract_to_chromadb(sample_vkp)


class TestUpdateMetadata:
    """Test update_metadata method."""
    
    def test_update_metadata_success(self, vkp_puller, sample_vkp, mock_version_manager):
        """Test successful metadata update."""
        success = vkp_puller.update_metadata(sample_vkp)
        
        assert success
        mock_version_manager.register_version.assert_called_once_with(
            subject=sample_vkp.subject,
            grade=sample_vkp.grade,
            semester=sample_vkp.semester,
            version=sample_vkp.version,
            chunk_count=sample_vkp.total_chunks,
            checksum=sample_vkp.checksum
        )
    
    def test_update_metadata_failure(self, vkp_puller, sample_vkp, mock_version_manager):
        """Test metadata update failure."""
        # Mock database error
        mock_version_manager.register_version = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(RuntimeError, match="Metadata update failed"):
            vkp_puller.update_metadata(sample_vkp)


class TestOfflineMode:
    """Test offline mode behavior."""
    
    @patch('socket.create_connection')
    def test_check_internet_connectivity_online(self, mock_socket, vkp_puller):
        """Test internet connectivity check when online."""
        mock_socket.return_value = Mock()
        
        # Note: check_internet_connectivity tries to connect to S3
        # We need to mock the S3 client
        with patch('src.vkp.puller.boto3.client') as mock_boto:
            mock_s3 = Mock()
            mock_boto.return_value = mock_s3
            mock_s3.head_bucket = Mock()
            
            is_online = vkp_puller.check_internet_connectivity()
            assert is_online
    
    @patch('socket.create_connection')
    def test_check_internet_connectivity_offline(self, mock_socket, vkp_puller):
        """Test internet connectivity check when offline."""
        mock_socket.side_effect = OSError("Network unreachable")
        
        with patch('src.vkp.puller.boto3.client') as mock_boto:
            mock_boto.side_effect = Exception("No connection")
            
            is_online = vkp_puller.check_internet_connectivity()
            assert not is_online
    
    def test_pull_all_updates_offline_mode(self, vkp_puller):
        """Test pull_all_updates in offline mode."""
        # Mock offline
        vkp_puller.check_internet_connectivity = Mock(return_value=False)
        
        stats = vkp_puller.pull_all_updates()
        
        # Verify offline mode was detected
        assert stats['skipped_updates'] == -1
        assert stats['successful_updates'] == 0
        assert stats['failed_updates'] == 0


class TestPullUpdate:
    """Test pull_update method."""
    
    @patch('src.vkp.puller.boto3.client')
    def test_pull_update_full_download(self, mock_boto_client, vkp_puller, sample_vkp, 
                                       mock_version_manager, mock_chroma_manager):
        """Test pull_update with full download."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket = Mock()
        
        # Serialize VKP
        packager = VKPPackager()
        vkp_data = packager.serialize(sample_vkp)
        
        # Mock S3 get_object response
        mock_response = {'Body': Mock()}
        mock_response['Body'].read = Mock(return_value=vkp_data)
        mock_s3.get_object = Mock(return_value=mock_response)
        
        # Create update
        update = VKPUpdate(
            subject="matematika",
            grade=10,
            semester=1,
            cloud_version="1.0.0",
            local_version=None,
            s3_key="matematika/kelas_10/v1.0.0.vkp",
            size_bytes=1024
        )
        
        # Pull update
        success = vkp_puller.pull_update(update, use_delta=False)
        
        # Verify
        assert success
        mock_chroma_manager.create_collection.assert_called_once()
        mock_version_manager.register_version.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
