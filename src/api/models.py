"""
API Data Models
Pydantic models for request/response validation
"""

from pydantic import BaseModel
from typing import List, Optional, Dict


# ===========================
# Authentication Models
# ===========================
class LoginRequest(BaseModel):
    username: str
    password: str
    role: str


class LoginResponse(BaseModel):
    success: bool
    token: str
    message: str
    role: str


class TokenVerifyRequest(BaseModel):
    pass


class TokenVerifyResponse(BaseModel):
    valid: bool
    role: Optional[str] = None
    username: Optional[str] = None


# ===========================
# Chat Models
# ===========================
class ChatRequest(BaseModel):
    message: str
    subject_filter: Optional[str] = "all"
    history: Optional[List[Dict]] = []


class ChatResponse(BaseModel):
    response: str
    source: Optional[str] = None
    confidence: Optional[float] = None


# ===========================
# Teacher Dashboard Models
# ===========================
class TeacherStats(BaseModel):
    total_questions: int
    popular_topic: str
    active_students: int
    topics: List[Dict]


# ===========================
# Admin Panel Models
# ===========================
class AdminStatus(BaseModel):
    model_status: str
    db_status: str
    version: str
    ram_usage: str
    storage_usage: str


# ===========================
# Queue Models
# ===========================
class QueueStats(BaseModel):
    active_count: int
    queued_count: int
    completed_count: int
    max_concurrent: int
    queue_full: bool
    max_queue_size: int


# ===========================
# Student Progress Models
# ===========================
class WeakArea(BaseModel):
    topic: str
    mastery_level: float
    weakness_score: float
    recommendation: str


class PracticeQuestion(BaseModel):
    topic: str
    difficulty: str
    question: str
    hint: str


class StudentProgress(BaseModel):
    success: bool
    mastery_levels: Dict[str, float]
    weak_areas: List[WeakArea]
    total_questions: int
    average_mastery: float
