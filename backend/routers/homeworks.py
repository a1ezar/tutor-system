from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Optional
import json

from core.database import get_db
from routers.auth import get_current_user, require_tutor, require_student
from models.models import User, Student, Homework, Question, HomeworkAttempt, Answer, Grade
from schemas.schemas import (
    HomeworkCreate, HomeworkOut, HomeworkListItem, HomeworkForStudent,
    QuestionForStudent, HomeworkSubmit, AttemptResult, AnswerOut
)

router = APIRouter(prefix="/homeworks", tags=["homeworks"])


# ============================================================
# РЕПЕТИТОР: управление заданиями
# ============================================================

@router.post("/", response_model=HomeworkOut)
def create_homework(
    data: HomeworkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor)
):
    """Репетитор создаёт домашнее задание с вопросами"""
    # Проверяем что ученик принадлежит этому репетитору
    student = db.query(Student).filter(
        Student.id == data.student_id,
        Student.tutor_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    if len(data.questions) == 0:
        raise HTTPException(status_code=400, detail="Нужен минимум 1 вопрос")

    homework = Homework(
        tutor_id=current_user.id,
        student_id=data.student_id,
        title=data.title,
        topic=data.topic,
        description=data.description,
        due_date=data.due_date,
    )
    db.add(homework)
    db.flush()

    for i, q in enumerate(data.questions):
        question = Question(
            homework_id=homework.id,
            order_num=i + 1,
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            correct_answer=q.correct_answer,
            points=q.points or 1.0,
        )
        db.add(question)

    db.commit()
    db.refresh(homework)
    return homework


@router.get("/", response_model=list[HomeworkListItem])
def list_homeworks(
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor)
):
    """Репетитор получает список всех своих заданий"""
    query = db.query(Homework).filter(Homework.tutor_id == current_user.id)
    if student_id:
        query = query.filter(Homework.student_id == student_id)

    homeworks = query.order_by(Homework.created_at.desc()).all()

    result = []
    for hw in homeworks:
        student = db.query(Student).filter(Student.id == hw.student_id).first()
        questions_count = len(hw.questions)
        attempts = hw.attempts
        best_score = None
        if attempts:
            scores = [a.score for a in attempts if a.score is not None]
            if scores:
                best_score = max(scores)

        result.append(HomeworkListItem(
            id=hw.id,
            student_id=hw.student_id,
            student_name=student.full_name if student else "",
            title=hw.title,
            topic=hw.topic,
            due_date=hw.due_date,
            created_at=hw.created_at,
            questions_count=questions_count,
            attempts_count=len(attempts),
            best_score=best_score,
        ))

    return result


@router.get("/{homework_id}", response_model=HomeworkOut)
def get_homework(
    homework_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor)
):
    """Репетитор получает задание с вопросами и ответами"""
    homework = db.query(Homework).options(
        joinedload(Homework.questions)
    ).filter(
        Homework.id == homework_id,
        Homework.tutor_id == current_user.id
    ).first()
    if not homework:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    return homework


@router.delete("/{homework_id}")
def delete_homework(
    homework_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor)
):
    homework = db.query(Homework).filter(
        Homework.id == homework_id,
        Homework.tutor_id == current_user.id
    ).first()
    if not homework:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    db.delete(homework)
    db.commit()
    return {"detail": "Задание удалено"}


@router.get("/{homework_id}/attempts")
def get_homework_attempts(
    homework_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor)
):
    """Репетитор смотрит все попытки ученика по заданию"""
    homework = db.query(Homework).filter(
        Homework.id == homework_id,
        Homework.tutor_id == current_user.id
    ).first()
    if not homework:
        raise HTTPException(status_code=404, detail="Задание не найдено")

    attempts = db.query(HomeworkAttempt).options(
        joinedload(HomeworkAttempt.answers)
    ).filter(
        HomeworkAttempt.homework_id == homework_id
    ).order_by(HomeworkAttempt.started_at.desc()).all()

    result = []
    for attempt in attempts:
        result.append({
            "id": attempt.id,
            "score": attempt.score,
            "max_score": attempt.max_score,
            "percentage": round((attempt.score / attempt.max_score * 100), 1) if attempt.score and attempt.max_score else 0,
            "started_at": str(attempt.started_at),
            "completed_at": str(attempt.completed_at) if attempt.completed_at else None,
            "answers": [
                {
                    "question_id": a.question_id,
                    "student_answer": a.student_answer,
                    "is_correct": a.is_correct,
                    "points_earned": a.points_earned,
                }
                for a in attempt.answers
            ]
        })

    return {"homework_id": homework_id, "attempts": result}


# ============================================================
# УЧЕНИК: просмотр и выполнение заданий
# ============================================================

