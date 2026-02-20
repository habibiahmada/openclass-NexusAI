# Implementation Plan: Phase 4 Local Application

## Overview

This implementation plan breaks down the Streamlit-based UI development into discrete coding tasks. The approach follows a bottom-up strategy: build core modules first, then integrate them into the main application, and finally add polish and error handling.

The implementation leverages existing Phase 1-3 components (Complete_Pipeline, RAG_Pipeline, Inference_Engine, ChromaDB) and focuses on creating a clean, efficient UI layer.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create src/ui/ directory for UI modules
  - Create app.py as main entry point
  - Verify Streamlit is installed in requirements.txt
  - Create tests/unit/ and tests/property/ directories
  - _Requirements: All requirements (foundation)_

- [ ] 2. Implement error handler module
  - [x] 2.1 Create src/ui/error_handler.py with ErrorMessages class
    - Define Indonesian error message constants
    - Implement get_error_message() function with string formatting
    - Implement display_error() function using st.error()
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 2.2 Write unit tests for error messages
    - Test each error message constant
    - Test get_error_message() with different error types
    - Test display_error() output format
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 3. Implement data models
  - [x] 3.1 Create src/ui/models.py with dataclasses
    - Implement ChatMessage dataclass
    - Implement SourceCitation dataclass with format_citation() method
    - Implement PipelineStatus dataclass with status text methods
    - _Requirements: 1.4, 3.3, 3.4, 6.5_
  
  - [x] 3.2 Write property test for source citation formatting
    - **Property 3: Source Citation Completeness**
    - **Validates: Requirements 1.4, 6.1, 6.2, 6.3, 6.5**
  
  - [x] 3.3 Write unit tests for data models
    - Test ChatMessage creation and fields
    - Test SourceCitation.format_citation() output
    - Test PipelineStatus status text methods
    - _Requirements: 1.4, 3.3, 3.4, 6.5_

- [ ] 4. Implement pipeline manager module
  - [x] 4.1 Create src/ui/pipeline_manager.py with PipelineManager class
    - Implement __init__() to initialize pipeline as None
    - Implement initialize_pipeline() with lazy loading and error handling
    - Implement get_pipeline() to return cached pipeline instance
    - Implement get_status() to extract PipelineStatus from pipeline
    - Implement process_query() to stream responses from pipeline
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.5_
  
  - [x] 4.2 Write property test for lazy initialization
    - **Property 10: Lazy Initialization**
    - **Validates: Requirements 5.1, 5.2**
  
  - [x] 4.3 Write property test for pipeline instance reuse
    - **Property 11: Pipeline Instance Reuse**
    - **Validates: Requirements 5.5**
  
  - [x] 4.4 Write unit tests for pipeline manager
    - Test initialize_pipeline() success and failure cases
    - Test get_status() with different pipeline states
    - Test process_query() error handling
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 5. Implement subject filter module
  - [x] 5.1 Create src/ui/subject_filter.py
    - Define SUBJECTS constant list
    - Implement render_subject_filter() using st.selectbox()
    - Implement map_subject_to_filter() to convert UI selection to pipeline filter
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [x] 5.2 Write property test for filter propagation
    - **Property 4: Subject Filter Propagation**
    - **Validates: Requirements 1.5, 8.3**
  
  - [x] 5.3 Write unit tests for subject filter
    - Test map_subject_to_filter() with "Semua" returns None
    - Test map_subject_to_filter() with specific subjects returns lowercase
    - Test SUBJECTS list contains all required subjects
    - _Requirements: 8.1, 8.2, 8.3_

- [ ] 6. Implement status dashboard module
  - [x] 6.1 Create src/ui/status_dashboard.py
    - Implement get_status_indicator() to return emoji based on status
    - Implement format_memory_usage() with warning for >2.5GB
    - Implement render_status_dashboard() using st.sidebar
    - Display database status with document count
    - Display model status with indicator
    - Display memory usage with warning if needed
    - Display last update timestamp
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 6.2 Write property test for status display accuracy
    - **Property 8: Status Display Accuracy**
    - **Validates: Requirements 3.3, 3.4**
  
  - [x] 6.3 Write unit tests for status dashboard
    - Test get_status_indicator() returns correct emojis
    - Test format_memory_usage() shows warning at threshold
    - Test render_status_dashboard() with different pipeline states
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 7. Checkpoint - Ensure all module tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement chat interface module
  - [x] 8.1 Create src/ui/chat_interface.py
    - Implement display_sources() to render source citations
    - Implement display_message() to render a single message with role-based styling
    - Implement stream_response() to process query and yield tokens
    - Implement render_chat_interface() to display history and handle input
    - Add copy button for responses using st.button() and st.write()
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 6.1, 6.2, 6.3, 6.4, 9.1, 9.2, 9.3_
  
  - [x] 8.2 Write property test for question display
    - **Property 1: Question Display in Chat History**
    - **Validates: Requirements 1.2**
  
  - [x] 8.3 Write property test for response streaming
    - **Property 2: Response Streaming**
    - **Validates: Requirements 1.3, 5.4, 9.1**
  
  - [x] 8.4 Write property test for chat history accumulation
    - **Property 5: Chat History Accumulation**
    - **Validates: Requirements 2.1**
  
  - [x] 8.5 Write property test for typing indicator lifecycle
    - **Property 14: Typing Indicator Lifecycle**
    - **Validates: Requirements 9.2, 9.3**
  
  - [ ] 8.6 Write unit tests for chat interface
    - Test display_sources() formats citations correctly
    - Test display_message() handles user and assistant roles
    - Test stream_response() error handling
    - _Requirements: 1.4, 6.1, 6.2, 6.3, 6.5_

