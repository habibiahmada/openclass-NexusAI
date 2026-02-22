"""
Mastery Tracker

Tracks student mastery levels per topic using a scoring algorithm based on:
- Question frequency (more questions = lower mastery)
- Question complexity (harder questions = higher mastery)
- Retention (time between questions = better retention)
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class MasteryData:
    """Data structure for mastery tracking"""
    mastery_level: float
    question_count: int
    avg_complexity: float
    last_question_date: datetime


class MasteryTracker:
    """
    Tracks topic mastery per student with mastery_level score (0.0 to 1.0)
    
    Mastery Scoring Algorithm:
    - frequency_factor: 1.0 / (1.0 + question_count * 0.1)
    - complexity_factor: min(avg_complexity, 1.0)
    - retention_factor: min(retention_days / 30.0, 1.0)
    - mastery = (frequency_factor * 0.3 + complexity_factor * 0.5 + retention_factor * 0.2)
    """
    
    # Topic classification keywords
    TOPIC_KEYWORDS = {
        'matematika': {
            'aljabar': ['persamaan', 'variabel', 'fungsi', 'polinomial'],
            'geometri': ['segitiga', 'lingkaran', 'pythagoras', 'sudut', 'luas', 'volume'],
            'trigonometri': ['sinus', 'cosinus', 'tangen', 'sin', 'cos', 'tan'],
            'kalkulus': ['turunan', 'integral', 'limit', 'diferensial'],
            'statistika': ['mean', 'median', 'modus', 'probabilitas', 'distribusi'],
            'matriks': ['matriks', 'determinan', 'invers'],
        },
        'informatika': {
            'pemrograman': ['python', 'java', 'c++', 'kode', 'program', 'algoritma'],
            'struktur_data': ['array', 'linked list', 'stack', 'queue', 'tree', 'graph'],
            'database': ['sql', 'database', 'tabel', 'query', 'relasi'],
            'jaringan': ['network', 'tcp', 'ip', 'protokol', 'internet'],
            'keamanan': ['enkripsi', 'hash', 'password', 'security', 'keamanan'],
        },
    }
    
    def __init__(self, db_manager):
        """
        Initialize MasteryTracker with database connection
        
        Args:
            db_manager: DatabaseManager instance for persistence
        """
        self.db = db_manager
    
    def classify_topic(self, question: str, subject: str = 'matematika') -> str:
        """
        Classify question into a topic using keyword matching
        
        Args:
            question: The student's question text
            subject: The subject area (default: 'matematika')
        
        Returns:
            Topic name (e.g., 'aljabar', 'geometri') or 'general' if no match
        """
        question_lower = question.lower()
        
        # Get keywords for subject
        subject_keywords = self.TOPIC_KEYWORDS.get(subject, {})
        
        # Count keyword matches per topic
        topic_scores = {}
        for topic, keywords in subject_keywords.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                topic_scores[topic] = score
        
        # Return topic with highest score
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        
        return 'general'
    
    def calculate_question_complexity(self, question: str) -> float:
        """
        Calculate question complexity based on length and keywords
        
        Args:
            question: The student's question text
        
        Returns:
            Complexity score between 0.0 and 1.0
        """
        # Length factor (longer questions tend to be more complex)
        word_count = len(question.split())
        length_factor = min(word_count / 50.0, 1.0)  # Cap at 50 words
        
        # Complexity keywords
        complex_keywords = [
            'mengapa', 'bagaimana', 'jelaskan', 'buktikan', 'analisis',
            'bandingkan', 'evaluasi', 'sintesis', 'why', 'how', 'explain',
            'prove', 'analyze', 'compare', 'evaluate'
        ]
        
        question_lower = question.lower()
        keyword_count = sum(1 for keyword in complex_keywords if keyword in question_lower)
        keyword_factor = min(keyword_count / 3.0, 1.0)  # Cap at 3 keywords
        
        # Combined complexity (weighted average)
        complexity = length_factor * 0.4 + keyword_factor * 0.6
        
        return max(0.0, min(complexity, 1.0))
    
    def calculate_mastery(self, question_count: int, avg_complexity: float, 
                         retention_days: int) -> float:
        """
        Calculate mastery level using the scoring algorithm
        
        Args:
            question_count: Number of questions asked on this topic
            avg_complexity: Average complexity of questions (0.0 to 1.0)
            retention_days: Days since last question on this topic
        
        Returns:
            Mastery level between 0.0 (novice) and 1.0 (expert)
        """
        # Frequency factor: more questions = lower mastery (student struggling)
        frequency_factor = 1.0 / (1.0 + question_count * 0.1)
        
        # Complexity factor: harder questions = higher mastery
        complexity_factor = min(avg_complexity, 1.0)
        
        # Retention factor: longer gaps = better retention
        retention_factor = min(retention_days / 30.0, 1.0)
        
        # Weighted combination
        mastery = (frequency_factor * 0.3 + 
                  complexity_factor * 0.5 + 
                  retention_factor * 0.2)
        
        # Ensure bounds [0.0, 1.0]
        return max(0.0, min(mastery, 1.0))
    
    def update_mastery(self, user_id: int, subject_id: int, topic: str, 
                      question_complexity: float) -> float:
        """
        Update mastery level after a student asks a question
        
        Args:
            user_id: Student user ID
            subject_id: Subject ID
            topic: Topic name
            question_complexity: Complexity of the current question (0.0 to 1.0)
        
        Returns:
            Updated mastery level (0.0 to 1.0)
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get existing mastery data
            cursor.execute("""
                SELECT question_count, avg_complexity, last_question_date
                FROM topic_mastery
                WHERE user_id = %s AND subject_id = %s AND topic = %s
            """, (user_id, subject_id, topic))
            
            result = cursor.fetchone()
            
            if result and len(result) == 3:
                # Update existing record
                question_count, avg_complexity, last_question_date = result
                
                # Calculate retention days
                retention_days = (datetime.now() - last_question_date).days
                
                # Update question count and average complexity
                new_question_count = question_count + 1
                new_avg_complexity = (
                    (avg_complexity * question_count + question_complexity) / 
                    new_question_count
                )
                
                # Calculate new mastery level
                mastery_level = self.calculate_mastery(
                    new_question_count, 
                    new_avg_complexity, 
                    retention_days
                )
                
                # Update database
                cursor.execute("""
                    UPDATE topic_mastery
                    SET question_count = %s,
                        avg_complexity = %s,
                        mastery_level = %s,
                        last_question_date = %s,
                        updated_at = %s
                    WHERE user_id = %s AND subject_id = %s AND topic = %s
                """, (new_question_count, new_avg_complexity, mastery_level,
                     datetime.now(), datetime.now(), user_id, subject_id, topic))
            else:
                # Create new record
                mastery_level = self.calculate_mastery(1, question_complexity, 0)
                
                cursor.execute("""
                    INSERT INTO topic_mastery 
                    (user_id, subject_id, topic, question_count, avg_complexity, 
                     mastery_level, last_question_date, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_id, subject_id, topic, 1, question_complexity,
                     mastery_level, datetime.now(), datetime.now(), datetime.now()))
            
            conn.commit()
            cursor.close()
            return mastery_level
    
    def get_mastery_level(self, user_id: int, subject_id: int, topic: str) -> float:
        """
        Get current mastery level for a specific topic
        
        Args:
            user_id: Student user ID
            subject_id: Subject ID
            topic: Topic name
        
        Returns:
            Mastery level (0.0 to 1.0), or 0.0 if no data exists
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT mastery_level
                FROM topic_mastery
                WHERE user_id = %s AND subject_id = %s AND topic = %s
            """, (user_id, subject_id, topic))
            
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else 0.0
    
    def get_all_mastery(self, user_id: int, subject_id: int) -> Dict[str, float]:
        """
        Get all mastery levels for a student in a subject
        
        Args:
            user_id: Student user ID
            subject_id: Subject ID
        
        Returns:
            Dictionary mapping topic names to mastery levels
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT topic, mastery_level
                FROM topic_mastery
                WHERE user_id = %s AND subject_id = %s
                ORDER BY topic
            """, (user_id, subject_id))
            
            results = cursor.fetchall()
            return {topic: mastery_level for topic, mastery_level in results}
