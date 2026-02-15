"""
Educational Content Validator for OpenClass Nexus AI Phase 3.

This module provides Indonesian language quality validation, response quality
assessment, and curriculum alignment validation for educational content.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation result levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


class ValidationCategory(Enum):
    """Categories of educational validation."""
    LANGUAGE_QUALITY = "language_quality"
    EDUCATIONAL_CONTENT = "educational_content"
    CURRICULUM_ALIGNMENT = "curriculum_alignment"
    RESPONSE_STRUCTURE = "response_structure"
    SOURCE_ATTRIBUTION = "source_attribution"


@dataclass
class ValidationIssue:
    """Represents a validation issue in educational content."""
    category: ValidationCategory
    level: ValidationLevel
    message: str
    suggestion: str
    details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.details is None:
            self.details = {}


@dataclass
class EducationalValidationResult:
    """Result of educational content validation."""
    overall_score: float  # 0.0 to 1.0
    overall_level: ValidationLevel
    issues: List[ValidationIssue]
    strengths: List[str]
    recommendations: List[str]
    validation_timestamp: datetime
    
    # Category-specific scores
    language_score: float = 0.0
    content_score: float = 0.0
    curriculum_score: float = 0.0
    structure_score: float = 0.0
    attribution_score: float = 0.0
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if not hasattr(self, 'validation_timestamp') or self.validation_timestamp is None:
            self.validation_timestamp = datetime.now()


class IndonesianLanguageValidator:
    """Validates Indonesian language quality in educational responses."""
    
    # Common Indonesian educational terms and phrases
    EDUCATIONAL_TERMS = {
        'matematika', 'fisika', 'kimia', 'biologi', 'informatika',
        'bahasa indonesia', 'bahasa inggris', 'sejarah', 'geografi',
        'ekonomi', 'sosiologi', 'pembelajaran', 'siswa', 'guru',
        'materi', 'pelajaran', 'kurikulum', 'pendidikan'
    }
    
    # Formal Indonesian language patterns
    FORMAL_PATTERNS = [
        r'\b(adalah|merupakan|yaitu|yakni)\b',  # Definition markers
        r'\b(sehingga|oleh karena itu|dengan demikian)\b',  # Conclusion markers
        r'\b(pertama|kedua|ketiga|selanjutnya|akhirnya)\b',  # Sequence markers
        r'\b(misalnya|contohnya|seperti)\b',  # Example markers
    ]
    
    # Informal/inappropriate patterns to avoid
    INFORMAL_PATTERNS = [
        r'\b(gue|gw|lu|lo)\b',  # Informal pronouns
        r'\b(banget|bgt)\b',  # Informal intensifiers
        r'\b(gimana|gmn)\b',  # Informal question words
        r'\b(udah|udh)\b',  # Informal "already"
    ]
    
    def validate_language_quality(self, text: str) -> Tuple[float, List[ValidationIssue]]:
        """
        Validate Indonesian language quality.
        
        Args:
            text: Text to validate
            
        Returns:
            Tuple of (score, issues_list)
        """
        issues = []
        score_components = []
        
        # Check for empty or very short text
        if not text or len(text.strip()) < 10:
            issues.append(ValidationIssue(
                category=ValidationCategory.LANGUAGE_QUALITY,
                level=ValidationLevel.UNACCEPTABLE,
                message="Respons terlalu pendek atau kosong",
                suggestion="Berikan jawaban yang lebih lengkap dan informatif"
            ))
            return 0.0, issues
        
        # 1. Check formal language usage
        formal_score = self._check_formal_language(text, issues)
        score_components.append(formal_score)
        
        # 2. Check grammar and structure
        grammar_score = self._check_grammar_structure(text, issues)
        score_components.append(grammar_score)
        
        # 3. Check educational vocabulary usage
        vocab_score = self._check_educational_vocabulary(text, issues)
        score_components.append(vocab_score)
        
        # 4. Check sentence clarity and coherence
        clarity_score = self._check_clarity_coherence(text, issues)
        score_components.append(clarity_score)
        
        # Calculate overall language score
        overall_score = sum(score_components) / len(score_components)
        
        return overall_score, issues
    
    def _check_formal_language(self, text: str, issues: List[ValidationIssue]) -> float:
        """Check for formal Indonesian language usage."""
        text_lower = text.lower()
        
        # Check for informal patterns
        informal_count = 0
        for pattern in self.INFORMAL_PATTERNS:
            matches = re.findall(pattern, text_lower)
            informal_count += len(matches)
            if matches:
                issues.append(ValidationIssue(
                    category=ValidationCategory.LANGUAGE_QUALITY,
                    level=ValidationLevel.POOR,
                    message=f"Penggunaan bahasa informal ditemukan: {', '.join(matches)}",
                    suggestion="Gunakan bahasa formal yang sesuai untuk konteks pendidikan"
                ))
        
        # Check for formal patterns (positive indicators)
        formal_count = 0
        for pattern in self.FORMAL_PATTERNS:
            formal_count += len(re.findall(pattern, text_lower))
        
        # Calculate score based on formal vs informal usage
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        informal_ratio = informal_count / total_words
        formal_ratio = formal_count / total_words
        
        # Score: high formal ratio is good, high informal ratio is bad
        score = max(0.0, min(1.0, 0.8 + formal_ratio * 0.2 - informal_ratio * 0.5))
        
        return score
    
    def _check_grammar_structure(self, text: str, issues: List[ValidationIssue]) -> float:
        """Check basic grammar and sentence structure."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            issues.append(ValidationIssue(
                category=ValidationCategory.LANGUAGE_QUALITY,
                level=ValidationLevel.POOR,
                message="Tidak ada kalimat lengkap yang terdeteksi",
                suggestion="Pastikan respons menggunakan kalimat lengkap dengan tanda baca yang tepat"
            ))
            return 0.2
        
        score_components = []
        
        # Check sentence length variety
        sentence_lengths = [len(s.split()) for s in sentences]
        avg_length = sum(sentence_lengths) / len(sentence_lengths)
        
        if avg_length < 3:
            issues.append(ValidationIssue(
                category=ValidationCategory.LANGUAGE_QUALITY,
                level=ValidationLevel.ACCEPTABLE,
                message="Kalimat terlalu pendek rata-rata",
                suggestion="Gunakan kalimat yang lebih lengkap dan informatif"
            ))
            score_components.append(0.6)
        elif avg_length > 25:
            issues.append(ValidationIssue(
                category=ValidationCategory.LANGUAGE_QUALITY,
                level=ValidationLevel.ACCEPTABLE,
                message="Kalimat terlalu panjang rata-rata",
                suggestion="Pecah kalimat panjang menjadi beberapa kalimat yang lebih pendek"
            ))
            score_components.append(0.7)
        else:
            score_components.append(0.9)
        
        # Check for proper capitalization
        capitalization_score = self._check_capitalization(text, issues)
        score_components.append(capitalization_score)
        
        return sum(score_components) / len(score_components)
    
    def _check_educational_vocabulary(self, text: str, issues: List[ValidationIssue]) -> float:
        """Check usage of appropriate educational vocabulary."""
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        # Count educational terms used
        educational_terms_used = words.intersection(self.EDUCATIONAL_TERMS)
        
        if not educational_terms_used and len(words) > 20:
            issues.append(ValidationIssue(
                category=ValidationCategory.LANGUAGE_QUALITY,
                level=ValidationLevel.ACCEPTABLE,
                message="Kurang menggunakan terminologi pendidikan yang tepat",
                suggestion="Gunakan istilah-istilah pendidikan yang sesuai dengan konteks"
            ))
            return 0.6
        
        # Score based on educational vocabulary density
        vocab_density = len(educational_terms_used) / max(len(words), 1)
        score = min(1.0, 0.7 + vocab_density * 3.0)  # Boost score for educational terms
        
        return score
    
    def _check_clarity_coherence(self, text: str, issues: List[ValidationIssue]) -> float:
        """Check text clarity and coherence."""
        # Check for transition words and logical flow
        transition_patterns = [
            r'\b(pertama|kedua|ketiga|selanjutnya|kemudian|akhirnya)\b',
            r'\b(oleh karena itu|sehingga|dengan demikian|akibatnya)\b',
            r'\b(namun|tetapi|akan tetapi|meskipun|walaupun)\b',
            r'\b(misalnya|contohnya|seperti|yaitu|yakni)\b'
        ]
        
        transition_count = 0
        for pattern in transition_patterns:
            transition_count += len(re.findall(pattern, text.lower()))
        
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        if sentence_count > 3 and transition_count == 0:
            issues.append(ValidationIssue(
                category=ValidationCategory.LANGUAGE_QUALITY,
                level=ValidationLevel.ACCEPTABLE,
                message="Kurang kata penghubung untuk kelancaran bacaan",
                suggestion="Gunakan kata penghubung seperti 'pertama', 'kemudian', 'oleh karena itu' untuk menghubungkan ide"
            ))
            return 0.6
        
        # Score based on transition word usage
        transition_ratio = transition_count / max(sentence_count, 1)
        score = min(1.0, 0.7 + transition_ratio * 0.3)
        
        return score
    
    def _check_capitalization(self, text: str, issues: List[ValidationIssue]) -> float:
        """Check proper capitalization."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.5
        
        capitalization_errors = 0
        for sentence in sentences:
            if sentence and not sentence[0].isupper():
                capitalization_errors += 1
        
        if capitalization_errors > 0:
            issues.append(ValidationIssue(
                category=ValidationCategory.LANGUAGE_QUALITY,
                level=ValidationLevel.ACCEPTABLE,
                message=f"Ditemukan {capitalization_errors} kalimat yang tidak dimulai dengan huruf kapital",
                suggestion="Pastikan setiap kalimat dimulai dengan huruf kapital"
            ))
        
        score = max(0.5, 1.0 - (capitalization_errors / len(sentences)) * 0.5)
        return score


class ResponseQualityAssessor:
    """Assesses the quality of educational responses."""
    
    def assess_response_quality(self, response: str, query: str, context: str) -> Tuple[float, List[ValidationIssue]]:
        """
        Assess overall response quality.
        
        Args:
            response: Generated response
            query: Original query
            context: Context used for generation
            
        Returns:
            Tuple of (score, issues_list)
        """
        issues = []
        score_components = []
        
        # 1. Check response completeness
        completeness_score = self._check_completeness(response, query, issues)
        score_components.append(completeness_score)
        
        # 2. Check response relevance
        relevance_score = self._check_relevance(response, query, issues)
        score_components.append(relevance_score)
        
        # 3. Check response structure
        structure_score = self._check_response_structure(response, issues)
        score_components.append(structure_score)
        
        # 4. Check source attribution
        attribution_score = self._check_source_attribution(response, context, issues)
        score_components.append(attribution_score)
        
        # 5. Check educational appropriateness
        educational_score = self._check_educational_appropriateness(response, issues)
        score_components.append(educational_score)
        
        overall_score = sum(score_components) / len(score_components)
        return overall_score, issues
    
    def _check_completeness(self, response: str, query: str, issues: List[ValidationIssue]) -> float:
        """Check if response adequately addresses the query."""
        if not response or len(response.strip()) < 20:
            issues.append(ValidationIssue(
                category=ValidationCategory.EDUCATIONAL_CONTENT,
                level=ValidationLevel.POOR,
                message="Respons terlalu pendek dan tidak lengkap",
                suggestion="Berikan jawaban yang lebih detail dan komprehensif"
            ))
            return 0.2
        
        # Check if response addresses key terms from query
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        response_words = set(re.findall(r'\b\w+\b', response.lower()))
        
        # Remove common stop words for better analysis
        stop_words = {'yang', 'dan', 'atau', 'dengan', 'untuk', 'dari', 'ke', 'di', 'pada', 'adalah', 'ini', 'itu'}
        query_content_words = query_words - stop_words
        
        if query_content_words:
            coverage = len(query_content_words.intersection(response_words)) / len(query_content_words)
            if coverage < 0.3:
                issues.append(ValidationIssue(
                    category=ValidationCategory.EDUCATIONAL_CONTENT,
                    level=ValidationLevel.ACCEPTABLE,
                    message="Respons kurang mengacu pada kata kunci dalam pertanyaan",
                    suggestion="Pastikan jawaban mengacu pada konsep-konsep utama dalam pertanyaan"
                ))
                return 0.6
            return min(1.0, 0.5 + coverage * 0.5)
        
        return 0.8
    
    def _check_relevance(self, response: str, query: str, issues: List[ValidationIssue]) -> float:
        """Check response relevance to the query."""
        # Simple relevance check based on topic similarity
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Check for off-topic responses
        if "maaf" in response_lower and ("tidak" in response_lower or "belum" in response_lower):
            # This is likely a fallback response, which is appropriate
            return 0.8
        
        # Check if response stays on topic
        if len(response) > 100:
            # For longer responses, check if they maintain topic focus
            sentences = re.split(r'[.!?]+', response)
            relevant_sentences = 0
            
            for sentence in sentences:
                if any(word in sentence.lower() for word in query.lower().split() if len(word) > 3):
                    relevant_sentences += 1
            
            if sentences and relevant_sentences / len(sentences) < 0.3:
                issues.append(ValidationIssue(
                    category=ValidationCategory.EDUCATIONAL_CONTENT,
                    level=ValidationLevel.ACCEPTABLE,
                    message="Respons mungkin menyimpang dari topik pertanyaan",
                    suggestion="Fokuskan jawaban pada topik yang ditanyakan"
                ))
                return 0.6
        
        return 0.9
    
    def _check_response_structure(self, response: str, issues: List[ValidationIssue]) -> float:
        """Check response structure and organization."""
        # Check for proper paragraph structure
        paragraphs = response.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if len(paragraphs) == 1 and len(response) > 200:
            issues.append(ValidationIssue(
                category=ValidationCategory.RESPONSE_STRUCTURE,
                level=ValidationLevel.ACCEPTABLE,
                message="Respons panjang sebaiknya dibagi menjadi beberapa paragraf",
                suggestion="Bagi jawaban menjadi paragraf-paragraf untuk kemudahan membaca"
            ))
            return 0.7
        
        # Check for examples or explanations
        has_examples = any(word in response.lower() for word in ['misalnya', 'contohnya', 'seperti', 'yaitu'])
        has_explanations = any(word in response.lower() for word in ['karena', 'sehingga', 'oleh karena itu'])
        
        structure_score = 0.6  # Base score
        if has_examples:
            structure_score += 0.2
        if has_explanations:
            structure_score += 0.2
        
        return min(1.0, structure_score)
    
    def _check_source_attribution(self, response: str, context: str, issues: List[ValidationIssue]) -> float:
        """Check if response properly attributes sources."""
        if not context or not context.strip():
            # No context provided, so attribution not expected
            return 0.8
        
        # Check for source references in response
        source_indicators = ['sumber:', 'referensi:', 'berdasarkan', 'menurut', 'dari materi']
        has_attribution = any(indicator in response.lower() for indicator in source_indicators)
        
        if not has_attribution and len(context) > 100:
            issues.append(ValidationIssue(
                category=ValidationCategory.SOURCE_ATTRIBUTION,
                level=ValidationLevel.ACCEPTABLE,
                message="Respons tidak menyertakan rujukan sumber materi",
                suggestion="Sertakan rujukan ke sumber materi yang digunakan"
            ))
            return 0.6
        
        return 0.9 if has_attribution else 0.7
    
    def _check_educational_appropriateness(self, response: str, issues: List[ValidationIssue]) -> float:
        """Check if response is appropriate for educational context."""
        response_lower = response.lower()
        
        # Check for inappropriate content
        inappropriate_terms = ['bodoh', 'tolol', 'goblok', 'idiot']
        if any(term in response_lower for term in inappropriate_terms):
            issues.append(ValidationIssue(
                category=ValidationCategory.EDUCATIONAL_CONTENT,
                level=ValidationLevel.UNACCEPTABLE,
                message="Respons mengandung kata-kata yang tidak pantas untuk konteks pendidikan",
                suggestion="Gunakan bahasa yang sopan dan mendidik"
            ))
            return 0.1
        
        # Check for encouraging/supportive tone
        positive_indicators = ['baik', 'bagus', 'benar', 'tepat', 'mari', 'coba', 'pelajari']
        has_positive_tone = any(indicator in response_lower for indicator in positive_indicators)
        
        if has_positive_tone:
            return 1.0
        
        return 0.8


class CurriculumAlignmentValidator:
    """Validates alignment with Indonesian curriculum standards."""
    
    # Indonesian curriculum subjects and their key topics
    CURRICULUM_SUBJECTS = {
        'matematika': {
            'kelas_10': ['aljabar', 'geometri', 'trigonometri', 'statistika', 'peluang'],
            'kelas_11': ['limit', 'turunan', 'integral', 'matriks', 'barisan'],
            'kelas_12': ['kalkulus', 'integral lanjut', 'statistika inferensial']
        },
        'fisika': {
            'kelas_10': ['gerak', 'gaya', 'energi', 'momentum', 'getaran'],
            'kelas_11': ['termodinamika', 'gelombang', 'optik', 'listrik'],
            'kelas_12': ['medan magnet', 'induksi', 'fisika modern', 'radioaktif']
        },
        'kimia': {
            'kelas_10': ['atom', 'ikatan kimia', 'stoikiometri', 'larutan'],
            'kelas_11': ['termokimia', 'laju reaksi', 'kesetimbangan', 'asam basa'],
            'kelas_12': ['elektrokimia', 'kimia organik', 'makromolekul']
        },
        'biologi': {
            'kelas_10': ['sel', 'jaringan', 'sistem organ', 'keanekaragaman hayati'],
            'kelas_11': ['metabolisme', 'respirasi', 'fotosintesis', 'reproduksi'],
            'kelas_12': ['genetika', 'evolusi', 'bioteknologi', 'ekologi']
        },
        'informatika': {
            'kelas_10': ['algoritma', 'pemrograman', 'struktur data', 'basis data'],
            'kelas_11': ['jaringan', 'keamanan', 'multimedia', 'web'],
            'kelas_12': ['kecerdasan buatan', 'machine learning', 'big data']
        }
    }
    
    def validate_curriculum_alignment(
        self, 
        response: str, 
        subject: Optional[str] = None, 
        grade: Optional[str] = None
    ) -> Tuple[float, List[ValidationIssue]]:
        """
        Validate alignment with curriculum standards.
        
        Args:
            response: Generated response
            subject: Subject area (optional)
            grade: Grade level (optional)
            
        Returns:
            Tuple of (score, issues_list)
        """
        issues = []
        
        if not subject or not grade:
            # Cannot validate without subject and grade information
            return 0.8, issues
        
        subject_lower = subject.lower()
        grade_lower = grade.lower()
        
        # Check if subject is in curriculum
        if subject_lower not in self.CURRICULUM_SUBJECTS:
            issues.append(ValidationIssue(
                category=ValidationCategory.CURRICULUM_ALIGNMENT,
                level=ValidationLevel.ACCEPTABLE,
                message=f"Mata pelajaran '{subject}' tidak ditemukan dalam kurikulum standar",
                suggestion="Pastikan mata pelajaran sesuai dengan kurikulum yang berlaku"
            ))
            return 0.6, issues
        
        # Check if grade is valid
        if grade_lower not in self.CURRICULUM_SUBJECTS[subject_lower]:
            issues.append(ValidationIssue(
                category=ValidationCategory.CURRICULUM_ALIGNMENT,
                level=ValidationLevel.ACCEPTABLE,
                message=f"Tingkat kelas '{grade}' tidak tersedia untuk mata pelajaran '{subject}'",
                suggestion="Periksa kesesuaian tingkat kelas dengan mata pelajaran"
            ))
            return 0.6, issues
        
        # Check topic alignment
        expected_topics = self.CURRICULUM_SUBJECTS[subject_lower][grade_lower]
        response_lower = response.lower()
        
        # Count how many curriculum topics are mentioned
        mentioned_topics = []
        for topic in expected_topics:
            if topic in response_lower:
                mentioned_topics.append(topic)
        
        if not mentioned_topics:
            issues.append(ValidationIssue(
                category=ValidationCategory.CURRICULUM_ALIGNMENT,
                level=ValidationLevel.ACCEPTABLE,
                message=f"Respons tidak mengacu pada topik kurikulum {subject} {grade}",
                suggestion=f"Sertakan topik-topik seperti: {', '.join(expected_topics[:3])}"
            ))
            return 0.5, issues
        
        # Calculate alignment score
        alignment_ratio = len(mentioned_topics) / len(expected_topics)
        score = min(1.0, 0.6 + alignment_ratio * 0.4)
        
        if alignment_ratio > 0.5:
            # Good alignment
            return score, issues
        else:
            issues.append(ValidationIssue(
                category=ValidationCategory.CURRICULUM_ALIGNMENT,
                level=ValidationLevel.GOOD,
                message=f"Respons mencakup beberapa topik kurikulum: {', '.join(mentioned_topics)}",
                suggestion="Pertahankan fokus pada topik-topik kurikulum yang relevan"
            ))
            return score, issues


class EducationalContentValidator:
    """
    Main educational content validator combining all validation components.
    
    This class provides comprehensive validation for Indonesian educational
    content including language quality, response assessment, and curriculum
    alignment as specified in requirements 5.5 and 1.2.
    """
    
    def __init__(self):
        """Initialize the educational content validator."""
        self.language_validator = IndonesianLanguageValidator()
        self.quality_assessor = ResponseQualityAssessor()
        self.curriculum_validator = CurriculumAlignmentValidator()
        
        logger.info("Initialized EducationalContentValidator")
    
    def validate_educational_response(
        self,
        response: str,
        query: str,
        context: str = "",
        subject: Optional[str] = None,
        grade: Optional[str] = None
    ) -> EducationalValidationResult:
        """
        Perform comprehensive educational content validation.
        
        Args:
            response: Generated response to validate
            query: Original user query
            context: Context used for generation
            subject: Subject area (optional)
            grade: Grade level (optional)
            
        Returns:
            EducationalValidationResult with comprehensive validation results
        """
        logger.info(f"Validating educational response for query: {query[:50]}...")
        
        all_issues = []
        all_strengths = []
        all_recommendations = []
        
        # 1. Validate Indonesian language quality
        language_score, language_issues = self.language_validator.validate_language_quality(response)
        all_issues.extend(language_issues)
        
        # 2. Assess response quality
        quality_score, quality_issues = self.quality_assessor.assess_response_quality(response, query, context)
        all_issues.extend(quality_issues)
        
        # 3. Validate curriculum alignment
        curriculum_score, curriculum_issues = self.curriculum_validator.validate_curriculum_alignment(
            response, subject, grade
        )
        all_issues.extend(curriculum_issues)
        
        # Calculate component scores
        structure_score = 0.8  # Default structure score
        attribution_score = 0.8  # Default attribution score
        
        # Extract specific scores from quality assessment
        if context:
            attribution_score = min(1.0, quality_score + 0.1)  # Boost if context is used
        
        # Calculate overall score
        score_weights = {
            'language': 0.3,
            'quality': 0.3,
            'curriculum': 0.2,
            'structure': 0.1,
            'attribution': 0.1
        }
        
        overall_score = (
            language_score * score_weights['language'] +
            quality_score * score_weights['quality'] +
            curriculum_score * score_weights['curriculum'] +
            structure_score * score_weights['structure'] +
            attribution_score * score_weights['attribution']
        )
        
        # Determine overall level
        if overall_score >= 0.9:
            overall_level = ValidationLevel.EXCELLENT
        elif overall_score >= 0.8:
            overall_level = ValidationLevel.GOOD
        elif overall_score >= 0.6:
            overall_level = ValidationLevel.ACCEPTABLE
        elif overall_score >= 0.4:
            overall_level = ValidationLevel.POOR
        else:
            overall_level = ValidationLevel.UNACCEPTABLE
        
        # Generate strengths and recommendations
        self._generate_strengths_and_recommendations(
            overall_score, language_score, quality_score, curriculum_score,
            all_strengths, all_recommendations
        )
        
        result = EducationalValidationResult(
            overall_score=overall_score,
            overall_level=overall_level,
            issues=all_issues,
            strengths=all_strengths,
            recommendations=all_recommendations,
            validation_timestamp=datetime.now(),
            language_score=language_score,
            content_score=quality_score,
            curriculum_score=curriculum_score,
            structure_score=structure_score,
            attribution_score=attribution_score
        )
        
        logger.info(f"Validation completed. Overall score: {overall_score:.2f} ({overall_level.value})")
        return result
    
    def _generate_strengths_and_recommendations(
        self,
        overall_score: float,
        language_score: float,
        quality_score: float,
        curriculum_score: float,
        strengths: List[str],
        recommendations: List[str]
    ) -> None:
        """Generate strengths and recommendations based on scores."""
        
        # Identify strengths
        if language_score >= 0.8:
            strengths.append("Penggunaan bahasa Indonesia yang baik dan formal")
        if quality_score >= 0.8:
            strengths.append("Kualitas respons yang tinggi dan relevan")
        if curriculum_score >= 0.8:
            strengths.append("Sesuai dengan standar kurikulum pendidikan")
        if overall_score >= 0.9:
            strengths.append("Respons berkualitas tinggi secara keseluruhan")
        
        # Generate recommendations
        if language_score < 0.7:
            recommendations.append("Tingkatkan penggunaan bahasa formal dan terminologi pendidikan")
        if quality_score < 0.7:
            recommendations.append("Berikan jawaban yang lebih lengkap dan terstruktur")
        if curriculum_score < 0.7:
            recommendations.append("Pastikan konten sesuai dengan kurikulum yang berlaku")
        if overall_score < 0.6:
            recommendations.append("Perlukan perbaikan menyeluruh pada kualitas respons")
        
        # Add general recommendations
        if not strengths:
            recommendations.append("Fokus pada peningkatan kualitas bahasa dan konten pendidikan")
        
        recommendations.append("Selalu sertakan contoh konkret untuk memperjelas penjelasan")
        recommendations.append("Pastikan jawaban mudah dipahami oleh siswa SMA/SMK")
    
    def get_validation_summary(self, result: EducationalValidationResult) -> Dict[str, Any]:
        """
        Get a summary of validation results.
        
        Args:
            result: Validation result to summarize
            
        Returns:
            Dictionary with validation summary
        """
        return {
            'overall_score': result.overall_score,
            'overall_level': result.overall_level.value,
            'component_scores': {
                'language_quality': result.language_score,
                'content_quality': result.content_score,
                'curriculum_alignment': result.curriculum_score,
                'response_structure': result.structure_score,
                'source_attribution': result.attribution_score
            },
            'issue_count': len(result.issues),
            'issues_by_category': self._group_issues_by_category(result.issues),
            'strengths_count': len(result.strengths),
            'recommendations_count': len(result.recommendations),
            'validation_timestamp': result.validation_timestamp.isoformat()
        }
    
    def _group_issues_by_category(self, issues: List[ValidationIssue]) -> Dict[str, int]:
        """Group issues by category for summary."""
        category_counts = {}
        for issue in issues:
            category = issue.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        return category_counts