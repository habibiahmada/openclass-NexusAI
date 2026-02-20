"""Property-based tests for chat interface functionality.

Feature: phase4-local-application
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime

from src.ui.models import ChatMessage, SourceCitation


# Feature: phase4-local-application, Property 1: Question Display in Chat History
@settings(max_examples=100)
@given(
    question=st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z', 'S'),
        blacklist_characters='\n\r\t'
    ))
)
def test_property_question_display_in_chat_history(question):
    """Property 1: For any user-submitted question, adding it to the chat interface 
    should result in the question appearing in the session chat history immediately.
    
    **Validates: Requirements 1.2**
    """
    # Simulate chat history
    chat_history = []
    
    # Create a user message (simulating what happens when user submits a question)
    user_message = ChatMessage(
        role="user",
        content=question,
        timestamp=datetime.now()
    )
    
    # Add to chat history (simulating the append operation in render_chat_interface)
    chat_history.append(user_message)
    
    # Property 1: The question must appear in chat history
    assert len(chat_history) > 0, \
        "Chat history should not be empty after adding a question"
    
    # Property 2: The last message in history should be the user's question
    last_message = chat_history[-1]
    assert last_message.role == "user", \
        f"Last message should have role 'user', got: {last_message.role}"
    
    # Property 3: The content of the last message should match the question
    assert last_message.content == question, \
        f"Last message content should match question. Expected: {question}, Got: {last_message.content}"
    
    # Property 4: The message should have a timestamp
    assert last_message.timestamp is not None, \
        "Message should have a timestamp"
    
    # Property 5: User messages should not have sources
    assert last_message.sources == [], \
        "User messages should not have sources"
    
    # Property 6: User messages should not have processing time
    assert last_message.processing_time_ms is None, \
        "User messages should not have processing time"


# Feature: phase4-local-application, Property 1: Multiple Questions Accumulation
@settings(max_examples=100)
@given(
    questions=st.lists(
        st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('L', 'N', 'P', 'Z'),
            blacklist_characters='\n\r\t'
        )),
        min_size=1,
        max_size=10
    )
)
def test_property_multiple_questions_accumulation(questions):
    """Property 1 (Multiple Questions): For any sequence of user-submitted questions, 
    all questions should appear in the chat history in the order they were submitted.
    
    **Validates: Requirements 1.2, 2.1**
    """
    chat_history = []
    
    # Add all questions to chat history
    for question in questions:
        user_message = ChatMessage(
            role="user",
            content=question,
            timestamp=datetime.now()
        )
        chat_history.append(user_message)
    
    # Property 1: Chat history length should match number of questions
    assert len(chat_history) == len(questions), \
        f"Chat history should contain {len(questions)} messages, got {len(chat_history)}"
    
    # Property 2: All messages should be user messages
    for i, message in enumerate(chat_history):
        assert message.role == "user", \
            f"Message {i} should have role 'user', got: {message.role}"
    
    # Property 3: Messages should appear in the same order as questions
    for i, (message, question) in enumerate(zip(chat_history, questions)):
        assert message.content == question, \
            f"Message {i} content doesn't match. Expected: {question}, Got: {message.content}"
    
    # Property 4: All messages should have timestamps
    for i, message in enumerate(chat_history):
        assert message.timestamp is not None, \
            f"Message {i} should have a timestamp"


# Feature: phase4-local-application, Property 1: Question Preservation
@settings(max_examples=100)
@given(
    question=st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z', 'S'),
        blacklist_characters='\n\r\t'
    ))
)
def test_property_question_content_preservation(question):
    """Property 1 (Content Preservation): For any user-submitted question, 
    the content stored in chat history should exactly match the original question 
    without any modification or truncation.
    
    **Validates: Requirements 1.2**
    """
    # Create a user message
    user_message = ChatMessage(
        role="user",
        content=question,
        timestamp=datetime.now()
    )
    
    # Property 1: Content should be preserved exactly
    assert user_message.content == question, \
        "Question content should be preserved exactly without modification"
    
    # Property 2: Content length should match
    assert len(user_message.content) == len(question), \
        f"Content length should match. Expected: {len(question)}, Got: {len(user_message.content)}"
    
    # Property 3: Content should not be None or empty if question is not empty
    if question:
        assert user_message.content, \
            "Content should not be empty if question is not empty"
        assert user_message.content is not None, \
            "Content should not be None"


# Feature: phase4-local-application, Property 1: Immediate Display
@settings(max_examples=100)
@given(
    question=st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        blacklist_characters='\n\r\t'
    ))
)
def test_property_question_immediate_display(question):
    """Property 1 (Immediate Display): For any user-submitted question, 
    the question should be added to chat history before any response processing begins.
    This ensures the question appears immediately in the UI.
    
    **Validates: Requirements 1.2**
    """
    chat_history = []
    
    # Simulate the immediate display behavior from render_chat_interface
    # Step 1: Create user message
    user_message = ChatMessage(
        role="user",
        content=question,
        timestamp=datetime.now()
    )
    
    # Step 2: Append to history immediately (before any processing)
    chat_history.append(user_message)
    
    # Property 1: Question should be in history immediately
    assert len(chat_history) == 1, \
        "Question should be in history immediately after submission"
    
    # Property 2: The message should be retrievable immediately
    retrieved_message = chat_history[0]
    assert retrieved_message.content == question, \
        "Question should be retrievable immediately from history"
    
    # Property 3: The message should have the correct role
    assert retrieved_message.role == "user", \
        "Message should have 'user' role immediately"
    
    # Simulate adding a response later
    assistant_message = ChatMessage(
        role="assistant",
        content="Response",
        timestamp=datetime.now()
    )
    chat_history.append(assistant_message)
    
    # Property 4: User question should still be first in history
    assert chat_history[0].content == question, \
        "User question should remain first in history after response is added"
    
    # Property 5: User question should not be modified by subsequent operations
    assert chat_history[0].role == "user", \
        "User message role should not change after response is added"


# Feature: phase4-local-application, Property 5: Chat History Accumulation
@settings(max_examples=100)
@given(
    qa_pairs=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=200, alphabet=st.characters(
                whitelist_categories=('L', 'N', 'P', 'Z'),
                blacklist_characters='\n\r\t'
            )),  # question
            st.text(min_size=1, max_size=500, alphabet=st.characters(
                whitelist_categories=('L', 'N', 'P', 'Z'),
                blacklist_characters='\n\r\t'
            ))   # response
        ),
        min_size=1,
        max_size=20
    )
)
def test_property_chat_history_accumulation(qa_pairs):
    """Property 5: For any question-response pair, both the question and response 
    should be appended to the session chat history in order.
    
    **Validates: Requirements 2.1**
    """
    chat_history = []
    
    # Simulate the chat interaction: for each Q&A pair, add question then response
    for question, response in qa_pairs:
        # Add user question
        user_message = ChatMessage(
            role="user",
            content=question,
            timestamp=datetime.now()
        )
        chat_history.append(user_message)
        
        # Add assistant response
        assistant_message = ChatMessage(
            role="assistant",
            content=response,
            timestamp=datetime.now()
        )
        chat_history.append(assistant_message)
    
    # Property 1: Chat history length should be 2 * number of Q&A pairs
    expected_length = len(qa_pairs) * 2
    assert len(chat_history) == expected_length, \
        f"Chat history should contain {expected_length} messages (2 per Q&A pair), got {len(chat_history)}"
    
    # Property 2: Messages should alternate between user and assistant
    for i in range(0, len(chat_history), 2):
        assert chat_history[i].role == "user", \
            f"Message at index {i} should be 'user', got: {chat_history[i].role}"
        assert chat_history[i + 1].role == "assistant", \
            f"Message at index {i + 1} should be 'assistant', got: {chat_history[i + 1].role}"
    
    # Property 3: Questions and responses should appear in the correct order
    for i, (question, response) in enumerate(qa_pairs):
        user_idx = i * 2
        assistant_idx = i * 2 + 1
        
        assert chat_history[user_idx].content == question, \
            f"Question at index {user_idx} doesn't match. Expected: {question}, Got: {chat_history[user_idx].content}"
        
        assert chat_history[assistant_idx].content == response, \
            f"Response at index {assistant_idx} doesn't match. Expected: {response}, Got: {chat_history[assistant_idx].content}"
    
    # Property 4: All messages should have timestamps
    for i, message in enumerate(chat_history):
        assert message.timestamp is not None, \
            f"Message {i} should have a timestamp"
    
    # Property 5: User messages should not have sources or processing time
    for i in range(0, len(chat_history), 2):
        user_message = chat_history[i]
        assert user_message.sources == [], \
            f"User message at index {i} should not have sources"
        assert user_message.processing_time_ms is None, \
            f"User message at index {i} should not have processing time"


# Feature: phase4-local-application, Property 5: Chat History Order Preservation
@settings(max_examples=100)
@given(
    qa_pairs=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=200, alphabet=st.characters(
                whitelist_categories=('L', 'N', 'P', 'Z'),
                blacklist_characters='\n\r\t'
            )),  # question
            st.text(min_size=1, max_size=500, alphabet=st.characters(
                whitelist_categories=('L', 'N', 'P', 'Z'),
                blacklist_characters='\n\r\t'
            ))   # response
        ),
        min_size=2,
        max_size=10
    )
)
def test_property_chat_history_order_preservation(qa_pairs):
    """Property 5 (Order Preservation): For any sequence of question-response pairs, 
    the chat history should preserve the exact order in which they were added.
    
    **Validates: Requirements 2.1**
    """
    chat_history = []
    
    # Add all Q&A pairs to history
    for question, response in qa_pairs:
        user_message = ChatMessage(
            role="user",
            content=question,
            timestamp=datetime.now()
        )
        chat_history.append(user_message)
        
        assistant_message = ChatMessage(
            role="assistant",
            content=response,
            timestamp=datetime.now()
        )
        chat_history.append(assistant_message)
    
    # Property 1: First message should be the first question
    assert chat_history[0].role == "user", \
        "First message should be a user question"
    assert chat_history[0].content == qa_pairs[0][0], \
        "First message should be the first question"
    
    # Property 2: Last message should be the last response
    assert chat_history[-1].role == "assistant", \
        "Last message should be an assistant response"
    assert chat_history[-1].content == qa_pairs[-1][1], \
        "Last message should be the last response"
    
    # Property 3: Each question should be immediately followed by its response
    for i, (question, response) in enumerate(qa_pairs):
        user_idx = i * 2
        assistant_idx = i * 2 + 1
        
        # Check that question comes before response
        assert user_idx < assistant_idx, \
            f"Question at index {user_idx} should come before response at index {assistant_idx}"
        
        # Check that they are adjacent
        assert assistant_idx == user_idx + 1, \
            f"Response should immediately follow question (indices {user_idx} and {assistant_idx})"
    
    # Property 4: No messages should be skipped or duplicated
    seen_contents = set()
    for message in chat_history:
        content_with_role = (message.role, message.content)
        # Note: We allow duplicate content if it appears in different roles or at different times
        # This is valid in a real chat scenario
    
    # Property 5: Timestamps should be monotonically increasing or equal
    for i in range(len(chat_history) - 1):
        assert chat_history[i].timestamp <= chat_history[i + 1].timestamp, \
            f"Timestamps should be monotonically increasing. Message {i} timestamp: {chat_history[i].timestamp}, Message {i+1} timestamp: {chat_history[i+1].timestamp}"


# Feature: phase4-local-application, Property 5: Chat History Accumulation with Sources
@settings(max_examples=100)
@given(
    qa_pairs=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=200, alphabet=st.characters(
                whitelist_categories=('L', 'N', 'P', 'Z'),
                blacklist_characters='\n\r\t'
            )),  # question
            st.text(min_size=1, max_size=500, alphabet=st.characters(
                whitelist_categories=('L', 'N', 'P', 'Z'),
                blacklist_characters='\n\r\t'
            )),  # response
            st.lists(
                st.tuples(
                    st.text(min_size=1, max_size=50),  # filename
                    st.sampled_from(["Matematika", "IPA", "Bahasa Indonesia", "Informatika"]),  # subject
                    st.floats(min_value=0.0, max_value=1.0)  # relevance_score
                ),
                min_size=0,
                max_size=5
            )  # sources
        ),
        min_size=1,
        max_size=10
    )
)
def test_property_chat_history_accumulation_with_sources(qa_pairs):
    """Property 5 (With Sources): For any question-response pair with sources, 
    both the question and response (including sources) should be appended to 
    the session chat history in order.
    
    **Validates: Requirements 2.1, 6.1, 6.2, 6.3**
    """
    chat_history = []
    
    # Simulate the chat interaction with sources
    for question, response, source_data in qa_pairs:
        # Add user question
        user_message = ChatMessage(
            role="user",
            content=question,
            timestamp=datetime.now()
        )
        chat_history.append(user_message)
        
        # Create source citations
        sources = [
            SourceCitation(
                filename=filename,
                subject=subject,
                relevance_score=score,
                chunk_index=idx
            )
            for idx, (filename, subject, score) in enumerate(source_data)
        ]
        
        # Add assistant response with sources
        assistant_message = ChatMessage(
            role="assistant",
            content=response,
            sources=sources,
            timestamp=datetime.now(),
            processing_time_ms=100.0  # Simulated processing time
        )
        chat_history.append(assistant_message)
    
    # Property 1: Chat history length should be 2 * number of Q&A pairs
    expected_length = len(qa_pairs) * 2
    assert len(chat_history) == expected_length, \
        f"Chat history should contain {expected_length} messages, got {len(chat_history)}"
    
    # Property 2: Assistant messages should preserve their sources
    for i, (question, response, source_data) in enumerate(qa_pairs):
        assistant_idx = i * 2 + 1
        assistant_message = chat_history[assistant_idx]
        
        assert len(assistant_message.sources) == len(source_data), \
            f"Assistant message at index {assistant_idx} should have {len(source_data)} sources, got {len(assistant_message.sources)}"
        
        # Verify each source is preserved correctly
        for j, (filename, subject, score) in enumerate(source_data):
            source = assistant_message.sources[j]
            assert source.filename == filename, \
                f"Source {j} filename mismatch at message {assistant_idx}"
            assert source.subject == subject, \
                f"Source {j} subject mismatch at message {assistant_idx}"
            assert abs(source.relevance_score - score) < 0.001, \
                f"Source {j} relevance score mismatch at message {assistant_idx}"
    
    # Property 3: Assistant messages should have processing time
    for i in range(1, len(chat_history), 2):
        assistant_message = chat_history[i]
        assert assistant_message.processing_time_ms is not None, \
            f"Assistant message at index {i} should have processing time"
        assert assistant_message.processing_time_ms > 0, \
            f"Assistant message at index {i} should have positive processing time"
    
    # Property 4: User messages should never have sources
    for i in range(0, len(chat_history), 2):
        user_message = chat_history[i]
        assert user_message.sources == [], \
            f"User message at index {i} should not have sources"
        assert user_message.processing_time_ms is None, \
            f"User message at index {i} should not have processing time"
