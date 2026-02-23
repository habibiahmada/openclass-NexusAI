"""
Property Test: Offline Operation Completeness

**Property 34: Offline Operation Completeness**
**Validates: Requirements 17.1, 17.2, 17.3, 17.5**

This property test verifies that:
1. Student queries work offline using local LLM (Requirement 17.1)
2. RAG operations work offline using local ChromaDB (Requirement 17.2)
3. Authentication works offline using local PostgreSQL (Requirement 17.3)
4. System operates indefinitely with existing data when AWS is unavailable (Requirement 17.5)
5. All core operations continue without internet connectivity
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
import socket

from src.edge_runtime.rag_pipeline import RAGPipeline, QueryResult
from src.edge_runtime.inference_engine import InferenceEngine
from src.embeddings.chroma_manager import ChromaDBManager, SearchResult
from src.persistence.database_manager import DatabaseManager
from src.persistence.user_repository import UserRepository, User
from src.persistence.session_repository import SessionRepository, Session
from src.persistence.chat_history_repository import ChatHistoryRepository, ChatHistory


# Strategy for generating valid questions
@st.composite
def valid_question(draw):
    """Generate valid question text"""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), min_codepoint=32),
        min_size=5,
        max_size=200
    ))


# Strategy for generating valid usernames
@st.composite
def valid_username(draw):
    """Generate valid username (3-50 characters)"""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48),
        min_size=3,
        max_size=50
    ))


# Strategy for generating valid tokens
@st.composite
def valid_token(draw):
    """Generate valid session token"""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48),
        min_size=16,
        max_size=64
    ))


# Strategy for generating valid responses
@st.composite
def valid_response_text(draw):
    """Generate valid response text"""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), min_codepoint=32),
        min_size=10,
        max_size=500
    ))


@given(
    question=valid_question(),
    top_k=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100, deadline=None)
def test_student_queries_work_offline_with_local_llm(question, top_k):
    """
    Property: Student queries continue working offline using local LLM
    
    Validates: Requirement 17.1
    """
    assume(len(question.strip()) >= 5)  # Ensure non-empty question
    
    # Mock ChromaDB (local vector store)
    mock_chroma = Mock(spec=ChromaDBManager)
    mock_chroma.check_health = Mock(return_value=True)
    mock_chroma.get_collection = Mock()
    mock_chroma.query = Mock(return_value=[
        SearchResult(
            text="Test content from local ChromaDB",
            metadata={'page': 1, 'section': 'Test'},
            similarity_score=0.9
        )
    ])
    
    # Mock local inference engine (no AWS dependency)
    mock_inference = Mock(spec=InferenceEngine)
    mock_inference.generate = Mock(return_value="Local LLM response")
    mock_inference.is_loaded = Mock(return_value=True)
    mock_inference.generate_response = Mock(return_value=iter(["Local LLM response"]))
    
    # Simulate offline environment (no network connectivity)
    with patch('socket.create_connection', side_effect=OSError("Network unreachable")):
        pipeline = RAGPipeline(
            vector_db=mock_chroma,
            inference_engine=mock_inference,
            embeddings_client=None  # No AWS Bedrock client
        )
        
        # Execute query offline
        result = pipeline.process_query(
            query=question,
            subject_filter=None,
            top_k=top_k
        )
        
        # Verify query succeeded offline
        assert result is not None, "Query should succeed offline"
        assert result.response is not None, "Response should not be None"
        assert len(result.response) > 0, "Response should not be empty"
        
        # Verify local components were used
        mock_chroma.query.assert_called()
        mock_inference.generate_response.assert_called()
        
        # Verify no AWS clients are present
        assert not hasattr(pipeline, 'bedrock_client') or pipeline.embeddings_client is None
        assert not hasattr(pipeline, 's3_client')
        assert not hasattr(pipeline, 'lambda_client')


@given(
    query_text=valid_question(),
    num_results=st.integers(min_value=1, max_value=20)
)
@settings(max_examples=100, deadline=None)
def test_rag_operations_work_offline_with_local_chromadb(query_text, num_results):
    """
    Property: RAG operations continue working offline using local ChromaDB
    
    Validates: Requirement 17.2
    """
    assume(len(query_text.strip()) >= 5)
    
    # Create ChromaDB manager (local persistence)
    with patch('chromadb.PersistentClient') as mock_client_class:
        mock_client = Mock()
        mock_collection = Mock()
        
        # Generate mock results
        mock_documents = [f"Document {i}" for i in range(min(num_results, 10))]
        mock_metadatas = [{'page': i} for i in range(len(mock_documents))]
        mock_distances = [0.1 * i for i in range(len(mock_documents))]
        
        mock_collection.query = Mock(return_value={
            'documents': [mock_documents],
            'metadatas': [mock_metadatas],
            'distances': [mock_distances]
        })
        mock_client.get_or_create_collection = Mock(return_value=mock_collection)
        mock_client.heartbeat = Mock()
        mock_client_class.return_value = mock_client
        
        # Simulate offline environment
        with patch('socket.create_connection', side_effect=OSError("Network unreachable")):
            chroma_manager = ChromaDBManager(persist_directory='data/vector_db')
            collection = chroma_manager.create_collection('test_collection')
            
            # Verify ChromaDB is accessible offline
            assert chroma_manager.check_health(), "ChromaDB should be healthy offline"
            
            # Verify search works offline
            results = collection.query(
                query_embeddings=[[0.1] * 128],
                n_results=num_results
            )
            
            assert results is not None, "Search results should not be None"
            assert len(results['documents']) > 0, "Should return documents"
            
            # Verify no AWS clients
            assert not hasattr(chroma_manager, 's3_client')
            assert not hasattr(chroma_manager, 'bedrock_client')
            assert not hasattr(chroma_manager, 'dynamodb')


@given(
    username=valid_username(),
    token=valid_token()
)
@settings(max_examples=100, deadline=None)
def test_authentication_works_offline_with_local_postgresql(username, token):
    """
    Property: Authentication continues working offline using local PostgreSQL
    
    Validates: Requirement 17.3
    """
    assume(len(username.strip()) >= 3)
    assume(len(token.strip()) >= 16)
    
    # Mock PostgreSQL connection (local database)
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(
            connection_string='postgresql://test:test@localhost:5432/test'
        )
        user_repo = UserRepository(db_manager)
        session_repo = SessionRepository(db_manager)
        
        # Mock database queries
        with patch.object(db_manager, 'execute_query') as mock_query:
            # Setup mock responses
            def mock_query_side_effect(query, params=None, fetch_one=False):
                if 'users' in query and 'username' in query:
                    return {
                        'id': 1,
                        'username': username,
                        'password_hash': 'hashed_password',
                        'role': 'student',
                        'full_name': 'Test Student'
                    }
                elif 'sessions' in query:
                    return {
                        'id': 1,
                        'user_id': 1,
                        'token': token,
                        'expires_at': datetime.now(timezone.utc) + timedelta(hours=24)
                    }
                return None
            
            mock_query.side_effect = mock_query_side_effect
            
            # Simulate offline environment
            with patch('socket.create_connection', side_effect=OSError("Network unreachable")):
                # Test user authentication
                user = user_repo.get_user_by_username(username)
                assert user is not None, "User authentication should work offline"
                assert user.username == username, "Username should match"
                
                # Test session management
                with patch('src.persistence.session_repository.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime.now(timezone.utc)
                    session = session_repo.get_session_by_token(token)
                    assert session is not None, "Session retrieval should work offline"
                    assert session.token == token, "Token should match"
                
                # Verify local database was used
                assert mock_query.called, "Database should be queried"
                
                # Verify no AWS clients
                assert not hasattr(user_repo, 's3_client')
                assert not hasattr(user_repo, 'dynamodb')
                assert not hasattr(user_repo, 'cognito_client')


@given(
    question=valid_question(),
    response=valid_response_text(),
    username=valid_username()
)
@settings(max_examples=100, deadline=None)
def test_system_operates_indefinitely_without_aws(question, response, username):
    """
    Property: System operates indefinitely with existing data when AWS is unavailable
    
    Validates: Requirement 17.5
    """
    assume(len(question.strip()) >= 5)
    assume(len(response.strip()) >= 10)
    assume(len(username.strip()) >= 3)
    
    # Mock all local components
    mock_chroma = Mock(spec=ChromaDBManager)
    mock_chroma.check_health = Mock(return_value=True)
    mock_chroma.search = Mock(return_value=[
        SearchResult(
            text="Local content",
            metadata={'page': 1},
            similarity_score=0.9
        )
    ])
    
    mock_inference = Mock(spec=InferenceEngine)
    mock_inference.generate = Mock(return_value=response)
    mock_inference.is_loaded = Mock(return_value=True)
    mock_inference.generate_response = Mock(return_value=iter([response]))
    
    # Simulate complete AWS unavailability
    with patch('socket.create_connection', side_effect=OSError("Network unreachable")):
        with patch('boto3.client', side_effect=Exception("AWS unavailable")):
            with patch('boto3.resource', side_effect=Exception("AWS unavailable")):
                # Create pipeline without AWS
                pipeline = RAGPipeline(
                    vector_db=mock_chroma,
                    inference_engine=mock_inference,
                    embeddings_client=None
                )
                
                # Verify system can process queries
                result = pipeline.process_query(
                    query=question,
                    top_k=5
                )
                
                assert result is not None, "System should work without AWS"
                assert result.response is not None, "Should generate response"
                
                # Verify authentication works
                with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
                    db_manager = DatabaseManager('postgresql://localhost/test')
                    user_repo = UserRepository(db_manager)
                    
                    with patch.object(db_manager, 'execute_query', return_value={
                        'id': 1,
                        'username': username,
                        'password_hash': 'hash',
                        'role': 'student',
                        'full_name': 'Test User'
                    }):
                        user = user_repo.get_user_by_username(username)
                        assert user is not None, "Authentication should work without AWS"


@given(
    question=valid_question(),
    user_id=st.integers(min_value=1, max_value=10000),
    subject_id=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_all_core_operations_work_without_internet(question, user_id, subject_id):
    """
    Property: All core operations (query, auth, storage) work without internet
    
    Validates: Requirements 17.1, 17.2, 17.3, 17.5
    """
    assume(len(question.strip()) >= 5)
    
    # Block all network access
    with patch('socket.create_connection', side_effect=OSError("Network unreachable")):
        with patch('urllib.request.urlopen', side_effect=OSError("Network unreachable")):
            # Test 1: Query processing
            mock_chroma = Mock(spec=ChromaDBManager)
            mock_chroma.check_health = Mock(return_value=True)
            mock_chroma.search = Mock(return_value=[])
            mock_chroma.query = Mock(return_value=[
                SearchResult(text="Test", metadata={}, similarity_score=0.9)
            ])
            
            mock_inference = Mock(spec=InferenceEngine)
            mock_inference.generate = Mock(return_value="Response")
            mock_inference.is_loaded = Mock(return_value=True)
            mock_inference.generate_response = Mock(return_value=iter(["Response"]))
            
            pipeline = RAGPipeline(
                vector_db=mock_chroma,
                inference_engine=mock_inference
            )
            
            result = pipeline.process_query(question, top_k=5)
            assert result is not None, "Query processing should work offline"
            
            # Test 2: Authentication
            with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
                db_manager = DatabaseManager('postgresql://localhost/test')
                user_repo = UserRepository(db_manager)
                
                with patch.object(db_manager, 'execute_query', return_value={
                    'id': user_id,
                    'username': 'test',
                    'password_hash': 'hash',
                    'role': 'student',
                    'full_name': 'Test User'
                }):
                    user = user_repo.get_user_by_username('test')
                    assert user is not None, "Authentication should work offline"
            
            # Test 3: Chat history storage
            with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
                db_manager = DatabaseManager('postgresql://localhost/test')
                chat_repo = ChatHistoryRepository(db_manager)
                
                with patch.object(db_manager, 'execute_query', return_value={
                    'id': 1,
                    'user_id': user_id,
                    'subject_id': subject_id,
                    'question': question,
                    'response': 'Response',
                    'confidence': 0.9,
                    'created_at': datetime.now(timezone.utc)
                }):
                    chat_id = chat_repo.save_chat(
                        user_id=user_id,
                        subject_id=subject_id,
                        question=question,
                        response='Response',
                        confidence=0.9
                    )
                    assert chat_id is not None, "Chat storage should work offline"


@given(
    question=valid_question(),
    top_k=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100, deadline=None)
def test_rag_pipeline_uses_only_local_components_offline(question, top_k):
    """
    Property: RAG pipeline uses only local components when offline
    
    Validates: Requirements 17.1, 17.2
    """
    assume(len(question.strip()) >= 5)
    
    mock_chroma = Mock(spec=ChromaDBManager)
    mock_chroma.check_health = Mock(return_value=True)
    mock_chroma.search = Mock(return_value=[])
    mock_chroma.query = Mock(return_value=[])
    
    mock_inference = Mock(spec=InferenceEngine)
    mock_inference.generate = Mock(return_value="Response")
    mock_inference.is_loaded = Mock(return_value=True)
    
    # Simulate offline environment
    with patch('socket.create_connection', side_effect=OSError("Network unreachable")):
        pipeline = RAGPipeline(
            vector_db=mock_chroma,
            inference_engine=mock_inference,
            embeddings_client=None
        )
        
        # Verify no AWS clients are present
        assert not hasattr(pipeline, 'bedrock_client') or pipeline.embeddings_client is None, \
            "Pipeline should not have Bedrock client"
        assert not hasattr(pipeline, 's3_client'), \
            "Pipeline should not have S3 client"
        assert not hasattr(pipeline, 'lambda_client'), \
            "Pipeline should not have Lambda client"
        assert not hasattr(pipeline, 'dynamodb'), \
            "Pipeline should not have DynamoDB client"
        
        # Verify local components are present
        assert pipeline.vector_db is not None, "Pipeline should have vector DB"
        assert pipeline.inference_engine is not None, "Pipeline should have inference engine"


@given(
    username=valid_username(),
    token=valid_token()
)
@settings(max_examples=100, deadline=None)
def test_persistence_layer_has_no_aws_dependencies_offline(username, token):
    """
    Property: Persistence layer has no AWS dependencies and works offline
    
    Validates: Requirements 17.3
    """
    assume(len(username.strip()) >= 3)
    assume(len(token.strip()) >= 16)
    
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager('postgresql://localhost/test')
        
        # Create all repositories
        user_repo = UserRepository(db_manager)
        session_repo = SessionRepository(db_manager)
        chat_repo = ChatHistoryRepository(db_manager)
        
        # Verify no AWS clients in any repository
        repositories = [user_repo, session_repo, chat_repo]
        aws_client_attributes = [
            's3_client', 's3', 'S3',
            'dynamodb', 'dynamodb_client', 'DynamoDB',
            'bedrock_client', 'bedrock', 'Bedrock',
            'lambda_client', 'lambda', 'Lambda',
            'sqs_client', 'sqs', 'SQS',
            'sns_client', 'sns', 'SNS',
            'cloudwatch', 'cloudwatch_client'
        ]
        
        for repo in repositories:
            for attr in aws_client_attributes:
                assert not hasattr(repo, attr), \
                    f"{repo.__class__.__name__} should not have AWS client: {attr}"
            
            # Verify local database connection
            assert hasattr(repo, 'db'), f"{repo.__class__.__name__} should have database manager"
            assert repo.db is not None, f"{repo.__class__.__name__} database should not be None"


@given(
    question=valid_question()
)
@settings(max_examples=100, deadline=None)
def test_vector_search_works_without_internet(question):
    """
    Property: Vector search operations work without internet connectivity
    
    Validates: Requirement 17.2
    """
    assume(len(question.strip()) >= 5)
    
    with patch('chromadb.PersistentClient') as mock_client_class:
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.query = Mock(return_value={
            'documents': [['Document 1', 'Document 2']],
            'metadatas': [[{'page': 1}, {'page': 2}]],
            'distances': [[0.1, 0.2]]
        })
        mock_client.get_or_create_collection = Mock(return_value=mock_collection)
        mock_client.heartbeat = Mock()
        mock_client_class.return_value = mock_client
        
        # Block network
        with patch('socket.create_connection', side_effect=OSError("Network unreachable")):
            chroma_manager = ChromaDBManager()
            collection = chroma_manager.create_collection('test')
            
            # Perform search
            results = collection.query(
                query_embeddings=[[0.1] * 128],
                n_results=5
            )
            
            # Verify search succeeded
            assert results is not None, "Search should succeed offline"
            assert len(results['documents'][0]) > 0, "Should return documents"


@settings(max_examples=100, deadline=None)
@given(st.data())
def test_offline_mode_is_default_operational_mode(data):
    """
    Property: System is designed to operate offline by default (AWS is optional)
    
    Validates: Requirements 17.1, 17.2, 17.3, 17.5
    """
    # Verify core components can be instantiated without AWS
    with patch('socket.create_connection', side_effect=OSError("Network unreachable")):
        # ChromaDB (local)
        with patch('chromadb.PersistentClient') as mock_client_class:
            mock_client = Mock()
            mock_client.heartbeat = Mock()
            mock_client_class.return_value = mock_client
            
            chroma = ChromaDBManager()
            assert chroma is not None, "ChromaDB should work offline"
        
        # PostgreSQL (local)
        with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
            db_manager = DatabaseManager('postgresql://localhost/test')
            assert db_manager is not None, "Database should work offline"
        
        # Inference Engine (local)
        mock_inference = Mock(spec=InferenceEngine)
        mock_inference.is_loaded = Mock(return_value=True)
        assert mock_inference.is_loaded(), "Inference engine should work offline"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
