"""
Weak Area Detector

Identifies topics where students need additional practice based on:
- Low mastery levels (< 0.4 threshold)
- High question frequency
- Low complexity questions
- Short retention periods
"""

from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class WeakArea:
    """Data structure for weak area information"""
    topic: str
    mastery_level: float
    weakness_score: float
    question_count: int
    avg_complexity: float
    last_question_date: datetime
    recommendation: str


class WeakAreaDetector:
    """
    Detects weak areas based on mastery levels and question patterns
    
    Weak area criteria:
    1. Mastery level < 0.4 (threshold)
    2. High question frequency (> 5 questions in 7 days)
    3. Low complexity questions (avg < 0.5)
    4. Short retention (< 3 days between questions)
    """
    
    def __init__(self, db_manager, mastery_threshold: float = 0.4):
        """
        Initialize WeakAreaDetector
        
        Args:
            db_manager: DatabaseManager instance for persistence
            mastery_threshold: Threshold below which a topic is considered weak (default: 0.4)
        """
        self.db = db_manager
        self.mastery_threshold = mastery_threshold
    
    def calculate_weakness_score(self, mastery_level: float, question_count: int,
                                 avg_complexity: float, retention_days: int) -> float:
        """
        Calculate weakness score (higher = more need for practice)
        
        Args:
            mastery_level: Current mastery level (0.0 to 1.0)
            question_count: Number of questions asked
            avg_complexity: Average question complexity (0.0 to 1.0)
            retention_days: Days since last question
        
        Returns:
            Weakness score (0.0 to 1.0, higher = weaker)
        """
        # Invert mastery level (low mastery = high weakness)
        mastery_weakness = 1.0 - mastery_level
        
        # High question frequency indicates struggle
        frequency_weakness = min(question_count / 10.0, 1.0)
        
        # Low complexity indicates avoiding difficult questions
        complexity_weakness = 1.0 - avg_complexity
        
        # Short retention indicates poor understanding
        retention_weakness = 1.0 - min(retention_days / 7.0, 1.0)
        
        # Weighted combination
        weakness_score = (
            mastery_weakness * 0.4 +
            frequency_weakness * 0.3 +
            complexity_weakness * 0.2 +
            retention_weakness * 0.1
        )
        
        return max(0.0, min(weakness_score, 1.0))
    
    def is_weak_area(self, mastery_level: float, question_count: int,
                    avg_complexity: float, retention_days: int) -> bool:
        """
        Determine if a topic qualifies as a weak area
        
        Args:
            mastery_level: Current mastery level (0.0 to 1.0)
            question_count: Number of questions asked
            avg_complexity: Average question complexity (0.0 to 1.0)
            retention_days: Days since last question
        
        Returns:
            True if topic is a weak area, False otherwise
        """
        # Primary criterion: low mastery
        if mastery_level < self.mastery_threshold:
            return True
        
        # Secondary criterion: high frequency with short retention
        if question_count > 5 and retention_days < 3:
            return True
        
        # Tertiary criterion: low complexity with high frequency
        if avg_complexity < 0.5 and question_count > 3:
            return True
        
        return False
    
    def detect_weak_areas(self, user_id: int, subject_id: int,
                         threshold: Optional[float] = None) -> List[WeakArea]:
        """
        Detect all weak areas for a student in a subject
        
        Args:
            user_id: Student user ID
            subject_id: Subject ID
            threshold: Optional custom mastery threshold (default: use instance threshold)
        
        Returns:
            List of WeakArea objects, sorted by weakness score (descending)
        """
        if threshold is None:
            threshold = self.mastery_threshold
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all topics with mastery data
            cursor.execute("""
                SELECT topic, mastery_level, question_count, avg_complexity, last_question_date
                FROM topic_mastery
                WHERE user_id = %s AND subject_id = %s
                ORDER BY mastery_level ASC
            """, (user_id, subject_id))
            
            results = cursor.fetchall()
            weak_areas = []
            
            for topic, mastery_level, question_count, avg_complexity, last_question_date in results:
                # Calculate retention days
                retention_days = (datetime.now() - last_question_date).days
                
                # Check if weak area
                if self.is_weak_area(mastery_level, question_count, avg_complexity, retention_days):
                    # Calculate weakness score
                    weakness_score = self.calculate_weakness_score(
                        mastery_level, question_count, avg_complexity, retention_days
                    )
                    
                    # Generate recommendation
                    recommendation = self.recommend_practice(
                        topic, mastery_level, question_count, avg_complexity
                    )
                    
                    weak_area = WeakArea(
                        topic=topic,
                        mastery_level=mastery_level,
                        weakness_score=weakness_score,
                        question_count=question_count,
                        avg_complexity=avg_complexity,
                        last_question_date=last_question_date,
                        recommendation=recommendation
                    )
                    
                    weak_areas.append(weak_area)
                    
                    # Store in database
                    self._store_weak_area(user_id, subject_id, weak_area)
            
            cursor.close()
            
            # Sort by weakness score (highest first)
            weak_areas.sort(key=lambda x: x.weakness_score, reverse=True)
            
            return weak_areas
    
    def _store_weak_area(self, user_id: int, subject_id: int, weak_area: WeakArea):
        """
        Store weak area in database
        
        Args:
            user_id: Student user ID
            subject_id: Subject ID
            weak_area: WeakArea object to store
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if weak area already exists
            cursor.execute("""
                SELECT id FROM weak_areas
                WHERE user_id = %s AND subject_id = %s AND topic = %s
            """, (user_id, subject_id, weak_area.topic))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing record
                cursor.execute("""
                    UPDATE weak_areas
                    SET weakness_score = %s,
                        recommendation = %s,
                        detected_at = %s
                    WHERE user_id = %s AND subject_id = %s AND topic = %s
                """, (weak_area.weakness_score, weak_area.recommendation,
                     datetime.now(), user_id, subject_id, weak_area.topic))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO weak_areas
                    (user_id, subject_id, topic, weakness_score, recommendation, detected_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, subject_id, weak_area.topic, weak_area.weakness_score,
                     weak_area.recommendation, datetime.now()))
            
            conn.commit()
            cursor.close()
    
    def get_weakness_score(self, user_id: int, subject_id: int, topic: str) -> float:
        """
        Get weakness score for a specific topic
        
        Args:
            user_id: Student user ID
            subject_id: Subject ID
            topic: Topic name
        
        Returns:
            Weakness score (0.0 to 1.0), or 0.0 if no data exists
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT weakness_score
                FROM weak_areas
                WHERE user_id = %s AND subject_id = %s AND topic = %s
            """, (user_id, subject_id, topic))
            
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else 0.0
    
    def recommend_practice(self, topic: str, mastery_level: float,
                          question_count: int, avg_complexity: float) -> str:
        """
        Generate practice recommendation based on weak area characteristics
        
        Args:
            topic: Topic name
            mastery_level: Current mastery level
            question_count: Number of questions asked
            avg_complexity: Average question complexity
        
        Returns:
            Recommendation string
        """
        if mastery_level < 0.2:
            return f"Review fundamental concepts of {topic}. Start with basic examples and definitions."
        elif mastery_level < 0.4:
            if avg_complexity < 0.5:
                return f"Practice {topic} with progressively harder problems. Challenge yourself with more complex questions."
            else:
                return f"Continue practicing {topic}. Focus on understanding core principles before moving to advanced topics."
        elif question_count > 5:
            return f"You're asking many questions about {topic}. Consider reviewing your notes or textbook systematically."
        else:
            return f"Practice {topic} regularly to improve retention and understanding."
