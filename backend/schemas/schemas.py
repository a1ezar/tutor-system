from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


# --- User ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str = "tutor"
    created_at: datetime

    class Config:
        from_attributes = True


# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# --- Student ---
class StudentCreate(BaseModel):
    full_name: str
    subject: str
    phone: Optional[str] = None
    notes: Optional[str] = None

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    subject: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

class StudentOut(BaseModel):
    id: int
    full_name: str
    subject: str
    phone: Optional[str]
    notes: Optional[str]
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Создание аккаунта ученика ---
class StudentAccountCreate(BaseModel):
    student_id: int
    email: EmailStr
    password: str


# --- Lesson ---
class LessonCreate(BaseModel):
    student_id: int
    scheduled_at: datetime
    duration_minutes: Optional[int] = 60
    topic: Optional[str] = None
    notes: Optional[str] = None
    series_id: Optional[str] = None

class LessonUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    topic: Optional[str] = None
    notes: Optional[str] = None
    completed: Optional[int] = None

class LessonOut(BaseModel):
    id: int
    student_id: int
    scheduled_at: datetime
    duration_minutes: int
    topic: Optional[str]
    notes: Optional[str]
    completed: int
    series_id: Optional[str] = None

    class Config:
        from_attributes = True


# --- Grade ---
class GradeCreate(BaseModel):
    student_id: int
    lesson_id: Optional[int] = None
    topic: str
    value: float
    comment: Optional[str] = None

class GradeUpdate(BaseModel):
    topic: Optional[str] = None
    value: Optional[float] = None
    comment: Optional[str] = None

class GradeOut(BaseModel):
    id: int
    student_id: int
    lesson_id: Optional[int]
    topic: str
    value: float
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# ДОМАШНИЕ ЗАДАНИЯ
# ============================================================

# --- Question ---
class QuestionCreate(BaseModel):
    question_text: str
    question_type: str  # "test", "number", "text"
    options: Optional[str] = None  # JSON строка для тестов
    correct_answer: str
    points: Optional[float] = 1.0

class QuestionOut(BaseModel):
    id: int
    order_num: int
    question_text: str
    question_type: str
    options: Optional[str]
    correct_answer: Optional[str] = None  # скрываем от ученика при выдаче
    points: float

    class Config:
        from_attributes = True

class QuestionForStudent(BaseModel):
    """Вопрос без правильного ответа — для ученика"""
    id: int
    order_num: int
    question_text: str
    question_type: str
    options: Optional[str]
    points: float

    class Config:
        from_attributes = True


# --- Homework ---
class HomeworkCreate(BaseModel):
    student_id: int
    title: str
    topic: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    questions: List[QuestionCreate]

class HomeworkOut(BaseModel):
    id: int
    student_id: int
    title: str
    topic: str
    description: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime
    questions: List[QuestionOut] = []

    class Config:
        from_attributes = True

class HomeworkForStudent(BaseModel):
    """ДЗ для ученика — без правильных ответов"""
    id: int
    title: str
    topic: str
    description: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime
    questions: List[QuestionForStudent] = []
    status: str = "new"  # "new", "in_progress", "completed"

    class Config:
        from_attributes = True

class HomeworkListItem(BaseModel):
    id: int
    student_id: int
    student_name: str = ""
    title: str
    topic: str
    due_date: Optional[datetime]
    created_at: datetime
    questions_count: int = 0
    attempts_count: int = 0
    best_score: Optional[float] = None

    class Config:
        from_attributes = True


# --- Answer ---
class AnswerSubmit(BaseModel):
    question_id: int
    student_answer: str

class AnswerOut(BaseModel):
    id: int
    question_id: int
    student_answer: Optional[str]
    is_correct: Optional[int]
    points_earned: float

    class Config:
        from_attributes = True


# --- HomeworkAttempt ---
class HomeworkSubmit(BaseModel):
    answers: List[AnswerSubmit]

class AttemptOut(BaseModel):
    id: int
    homework_id: int
    score: Optional[float]
    max_score: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
    answers: List[AnswerOut] = []

    class Config:
        from_attributes = True

class AttemptResult(BaseModel):
    attempt_id: int
    score: float
    max_score: float
    percentage: float
    grade_10: float  # оценка по 10-балльной шкале
    answers: List[AnswerOut] = []
    auto_graded: bool = True