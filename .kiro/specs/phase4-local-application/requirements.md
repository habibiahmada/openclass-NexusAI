# Requirements Document

## Introduction

Phase 4 of the OpenClass Nexus AI project focuses on building a Streamlit-based user interface for the offline AI tutor system. This interface enables teachers and students in Indonesian schools to interact with the local AI tutor through a simple, intuitive chat interface that works completely offline after initial setup.

The application integrates with existing components from Phases 1-3: the RAG pipeline, local inference engine, ChromaDB vector database, and complete pipeline integration.

## Glossary

- **System**: The Streamlit-based local application interface
- **RAG_Pipeline**: The existing retrieval-augmented generation pipeline from src/local_inference/rag_pipeline.py
- **Inference_Engine**: The local inference engine using llama.cpp from src/local_inference/inference_engine.py
- **Vector_DB**: The ChromaDB vector database manager from src/embeddings/chroma_manager.py
- **Complete_Pipeline**: The integrated pipeline from src/local_inference/complete_pipeline.py
- **Chat_Interface**: The main user interface component for question-answering
- **Status_Dashboard**: The system monitoring component showing database and model status
- **Session_State**: Streamlit's session state for managing chat history and component state
- **Subject_Filter**: Filter for educational subjects (Matematika, IPA, Bahasa Indonesia, Informatika, Semua)

## Requirements

### Requirement 1: Chat Interface

**User Story:** As a teacher or student, I want to ask questions in Indonesian and receive answers with source citations, so that I can learn from the offline AI tutor.

#### Acceptance Criteria

1. WHEN the application starts, THE Chat_Interface SHALL display an empty message history and an input field
2. WHEN a user submits a question, THE System SHALL display the question in the chat history immediately
3. WHEN the RAG_Pipeline processes a query, THE System SHALL stream the response in real-time to the chat interface
4. WHEN a response is complete, THE System SHALL display source citations including book name and subject
5. WHEN a user selects a subject filter, THE System SHALL pass the filter to the RAG_Pipeline for context retrieval

### Requirement 2: Session Management

**User Story:** As a user, I want my chat history to persist during my session, so that I can review previous questions and answers.

#### Acceptance Criteria

1. WHEN a user submits a question, THE System SHALL append the question and response to the session chat history
2. WHEN the application reloads, THE System SHALL restore the chat history from Session_State
3. WHEN chat history exceeds 50 messages, THE System SHALL maintain all messages in scrollable view
4. THE System SHALL store chat history only in Session_State without persisting to disk

### Requirement 3: System Status Monitoring

**User Story:** As a user, I want to see the system status, so that I know if the database and model are ready.

#### Acceptance Criteria

1. WHEN the application starts, THE Status_Dashboard SHALL display the database loading status
2. WHEN the application starts, THE Status_Dashboard SHALL display the model loading status
3. WHEN the Inference_Engine is loaded, THE Status_Dashboard SHALL show "Model: Ready" with a green indicator
4. WHEN the Vector_DB is loaded, THE Status_Dashboard SHALL show "Database: Loaded" with document count
5. WHEN memory usage exceeds 2.5GB, THE Status_Dashboard SHALL display a warning indicator

### Requirement 4: Offline-First Initialization

**User Story:** As a user, I want the application to initialize automatically on first run, so that I can start using it without manual setup.

#### Acceptance Criteria

1. WHEN the application starts for the first time, THE System SHALL initialize the Complete_Pipeline automatically
2. WHEN the Vector_DB collection does not exist, THE System SHALL display an error message in Indonesian
3. WHEN the model file is missing, THE System SHALL display an error message with the expected file path
4. WHEN initialization fails, THE System SHALL display the error reason in Indonesian and provide recovery suggestions
5. THE System SHALL complete initialization within 30 seconds on a 4GB RAM system

### Requirement 5: Performance Optimization

**User Story:** As a user on a 4GB RAM laptop, I want the application to use memory efficiently, so that it runs smoothly without crashing.

#### Acceptance Criteria

1. WHEN the application initializes, THE System SHALL use lazy loading for the Inference_Engine
2. WHEN the application initializes, THE System SHALL use lazy loading for the Vector_DB
3. WHEN the application is idle, THE System SHALL maintain memory usage below 3GB
4. WHEN processing a query, THE System SHALL stream responses to avoid blocking the UI
5. THE System SHALL reuse the same Complete_Pipeline instance across all queries in a session

### Requirement 6: Educational Features

**User Story:** As a student, I want to see which books my answers come from, so that I can reference the original material.

#### Acceptance Criteria

1. WHEN a response is generated, THE System SHALL display source book filenames below the answer
2. WHEN a response is generated, THE System SHALL display the subject for each source
3. WHEN a response is generated, THE System SHALL display relevance scores for each source
4. WHEN a user clicks a copy button, THE System SHALL copy the response text to clipboard
5. THE System SHALL format source citations as "📚 [Subject] - [Filename] (Relevance: [Score])"

### Requirement 7: Error Handling

**User Story:** As a user, I want clear error messages in Indonesian, so that I understand what went wrong and how to fix it.

#### Acceptance Criteria

1. WHEN the Vector_DB is empty, THE System SHALL display "Database kosong. Silakan jalankan pipeline ETL terlebih dahulu."
2. WHEN the model fails to load, THE System SHALL display "Model gagal dimuat. Periksa file model di [path]."
3. WHEN a query fails, THE System SHALL display "Terjadi kesalahan. Silakan coba lagi."
4. WHEN memory is insufficient, THE System SHALL display "Memori tidak cukup. Tutup aplikasi lain dan coba lagi."
5. WHEN an error occurs, THE System SHALL log the full error details to the console for debugging

### Requirement 8: Subject Filtering

**User Story:** As a user, I want to filter questions by subject, so that I get more relevant answers from specific subjects.

#### Acceptance Criteria

1. WHEN the application starts, THE System SHALL display a subject filter dropdown with options: "Semua", "Matematika", "IPA", "Bahasa Indonesia", "Informatika"
2. WHEN a user selects "Semua", THE System SHALL query all subjects in the Vector_DB
3. WHEN a user selects a specific subject, THE System SHALL pass the subject filter to the RAG_Pipeline
4. WHEN the subject filter changes, THE System SHALL apply the filter to subsequent queries only
5. THE System SHALL display the active subject filter in the chat interface

### Requirement 9: Response Streaming

**User Story:** As a user, I want to see responses appear gradually, so that I know the system is working and don't have to wait for the complete answer.

#### Acceptance Criteria

1. WHEN the Inference_Engine generates a response, THE System SHALL display each token as it is generated
2. WHEN streaming is active, THE System SHALL show a typing indicator
3. WHEN streaming completes, THE System SHALL remove the typing indicator
4. WHEN streaming fails, THE System SHALL display the partial response and an error message
5. THE System SHALL update the UI at least every 100ms during streaming

### Requirement 10: UI Layout and Design

**User Story:** As a user, I want a clean and simple interface, so that I can focus on learning without distractions.

#### Acceptance Criteria

1. THE System SHALL use a sidebar for the Status_Dashboard and subject filter
2. THE System SHALL use the main area for the Chat_Interface
3. THE System SHALL display messages with alternating background colors for user and assistant
4. THE System SHALL use Indonesian language for all UI labels and messages
5. THE System SHALL display the application title "OpenClass Nexus AI - Tutor Offline" at the top
