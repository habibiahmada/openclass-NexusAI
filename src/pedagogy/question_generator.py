"""
Adaptive Question Generator

Generates practice questions targeting weak areas with difficulty adjustment
based on current mastery level.
"""

from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
import random


@dataclass
class Question:
    """Data structure for practice questions"""
    id: Optional[int]
    subject_id: int
    topic: str
    difficulty: str
    question_text: str
    answer_hint: Optional[str]
    created_at: datetime


class AdaptiveQuestionGenerator:
    """
    Generates adaptive practice questions targeting weak areas
    
    Difficulty levels based on mastery:
    - 0.0 - 0.3: easy (foundational concepts)
    - 0.3 - 0.6: medium (application problems)
    - 0.6 - 1.0: hard (complex scenarios)
    """
    
    # Question templates by subject and topic
    QUESTION_TEMPLATES = {
        'matematika': {
            'aljabar': {
                'easy': [
                    "Selesaikan persamaan linear: {a}x + {b} = {c}",
                    "Tentukan nilai x dari persamaan: {a}x = {b}",
                    "Sederhanakan ekspresi: {a}x + {b}x",
                ],
                'medium': [
                    "Selesaikan persamaan kuadrat: {a}x² + {b}x + {c} = 0",
                    "Tentukan akar-akar dari persamaan: x² - {a}x + {b} = 0",
                    "Faktorkan polinomial: x² + {a}x + {b}",
                ],
                'hard': [
                    "Buktikan bahwa jika f(x) = {a}x² + {b}x + {c}, maka f'(x) = {d}x + {e}",
                    "Tentukan domain dan range dari fungsi: f(x) = √({a}x + {b})",
                    "Selesaikan sistem persamaan: {a}x + {b}y = {c} dan {d}x + {e}y = {f}",
                ],
            },
            'geometri': {
                'easy': [
                    "Hitung luas segitiga dengan alas {a} cm dan tinggi {b} cm",
                    "Hitung keliling persegi dengan sisi {a} cm",
                    "Hitung luas lingkaran dengan jari-jari {a} cm (π = 3.14)",
                ],
                'medium': [
                    "Sebuah segitiga memiliki sisi {a} cm, {b} cm, dan {c} cm. Hitung luasnya menggunakan rumus Heron",
                    "Hitung volume kubus dengan panjang rusuk {a} cm",
                    "Tentukan panjang sisi miring segitiga siku-siku dengan sisi {a} cm dan {b} cm",
                ],
                'hard': [
                    "Buktikan teorema Pythagoras menggunakan luas persegi",
                    "Hitung luas permukaan bola dengan jari-jari {a} cm",
                    "Tentukan sudut antara dua vektor: v₁ = ({a}, {b}) dan v₂ = ({c}, {d})",
                ],
            },
            'trigonometri': {
                'easy': [
                    "Hitung sin({a}°) jika diketahui segitiga siku-siku dengan sisi depan {b} dan hipotenusa {c}",
                    "Tentukan nilai cos(0°) dan sin(90°)",
                    "Jika tan(θ) = {a}/{b}, tentukan nilai θ",
                ],
                'medium': [
                    "Buktikan identitas: sin²(θ) + cos²(θ) = 1",
                    "Selesaikan persamaan: sin(x) = {a} untuk 0° ≤ x ≤ 360°",
                    "Hitung nilai tan(45°) + sin(30°) + cos(60°)",
                ],
                'hard': [
                    "Buktikan rumus sudut ganda: sin(2θ) = 2sin(θ)cos(θ)",
                    "Selesaikan persamaan trigonometri: {a}sin(x) + {b}cos(x) = {c}",
                    "Tentukan nilai maksimum dan minimum dari f(x) = {a}sin(x) + {b}cos(x)",
                ],
            },
        },
        'informatika': {
            'pemrograman': {
                'easy': [
                    "Tulis program Python untuk mencetak 'Hello World'",
                    "Buat variabel untuk menyimpan nama dan umur, lalu cetak hasilnya",
                    "Tulis fungsi untuk menghitung luas persegi panjang",
                ],
                'medium': [
                    "Tulis program untuk mencari bilangan prima antara 1 dan {a}",
                    "Buat fungsi rekursif untuk menghitung faktorial dari {a}",
                    "Implementasikan algoritma bubble sort untuk mengurutkan array",
                ],
                'hard': [
                    "Implementasikan algoritma quicksort dengan kompleksitas O(n log n)",
                    "Tulis program untuk menyelesaikan masalah knapsack menggunakan dynamic programming",
                    "Buat class untuk implementasi binary search tree dengan operasi insert, delete, dan search",
                ],
            },
            'struktur_data': {
                'easy': [
                    "Jelaskan perbedaan antara array dan linked list",
                    "Buat implementasi stack menggunakan list Python",
                    "Tulis fungsi untuk menambah elemen ke queue",
                ],
                'medium': [
                    "Implementasikan linked list dengan operasi insert, delete, dan search",
                    "Buat binary tree dan implementasikan traversal in-order",
                    "Jelaskan kompleksitas waktu untuk operasi pada hash table",
                ],
                'hard': [
                    "Implementasikan AVL tree dengan operasi balancing",
                    "Buat graph menggunakan adjacency list dan implementasikan BFS dan DFS",
                    "Implementasikan heap sort dengan kompleksitas O(n log n)",
                ],
            },
        },
    }
    
    def __init__(self, db_manager):
        """
        Initialize AdaptiveQuestionGenerator
        
        Args:
            db_manager: DatabaseManager instance for persistence
        """
        self.db = db_manager
    
    def adjust_difficulty(self, mastery_level: float) -> str:
        """
        Adjust question difficulty based on mastery level
        
        Args:
            mastery_level: Current mastery level (0.0 to 1.0)
        
        Returns:
            Difficulty level: 'easy', 'medium', or 'hard'
        """
        if mastery_level < 0.3:
            return 'easy'
        elif mastery_level < 0.6:
            return 'medium'
        else:
            return 'hard'
    
    def generate_question(self, subject_id: int, topic: str, 
                         difficulty: str, mastery_level: float,
                         subject_name: str = 'matematika') -> Question:
        """
        Generate a practice question for a specific topic
        
        Args:
            subject_id: Subject ID
            topic: Topic name
            difficulty: Difficulty level ('easy', 'medium', 'hard')
            mastery_level: Current mastery level (for context)
            subject_name: Subject name (default: 'matematika')
        
        Returns:
            Question object
        """
        # Get templates for subject and topic
        subject_templates = self.QUESTION_TEMPLATES.get(subject_name, {})
        topic_templates = subject_templates.get(topic, {})
        
        # Get templates for difficulty level
        difficulty_templates = topic_templates.get(difficulty, [])
        
        if not difficulty_templates:
            # Fallback to generic question
            question_text = f"Practice problem for {topic} at {difficulty} level"
            answer_hint = "Review your textbook and notes for this topic"
        else:
            # Select random template
            template = random.choice(difficulty_templates)
            
            # Generate random values for placeholders
            values = {
                'a': random.randint(1, 10),
                'b': random.randint(1, 10),
                'c': random.randint(1, 20),
                'd': random.randint(1, 10),
                'e': random.randint(1, 10),
                'f': random.randint(1, 20),
            }
            
            # Format template with values
            question_text = template.format(**values)
            answer_hint = self._generate_hint(topic, difficulty)
        
        # Create question object
        question = Question(
            id=None,
            subject_id=subject_id,
            topic=topic,
            difficulty=difficulty,
            question_text=question_text,
            answer_hint=answer_hint,
            created_at=datetime.now()
        )
        
        # Store in database
        question_id = self._store_question(question)
        question.id = question_id
        
        return question
    
    def _generate_hint(self, topic: str, difficulty: str) -> str:
        """
        Generate answer hint based on topic and difficulty
        
        Args:
            topic: Topic name
            difficulty: Difficulty level
        
        Returns:
            Hint string
        """
        hints = {
            'easy': f"Review the basic concepts of {topic}. Start with definitions and simple examples.",
            'medium': f"Apply the formulas and methods you learned for {topic}. Break the problem into steps.",
            'hard': f"This requires deep understanding of {topic}. Consider multiple approaches and verify your answer.",
        }
        
        return hints.get(difficulty, "Work through the problem step by step.")
    
    def _store_question(self, question: Question) -> int:
        """
        Store question in database
        
        Args:
            question: Question object to store
        
        Returns:
            Question ID
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO practice_questions
                (subject_id, topic, difficulty, question_text, answer_hint, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (question.subject_id, question.topic, question.difficulty,
                 question.question_text, question.answer_hint, question.created_at))
            
            question_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            return question_id
    
    def get_practice_set(self, user_id: int, subject_id: int, count: int = 5,
                        subject_name: str = 'matematika') -> List[Question]:
        """
        Generate a set of practice questions targeting weak areas
        
        Args:
            user_id: Student user ID
            subject_id: Subject ID
            count: Number of questions to generate (default: 5)
            subject_name: Subject name (default: 'matematika')
        
        Returns:
            List of Question objects
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get weak areas ordered by weakness score
            cursor.execute("""
                SELECT wa.topic, tm.mastery_level
                FROM weak_areas wa
                JOIN topic_mastery tm ON 
                    wa.user_id = tm.user_id AND 
                    wa.subject_id = tm.subject_id AND 
                    wa.topic = tm.topic
                WHERE wa.user_id = %s AND wa.subject_id = %s
                ORDER BY wa.weakness_score DESC
                LIMIT %s
            """, (user_id, subject_id, count))
            
            weak_areas = cursor.fetchall()
            cursor.close()
            
            if not weak_areas:
                # No weak areas, return empty list
                return []
            
            # Generate questions for each weak area
            questions = []
            for topic, mastery_level in weak_areas:
                difficulty = self.adjust_difficulty(mastery_level)
                question = self.generate_question(
                    subject_id, topic, difficulty, mastery_level, subject_name
                )
                questions.append(question)
            
            return questions
