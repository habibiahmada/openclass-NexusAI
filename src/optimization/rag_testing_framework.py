"""
RAG Pipeline Testing Framework for OpenClass Nexus AI Phase 3.

This module provides comprehensive testing capabilities for the RAG pipeline,
including educational content retrieval validation, source attribution verification,
and relevance scoring as specified in requirements 2.3 and 6.4.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json

from src.edge_runtime.rag_pipeline import RAGPipeline, QueryResult
from src.edge_runtime.educational_validator import EducationalContentValidator, EducationalValidationResult
from src.embeddings.chroma_manager import ChromaDBManager, SearchResult
from src.embeddings.bedrock_client import BedrockEmbeddingsClient

logger = logging.getLogger(__name__)


@dataclass
class RetrievalTestResult:
    """Result from RAG pipeline retrieval testing."""
    query: str
    retrieved_documents: List[SearchResult]
    retrieval_time_ms: float
    relevance_scores: List[float]
    source_attribution_accuracy: float
    curriculum_alignment_score: float
    average_relevance_score: float
    sources_found: List[str]
    test_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'query': self.query,
            'retrieved_documents_count': len(self.retrieved_documents),
            'retrieval_time_ms': self.retrieval_time_ms,
            'relevance_scores': self.relevance_scores,
            'source_attribution_accuracy': self.source_attribution_accuracy,
            'curriculum_alignment_score': self.curriculum_alignment_score,
            'average_relevance_score': self.average_relevance_score,
            'sources_found': self.sources_found,
            'test_timestamp': self.test_timestamp.isoformat()
        }


@dataclass
class SourceAttributionResult:
    """Result from source attribution verification."""
    query: str
    response: str
    context_sources: List[str]
    attributed_sources: List[str]
    attribution_accuracy: float
    missing_attributions: List[str]
    false_attributions: List[str]
    bse_kemdikbud_sources: List[str]
    proper_citation_format: bool
    test_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'query': self.query,
            'response_length': len(self.response),
            'context_sources_count': len(self.context_sources),
            'attributed_sources_count': len(self.attributed_sources),
            'attribution_accuracy': self.attribution_accuracy,
            'missing_attributions': self.missing_attributions,
            'false_attributions': self.false_attributions,
            'bse_kemdikbud_sources': self.bse_kemdikbud_sources,
            'proper_citation_format': self.proper_citation_format,
            'test_timestamp': self.test_timestamp.isoformat()
        }


@dataclass
class QualityAssessmentResult:
    """Result from content quality assessment."""
    query: str
    response: str
    relevance_score: float
    completeness_score: float
    accuracy_score: float
    age_appropriateness_score: float
    language_quality_score: float
    overall_quality_score: float
    quality_issues: List[str]
    quality_strengths: List[str]
    test_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'query': self.query,
            'response_length': len(self.response),
            'relevance_score': self.relevance_score,
            'completeness_score': self.completeness_score,
            'accuracy_score': self.accuracy_score,
            'age_appropriateness_score': self.age_appropriateness_score,
            'language_quality_score': self.language_quality_score,
            'overall_quality_score': self.overall_quality_score,
            'quality_issues_count': len(self.quality_issues),
            'quality_strengths_count': len(self.quality_strengths),
            'test_timestamp': self.test_timestamp.isoformat()
        }


@dataclass
class RAGTestingReport:
    """Comprehensive RAG pipeline testing report."""
    test_session_id: str
    test_timestamp: datetime
    total_queries_tested: int
    retrieval_tests: List[RetrievalTestResult]
    attribution_tests: List[SourceAttributionResult]
    quality_assessments: List[QualityAssessmentResult]
    
    # Summary metrics
    average_retrieval_time_ms: float = 0.0
    average_relevance_score: float = 0.0
    average_attribution_accuracy: float = 0.0
    average_quality_score: float = 0.0
    overall_test_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'test_session_id': self.test_session_id,
            'test_timestamp': self.test_timestamp.isoformat(),
            'summary': {
                'total_queries_tested': self.total_queries_tested,
                'average_retrieval_time_ms': self.average_retrieval_time_ms,
                'average_relevance_score': self.average_relevance_score,
                'average_attribution_accuracy': self.average_attribution_accuracy,
                'average_quality_score': self.average_quality_score,
                'overall_test_score': self.overall_test_score
            },
            'retrieval_tests': [test.to_dict() for test in self.retrieval_tests],
            'attribution_tests': [test.to_dict() for test in self.attribution_tests],
            'quality_assessments': [test.to_dict() for test in self.quality_assessments]
        }


class RAGPipelineTestingFramework:
    """
    Comprehensive testing framework for RAG pipeline validation.
    
    This framework provides testing capabilities for:
    - Educational content retrieval validation
    - Source attribution verification system
    - Relevance scoring and quality assessment
    
    Implements requirements 2.3 and 6.4 from the specification.
    """
    
    # Test queries for different educational scenarios
    TEST_QUERIES = [
        {
            'query': 'Jelaskan konsep algoritma dalam informatika',
            'subject': 'informatika',
            'grade': 'kelas_10',
            'expected_sources': ['informatika', 'algoritma', 'pemrograman'],
            'expected_topics': ['algoritma', 'langkah-langkah', 'pseudocode']
        },
        {
            'query': 'Apa itu struktur data array dan bagaimana cara kerjanya?',
            'subject': 'informatika',
            'grade': 'kelas_10',
            'expected_sources': ['informatika', 'struktur data'],
            'expected_topics': ['array', 'indeks', 'elemen', 'akses']
        },
        {
            'query': 'Bagaimana cara kerja basis data relasional?',
            'subject': 'informatika',
            'grade': 'kelas_10',
            'expected_sources': ['informatika', 'basis data'],
            'expected_topics': ['tabel', 'relasi', 'primary key', 'foreign key']
        },
        {
            'query': 'Jelaskan perbedaan hardware dan software komputer',
            'subject': 'informatika',
            'grade': 'kelas_10',
            'expected_sources': ['informatika', 'komputer'],
            'expected_topics': ['hardware', 'software', 'komponen', 'perangkat']
        },
        {
            'query': 'Apa yang dimaksud dengan jaringan komputer LAN dan WAN?',
            'subject': 'informatika',
            'grade': 'kelas_11',
            'expected_sources': ['informatika', 'jaringan'],
            'expected_topics': ['LAN', 'WAN', 'topologi', 'protokol']
        }
    ]
    
    def __init__(self, 
                 rag_pipeline: RAGPipeline,
                 educational_validator: Optional[EducationalContentValidator] = None):
        """
        Initialize the RAG pipeline testing framework.
        
        Args:
            rag_pipeline: RAG pipeline instance to test
            educational_validator: Educational content validator (creates default if None)
        """
        self.rag_pipeline = rag_pipeline
        self.educational_validator = educational_validator or EducationalContentValidator()
        
        # Testing statistics
        self.test_stats = {
            'total_tests_run': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'total_test_time_ms': 0.0
        }
        
        logger.info("RAGPipelineTestingFramework initialized")
    
    def test_educational_content_retrieval(self, 
                                         queries: Optional[List[Dict[str, Any]]] = None,
                                         top_k: int = 5) -> List[RetrievalTestResult]:
        """
        Test educational content retrieval validation.
        
        Args:
            queries: List of test queries (uses default if None)
            top_k: Number of documents to retrieve per query
            
        Returns:
            List of RetrievalTestResult objects
        """
        queries_to_test = queries or self.TEST_QUERIES
        retrieval_results = []
        
        logger.info(f"Testing educational content retrieval for {len(queries_to_test)} queries")
        
        for i, query_info in enumerate(queries_to_test):
            try:
                logger.info(f"Testing retrieval {i+1}/{len(queries_to_test)}: {query_info['query'][:50]}...")
                
                start_time = time.time()
                
                # Test retrieval directly through RAG pipeline
                context, selected_docs = self.rag_pipeline.retrieve_context(
                    query=query_info['query'],
                    subject_filter=query_info.get('subject'),
                    grade_filter=query_info.get('grade'),
                    top_k=top_k
                )
                
                retrieval_time_ms = (time.time() - start_time) * 1000
                
                # Convert selected_docs to SearchResult format for analysis
                search_results = []
                for doc in selected_docs:
                    search_result = SearchResult(
                        text=doc.text,
                        metadata=doc.metadata,
                        similarity_score=doc.relevance_score
                    )
                    search_results.append(search_result)
                
                # Analyze retrieval quality
                relevance_scores = self._calculate_relevance_scores(
                    query_info, search_results
                )
                
                source_attribution_accuracy = self._calculate_source_attribution_accuracy(
                    query_info, search_results
                )
                
                curriculum_alignment_score = self._calculate_curriculum_alignment(
                    query_info, search_results
                )
                
                average_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
                
                sources_found = [
                    result.metadata.get('source_file', 'Unknown')
                    for result in search_results
                ]
                
                # Create test result
                test_result = RetrievalTestResult(
                    query=query_info['query'],
                    retrieved_documents=search_results,
                    retrieval_time_ms=retrieval_time_ms,
                    relevance_scores=relevance_scores,
                    source_attribution_accuracy=source_attribution_accuracy,
                    curriculum_alignment_score=curriculum_alignment_score,
                    average_relevance_score=average_relevance,
                    sources_found=sources_found
                )
                
                retrieval_results.append(test_result)
                self.test_stats['successful_tests'] += 1
                
                logger.info(f"Retrieval test {i+1} completed successfully")
                
            except Exception as e:
                logger.error(f"Error in retrieval test {i+1}: {e}")
                self.test_stats['failed_tests'] += 1
                
                # Create error result
                error_result = RetrievalTestResult(
                    query=query_info['query'],
                    retrieved_documents=[],
                    retrieval_time_ms=0.0,
                    relevance_scores=[],
                    source_attribution_accuracy=0.0,
                    curriculum_alignment_score=0.0,
                    average_relevance_score=0.0,
                    sources_found=[]
                )
                retrieval_results.append(error_result)
        
        self.test_stats['total_tests_run'] += len(queries_to_test)
        
        logger.info(f"Educational content retrieval testing completed: {len(retrieval_results)} results")
        return retrieval_results
    
    def test_source_attribution_verification(self, 
                                           queries: Optional[List[Dict[str, Any]]] = None) -> List[SourceAttributionResult]:
        """
        Test source attribution verification system.
        
        Args:
            queries: List of test queries (uses default if None)
            
        Returns:
            List of SourceAttributionResult objects
        """
        queries_to_test = queries or self.TEST_QUERIES
        attribution_results = []
        
        logger.info(f"Testing source attribution verification for {len(queries_to_test)} queries")
        
        for i, query_info in enumerate(queries_to_test):
            try:
                logger.info(f"Testing attribution {i+1}/{len(queries_to_test)}: {query_info['query'][:50]}...")
                
                # Process query through RAG pipeline to get response with sources
                result = self.rag_pipeline.process_query(
                    query=query_info['query'],
                    subject_filter=query_info.get('subject'),
                    grade_filter=query_info.get('grade')
                )
                
                if isinstance(result, QueryResult):
                    response = result.response
                    context_sources = [
                        source.get('filename', 'Unknown')
                        for source in result.sources
                    ]
                else:
                    response = str(result)
                    context_sources = []
                
                # Analyze source attribution in response
                attribution_analysis = self._analyze_source_attribution(
                    query_info['query'], response, context_sources
                )
                
                attribution_results.append(attribution_analysis)
                self.test_stats['successful_tests'] += 1
                
                logger.info(f"Attribution test {i+1} completed successfully")
                
            except Exception as e:
                logger.error(f"Error in attribution test {i+1}: {e}")
                self.test_stats['failed_tests'] += 1
                
                # Create error result
                error_result = SourceAttributionResult(
                    query=query_info['query'],
                    response="Error processing query",
                    context_sources=[],
                    attributed_sources=[],
                    attribution_accuracy=0.0,
                    missing_attributions=[],
                    false_attributions=[],
                    bse_kemdikbud_sources=[],
                    proper_citation_format=False
                )
                attribution_results.append(error_result)
        
        self.test_stats['total_tests_run'] += len(queries_to_test)
        
        logger.info(f"Source attribution verification testing completed: {len(attribution_results)} results")
        return attribution_results
    
    def test_relevance_scoring_and_quality(self, 
                                         queries: Optional[List[Dict[str, Any]]] = None) -> List[QualityAssessmentResult]:
        """
        Test relevance scoring and quality assessment.
        
        Args:
            queries: List of test queries (uses default if None)
            
        Returns:
            List of QualityAssessmentResult objects
        """
        queries_to_test = queries or self.TEST_QUERIES
        quality_results = []
        
        logger.info(f"Testing relevance scoring and quality assessment for {len(queries_to_test)} queries")
        
        for i, query_info in enumerate(queries_to_test):
            try:
                logger.info(f"Testing quality {i+1}/{len(queries_to_test)}: {query_info['query'][:50]}...")
                
                # Process query through RAG pipeline
                result = self.rag_pipeline.process_query(
                    query=query_info['query'],
                    subject_filter=query_info.get('subject'),
                    grade_filter=query_info.get('grade')
                )
                
                if isinstance(result, QueryResult):
                    response = result.response
                    context = result.context_used
                else:
                    response = str(result)
                    context = ""
                
                # Perform comprehensive quality assessment
                quality_assessment = self._assess_response_quality(
                    query_info, response, context
                )
                
                quality_results.append(quality_assessment)
                self.test_stats['successful_tests'] += 1
                
                logger.info(f"Quality test {i+1} completed successfully")
                
            except Exception as e:
                logger.error(f"Error in quality test {i+1}: {e}")
                self.test_stats['failed_tests'] += 1
                
                # Create error result
                error_result = QualityAssessmentResult(
                    query=query_info['query'],
                    response="Error processing query",
                    relevance_score=0.0,
                    completeness_score=0.0,
                    accuracy_score=0.0,
                    age_appropriateness_score=0.0,
                    language_quality_score=0.0,
                    overall_quality_score=0.0,
                    quality_issues=["Processing error"],
                    quality_strengths=[]
                )
                quality_results.append(error_result)
        
        self.test_stats['total_tests_run'] += len(queries_to_test)
        
        logger.info(f"Relevance scoring and quality assessment completed: {len(quality_results)} results")
        return quality_results
    
    def run_comprehensive_rag_test(self, 
                                  queries: Optional[List[Dict[str, Any]]] = None,
                                  test_session_id: Optional[str] = None) -> RAGTestingReport:
        """
        Run comprehensive RAG pipeline testing.
        
        Args:
            queries: List of test queries (uses default if None)
            test_session_id: Unique identifier for test session
            
        Returns:
            RAGTestingReport with complete test results
        """
        if not test_session_id:
            test_session_id = f"rag_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        queries_to_test = queries or self.TEST_QUERIES
        
        logger.info(f"Running comprehensive RAG test session: {test_session_id}")
        logger.info(f"Testing {len(queries_to_test)} queries")
        
        start_time = time.time()
        
        # Run all test categories
        retrieval_tests = self.test_educational_content_retrieval(queries_to_test)
        attribution_tests = self.test_source_attribution_verification(queries_to_test)
        quality_assessments = self.test_relevance_scoring_and_quality(queries_to_test)
        
        total_test_time = (time.time() - start_time) * 1000
        self.test_stats['total_test_time_ms'] += total_test_time
        
        # Calculate summary metrics
        avg_retrieval_time = sum(t.retrieval_time_ms for t in retrieval_tests) / len(retrieval_tests) if retrieval_tests else 0.0
        avg_relevance_score = sum(t.average_relevance_score for t in retrieval_tests) / len(retrieval_tests) if retrieval_tests else 0.0
        avg_attribution_accuracy = sum(t.attribution_accuracy for t in attribution_tests) / len(attribution_tests) if attribution_tests else 0.0
        avg_quality_score = sum(t.overall_quality_score for t in quality_assessments) / len(quality_assessments) if quality_assessments else 0.0
        
        # Calculate overall test score
        overall_score = (avg_relevance_score + avg_attribution_accuracy + avg_quality_score) / 3
        
        # Create comprehensive report
        report = RAGTestingReport(
            test_session_id=test_session_id,
            test_timestamp=datetime.now(),
            total_queries_tested=len(queries_to_test),
            retrieval_tests=retrieval_tests,
            attribution_tests=attribution_tests,
            quality_assessments=quality_assessments,
            average_retrieval_time_ms=avg_retrieval_time,
            average_relevance_score=avg_relevance_score,
            average_attribution_accuracy=avg_attribution_accuracy,
            average_quality_score=avg_quality_score,
            overall_test_score=overall_score
        )
        
        logger.info(f"Comprehensive RAG test completed: {overall_score:.2f} overall score")
        return report
    
    def _calculate_relevance_scores(self, 
                                  query_info: Dict[str, Any], 
                                  search_results: List[SearchResult]) -> List[float]:
        """Calculate relevance scores for retrieved documents."""
        relevance_scores = []
        expected_topics = query_info.get('expected_topics', [])
        
        for result in search_results:
            # Base score from similarity
            base_score = result.similarity_score
            
            # Boost score if document contains expected topics
            topic_boost = 0.0
            if expected_topics:
                text_lower = result.text.lower()
                matching_topics = sum(1 for topic in expected_topics if topic.lower() in text_lower)
                topic_boost = (matching_topics / len(expected_topics)) * 0.2
            
            # Subject alignment boost
            subject_boost = 0.0
            expected_subject = query_info.get('subject', '')
            if expected_subject and result.metadata.get('subject', '').lower() == expected_subject.lower():
                subject_boost = 0.1
            
            # Grade alignment boost
            grade_boost = 0.0
            expected_grade = query_info.get('grade', '')
            if expected_grade and result.metadata.get('grade', '').lower() == expected_grade.lower():
                grade_boost = 0.1
            
            final_score = min(1.0, base_score + topic_boost + subject_boost + grade_boost)
            relevance_scores.append(final_score)
        
        return relevance_scores
    
    def _calculate_source_attribution_accuracy(self, 
                                             query_info: Dict[str, Any], 
                                             search_results: List[SearchResult]) -> float:
        """Calculate source attribution accuracy."""
        if not search_results:
            return 0.0
        
        expected_sources = query_info.get('expected_sources', [])
        if not expected_sources:
            return 0.8  # Default score when no specific sources expected
        
        found_sources = []
        for result in search_results:
            source_file = result.metadata.get('source_file', '').lower()
            subject = result.metadata.get('subject', '').lower()
            found_sources.extend([source_file, subject])
        
        # Calculate how many expected sources were found
        matches = 0
        for expected in expected_sources:
            if any(expected.lower() in source.lower() for source in found_sources):
                matches += 1
        
        accuracy = matches / len(expected_sources) if expected_sources else 0.0
        return min(1.0, accuracy)
    
    def _calculate_curriculum_alignment(self, 
                                      query_info: Dict[str, Any], 
                                      search_results: List[SearchResult]) -> float:
        """Calculate curriculum alignment score."""
        if not search_results:
            return 0.0
        
        expected_grade = query_info.get('grade', '')
        expected_subject = query_info.get('subject', '')
        
        aligned_docs = 0
        for result in search_results:
            doc_grade = result.metadata.get('grade', '').lower()
            doc_subject = result.metadata.get('subject', '').lower()
            
            grade_match = not expected_grade or doc_grade == expected_grade.lower()
            subject_match = not expected_subject or doc_subject == expected_subject.lower()
            
            if grade_match and subject_match:
                aligned_docs += 1
        
        alignment_score = aligned_docs / len(search_results)
        return alignment_score
    
    def _analyze_source_attribution(self, 
                                  query: str, 
                                  response: str, 
                                  context_sources: List[str]) -> SourceAttributionResult:
        """Analyze source attribution in response."""
        response_lower = response.lower()
        
        # Look for attribution indicators in response
        attribution_indicators = [
            'sumber:', 'referensi:', 'berdasarkan', 'menurut', 'dari materi',
            'dikutip dari', 'bersumber dari', 'merujuk pada'
        ]
        
        attributed_sources = []
        for source in context_sources:
            source_name = Path(source).stem.lower()
            if any(indicator in response_lower for indicator in attribution_indicators):
                if source_name in response_lower or source.lower() in response_lower:
                    attributed_sources.append(source)
        
        # Check for BSE Kemdikbud sources
        bse_kemdikbud_sources = [
            source for source in context_sources
            if any(keyword in source.lower() for keyword in ['bse', 'kemdikbud', 'kemendikbud'])
        ]
        
        # Calculate attribution accuracy
        if context_sources:
            attribution_accuracy = len(attributed_sources) / len(context_sources)
        else:
            attribution_accuracy = 1.0  # Perfect if no sources to attribute
        
        # Find missing and false attributions
        missing_attributions = [
            source for source in context_sources
            if source not in attributed_sources
        ]
        
        false_attributions = [
            source for source in attributed_sources
            if source not in context_sources
        ]
        
        # Check citation format
        proper_citation_format = any(indicator in response_lower for indicator in attribution_indicators)
        
        return SourceAttributionResult(
            query=query,
            response=response,
            context_sources=context_sources,
            attributed_sources=attributed_sources,
            attribution_accuracy=attribution_accuracy,
            missing_attributions=missing_attributions,
            false_attributions=false_attributions,
            bse_kemdikbud_sources=bse_kemdikbud_sources,
            proper_citation_format=proper_citation_format
        )
    
    def _assess_response_quality(self, 
                               query_info: Dict[str, Any], 
                               response: str, 
                               context: str) -> QualityAssessmentResult:
        """Assess comprehensive response quality."""
        query = query_info['query']
        
        # Use educational validator for comprehensive assessment
        validation_result = self.educational_validator.validate_educational_response(
            response=response,
            query=query,
            context=context,
            subject=query_info.get('subject'),
            grade=query_info.get('grade')
        )
        
        # Extract scores from validation result
        relevance_score = validation_result.content_score
        completeness_score = min(1.0, len(response) / 200)  # Rough completeness based on length
        accuracy_score = validation_result.curriculum_score
        age_appropriateness_score = 0.8  # Default score, could be enhanced
        language_quality_score = validation_result.language_score
        overall_quality_score = validation_result.overall_score
        
        # Extract issues and strengths
        quality_issues = [issue.message for issue in validation_result.issues]
        quality_strengths = validation_result.strengths
        
        return QualityAssessmentResult(
            query=query,
            response=response,
            relevance_score=relevance_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            age_appropriateness_score=age_appropriateness_score,
            language_quality_score=language_quality_score,
            overall_quality_score=overall_quality_score,
            quality_issues=quality_issues,
            quality_strengths=quality_strengths
        )
    
    def export_test_report(self, 
                          report: RAGTestingReport, 
                          output_path: Path,
                          format: str = 'json') -> None:
        """
        Export RAG testing report to file.
        
        Args:
            report: RAG testing report to export
            output_path: Path to output file
            format: Export format ('json' or 'html')
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'html':
                html_content = self._generate_html_test_report(report)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"RAG testing report exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting RAG testing report: {e}")
            raise
    
    def _generate_html_test_report(self, report: RAGTestingReport) -> str:
        """Generate HTML report from RAG testing data."""
        html_template = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG Pipeline Testing Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }
        .metric-value { font-size: 20px; font-weight: bold; color: #007bff; }
        .metric-label { color: #666; font-size: 14px; }
        .test-section { margin-bottom: 30px; }
        .test-item { border: 1px solid #ddd; margin-bottom: 15px; border-radius: 6px; overflow: hidden; }
        .test-header { background: #f8f9fa; padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold; }
        .test-content { padding: 15px; }
        .score-good { color: #28a745; }
        .score-ok { color: #ffc107; }
        .score-poor { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RAG Pipeline Testing Report</h1>
            <p>Session: {session_id}</p>
            <p>Generated: {timestamp}</p>
        </div>
        
        <div class="summary">
            <div class="metric-card">
                <div class="metric-value">{total_queries}</div>
                <div class="metric-label">Total Queries Tested</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_retrieval_time:.1f}ms</div>
                <div class="metric-label">Avg Retrieval Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_relevance:.2f}</div>
                <div class="metric-label">Avg Relevance Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_attribution:.2f}</div>
                <div class="metric-label">Avg Attribution Accuracy</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_quality:.2f}</div>
                <div class="metric-label">Avg Quality Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{overall_score:.2f}</div>
                <div class="metric-label">Overall Test Score</div>
            </div>
        </div>
        
        <div class="test-section">
            <h2>Test Results Summary</h2>
            <p>Comprehensive RAG pipeline testing completed with {total_queries} queries across retrieval, attribution, and quality assessment categories.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template.format(
            session_id=report.test_session_id,
            timestamp=report.test_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            total_queries=report.total_queries_tested,
            avg_retrieval_time=report.average_retrieval_time_ms,
            avg_relevance=report.average_relevance_score,
            avg_attribution=report.average_attribution_accuracy,
            avg_quality=report.average_quality_score,
            overall_score=report.overall_test_score
        )
    
    def get_testing_stats(self) -> Dict[str, Any]:
        """Get current testing statistics."""
        return self.test_stats.copy()


# Utility functions
def create_rag_testing_framework(
    chroma_db_path: str = "./data/vector_db",
    model_cache_dir: str = "./models/cache"
) -> RAGPipelineTestingFramework:
    """
    Create a RAG testing framework with recommended settings.
    
    Args:
        chroma_db_path: Path to ChromaDB database
        model_cache_dir: Directory for model storage
        
    Returns:
        RAGPipelineTestingFramework instance
    """
    from src.edge_runtime.inference_engine import InferenceEngine
    from src.edge_runtime.context_manager import ContextManager
    
    # Create components
    vector_db = ChromaDBManager(chroma_db_path)
    inference_engine = InferenceEngine(model_cache_dir)
    context_manager = ContextManager()
    
    # Create RAG pipeline
    rag_pipeline = RAGPipeline(
        vector_db=vector_db,
        inference_engine=inference_engine,
        context_manager=context_manager
    )
    
    return RAGPipelineTestingFramework(rag_pipeline)


# Example usage
def example_rag_testing():
    """Example of how to use the RAG testing framework."""
    print("RAG Pipeline Testing Framework Example")
    print("This example shows how to use the RAGPipelineTestingFramework")
    
    # Create testing framework
    # testing_framework = create_rag_testing_framework()
    
    print("Testing framework created")
    print("In practice, you would:")
    print("1. Initialize the RAG pipeline")
    print("2. Run comprehensive tests")
    print("3. Generate testing report")
    print("4. Export results")


if __name__ == "__main__":
    example_rag_testing()