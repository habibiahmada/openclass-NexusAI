-- OpenClass Nexus AI - PostgreSQL Database Schema
-- Architecture Alignment Refactoring - Phase 2
-- This schema supports the pedagogical engine and persistence requirements

-- ============================================================================
-- CORE USER MANAGEMENT
-- ============================================================================

-- Users table
-- Stores user accounts for students, teachers, and administrators
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- SHA256 hashed passwords
    role VARCHAR(20) NOT NULL CHECK (role IN ('siswa', 'guru', 'admin')),
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table
-- Manages user authentication tokens with 24-hour expiration
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CURRICULUM MANAGEMENT
-- ============================================================================

-- Subjects table (Dynamic subjects)
-- Stores subject metadata for grades 10-12
CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    grade INTEGER NOT NULL CHECK (grade BETWEEN 10 AND 12),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,  -- e.g., "MAT_10", "INF_11"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Books table (Dynamic curriculum)
-- Tracks curriculum books and their VKP versions
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    filename VARCHAR(255),
    vkp_version VARCHAR(20),  -- Semantic versioning (e.g., "1.2.0")
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CHAT HISTORY AND INTERACTIONS
-- ============================================================================

-- Chat history table
-- Persists all student-AI interactions for learning analytics
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    confidence FLOAT,  -- LLM confidence score (0.0 to 1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PEDAGOGICAL INTELLIGENCE ENGINE
-- ============================================================================

-- Topic mastery tracking
-- Tracks student mastery levels per topic (0.0 = novice, 1.0 = expert)
CREATE TABLE topic_mastery (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    mastery_level FLOAT DEFAULT 0.0 CHECK (mastery_level BETWEEN 0.0 AND 1.0),
    question_count INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    last_interaction TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, subject_id, topic)  -- One mastery record per user-subject-topic
);

-- Weak areas detection
-- Identifies topics where students need additional practice
CREATE TABLE weak_areas (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    weakness_score FLOAT,  -- Higher score = weaker understanding
    recommended_practice TEXT,  -- Suggested practice activities
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Practice questions
-- Stores adaptive practice questions for weak area reinforcement
CREATE TABLE practice_questions (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Chat history indexes for fast retrieval
CREATE INDEX idx_chat_history_user ON chat_history(user_id);
CREATE INDEX idx_chat_history_created ON chat_history(created_at);
CREATE INDEX idx_chat_history_subject ON chat_history(subject_id);

-- Session management indexes
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- Pedagogical engine indexes
CREATE INDEX idx_topic_mastery_user_subject ON topic_mastery(user_id, subject_id);
CREATE INDEX idx_weak_areas_user_subject ON weak_areas(user_id, subject_id);
CREATE INDEX idx_practice_questions_subject_topic ON practice_questions(subject_id, topic);

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE users IS 'User accounts for students, teachers, and administrators';
COMMENT ON TABLE sessions IS 'Authentication tokens with 24-hour expiration';
COMMENT ON TABLE subjects IS 'Dynamic subject metadata for grades 10-12';
COMMENT ON TABLE books IS 'Curriculum books with VKP version tracking';
COMMENT ON TABLE chat_history IS 'Complete history of student-AI interactions';
COMMENT ON TABLE topic_mastery IS 'Student mastery levels per topic (0.0-1.0 scale)';
COMMENT ON TABLE weak_areas IS 'Detected weak areas requiring practice';
COMMENT ON TABLE practice_questions IS 'Adaptive practice questions for reinforcement';

COMMENT ON COLUMN users.password_hash IS 'SHA256 hashed password for security';
COMMENT ON COLUMN users.role IS 'User role: siswa (student), guru (teacher), or admin';
COMMENT ON COLUMN sessions.expires_at IS 'Session expiration timestamp (24 hours from creation)';
COMMENT ON COLUMN books.vkp_version IS 'Versioned Knowledge Package version (semantic versioning)';
COMMENT ON COLUMN chat_history.confidence IS 'LLM confidence score (0.0 to 1.0)';
COMMENT ON COLUMN topic_mastery.mastery_level IS 'Mastery score: 0.0 (novice) to 1.0 (expert)';
COMMENT ON COLUMN weak_areas.weakness_score IS 'Weakness score: higher values indicate greater need for practice';
COMMENT ON COLUMN practice_questions.difficulty IS 'Question difficulty: easy, medium, or hard';
