from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base
import enum


class UserRole(str, enum.Enum):
    tutor = "tutor"
    student = "student"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="tutor", nullable=False)  # "tutor" или "student"
    created_at = Column(DateTime, default=datetime.utcnow)

    students = relationship("Student", back_populates="tutor", foreign_keys="Student.tutor_id")
    # Если пользователь — ученик, ссылка на его профиль Student
    student_profile = relationship("Student", back_populates="user_account", foreign_keys="Student.user_id", uselist=False)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    tutor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)  # аккаунт ученика
    created_at = Column(DateTime, default=datetime.utcnow)

    tutor = relationship("User", back_populates="students", foreign_keys=[tutor_id])
    user_account = relationship("User", back_populates="student_profile", foreign_keys=[user_id])
    lessons = relationship("Lesson", back_populates="student")
    grades = relationship("Grade", back_populates="student")
    homework_attempts = relationship("HomeworkAttempt", back_populates="student")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    topic = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    completed = Column(Integer, default=0)
    series_id = Column(String, nullable=True, index=True)

    student = relationship("Student", back_populates="lessons")
    grades = relationship("Grade", back_populates="lesson")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    topic = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="grades")
    lesson = relationship("Lesson", back_populates="grades")


# ============================================================
# ДОМАШНИЕ ЗАДАНИЯ
# ============================================================

class Homework(Base):
    """Домашнее задание, созданное репетитором"""
    __tablename__ = "homeworks"

    id = Column(Integer, primary_key=True, index=True)
    tutor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tutor = relationship("User")
    student = relationship("Student")
    questions = relationship("Question", back_populates="homework", cascade="all, delete-orphan")
    attempts = relationship("HomeworkAttempt", back_populates="homework", cascade="all, delete-orphan")


class Question(Base):
    """Вопрос в домашнем задании"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    homework_id = Column(Integer, ForeignKey("homeworks.id", ondelete="CASCADE"), nullable=False)
    order_num = Column(Integer, default=1)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)  # "test", "number", "text"
    # Для теста — варианты ответа (JSON строка: ["вариант1", "вариант2", ...])
    options = Column(Text, nullable=True)
    # Правильный ответ: для теста — индекс (0,1,2,3), для number — число, для text — эталонный текст
    correct_answer = Column(String, nullable=False)
    points = Column(Float, default=1.0)  # баллы за вопрос

    homework = relationship("Homework", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class HomeworkAttempt(Base):
    """Попытка выполнения ДЗ учеником"""
    __tablename__ = "homework_attempts"

    id = Column(Integer, primary_key=True, index=True)
    homework_id = Column(Integer, ForeignKey("homeworks.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    score = Column(Float, nullable=True)  # итоговый балл (рассчитывается автоматически)
    max_score = Column(Float, nullable=True)  # максимально возможный балл
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    homework = relationship("Homework", back_populates="attempts")
    student = relationship("Student", back_populates="homework_attempts")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete-orphan")


class Answer(Base):
    """Ответ ученика на вопрос"""
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("homework_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    student_answer = Column(String, nullable=True)  # ответ ученика
    is_correct = Column(Integer, nullable=True)  # 1 = верно, 0 = неверно, NULL = не проверено
    points_earned = Column(Float, default=0.0)

    attempt = relationship("HomeworkAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")