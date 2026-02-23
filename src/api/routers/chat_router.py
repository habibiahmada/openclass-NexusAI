"""
Chat Router
Handles student chat interactions with AI tutor
"""

import logging
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Dict

from ..models import ChatRequest, ChatResponse
from ..state import AppState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def create_chat_router(state: AppState, verify_token_dependency):
    """Create chat router with dependencies"""
    
    @router.post("", response_model=ChatResponse)
    async def chat(request: ChatRequest, token_data: Dict = Depends(verify_token_dependency)):
        """Main chat endpoint for student mode"""
        start_time = datetime.now()
        
        if not state.is_initialized:
            return ChatResponse(
                response=(
                    "⚠️ Sistem AI belum diinisialisasi.\n\n"
                    "Untuk menggunakan AI Tutor, jalankan setup berikut:\n\n"
                    "1. Process dokumen pembelajaran:\n"
                    "   python scripts/run_etl_pipeline.py\n\n"
                    "2. Download model AI (~2GB):\n"
                    "   python scripts/download_model.py\n\n"
                    "3. Check status sistem:\n"
                    "   python scripts/check_system_ready.py\n\n"
                    "4. Restart web server\n\n"
                ),
                source="Demo Mode",
                confidence=0.0
            )
        
        # Check if concurrency manager is available
        if not state.concurrency_initialized:
            logger.warning("Concurrency manager not available - processing without queue")
            return await _process_chat_without_queue(request, token_data, state)
        
        try:
            # Get subject_id from subject_filter
            subject_id = _get_subject_id(request.subject_filter, state)
            
            # Check if queue is full
            if state.concurrency_manager.is_queue_full():
                stats = state.concurrency_manager.get_queue_stats()
                estimated_wait = (stats.queued_count * 5) // 60
                raise HTTPException(
                    status_code=503,
                    detail=f"Server sedang penuh. Estimasi waktu tunggu: {estimated_wait} menit."
                )
            
            # Process with pipeline
            result = state.pipeline.process_query(
                query=request.message,
                subject_filter=request.subject_filter if request.subject_filter != "all" else None
            )
            
            # Save to database
            _save_chat_to_database(request, result, token_data, subject_id, state)
            
            # Extract source information
            source = None
            if result.sources:
                source = ", ".join([s.get("title", "Unknown") for s in result.sources[:2]])
            
            # Record telemetry
            _record_telemetry(start_time, True, state)
            
            return ChatResponse(
                response=result.response,
                source=source,
                confidence=0.0
            )
            
        except HTTPException:
            _record_telemetry(start_time, False, state)
            raise
        except Exception as e:
            logger.error(f"Error processing chat: {e}", exc_info=True)
            _record_telemetry(start_time, False, state)
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/stream")
    async def chat_stream(request: ChatRequest, token_data: Dict = Depends(verify_token_dependency)):
        """Streaming chat endpoint with SSE"""
        if not state.is_initialized:
            async def demo_stream():
                yield 'data: {"error": "Sistema AI belum diinisialisasi"}\n\n'
            
            return StreamingResponse(
                demo_stream(),
                media_type="text/event-stream"
            )
        
        if not state.concurrency_initialized:
            result = await chat(request, token_data)
            
            async def fallback_stream():
                yield f'data: {{"token": "{result.response}"}}\n\n'
                yield 'data: {"done": true}\n\n'
            
            return StreamingResponse(
                fallback_stream(),
                media_type="text/event-stream"
            )
        
        try:
            subject_id = _get_subject_id(request.subject_filter, state)
            
            # Check if queue is full
            if state.concurrency_manager.is_queue_full():
                async def queue_full_stream():
                    yield 'data: {"error": "Server sedang penuh"}\n\n'
                
                return StreamingResponse(
                    queue_full_stream(),
                    media_type="text/event-stream",
                    status_code=503
                )
            
            # Stream response
            async def stream_with_queue():
                # Process query
                result = state.pipeline.process_query(
                    query=request.message,
                    subject_filter=request.subject_filter if request.subject_filter != "all" else None
                )
                
                # Stream the response
                for char in result.response:
                    yield state.token_streamer.format_sse(char, "stream")
                    await asyncio.sleep(0.01)
                
                yield state.token_streamer.format_sse_complete("stream")
                
                # Save to database
                _save_chat_to_database(request, result, token_data, subject_id, state)
            
            return StreamingResponse(
                stream_with_queue(),
                media_type="text/event-stream"
            )
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}", exc_info=True)
            
            async def error_stream():
                yield f'data: {{"error": "{str(e)}"}}\n\n'
            
            return StreamingResponse(
                error_stream(),
                media_type="text/event-stream",
                status_code=500
            )
    
    return router