@router.get("/my/list")
def my_homeworks(
    db: Session = Depends(get_db),
    user_and_student=Depends(require_student)
):
    """Ученик получает список своих заданий"""
    current_user, student = user_and_student

    homeworks = db.query(Homework).filter(
        Homework.student_id == student.id
    ).order_by(Homework.created_at.desc()).all()

    result = []
    for hw in homeworks:
        # Определяем статус
        attempts = db.query(HomeworkAttempt).filter(
            HomeworkAttempt.homework_id == hw.id,
            HomeworkAttempt.student_id == student.id
        ).all()

        if not attempts:
            hw_status = "new"
        else:
            completed = [a for a in attempts if a.completed_at is not None]
            hw_status = "completed" if completed else "in_progress"

        best_score = None
        if attempts:
            scores = [a.score for a in attempts if a.score is not None]
            if scores:
                best_score = max(scores)

        result.append({
            "id": hw.id,
            "title": hw.title,
            "topic": hw.topic,
            "description": hw.description,
            "due_date": str(hw.due_date) if hw.due_date else None,
            "created_at": str(hw.created_at),
            "questions_count": len(hw.questions),
            "status": hw_status,
            "attempts_count": len(attempts),
            "best_score": best_score,
        })

    return {"homeworks": result}


@router.get("/my/{homework_id}")
def my_homework_detail(
    homework_id: int,
    db: Session = Depends(get_db),
    user_and_student=Depends(require_student)
):
    """Ученик получает задание для выполнения (без правильных ответов)"""
    current_user, student = user_and_student

    homework = db.query(Homework).options(
        joinedload(Homework.questions)
    ).filter(
        Homework.id == homework_id,
        Homework.student_id == student.id
    ).first()
    if not homework:
        raise HTTPException(status_code=404, detail="Задание не найдено")

    questions = []
    for q in sorted(homework.questions, key=lambda x: x.order_num):
        questions.append({
            "id": q.id,
            "order_num": q.order_num,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "options": q.options,
            "points": q.points,
            # correct_answer НЕ отдаём ученику!
        })

    return {
        "id": homework.id,
        "title": homework.title,
        "topic": homework.topic,
        "description": homework.description,
        "due_date": str(homework.due_date) if homework.due_date else None,
        "questions": questions,
    }


@router.post("/my/{homework_id}/submit", response_model=AttemptResult)
def submit_homework(
    homework_id: int,
    data: HomeworkSubmit,
    db: Session = Depends(get_db),
    user_and_student=Depends(require_student)
):
    """Ученик отправляет ответы — система автоматически проверяет"""
    current_user, student = user_and_student

    homework = db.query(Homework).options(
        joinedload(Homework.questions)
    ).filter(
        Homework.id == homework_id,
        Homework.student_id == student.id
    ).first()
    if not homework:
        raise HTTPException(status_code=404, detail="Задание не найдено")

    # Создаём попытку
    attempt = HomeworkAttempt(
        homework_id=homework_id,
        student_id=student.id,
    )
    db.add(attempt)
    db.flush()

    # Индексируем вопросы
    questions_map = {q.id: q for q in homework.questions}
    total_score = 0.0
    max_score = sum(q.points for q in homework.questions)

    answers_result = []

    for ans in data.answers:
        question = questions_map.get(ans.question_id)
        if not question:
            continue

        is_correct, points_earned = _check_answer(question, ans.student_answer)

        answer = Answer(
            attempt_id=attempt.id,
            question_id=question.id,
            student_answer=ans.student_answer,
            is_correct=is_correct,
            points_earned=points_earned,
        )
        db.add(answer)
        total_score += points_earned

        answers_result.append(AnswerOut(
            id=0,  # будет обновлено после commit
            question_id=question.id,
            student_answer=ans.student_answer,
            is_correct=is_correct,
            points_earned=points_earned,
        ))

    # Обновляем попытку
    attempt.score = round(total_score, 1)
    attempt.max_score = round(max_score, 1)
    attempt.completed_at = datetime.utcnow()

    # Автоматически выставляем оценку в Grade (по 10-балльной шкале)
    percentage = (total_score / max_score * 100) if max_score > 0 else 0
    grade_10 = round(total_score / max_score * 10, 1) if max_score > 0 else 0

    grade = Grade(
        student_id=student.id,
        topic=homework.topic,
        value=grade_10,
        comment=f"ДЗ: {homework.title} — {round(percentage, 1)}% ({round(total_score, 1)}/{round(max_score, 1)})",
    )
    db.add(grade)

    db.commit()

    return AttemptResult(
        attempt_id=attempt.id,
        score=round(total_score, 1),
        max_score=round(max_score, 1),
        percentage=round(percentage, 1),
        grade_10=grade_10,
        answers=answers_result,
        auto_graded=True,
    )


def _check_answer(question: Question, student_answer: str) -> tuple:
    """
    Автоматическая проверка ответа.
    Возвращает (is_correct: int, points_earned: float)
    """
    if not student_answer:
        return (0, 0.0)

    correct = question.correct_answer.strip()
    answer = student_answer.strip()

    if question.question_type == "test":
        # Для теста — сравниваем индекс выбранного варианта
        is_correct = 1 if answer == correct else 0
        return (is_correct, question.points if is_correct else 0.0)

    elif question.question_type == "number":
        # Для числового — сравниваем с допуском
        try:
            correct_num = float(correct)
            answer_num = float(answer)
            # Допуск 0.01 для округления
            is_correct = 1 if abs(correct_num - answer_num) < 0.01 else 0
            return (is_correct, question.points if is_correct else 0.0)
        except ValueError:
            return (0, 0.0)

    elif question.question_type == "text":
        # Для текста — точное совпадение (без учёта регистра)
        is_correct = 1 if answer.lower() == correct.lower() else 0
        return (is_correct, question.points if is_correct else 0.0)

    return (0, 0.0)