- [ ] 9. Implement main application
  - [x] 9.1 Create app.py with main() function
    - Set page config with title "OpenClass Nexus AI - Tutor Offline"
    - Implement initialize_session_state() to set up session variables
    - Initialize chat_history as empty list
    - Initialize pipeline_manager as None
    - Initialize current_subject_filter as "Semua"
    - Call initialize_session_state() at app start
    - _Requirements: 1.1, 2.2, 10.5_
  
  - [x] 9.2 Integrate sidebar components in app.py
    - Render status dashboard in sidebar using render_status_dashboard()
    - Render subject filter in sidebar using render_subject_filter()
    - Store selected filter in session state
    - _Requirements: 8.1, 8.5, 10.1_
  
  - [x] 9.3 Integrate chat interface in app.py main area
    - Render chat interface using render_chat_interface()
    - Pass chat_history from session state
    - Pass pipeline_manager from session state
    - Pass current_subject_filter from session state
    - _Requirements: 1.1, 1.2, 1.3, 10.2_
  
  - [x] 9.4 Implement lazy pipeline initialization in app.py
    - Check if pipeline_manager is None in session state
    - Initialize PipelineManager on first query submission
    - Store pipeline_manager in session state for reuse
    - Handle initialization errors with error_handler
    - _Requirements: 4.1, 5.1, 5.2, 5.5_
  
  - [ ] 9.5 Write property test for session state persistence
    - **Property 6: Session State Persistence**
    - **Validates: Requirements 2.2**
  
  - [ ] 9.6 Write property test for no disk persistence
    - **Property 7: No Disk Persistence**
    - **Validates: Requirements 2.4**
  
  - [ ] 9.7 Write unit tests for main application
    - Test initialize_session_state() creates correct keys
    - Test initial UI state (empty chat, correct layout)
    - Test sidebar contains dashboard and filter
    - Test main area contains chat interface
    - _Requirements: 1.1, 10.1, 10.2, 10.5_

- [ ] 10. Implement filter application timing
  - [x] 10.1 Update chat interface to apply filter only to new queries
    - Store filter value with each message in chat history
    - Display active filter in chat interface
    - Ensure filter changes don't affect existing messages
    - _Requirements: 8.4, 8.5_
  
  - [ ] 10.2 Write property test for filter application timing
    - **Property 12: Filter Application Timing**
    - **Validates: Requirements 8.4**
  
  - [ ] 10.3 Write property test for active filter display
    - **Property 13: Active Filter Display**
    - **Validates: Requirements 8.5**

- [ ] 11. Checkpoint - Ensure integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Add error handling and edge cases
  - [x] 12.1 Add error handling for empty database
    - Check document count in get_status()
    - Display Indonesian error message if count is 0
    - _Requirements: 7.1_
  
  - [x] 12.2 Add error handling for missing model
    - Catch FileNotFoundError in initialize_pipeline()
    - Display Indonesian error message with model path
    - _Requirements: 7.2_
  
  - [x] 12.3 Add error handling for query failures
    - Wrap process_query() in try-except
    - Display Indonesian error message on failure
    - Log full error details to console
    - _Requirements: 7.3, 7.5_
  
  - [x] 12.4 Add error handling for memory issues
    - Catch MemoryError in process_query()
    - Display Indonesian memory error message
    - _Requirements: 7.4_
  
  - [x] 12.5 Add handling for large chat histories
    - Ensure UI remains scrollable with >50 messages
    - Test with large message count
    - _Requirements: 2.3_
  
  - [ ] 12.6 Write property test for error message localization
    - **Property 9: Error Message Localization**
    - **Validates: Requirements 4.4, 7.5**
  
  - [ ] 12.7 Write unit tests for edge cases
    - Test empty database error message
    - Test missing model error message
    - Test query failure error message
    - Test memory error message
    - Test >50 messages in chat history
    - _Requirements: 2.3, 7.1, 7.2, 7.3, 7.4_

- [ ] 13. Add UI polish and language consistency
  - [x] 13.1 Ensure all UI labels are in Indonesian
    - Review all st.write(), st.header(), st.subheader() calls
    - Replace any English text with Indonesian
    - _Requirements: 10.4_
  
  - [x] 13.2 Add message styling with alternating colors
    - Use st.markdown() with custom CSS for user messages
    - Use st.markdown() with custom CSS for assistant messages
    - _Requirements: 10.3_
  
  - [x] 13.3 Add application title and branding
    - Set page title to "OpenClass Nexus AI - Tutor Offline"
    - Add header with title at top of main area
    - _Requirements: 10.5_
  
  - [ ] 13.4 Write property test for UI language consistency
    - **Property 15: UI Language Consistency**
    - **Validates: Requirements 10.4**
  
  - [ ] 13.5 Write unit tests for UI elements
    - Test application title is displayed
    - Test all labels are in Indonesian
    - _Requirements: 10.4, 10.5_

- [ ] 14. Final checkpoint - Complete testing and validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation follows a bottom-up approach: modules first, then integration
- All error messages must be in Indonesian as per requirements
- Memory optimization is achieved through lazy loading and session state caching
