# Changelog

All notable changes to OpenClass Nexus AI will be documented in this file.

## [Unreleased]

### Changed
- Reorganized documentation structure
- Moved all .md files from root to docs/ folder
- Cleaned up scripts/ folder, removed one-time use scripts
- Simplified project structure

### Added
- docs/guides/ folder for user guides
- docs/technical/ folder for technical documentation
- Comprehensive docs/README.md as documentation index
- CONTRIBUTING.md for contribution guidelines
- CHANGELOG.md for tracking changes

### Removed
- 14 redundant .md files from root folder
- 13 one-time use scripts from scripts/ folder
- optimization_output/ folder
- test_*.py files from root

## [Phase 3] - 2026-02-19

### Added
- Web UI with role-based access (Siswa, Guru, Admin)
- FastAPI backend server
- Authentication system
- Multi-user support

### Changed
- Migrated from Streamlit to Web UI
- Improved system architecture for school deployment

## [Phase 2] - 2026-02-18

### Added
- AWS Bedrock integration for embeddings
- S3 storage support
- Cloud embedding pipeline
- Local embedding fallback

## [Phase 1] - 2026-02-17

### Added
- Initial project setup
- ETL pipeline for PDF processing
- RAG pipeline implementation
- Local inference with llama.cpp
- ChromaDB vector database integration
