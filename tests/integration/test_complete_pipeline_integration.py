"""
Integration tests for the complete inference pipeline.

This module tests end-to-end query processing, offline functionality,
and performance under load for the complete Phase 3 pipeline integration.
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
import threading
import concurrent.futures

# Import the components we're testing
from src.local_inference.complete_pipeline import CompletePipeline, PipelineConfig
from src.local_inference.performance_benchmarking import (
    PerformanceBenchmarkRunner, IndonesianEducationalBenchmarks, run_quick_benchmark
)
from src.local_inference.batch_processor import QueryPriority
from src.embeddings.chroma_manager import ChromaDBManager


class TestCompletePipelineIntegration:
    """Integration tests for the complete inference pipeline."""
    
    @pytest.fixture
    def temp_directories(self):
        """Create temporary directories for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        model_dir = temp_dir / "models"
        chroma_dir = temp_dir / "chroma"
        
        model_dir.mkdir(parents=True)
        chroma_dir.mkdir(parents=True)
        
        yield {
            'temp_dir': temp_dir,
            'model_dir': model_dir,
            'chroma_dir': chroma_dir
        }
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_pipeline_config(self, temp_directories):
        """Create a mock pipeline configuration for testing."""
        return PipelineConfig(
            model_cache_dir=str(temp_directories['model_dir']),
            chroma_db_path=str(temp_directories['chroma_dir']),
            memory_limit_mb=2048,  # Lower for testing
            max_concurrent_queries=2,
            enable_performance_monitoring=True,
            enable_batch_processing=True,
            enable_graceful_degradation=False,  # Disable for simpler testing
            enable_educational_validation=False,  # Disable for simpler testing
            log_level="DEBUG"
        )
    
    @pytest.fixture
    def mock_inference_engine(self):
        """Create a mock inference engine for testing."""
        mock_engine = Mock()
        mock_engine.is_loaded = True
        mock_engine.load_model.return_value = True
        mock_engine.unload_model.return_value = None
        
        # Mock response generation
        def mock_generate_response(prompt, **kwargs):
            # Simulate realistic response generation
            response_text = f"Jawaban untuk pertanyaan: {prompt[:50]}... "
            response_text += "Ini adalah penjelasan edukatif dalam bahasa Indonesia. "
            response_text += "Konsep ini penting untuk dipahami dalam konteks pembelajaran."
            
            # Yield response in chunks to simulate streaming
            words = response_text.split()
            for word in words:
                yield word + " "
                time.sleep(0.001)  # Small delay to simulate processing
        
        mock_engine.generate_response = mock_generate_response
        
        # Mock metrics
        mock_engine.get_metrics.return_value = {
            'is_loaded': True,
            'memory_usage_mb': 1500.0,
            'cpu_usage_percent': 45.0,
            'available_memory_mb': 2048.0,
            'model_path': '/mock/model/path',
            'config': {}
        }
        
        return mock_engine
    
    @pytest.fixture
    def mock_vector_db(self, temp_directories):
        """Create a mock vector database for testing."""
        mock_db = Mock(spec=ChromaDBManager)
        mock_db.count_documents.return_value = 100
        
        # Mock search results
        def mock_query(query_embedding, n_results=5):
            # Return mock search results
            mock_results = []
            for i in range(min(n_results, 3)):  # Return up to 3 results
                mock_result = Mock()
                mock_result.content = f"Konten edukatif {i+1} yang relevan dengan query"
                mock_result.metadata = {
                    'source_file': f'document_{i+1}.pdf',
                    'subject': 'informatika',
                    'grade': 'kelas_10',
                    'chunk_index': i
                }
                mock_result.relevance_score = 0.9 - (i * 0.1)
                mock_results.append(mock_result)
            return mock_results
        
        mock_db.query = mock_query
        mock_db.get_collection.return_value = Mock()
        
        return mock_db
    
    def test_end_to_end_query_processing(self, mock_pipeline_config, temp_directories, mock_inference_engine, mock_vector_db):
        """Test complete end-to-end query processing through the pipeline."""
        # Create pipeline with mocked components
        pipeline = CompletePipeline(mock_pipeline_config)
        
        # Mock the initialization methods to avoid real model loading
        with patch.object(pipeline, '_initialize_model_management') as mock_init_model, \
             patch.object(pipeline, '_initialize_inference_engine') as mock_init_engine, \
             patch.object(pipeline, '_initialize_vector_database') as mock_init_db, \
             patch.object(pipeline, '_initialize_rag_pipeline') as mock_init_rag:
            
            # Setup required attributes that would be set during initialization
            from src.local_inference.model_config import ModelConfig, InferenceConfig
            pipeline.model_config = ModelConfig()
            pipeline.inference_configs = {"default": InferenceConfig()}
            
            # Setup mocks
            pipeline.inference_engine = mock_inference_engine
            pipeline.vector_db = mock_vector_db
            
            # Mock RAG pipeline
            mock_rag = Mock()
            def mock_process_query(query, **kwargs):
                mock_result = Mock()
                mock_result.response = f"Penjelasan edukatif untuk: {query}"
                mock_result.processing_time_ms = 2500.0
                mock_result.context_stats = {
                    'context_tokens': len(query.split()) * 2,
                    'total_documents': 3
                }
                mock_result.sources = [
                    {'filename': 'doc1.pdf', 'subject': 'informatika', 'relevance_score': 0.9}
                ]
                mock_result.is_fallback = False
                return mock_result
            
            mock_rag.process_query = mock_process_query
            pipeline.rag_pipeline = mock_rag
            
            # Initialize and start pipeline
            assert pipeline.initialize() == True
            assert pipeline.start() == True
            
            try:
                # Test basic query processing
                test_queries = [
                    "Apa itu algoritma dalam informatika?",
                    "Jelaskan konsep variabel dalam pemrograman!",
                    "Bagaimana cara kerja struktur data array?"
                ]
                
                results = []
                for query in test_queries:
                    result = pipeline.process_query(query, subject_filter="informatika")
                    results.append(result)
                    
                    # Verify result structure
                    assert hasattr(result, 'response')
                    assert hasattr(result, 'processing_time_ms')
                    assert result.response is not None
                    assert len(result.response) > 0
                    assert result.processing_time_ms > 0
                    
                    # Verify Indonesian educational content
                    assert "penjelasan" in result.response.lower() or "edukatif" in result.response.lower()
                
                # Verify all queries were processed
                assert len(results) == len(test_queries)
                
                # Test pipeline status
                status = pipeline.get_pipeline_status()
                assert status['pipeline']['running'] == True
                assert status['pipeline']['initialized'] == True
                assert status['components']['inference_engine'] == True
                assert status['components']['rag_pipeline'] == True
                
                # Test health check
                health = pipeline.get_health_check()
                assert health['overall_status'] in ['healthy', 'warning']
                assert health['checks']['pipeline_running'] == True
                
            finally:
                pipeline.stop()
    
    def test_offline_functionality(self, mock_pipeline_config, temp_directories, mock_inference_engine, mock_vector_db):
        """Test that the pipeline works completely offline."""
        pipeline = CompletePipeline(mock_pipeline_config)
        
        # Mock all external dependencies to simulate offline mode
        with patch.object(pipeline, '_initialize_model_management') as mock_init_model, \
             patch.object(pipeline, '_initialize_inference_engine') as mock_init_engine, \
             patch.object(pipeline, '_initialize_vector_database') as mock_init_db, \
             patch('src.embeddings.bedrock_client.BedrockEmbeddingsClient') as mock_bedrock:
            
            # Setup required attributes that would be set during initialization
            from src.local_inference.model_config import ModelConfig, InferenceConfig
            pipeline.model_config = ModelConfig()
            pipeline.inference_configs = {"default": InferenceConfig()}
            
            # Simulate Bedrock being unavailable (offline)
            mock_bedrock.side_effect = Exception("Network unavailable")
            
            # Setup offline-capable mocks
            pipeline.inference_engine = mock_inference_engine
            pipeline.vector_db = mock_vector_db
            pipeline.embeddings_client = None  # No cloud embeddings
            
            # Mock RAG pipeline for offline operation
            mock_rag = Mock()
            def mock_offline_process_query(query, **kwargs):
                # Simulate offline processing with local embeddings
                mock_result = Mock()
                mock_result.response = f"Offline response: {query} - Penjelasan menggunakan knowledge base lokal."
                mock_result.processing_time_ms = 3000.0
                mock_result.context_stats = {'context_tokens': 50, 'total_documents': 2}
                mock_result.sources = [{'filename': 'local_doc.pdf', 'subject': 'informatika'}]
                mock_result.is_fallback = False
                return mock_result
            
            mock_rag.process_query = mock_offline_process_query
            pipeline.rag_pipeline = mock_rag
            
            # Initialize and test offline functionality
            assert pipeline.initialize() == True
            assert pipeline.start() == True
            
            try:
                # Test offline query processing
                offline_query = "Jelaskan konsep pemrograman dalam mode offline!"
                result = pipeline.process_query(offline_query)
                
                # Verify offline processing works
                assert result is not None
                assert "offline" in result.response.lower() or "lokal" in result.response.lower()
                assert result.processing_time_ms > 0
                
                # Verify no external dependencies were used
                assert pipeline.embeddings_client is None
                
                # Test multiple offline queries
                offline_queries = [
                    "Apa itu array dalam pemrograman?",
                    "Bagaimana cara kerja algoritma sorting?",
                    "Jelaskan konsep rekursi!"
                ]
                
                offline_results = []
                for query in offline_queries:
                    result = pipeline.process_query(query)
                    offline_results.append(result)
                    assert result.response is not None
                
                assert len(offline_results) == len(offline_queries)
                
            finally:
                pipeline.stop()
    
    def test_performance_under_load(self, mock_pipeline_config, temp_directories, mock_inference_engine, mock_vector_db):
        """Test pipeline performance under concurrent load."""
        # Configure for load testing
        load_config = mock_pipeline_config
        load_config.max_concurrent_queries = 3
        load_config.enable_batch_processing = True
        
        pipeline = CompletePipeline(load_config)
        
        # Mock components for load testing
        with patch.object(pipeline, '_initialize_model_management') as mock_init_model, \
             patch.object(pipeline, '_initialize_inference_engine') as mock_init_engine, \
             patch.object(pipeline, '_initialize_vector_database') as mock_init_db:
            
            # Setup required attributes that would be set during initialization
            from src.local_inference.model_config import ModelConfig, InferenceConfig
            pipeline.model_config = ModelConfig()
            pipeline.inference_configs = {"default": InferenceConfig()}
            
            # Setup performance-oriented mocks
            pipeline.inference_engine = mock_inference_engine
            pipeline.vector_db = mock_vector_db
            
            # Mock RAG pipeline with performance tracking
            mock_rag = Mock()
            processed_queries = []
            processing_times = []
            
            def mock_load_process_query(query, **kwargs):
                start_time = time.time()
                processed_queries.append(query)
                
                # Simulate variable processing time
                processing_delay = 0.1 + (len(processed_queries) % 3) * 0.05
                time.sleep(processing_delay)
                
                end_time = time.time()
                processing_time = (end_time - start_time) * 1000
                processing_times.append(processing_time)
                
                mock_result = Mock()
                mock_result.response = f"Load test response {len(processed_queries)}: {query}"
                mock_result.processing_time_ms = processing_time
                mock_result.context_stats = {'context_tokens': 40, 'total_documents': 2}
                mock_result.sources = []
                mock_result.is_fallback = False
                return mock_result
            
            mock_rag.process_query = mock_load_process_query
            pipeline.rag_pipeline = mock_rag
            
            # Initialize pipeline
            assert pipeline.initialize() == True
            assert pipeline.start() == True
            
            try:
                # Generate load test queries
                load_queries = [
                    f"Query {i}: Jelaskan konsep {concept} dalam informatika!"
                    for i, concept in enumerate([
                        "algoritma", "struktur data", "pemrograman", "database",
                        "jaringan", "keamanan", "AI", "machine learning",
                        "web development", "mobile development"
                    ])
                ]
                
                # Test concurrent processing
                start_time = time.time()
                
                # Submit queries concurrently using batch processing
                query_ids = []
                for query in load_queries:
                    query_id = pipeline.process_query(
                        query, 
                        priority=QueryPriority.NORMAL,
                        use_batch_processing=True
                    )
                    query_ids.append(query_id)
                
                # Wait for all queries to complete
                completed_results = []
                max_wait_time = 30.0  # 30 seconds max wait
                wait_start = time.time()
                
                while len(completed_results) < len(query_ids) and (time.time() - wait_start) < max_wait_time:
                    for query_id in query_ids:
                        if query_id not in [r.get('query_id') for r in completed_results]:
                            result = pipeline.get_batch_result(query_id, timeout=0.1)
                            if result and result.get('success'):
                                completed_results.append(result)
                    time.sleep(0.1)
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # Verify load test results
                assert len(completed_results) > 0, "No queries completed during load test"
                
                # Calculate performance metrics
                if completed_results:
                    avg_response_time = sum(r['processing_time_ms'] for r in completed_results) / len(completed_results)
                    throughput = len(completed_results) / total_time
                    
                    # Performance assertions
                    assert avg_response_time < 10000, f"Average response time too high: {avg_response_time}ms"
                    assert throughput > 0.1, f"Throughput too low: {throughput} queries/sec"
                
                # Test pipeline status under load
                status = pipeline.get_pipeline_status()
                assert status['pipeline']['running'] == True
                
                if 'batch_processing' in status:
                    batch_status = status['batch_processing']
                    # Verify batch processing handled the load
                    assert batch_status['processing_active'] == True
                
                # Test health check under load
                health = pipeline.get_health_check()
                assert health['overall_status'] in ['healthy', 'warning']
                
            finally:
                pipeline.stop()
    
    def test_pipeline_error_handling(self, mock_pipeline_config, temp_directories, mock_vector_db):
        """Test pipeline error handling and recovery."""
        pipeline = CompletePipeline(mock_pipeline_config)
        
        with patch.object(pipeline, '_initialize_model_management') as mock_init_model, \
             patch.object(pipeline, '_initialize_inference_engine') as mock_init_engine, \
             patch.object(pipeline, '_initialize_vector_database') as mock_init_db:
            
            # Setup required attributes that would be set during initialization
            from src.local_inference.model_config import ModelConfig, InferenceConfig
            pipeline.model_config = ModelConfig()
            pipeline.inference_configs = {"default": InferenceConfig()}
            
            # Setup mocks that can simulate errors
            mock_inference_engine = Mock()
            mock_inference_engine.is_loaded = True
            mock_inference_engine.load_model.return_value = True
            
            # Mock that sometimes fails
            call_count = 0
            def mock_generate_with_errors(prompt, **kwargs):
                nonlocal call_count
                call_count += 1
                
                if call_count % 3 == 0:  # Every 3rd call fails
                    raise RuntimeError("Simulated inference error")
                
                # Normal response
                yield f"Response for: {prompt[:30]}..."
            
            mock_inference_engine.generate_response = mock_generate_with_errors
            mock_inference_engine.get_metrics.return_value = {'memory_usage_mb': 1500}
            
            pipeline.inference_engine = mock_inference_engine
            pipeline.vector_db = mock_vector_db
            
            # Mock RAG pipeline with error handling
            mock_rag = Mock()
            def mock_error_prone_process_query(query, **kwargs):
                try:
                    # This will sometimes fail due to mock_generate_with_errors
                    response_chunks = list(pipeline.inference_engine.generate_response(query))
                    response = ''.join(response_chunks)
                    
                    mock_result = Mock()
                    mock_result.response = response
                    mock_result.processing_time_ms = 1500.0
                    mock_result.context_stats = {'context_tokens': 30}
                    mock_result.sources = []
                    mock_result.is_fallback = False
                    return mock_result
                    
                except Exception as e:
                    # Return fallback result
                    mock_result = Mock()
                    mock_result.response = "Maaf, terjadi kesalahan. Silakan coba lagi."
                    mock_result.processing_time_ms = 100.0
                    mock_result.context_stats = {'context_tokens': 0}
                    mock_result.sources = []
                    mock_result.is_fallback = True
                    return mock_result
            
            mock_rag.process_query = mock_error_prone_process_query
            pipeline.rag_pipeline = mock_rag
            
            # Initialize pipeline
            assert pipeline.initialize() == True
            assert pipeline.start() == True
            
            try:
                # Test error handling
                test_queries = [
                    "Query 1: Test normal processing",
                    "Query 2: Test normal processing", 
                    "Query 3: This should trigger an error",
                    "Query 4: Test recovery after error",
                    "Query 5: Test normal processing",
                    "Query 6: This should trigger another error"
                ]
                
                results = []
                successful_queries = 0
                fallback_responses = 0
                
                for query in test_queries:
                    try:
                        result = pipeline.process_query(query)
                        results.append(result)
                        
                        if hasattr(result, 'is_fallback') and result.is_fallback:
                            fallback_responses += 1
                        else:
                            successful_queries += 1
                            
                    except Exception as e:
                        # Pipeline should handle errors gracefully
                        pytest.fail(f"Pipeline should handle errors gracefully, but got: {e}")
                
                # Verify error handling
                assert len(results) == len(test_queries), "All queries should return some result"
                assert successful_queries > 0, "Some queries should succeed"
                assert fallback_responses > 0, "Some queries should trigger fallback responses"
                
                # Verify pipeline remains operational after errors
                status = pipeline.get_pipeline_status()
                assert status['pipeline']['running'] == True
                
                # Test recovery with a simple query
                recovery_result = pipeline.process_query("Simple recovery test query")
                assert recovery_result is not None
                
            finally:
                pipeline.stop()
    
    def test_benchmarking_integration(self, mock_pipeline_config, temp_directories, mock_inference_engine, mock_vector_db):
        """Test integration with performance benchmarking system."""
        pipeline = CompletePipeline(mock_pipeline_config)
        
        with patch.object(pipeline, '_initialize_model_management') as mock_init_model, \
             patch.object(pipeline, '_initialize_inference_engine') as mock_init_engine, \
             patch.object(pipeline, '_initialize_vector_database') as mock_init_db:
            
            # Setup required attributes that would be set during initialization
            from src.local_inference.model_config import ModelConfig, InferenceConfig
            pipeline.model_config = ModelConfig()
            pipeline.inference_configs = {"default": InferenceConfig()}
            
            # Setup mocks for benchmarking
            pipeline.inference_engine = mock_inference_engine
            pipeline.vector_db = mock_vector_db
            
            # Mock RAG pipeline for consistent benchmarking
            mock_rag = Mock()
            def mock_benchmark_process_query(query, **kwargs):
                # Simulate consistent processing for benchmarking
                processing_time = 1000 + len(query) * 10  # Predictable timing
                
                mock_result = Mock()
                mock_result.response = f"Benchmark response: {query} - Penjelasan edukatif lengkap."
                mock_result.processing_time_ms = processing_time
                mock_result.context_stats = {
                    'context_tokens': len(query.split()) * 2,
                    'total_documents': 3
                }
                mock_result.sources = [
                    {'filename': 'benchmark_doc.pdf', 'subject': 'informatika', 'relevance_score': 0.85}
                ]
                mock_result.is_fallback = False
                return mock_result
            
            mock_rag.process_query = mock_benchmark_process_query
            pipeline.rag_pipeline = mock_rag
            
            # Initialize pipeline
            assert pipeline.initialize() == True
            assert pipeline.start() == True
            
            try:
                # Test quick benchmark integration
                benchmark_result = run_quick_benchmark(pipeline)
                
                # Verify benchmark results
                assert benchmark_result is not None
                assert 'total_queries' in benchmark_result
                assert 'success_rate' in benchmark_result
                assert benchmark_result['total_queries'] > 0
                
                # Test full benchmark runner integration
                runner = PerformanceBenchmarkRunner(pipeline)
                generator = IndonesianEducationalBenchmarks()
                
                # Create a small test suite
                informatika_suite = generator.create_informatika_benchmark_suite()
                # Use only first 2 queries for faster testing
                informatika_suite.queries = informatika_suite.queries[:2]
                
                suite_result = runner.run_benchmark_suite(informatika_suite, concurrent_queries=1, warmup_queries=0)
                
                # Verify suite results
                assert suite_result is not None
                assert 'suite_name' in suite_result
                assert 'total_queries' in suite_result
                assert 'success_rate' in suite_result
                assert suite_result['total_queries'] == 2
                
                # Test report generation
                if runner.benchmark_results:
                    report = runner.generate_performance_report()
                    assert 'report_metadata' in report
                    assert 'executive_summary' in report
                    assert 'recommendations' in report
                
            finally:
                pipeline.stop()


if __name__ == "__main__":
    # Run a simple integration test
    print("Running simple integration test...")
    
    # Create temporary test setup
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        config = PipelineConfig(
            model_cache_dir=str(temp_dir / "models"),
            chroma_db_path=str(temp_dir / "chroma"),
            memory_limit_mb=2048,
            enable_performance_monitoring=True,
            enable_batch_processing=False,  # Disable for simple test
            enable_graceful_degradation=False,
            enable_educational_validation=False,
            log_level="INFO"
        )
        
        print(f"Test configuration: {config}")
        print("Integration tests are ready to run with pytest")
        print("These tests verify end-to-end pipeline functionality")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("Integration test setup completed successfully!")