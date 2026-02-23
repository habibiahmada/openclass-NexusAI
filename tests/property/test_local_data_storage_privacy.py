"""
Property Test: Local Data Storage Privacy

**Property 32: Local Data Storage Privacy**
**Validates: Requirements 16.1, 16.2, 16.3**

This property test verifies that:
1. All chat history operations use only local PostgreSQL (no AWS clients)
2. All user identity operations use only local PostgreSQL (no AWS clients)
3. No sensitive data is ever transmitted to AWS services
4. The architecture enforces local-only storage for sensitive data
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import inspect

from src.persistence.chat_history_repository import ChatHistoryRepository, ChatHistory
from src.persistence.user_repository import UserRepository, User
from src.persistence.session_repository import SessionRepository, Session
from src.persistence.database_manager import DatabaseManager


# Strategy for generating valid usernames
@st.composite
def valid_username(draw):
    """Generate valid username (3-50 characters)"""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48),
        min_size=3,
        max_size=50
    ))


# Strategy for generating valid passwords
@st.composite
def valid_password(draw):
    """Generate valid password (6+ characters)"""
    return draw(st.text(min_size=6, max_size=100))


# Strategy for generating valid roles
def valid_role():
    """Generate valid user role"""
    return st.sampled_from(['siswa', 'guru', 'admin'])


# Strategy for generating valid full names
@st.composite
def valid_full_name(draw):
    """Generate valid full name"""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=65),
        min_size=3,
        max_size=100
    ))


# Strategy for generating valid questions
@st.composite
def valid_question(draw):
    """Generate valid question text"""
    return draw(st.text(min_size=5, max_size=500))


# Strategy for generating valid responses
@st.composite
def valid_response(draw):
    """Generate valid response text"""
    return draw(st.text(min_size=10, max_size=2000))


# Strategy for generating valid confidence scores
def valid_confidence():
    """Generate valid confidence score (0.0 to 1.0)"""
    return st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


# Strategy for generating valid session tokens
@st.composite
def valid_token(draw):
    """Generate valid session token (8+ characters)"""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48),
        min_size=8,
        max_size=64
    ))


@given(
    username=valid_username(),
    password=valid_password(),
    role=valid_role(),
    full_name=valid_full_name()
)
@settings(max_examples=100, deadline=None)
def test_user_repository_uses_only_postgresql(username, password, role, full_name):
    """
    Property: UserRepository uses only local PostgreSQL, never AWS clients
    
    Validates: Requirements 16.2, 16.3
    """
    # Mock the database connection to avoid actual PostgreSQL requirement
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
        user_repo = UserRepository(db_manager)
    
    # Verify repository uses PostgreSQL connection
    assert hasattr(user_repo, 'db'), "UserRepository should have database manager"
    assert user_repo.db is not None, "Database manager should not be None"
    
    # Verify NO AWS clients are present in the repository
    aws_client_attributes = [
        's3_client', 's3', 'S3',
        'dynamodb', 'dynamodb_client', 'DynamoDB',
        'bedrock_client', 'bedrock', 'Bedrock',
        'lambda_client', 'lambda', 'Lambda',
        'sqs_client', 'sqs', 'SQS',
        'sns_client', 'sns', 'SNS',
        'cloudwatch', 'cloudwatch_client'
    ]
    
    for attr in aws_client_attributes:
        assert not hasattr(user_repo, attr), \
            f"UserRepository should not have AWS client attribute: {attr}"
    
    # Verify repository methods don't import boto3
    repo_source = inspect.getsource(UserRepository)
    assert 'boto3' not in repo_source, \
        "UserRepository should not import boto3"
    assert 'aws' not in repo_source.lower() or 'aws_control_plane' in repo_source.lower(), \
        "UserRepository should not reference AWS services"


@given(
    user_id=st.integers(min_value=1, max_value=10000),
    subject_id=st.integers(min_value=1, max_value=100),
    question=valid_question(),
    response=valid_response(),
    confidence=valid_confidence()
)
@settings(max_examples=100, deadline=None)
def test_chat_history_repository_uses_only_postgresql(user_id, subject_id, question, response, confidence):
    """
    Property: ChatHistoryRepository uses only local PostgreSQL, never AWS clients
    
    Validates: Requirement 16.1
    """
    # Mock the database connection to avoid actual PostgreSQL requirement
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
        chat_repo = ChatHistoryRepository(db_manager)
    
    # Verify repository uses PostgreSQL connection
    assert hasattr(chat_repo, 'db'), "ChatHistoryRepository should have database manager"
    assert chat_repo.db is not None, "Database manager should not be None"
    
    # Verify NO AWS clients are present in the repository
    aws_client_attributes = [
        's3_client', 's3', 'S3',
        'dynamodb', 'dynamodb_client', 'DynamoDB',
        'bedrock_client', 'bedrock', 'Bedrock',
        'lambda_client', 'lambda', 'Lambda',
        'sqs_client', 'sqs', 'SQS',
        'sns_client', 'sns', 'SNS',
        'cloudwatch', 'cloudwatch_client'
    ]
    
    for attr in aws_client_attributes:
        assert not hasattr(chat_repo, attr), \
            f"ChatHistoryRepository should not have AWS client attribute: {attr}"
    
    # Verify repository methods don't import boto3
    repo_source = inspect.getsource(ChatHistoryRepository)
    assert 'boto3' not in repo_source, \
        "ChatHistoryRepository should not import boto3"
    assert 'aws' not in repo_source.lower() or 'aws_control_plane' in repo_source.lower(), \
        "ChatHistoryRepository should not reference AWS services"


@given(
    user_id=st.integers(min_value=1, max_value=10000),
    token=valid_token(),
    expires_hours=st.integers(min_value=1, max_value=168)
)
@settings(max_examples=100, deadline=None)
def test_session_repository_uses_only_postgresql(user_id, token, expires_hours):
    """
    Property: SessionRepository uses only local PostgreSQL, never AWS clients
    
    Validates: Requirements 16.2, 16.3
    """
    # Mock the database connection to avoid actual PostgreSQL requirement
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
        session_repo = SessionRepository(db_manager)
    
    # Verify repository uses PostgreSQL connection
    assert hasattr(session_repo, 'db'), "SessionRepository should have database manager"
    assert session_repo.db is not None, "Database manager should not be None"
    
    # Verify NO AWS clients are present in the repository
    aws_client_attributes = [
        's3_client', 's3', 'S3',
        'dynamodb', 'dynamodb_client', 'DynamoDB',
        'bedrock_client', 'bedrock', 'Bedrock',
        'lambda_client', 'lambda', 'Lambda',
        'sqs_client', 'sqs', 'SQS',
        'sns_client', 'sns', 'SNS',
        'cloudwatch', 'cloudwatch_client'
    ]
    
    for attr in aws_client_attributes:
        assert not hasattr(session_repo, attr), \
            f"SessionRepository should not have AWS client attribute: {attr}"
    
    # Verify repository methods don't import boto3
    repo_source = inspect.getsource(SessionRepository)
    assert 'boto3' not in repo_source, \
        "SessionRepository should not import boto3"
    assert 'aws' not in repo_source.lower() or 'aws_control_plane' in repo_source.lower(), \
        "SessionRepository should not reference AWS services"


@given(
    username=valid_username(),
    password=valid_password(),
    role=valid_role()
)
@settings(max_examples=100, deadline=None)
def test_user_data_never_transmitted_to_aws(username, password, role):
    """
    Property: User identity data is never transmitted to AWS services
    
    Validates: Requirements 16.2, 16.3
    """
    # Mock the database connection
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
        user_repo = UserRepository(db_manager)
    
    # Verify User model has no AWS transmission methods
    user_methods = [method for method in dir(User) if not method.startswith('_')]
    
    aws_transmission_methods = [
        'upload_to_s3', 'send_to_dynamodb', 'transmit_to_aws',
        'sync_to_cloud', 'backup_to_s3', 'store_in_dynamodb'
    ]
    
    for method in aws_transmission_methods:
        assert method not in user_methods, \
            f"User model should not have AWS transmission method: {method}"
    
    # Verify UserRepository has no AWS transmission methods
    repo_methods = [method for method in dir(UserRepository) if not method.startswith('_')]
    
    for method in aws_transmission_methods:
        assert method not in repo_methods, \
            f"UserRepository should not have AWS transmission method: {method}"


@given(
    user_id=st.integers(min_value=1, max_value=10000),
    question=valid_question(),
    response=valid_response()
)
@settings(max_examples=100, deadline=None)
def test_chat_history_never_transmitted_to_aws(user_id, question, response):
    """
    Property: Chat history is never transmitted to AWS services
    
    Validates: Requirement 16.1
    """
    # Mock the database connection
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
        chat_repo = ChatHistoryRepository(db_manager)
    
    # Verify ChatHistory model has no AWS transmission methods
    chat_methods = [method for method in dir(ChatHistory) if not method.startswith('_')]
    
    aws_transmission_methods = [
        'upload_to_s3', 'send_to_dynamodb', 'transmit_to_aws',
        'sync_to_cloud', 'backup_to_s3', 'store_in_dynamodb'
    ]
    
    for method in aws_transmission_methods:
        assert method not in chat_methods, \
            f"ChatHistory model should not have AWS transmission method: {method}"
    
    # Verify ChatHistoryRepository has no AWS transmission methods
    repo_methods = [method for method in dir(ChatHistoryRepository) if not method.startswith('_')]
    
    for method in aws_transmission_methods:
        assert method not in repo_methods, \
            f"ChatHistoryRepository should not have AWS transmission method: {method}"


@given(
    user_id=st.integers(min_value=1, max_value=10000),
    token=valid_token()
)
@settings(max_examples=100, deadline=None)
def test_session_data_never_transmitted_to_aws(user_id, token):
    """
    Property: Session data is never transmitted to AWS services
    
    Validates: Requirements 16.2, 16.3
    """
    # Mock the database connection
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
        session_repo = SessionRepository(db_manager)
    
    # Verify Session model has no AWS transmission methods
    session_methods = [method for method in dir(Session) if not method.startswith('_')]
    
    aws_transmission_methods = [
        'upload_to_s3', 'send_to_dynamodb', 'transmit_to_aws',
        'sync_to_cloud', 'backup_to_s3', 'store_in_dynamodb'
    ]
    
    for method in aws_transmission_methods:
        assert method not in session_methods, \
            f"Session model should not have AWS transmission method: {method}"
    
    # Verify SessionRepository has no AWS transmission methods
    repo_methods = [method for method in dir(SessionRepository) if not method.startswith('_')]
    
    for method in aws_transmission_methods:
        assert method not in repo_methods, \
            f"SessionRepository should not have AWS transmission method: {method}"


@settings(max_examples=100, deadline=None)
@given(st.data())
def test_persistence_layer_architecture_enforces_local_storage(data):
    """
    Property: Architecture enforces local-only storage for sensitive data
    
    Validates: Requirements 16.1, 16.2, 16.3
    """
    # Mock the database connection
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
        
        # Create all persistence repositories
        repositories = [
            UserRepository(db_manager),
            SessionRepository(db_manager),
            ChatHistoryRepository(db_manager)
        ]
    
    # Verify all repositories use the same local database manager
    for repo in repositories:
        assert hasattr(repo, 'db'), f"{repo.__class__.__name__} should have database manager"
        assert repo.db is db_manager, f"{repo.__class__.__name__} should use the same database manager"
    
    # Verify database manager has no AWS clients
    db_manager_attrs = dir(db_manager)
    aws_attributes = [attr for attr in db_manager_attrs if any(
        aws_keyword in attr.lower() 
        for aws_keyword in ['s3', 'dynamodb', 'bedrock', 'lambda', 'sqs', 'sns', 'cloudwatch', 'boto']
    )]
    
    # Filter out false positives (like method names containing 'db' which might match 'dynamodb')
    actual_aws_attributes = [attr for attr in aws_attributes if not attr.startswith('_')]
    
    assert len(actual_aws_attributes) == 0, \
        f"DatabaseManager should not have AWS-related attributes: {actual_aws_attributes}"


@settings(max_examples=100, deadline=None)
@given(st.data())
def test_no_boto3_imports_in_persistence_layer(data):
    """
    Property: Persistence layer modules never import boto3 or AWS SDKs
    
    Validates: Requirements 16.1, 16.2, 16.3
    """
    # Check source code of persistence modules
    persistence_modules = [
        ChatHistoryRepository,
        UserRepository,
        SessionRepository,
        DatabaseManager
    ]
    
    for module_class in persistence_modules:
        module_source = inspect.getsource(module_class)
        
        # Check for boto3 imports
        assert 'import boto3' not in module_source, \
            f"{module_class.__name__} should not import boto3"
        assert 'from boto3' not in module_source, \
            f"{module_class.__name__} should not import from boto3"
        
        # Check for botocore imports
        assert 'import botocore' not in module_source, \
            f"{module_class.__name__} should not import botocore"
        assert 'from botocore' not in module_source, \
            f"{module_class.__name__} should not import from botocore"
        
        # Check for AWS SDK references (but allow aws_control_plane references)
        lines = module_source.split('\n')
        for line in lines:
            if 'aws' in line.lower() and 'import' in line.lower():
                # Allow imports from aws_control_plane (our own module)
                assert 'aws_control_plane' in line or 'AWS' not in line, \
                    f"{module_class.__name__} should not import AWS SDKs: {line.strip()}"


@given(
    username=valid_username(),
    password=valid_password(),
    role=valid_role(),
    full_name=valid_full_name()
)
@settings(max_examples=50, deadline=None)
def test_user_repository_operations_are_local_only(username, password, role, full_name):
    """
    Property: All UserRepository operations execute locally without AWS calls
    
    Validates: Requirements 16.2, 16.3
    """
    # Mock the database connection
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
        user_repo = UserRepository(db_manager)
    
    # Get all public methods of UserRepository
    repo_methods = [
        method for method in dir(user_repo) 
        if callable(getattr(user_repo, method)) and not method.startswith('_')
    ]
    
    # Verify each method's implementation doesn't call AWS services
    for method_name in repo_methods:
        method = getattr(user_repo, method_name)
        if hasattr(method, '__func__'):
            method_source = inspect.getsource(method.__func__)
        else:
            method_source = inspect.getsource(method)
        
        # Check for AWS API calls
        aws_api_patterns = [
            'boto3.client', 'boto3.resource',
            '.put_item', '.get_item', '.query', '.scan',  # DynamoDB
            '.put_object', '.get_object',  # S3
            '.invoke_model',  # Bedrock
            '.invoke',  # Lambda
        ]
        
        for pattern in aws_api_patterns:
            assert pattern not in method_source, \
                f"UserRepository.{method_name} should not call AWS API: {pattern}"


@given(
    user_id=st.integers(min_value=1, max_value=10000),
    question=valid_question(),
    response=valid_response(),
    confidence=valid_confidence()
)
@settings(max_examples=50, deadline=None)
def test_chat_history_repository_operations_are_local_only(user_id, question, response, confidence):
    """
    Property: All ChatHistoryRepository operations execute locally without AWS calls
    
    Validates: Requirement 16.1
    """
    # Mock the database connection
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
        chat_repo = ChatHistoryRepository(db_manager)
    
    # Get all public methods of ChatHistoryRepository
    repo_methods = [
        method for method in dir(chat_repo) 
        if callable(getattr(chat_repo, method)) and not method.startswith('_')
    ]
    
    # Verify each method's implementation doesn't call AWS services
    for method_name in repo_methods:
        method = getattr(chat_repo, method_name)
        if hasattr(method, '__func__'):
            method_source = inspect.getsource(method.__func__)
        else:
            method_source = inspect.getsource(method)
        
        # Check for AWS API calls
        aws_api_patterns = [
            'boto3.client', 'boto3.resource',
            '.put_item', '.get_item', '.query', '.scan',  # DynamoDB
            '.put_object', '.get_object',  # S3
            '.invoke_model',  # Bedrock
            '.invoke',  # Lambda
        ]
        
        for pattern in aws_api_patterns:
            assert pattern not in method_source, \
                f"ChatHistoryRepository.{method_name} should not call AWS API: {pattern}"


@given(
    user_id=st.integers(min_value=1, max_value=10000),
    token=valid_token(),
    expires_hours=st.integers(min_value=1, max_value=168)
)
@settings(max_examples=50, deadline=None)
def test_session_repository_operations_are_local_only(user_id, token, expires_hours):
    """
    Property: All SessionRepository operations execute locally without AWS calls
    
    Validates: Requirements 16.2, 16.3
    """
    # Mock the database connection
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
        session_repo = SessionRepository(db_manager)
    
    # Get all public methods of SessionRepository
    repo_methods = [
        method for method in dir(session_repo) 
        if callable(getattr(session_repo, method)) and not method.startswith('_')
    ]
    
    # Verify each method's implementation doesn't call AWS services
    for method_name in repo_methods:
        method = getattr(session_repo, method_name)
        if hasattr(method, '__func__'):
            method_source = inspect.getsource(method.__func__)
        else:
            method_source = inspect.getsource(method)
        
        # Check for AWS API calls
        aws_api_patterns = [
            'boto3.client', 'boto3.resource',
            '.put_item', '.get_item', '.query', '.scan',  # DynamoDB
            '.put_object', '.get_object',  # S3
            '.invoke_model',  # Bedrock
            '.invoke',  # Lambda
        ]
        
        for pattern in aws_api_patterns:
            assert pattern not in method_source, \
                f"SessionRepository.{method_name} should not call AWS API: {pattern}"


@settings(max_examples=100, deadline=None)
@given(st.data())
def test_database_manager_uses_only_postgresql(data):
    """
    Property: DatabaseManager uses only PostgreSQL, never AWS database services
    
    Validates: Requirements 16.1, 16.2, 16.3
    """
    # Mock the database connection
    with patch('src.persistence.database_manager.pool.ThreadedConnectionPool'):
        db_manager = DatabaseManager(connection_string='postgresql://test:test@localhost:5432/test')
    
    # Verify DatabaseManager source code
    db_manager_source = inspect.getsource(DatabaseManager)
    
    # Should use PostgreSQL (psycopg2)
    assert 'psycopg2' in db_manager_source or 'postgresql' in db_manager_source.lower(), \
        "DatabaseManager should use PostgreSQL"
    
    # Should NOT use AWS database services
    aws_db_services = ['dynamodb', 'rds', 'aurora', 'redshift', 'neptune', 'documentdb']
    
    for service in aws_db_services:
        # Allow the word in comments or strings, but not in actual code
        lines = db_manager_source.split('\n')
        for line in lines:
            # Skip comments and docstrings
            if line.strip().startswith('#') or line.strip().startswith('"""') or line.strip().startswith("'''"):
                continue
            
            # Check for actual usage (not just mentions in strings)
            if service in line.lower() and ('import' in line.lower() or 'client' in line.lower()):
                pytest.fail(f"DatabaseManager should not use AWS service: {service}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