async def _process_chat_without_queue(request: ChatRequest, token_data: Dict, state: AppState):
    """Fallback function to process chat without concurrency management"""
    start_time = datetime.now()
    
    try:
        result = state.pipeline.process_query(
            query=request.message,
            subject_filter=request.subject_filter if request.subject_filter != "all" else None
        )
        
        subject_id = _get_subject_id(request.subject_filter, state)
        _save_chat_to_database(request, result, token_data, subject_id, state)
        
        source = None
        if result.sources:
            source = ", ".join([s.get("title", "Unknown") for s in result.sources[:2]])
        
        _record_telemetry(start_time, True, state)
        
        return ChatResponse(
            response=result.response,
            source=source,
            confidence=0.0
        )
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        _record_telemetry(start_time, False, state)
        raise HTTPException(status_code=500, detail=str(e))


def _get_subject_id(subject_filter: str, state: AppState):
    """Get subject ID from subject filter"""
    if not subject_filter or subject_filter == "all":
        return None
    
    if state.subject_repo:
        try:
            subjects = state.subject_repo.get_all_subjects()
            for subject in subjects:
                if subject.name.lower() == subject_filter.lower():
                    return subject.id
        except Exception as e:
            logger.warning(f"Failed to get subject: {e}")
    
    return None


def _save_chat_to_database(request: ChatRequest, result, token_data: Dict, subject_id, state: AppState):
    """Save chat to database and process with pedagogical engine"""
    if not state.db_initialized or not state.chat_history_repo:
        return
    
    try:
        subject_name = 'informatika'
        
        if request.subject_filter and request.subject_filter != "all":
            subject_name = request.subject_filter
        
        state.chat_history_repo.save_chat(
            user_id=token_data['user_id'],
            subject_id=subject_id,
            question=request.message,
            response=result.response,
            confidence=0.0
        )
        
        logger.info(f"Chat saved to database for user_id={token_data['user_id']}")
        
        # Process with pedagogical engine
        if state.pedagogy_initialized and state.pedagogical_integration:
            try:
                pedagogical_result = state.pedagogical_integration.process_student_question(
                    user_id=token_data['user_id'],
                    subject_id=subject_id or 1,
                    question=request.message,
                    subject_name=subject_name,
                    suggest_practice=False
                )
                
                if pedagogical_result['success']:
                    logger.info(
                        f"Pedagogical tracking updated: "
                        f"topic={pedagogical_result['topic']}, "
                        f"mastery={pedagogical_result['mastery_level']:.2f}"
                    )
            except Exception as e:
                logger.error(f"Failed to process pedagogical tracking: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Failed to save chat: {e}", exc_info=True)


def _record_telemetry(start_time: datetime, success: bool, state: AppState):
    """Record telemetry metrics"""
    if not state.telemetry_initialized or not state.telemetry_collector:
        return
    
    try:
        latency = (datetime.now() - start_time).total_seconds() * 1000
        state.telemetry_collector.record_query(latency=latency, success=success)
        
        if not success:
            state.telemetry_collector.record_error(
                error_type="processing_error",
                error_message="Chat processing failed"
            )
    except Exception as e:
        logger.error(f"Failed to record telemetry: {e}")
