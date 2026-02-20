# 🐛 Bug Fixes Log

Catatan bug fixes yang telah diterapkan.

## 2026-02-20

### Frontend File Structure
- **File**: `scripts/start_web_ui.py`
- **Fix**: Updated to check for `css/` and `js/` folders

### API Server Initialization
- **File**: `api_server.py`
- **Fix**: Changed to use CompletePipeline
- **Fix**: Updated model cache directory to `./models`

### ChromaDB Initialization
- **Files**: `src/local_inference/complete_pipeline.py`, `scripts/check_system_ready.py`
- **Fix**: Changed parameter from `db_path` to `persist_directory`

### Model Path Method
- **File**: `src/local_inference/complete_pipeline.py`
- **Fix**: Changed `get_local_path()` to `get_model_path()`

### Memory Monitor
- **File**: `src/local_inference/complete_pipeline.py`
- **Fix**: Changed `get_available_memory()` to `get_system_memory().available_mb`

### Memory Requirements
- **File**: `src/local_inference/inference_engine.py`
- **Fix**: Lowered memory check threshold for memory-mapped models
