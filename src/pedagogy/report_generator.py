"""
Weekly Report Generator

Generates teacher reports on student progress including:
- Total questions asked
- Topics covered with mastery levels
- Weak areas identified
- Recommended practice topics
- Progress trends
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import json


@dataclass
class Report:
    """Data structure for student progress report"""
    user_id: int
    username: str
    full_name: str
    subject_id: int
    subject_name: str
    start_date: date
    end_date: date
    total_questions: int
    topics_covered: Dict[str, float]  # topic -> mastery_level
    weak_areas: List[str]
    recommended_practice: List[str]
    progress_trend: str  # 'improving', 'stable', 'declining'
    generated_at: datetime


@dataclass
class ClassSummary:
    """Data structure for class-wide summary"""
    subject_id: int
    subject_name: str
    grade: int
    total_students: int
    active_students: int
    average_questions_per_student: float
    most_common_topics: List[str]
    most_common_weak_areas: List[str]
    class_average_mastery: float
    generated_at: datetime


class WeeklyReportGenerator:
    """
    Generates weekly progress reports for teachers
    
    Report includes:
    - Student name and grade
    - Subject and date range
    - Total questions asked
    - Topics covered with mastery levels
    - Weak areas identified
    - Recommended practice topics
    - Progress trend (improving/stable/declining)
    """
    
    def __init__(self, db_manager):
        """
        Initialize WeeklyReportGenerator
        
        Args:
            db_manager: DatabaseManager instance for persistence
        """
        self.db = db_manager
    
    def generate_report(self, user_id: int, subject_id: int,
                       start_date: date, end_date: date) -> Report:
        """
        Generate weekly progress report for a student
        
        Args:
            user_id: Student user ID
            subject_id: Subject ID
            start_date: Report start date
            end_date: Report end date
        
        Returns:
            Report object
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get student info
            cursor.execute("""
                SELECT username, full_name
                FROM users
                WHERE id = %s
            """, (user_id,))
            
            user_result = cursor.fetchone()
            if not user_result:
                raise ValueError(f"User {user_id} not found")
            
            username, full_name = user_result
            
            # Get subject info
            cursor.execute("""
                SELECT name
                FROM subjects
                WHERE id = %s
            """, (subject_id,))
            
            subject_result = cursor.fetchone()
            if not subject_result:
                raise ValueError(f"Subject {subject_id} not found")
            
            subject_name = subject_result[0]
            
            # Count questions in date range
            cursor.execute("""
                SELECT COUNT(*)
                FROM chat_history
                WHERE user_id = %s 
                  AND subject_id = %s
                  AND created_at >= %s
                  AND created_at <= %s
            """, (user_id, subject_id, start_date, end_date))
            
            total_questions = cursor.fetchone()[0]
            
            # Get topics covered with mastery levels
            cursor.execute("""
                SELECT topic, mastery_level
                FROM topic_mastery
                WHERE user_id = %s AND subject_id = %s
                ORDER BY mastery_level DESC
            """, (user_id, subject_id))
            
            topics_covered = {topic: mastery_level 
                            for topic, mastery_level in cursor.fetchall()}
            
            # Get weak areas
            cursor.execute("""
                SELECT topic
                FROM weak_areas
                WHERE user_id = %s AND subject_id = %s
                ORDER BY weakness_score DESC
            """, (user_id, subject_id))
            
            weak_areas = [topic for (topic,) in cursor.fetchall()]
            
            # Generate recommendations
            recommended_practice = self._generate_recommendations(
                weak_areas, topics_covered
            )
            
            # Calculate progress trend
            progress_trend = self._calculate_progress_trend(
                user_id, subject_id, start_date, end_date
            )
            
            # Create report
            report = Report(
                user_id=user_id,
                username=username,
                full_name=full_name,
                subject_id=subject_id,
                subject_name=subject_name,
                start_date=start_date,
                end_date=end_date,
                total_questions=total_questions,
                topics_covered=topics_covered,
                weak_areas=weak_areas,
                recommended_practice=recommended_practice,
                progress_trend=progress_trend,
                generated_at=datetime.now()
            )
            
            return report
            
        finally:
            cursor.close()
    
    def _generate_recommendations(self, weak_areas: List[str],
                                 topics_covered: Dict[str, float]) -> List[str]:
        """
        Generate practice recommendations based on weak areas
        
        Args:
            weak_areas: List of weak area topics
            topics_covered: Dictionary of topics and mastery levels
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Prioritize weakest areas
        for topic in weak_areas[:3]:  # Top 3 weak areas
            mastery = topics_covered.get(topic, 0.0)
            
            if mastery < 0.2:
                recommendations.append(
                    f"Focus on fundamental concepts of {topic}. "
                    f"Review textbook chapters and work through basic examples."
                )
            elif mastery < 0.4:
                recommendations.append(
                    f"Practice {topic} with progressively harder problems. "
                    f"Aim for consistent daily practice."
                )
            else:
                recommendations.append(
                    f"Continue practicing {topic} to improve retention. "
                    f"Try explaining concepts to others."
                )
        
        # Add general recommendations
        if len(weak_areas) > 3:
            recommendations.append(
                f"Also review: {', '.join(weak_areas[3:5])} when time permits."
            )
        
        return recommendations
    
    def _calculate_progress_trend(self, user_id: int, subject_id: int,
                                 start_date: date, end_date: date) -> str:
        """
        Calculate progress trend by comparing mastery levels over time
        
        Args:
            user_id: Student user ID
            subject_id: Subject ID
            start_date: Report start date
            end_date: Report end date
        
        Returns:
            Trend string: 'improving', 'stable', or 'declining'
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get average mastery at start of period
            period_start = datetime.combine(start_date, datetime.min.time())
            
            cursor.execute("""
                SELECT AVG(mastery_level)
                FROM topic_mastery
                WHERE user_id = %s 
                  AND subject_id = %s
                  AND updated_at <= %s
            """, (user_id, subject_id, period_start))
            
            start_avg = cursor.fetchone()[0] or 0.0
            
            # Get average mastery at end of period
            period_end = datetime.combine(end_date, datetime.max.time())
            
            cursor.execute("""
                SELECT AVG(mastery_level)
                FROM topic_mastery
                WHERE user_id = %s 
                  AND subject_id = %s
                  AND updated_at <= %s
            """, (user_id, subject_id, period_end))
            
            end_avg = cursor.fetchone()[0] or 0.0
            
            # Calculate trend
            if end_avg - start_avg > 0.1:
                return 'improving'
            elif end_avg - start_avg < -0.1:
                return 'declining'
            else:
                return 'stable'
                
        finally:
            cursor.close()
    
    def get_class_summary(self, subject_id: int, grade: int) -> ClassSummary:
        """
        Generate class-wide summary for teachers
        
        Args:
            subject_id: Subject ID
            grade: Grade level
        
        Returns:
            ClassSummary object
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get subject info
            cursor.execute("""
                SELECT name
                FROM subjects
                WHERE id = %s
            """, (subject_id,))
            
            subject_result = cursor.fetchone()
            if not subject_result:
                raise ValueError(f"Subject {subject_id} not found")
            
            subject_name = subject_result[0]
            
            # Count total students in grade
            cursor.execute("""
                SELECT COUNT(DISTINCT u.id)
                FROM users u
                WHERE u.role = 'student'
            """)
            
            total_students = cursor.fetchone()[0]
            
            # Count active students (asked questions in last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id)
                FROM chat_history
                WHERE subject_id = %s
                  AND created_at >= %s
            """, (subject_id, seven_days_ago))
            
            active_students = cursor.fetchone()[0]
            
            # Calculate average questions per student
            cursor.execute("""
                SELECT COUNT(*) / NULLIF(COUNT(DISTINCT user_id), 0)
                FROM chat_history
                WHERE subject_id = %s
                  AND created_at >= %s
            """, (subject_id, seven_days_ago))
            
            avg_questions = cursor.fetchone()[0] or 0.0
            
            # Get most common topics
            cursor.execute("""
                SELECT topic, COUNT(*) as count
                FROM topic_mastery
                WHERE subject_id = %s
                GROUP BY topic
                ORDER BY count DESC
                LIMIT 5
            """, (subject_id,))
            
            most_common_topics = [topic for topic, _ in cursor.fetchall()]
            
            # Get most common weak areas
            cursor.execute("""
                SELECT topic, COUNT(*) as count
                FROM weak_areas
                WHERE subject_id = %s
                GROUP BY topic
                ORDER BY count DESC
                LIMIT 5
            """, (subject_id,))
            
            most_common_weak_areas = [topic for topic, _ in cursor.fetchall()]
            
            # Calculate class average mastery
            cursor.execute("""
                SELECT AVG(mastery_level)
                FROM topic_mastery
                WHERE subject_id = %s
            """, (subject_id,))
            
            class_avg_mastery = cursor.fetchone()[0] or 0.0
            
            # Create summary
            summary = ClassSummary(
                subject_id=subject_id,
                subject_name=subject_name,
                grade=grade,
                total_students=total_students,
                active_students=active_students,
                average_questions_per_student=float(avg_questions),
                most_common_topics=most_common_topics,
                most_common_weak_areas=most_common_weak_areas,
                class_average_mastery=float(class_avg_mastery),
                generated_at=datetime.now()
            )
            
            return summary
            
        finally:
            cursor.close()
    
    def export_report(self, report: Report, format: str = 'json') -> bytes:
        """
        Export report in specified format
        
        Args:
            report: Report object to export
            format: Export format ('json' or 'text')
        
        Returns:
            Exported report as bytes
        """
        if format == 'json':
            return self._export_json(report)
        elif format == 'text':
            return self._export_text(report)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self, report: Report) -> bytes:
        """Export report as JSON"""
        report_dict = {
            'user_id': report.user_id,
            'username': report.username,
            'full_name': report.full_name,
            'subject_id': report.subject_id,
            'subject_name': report.subject_name,
            'start_date': report.start_date.isoformat(),
            'end_date': report.end_date.isoformat(),
            'total_questions': report.total_questions,
            'topics_covered': report.topics_covered,
            'weak_areas': report.weak_areas,
            'recommended_practice': report.recommended_practice,
            'progress_trend': report.progress_trend,
            'generated_at': report.generated_at.isoformat(),
        }
        
        return json.dumps(report_dict, indent=2).encode('utf-8')
    
    def _export_text(self, report: Report) -> bytes:
        """Export report as plain text"""
        lines = [
            "=" * 60,
            "WEEKLY PROGRESS REPORT",
            "=" * 60,
            "",
            f"Student: {report.full_name} ({report.username})",
            f"Subject: {report.subject_name}",
            f"Period: {report.start_date} to {report.end_date}",
            f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "-" * 60,
            "ACTIVITY SUMMARY",
            "-" * 60,
            f"Total Questions Asked: {report.total_questions}",
            f"Progress Trend: {report.progress_trend.upper()}",
            "",
            "-" * 60,
            "TOPICS COVERED",
            "-" * 60,
        ]
        
        for topic, mastery in sorted(report.topics_covered.items(), 
                                    key=lambda x: x[1], reverse=True):
            mastery_pct = mastery * 100
            lines.append(f"  {topic:20s} - Mastery: {mastery_pct:5.1f}%")
        
        if report.weak_areas:
            lines.extend([
                "",
                "-" * 60,
                "WEAK AREAS IDENTIFIED",
                "-" * 60,
            ])
            for topic in report.weak_areas:
                lines.append(f"  • {topic}")
        
        if report.recommended_practice:
            lines.extend([
                "",
                "-" * 60,
                "RECOMMENDATIONS",
                "-" * 60,
            ])
            for i, recommendation in enumerate(report.recommended_practice, 1):
                lines.append(f"  {i}. {recommendation}")
        
        lines.extend([
            "",
            "=" * 60,
        ])
        
        return '\n'.join(lines).encode('utf-8')
