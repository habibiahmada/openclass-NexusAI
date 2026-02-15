"""
Fallback response handling for RAG pipeline.

This module provides appropriate fallback responses when no relevant
educational content is found, with Indonesian language support and
educational guidance.
"""

import logging
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class FallbackReason(Enum):
    """Reasons for fallback response."""
    NO_RELEVANT_CONTENT = "no_relevant_content"
    EMPTY_QUERY = "empty_query"
    TECHNICAL_ERROR = "technical_error"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    SUBJECT_NOT_AVAILABLE = "subject_not_available"


@dataclass
class FallbackResponse:
    """Fallback response with metadata."""
    message: str
    reason: FallbackReason
    suggestions: List[str]
    help_resources: List[Dict[str, str]]


class FallbackHandler:
    """
    Handles fallback responses for educational queries.
    
    Provides appropriate Indonesian language responses when the RAG pipeline
    cannot find relevant content, along with helpful suggestions and resources.
    """
    
    def __init__(self):
        """Initialize fallback handler with Indonesian educational responses."""
        self.fallback_messages = self._load_fallback_messages()
        self.subject_suggestions = self._load_subject_suggestions()
        self.help_resources = self._load_help_resources()
        
        logger.info("Initialized FallbackHandler with Indonesian educational responses")
    
    def generate_fallback_response(
        self, 
        query: str, 
        reason: FallbackReason,
        available_subjects: Optional[List[str]] = None,
        context_stats: Optional[Dict[str, Any]] = None
    ) -> FallbackResponse:
        """
        Generate appropriate fallback response based on the reason.
        
        Args:
            query: Original user query
            reason: Reason for fallback
            available_subjects: List of available subjects in database
            context_stats: Statistics about retrieved context
            
        Returns:
            FallbackResponse with message and suggestions
        """
        logger.info(f"Generating fallback response for reason: {reason.value}")
        
        # Get base message for the reason
        base_message = self._get_base_message(reason)
        
        # Generate contextual suggestions
        suggestions = self._generate_suggestions(query, reason, available_subjects)
        
        # Get help resources
        help_resources = self._get_help_resources(reason)
        
        # Customize message based on context
        customized_message = self._customize_message(
            base_message, query, reason, context_stats
        )
        
        return FallbackResponse(
            message=customized_message,
            reason=reason,
            suggestions=suggestions,
            help_resources=help_resources
        )
    
    def _get_base_message(self, reason: FallbackReason) -> str:
        """Get base fallback message for the given reason."""
        messages = self.fallback_messages.get(reason, [])
        if messages:
            return random.choice(messages)
        else:
            return self.fallback_messages[FallbackReason.NO_RELEVANT_CONTENT][0]
    
    def _customize_message(
        self, 
        base_message: str, 
        query: str, 
        reason: FallbackReason,
        context_stats: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Customize the base message with query-specific information.
        
        Args:
            base_message: Base fallback message
            query: User query
            reason: Fallback reason
            context_stats: Context statistics
            
        Returns:
            Customized message
        """
        # Add query-specific context
        if reason == FallbackReason.SUBJECT_NOT_AVAILABLE:
            # Try to identify the subject from query
            detected_subject = self._detect_subject_from_query(query)
            if detected_subject:
                base_message += f"\n\nSaya melihat Anda bertanya tentang {detected_subject}. "
                base_message += "Materi untuk mata pelajaran ini mungkin belum tersedia di database saya."
        
        elif reason == FallbackReason.INSUFFICIENT_CONTEXT:
            if context_stats and context_stats.get('total_documents', 0) > 0:
                base_message += f"\n\nSaya menemukan {context_stats['total_documents']} dokumen terkait, "
                base_message += "tetapi informasinya tidak cukup spesifik untuk menjawab pertanyaan Anda."
        
        return base_message
    
    def _generate_suggestions(
        self, 
        query: str, 
        reason: FallbackReason,
        available_subjects: Optional[List[str]] = None
    ) -> List[str]:
        """
        Generate helpful suggestions based on query and reason.
        
        Args:
            query: User query
            reason: Fallback reason
            available_subjects: Available subjects
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        if reason == FallbackReason.NO_RELEVANT_CONTENT:
            suggestions.extend([
                "Coba gunakan kata kunci yang lebih spesifik",
                "Sebutkan mata pelajaran dan kelas yang Anda maksud",
                "Gunakan istilah yang ada dalam buku pelajaran",
                "Coba pertanyaan yang lebih sederhana terlebih dahulu"
            ])
        
        elif reason == FallbackReason.EMPTY_QUERY:
            suggestions.extend([
                "Tuliskan pertanyaan yang jelas dan spesifik",
                "Sebutkan mata pelajaran yang ingin Anda tanyakan",
                "Berikan konteks atau topik yang ingin dipelajari"
            ])
        
        elif reason == FallbackReason.SUBJECT_NOT_AVAILABLE:
            if available_subjects:
                subject_list = ", ".join(available_subjects)
                suggestions.append(f"Mata pelajaran yang tersedia: {subject_list}")
            suggestions.extend([
                "Periksa ejaan nama mata pelajaran",
                "Coba gunakan nama mata pelajaran yang standar"
            ])
        
        elif reason == FallbackReason.TECHNICAL_ERROR:
            suggestions.extend([
                "Coba ulangi pertanyaan Anda",
                "Pastikan koneksi internet stabil",
                "Hubungi administrator jika masalah berlanjut"
            ])
        
        # Add subject-specific suggestions
        detected_subject = self._detect_subject_from_query(query)
        if detected_subject and detected_subject in self.subject_suggestions:
            suggestions.extend(self.subject_suggestions[detected_subject])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _get_help_resources(self, reason: FallbackReason) -> List[Dict[str, str]]:
        """Get help resources based on fallback reason."""
        base_resources = self.help_resources.get('general', [])
        
        if reason in self.help_resources:
            base_resources.extend(self.help_resources[reason])
        
        return base_resources
    
    def _detect_subject_from_query(self, query: str) -> Optional[str]:
        """
        Detect subject from query text.
        
        Args:
            query: User query
            
        Returns:
            Detected subject or None
        """
        query_lower = query.lower()
        
        subject_keywords = {
            'matematika': ['matematika', 'math', 'aljabar', 'geometri', 'kalkulus', 'statistik'],
            'fisika': ['fisika', 'physics', 'gaya', 'energi', 'gelombang', 'listrik'],
            'kimia': ['kimia', 'chemistry', 'molekul', 'atom', 'reaksi', 'unsur'],
            'biologi': ['biologi', 'biology', 'sel', 'genetika', 'evolusi', 'ekosistem'],
            'informatika': ['informatika', 'komputer', 'programming', 'algoritma', 'database'],
            'sejarah': ['sejarah', 'history', 'perang', 'kemerdekaan', 'kolonial'],
            'geografi': ['geografi', 'geography', 'peta', 'iklim', 'benua', 'negara'],
            'ekonomi': ['ekonomi', 'economy', 'pasar', 'inflasi', 'perdagangan'],
            'bahasa indonesia': ['bahasa indonesia', 'sastra', 'puisi', 'novel', 'tata bahasa'],
            'bahasa inggris': ['bahasa inggris', 'english', 'grammar', 'vocabulary']
        }
        
        for subject, keywords in subject_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return subject
        
        return None
    
    def _load_fallback_messages(self) -> Dict[FallbackReason, List[str]]:
        """Load fallback messages for different reasons."""
        return {
            FallbackReason.NO_RELEVANT_CONTENT: [
                "Maaf, saya tidak menemukan materi yang relevan dengan pertanyaan Anda di database saya.",
                "Informasi yang Anda cari belum tersedia dalam database materi pembelajaran saya.",
                "Saya belum memiliki materi yang sesuai dengan pertanyaan Anda saat ini.",
                "Materi terkait pertanyaan Anda belum ada dalam koleksi pembelajaran saya."
            ],
            
            FallbackReason.EMPTY_QUERY: [
                "Silakan tuliskan pertanyaan yang ingin Anda tanyakan.",
                "Saya siap membantu! Apa yang ingin Anda pelajari hari ini?",
                "Mohon berikan pertanyaan yang jelas agar saya dapat membantu Anda."
            ],
            
            FallbackReason.TECHNICAL_ERROR: [
                "Maaf, terjadi kesalahan teknis. Silakan coba lagi dalam beberapa saat.",
                "Sistem sedang mengalami gangguan. Mohon coba kembali nanti.",
                "Terjadi kesalahan dalam memproses pertanyaan Anda. Silakan ulangi."
            ],
            
            FallbackReason.INSUFFICIENT_CONTEXT: [
                "Informasi yang saya temukan tidak cukup lengkap untuk menjawab pertanyaan Anda.",
                "Materi yang tersedia belum cukup detail untuk memberikan jawaban yang memuaskan.",
                "Saya perlu informasi yang lebih spesifik untuk dapat membantu Anda dengan baik."
            ],
            
            FallbackReason.SUBJECT_NOT_AVAILABLE: [
                "Mata pelajaran yang Anda tanyakan belum tersedia dalam database saya.",
                "Materi untuk mata pelajaran tersebut belum ada dalam koleksi pembelajaran saya.",
                "Saat ini saya belum memiliki materi untuk mata pelajaran yang Anda maksud."
            ]
        }
    
    def _load_subject_suggestions(self) -> Dict[str, List[str]]:
        """Load subject-specific suggestions."""
        return {
            'matematika': [
                "Coba sebutkan topik spesifik seperti 'aljabar', 'geometri', atau 'statistik'",
                "Berikan contoh soal atau rumus yang ingin dipelajari"
            ],
            'fisika': [
                "Sebutkan konsep fisika seperti 'gaya', 'energi', atau 'gelombang'",
                "Berikan konteks seperti 'mekanika', 'termodinamika', atau 'listrik'"
            ],
            'kimia': [
                "Sebutkan topik seperti 'struktur atom', 'ikatan kimia', atau 'reaksi kimia'",
                "Berikan nama unsur atau senyawa yang ingin dipelajari"
            ],
            'biologi': [
                "Sebutkan sistem seperti 'sistem pencernaan', 'fotosintesis', atau 'genetika'",
                "Berikan nama organisme atau proses biologis yang spesifik"
            ],
            'informatika': [
                "Sebutkan topik seperti 'algoritma', 'database', atau 'pemrograman'",
                "Berikan bahasa pemrograman atau teknologi yang ingin dipelajari"
            ]
        }
    
    def _load_help_resources(self) -> Dict[str, List[Dict[str, str]]]:
        """Load help resources for different situations."""
        return {
            'general': [
                {
                    'title': 'Hubungi Guru',
                    'description': 'Konsultasikan dengan guru mata pelajaran untuk penjelasan lebih detail',
                    'action': 'Tanyakan langsung di kelas atau melalui platform pembelajaran sekolah'
                },
                {
                    'title': 'Buku Pelajaran',
                    'description': 'Periksa buku pelajaran resmi dari Kemendikbud',
                    'action': 'Baca materi terkait di buku cetak atau digital'
                }
            ],
            
            FallbackReason.NO_RELEVANT_CONTENT: [
                {
                    'title': 'Cari di Sumber Lain',
                    'description': 'Gunakan sumber pembelajaran online yang terpercaya',
                    'action': 'Kunjungi portal pembelajaran Kemendikbud atau platform edukasi lainnya'
                }
            ],
            
            FallbackReason.TECHNICAL_ERROR: [
                {
                    'title': 'Laporkan Masalah',
                    'description': 'Hubungi administrator sistem jika masalah berlanjut',
                    'action': 'Kirim laporan melalui email atau sistem pelaporan sekolah'
                }
            ]
        }
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """Get statistics about fallback responses."""
        return {
            'total_fallback_messages': sum(len(messages) for messages in self.fallback_messages.values()),
            'available_reasons': [reason.value for reason in FallbackReason],
            'subject_suggestions_count': len(self.subject_suggestions),
            'help_resources_count': sum(len(resources) for resources in self.help_resources.values())
        }