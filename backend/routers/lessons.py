from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from routers.auth import get_current_user
from models.models import Lesson, Student, User
from schemas.schemas import LessonCreate, LessonUpdate, LessonOut

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/", response_model=List[LessonOut])
def get_lessons(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Lesson).join(Student).filter(
        Student.tutor_id == current_user.id
    ).all()


@router.get("/student/{student_id}", response_model=List[LessonOut])
def get_lessons_by_student(student_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.tutor_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ученик не найден"
        )
    return db.query(Lesson).filter(Lesson.student_id == student_id).all()


@router.get("/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lesson = db.query(Lesson).join(Student).filter(
        Lesson.id == lesson_id,
        Student.tutor_id == current_user.id
    ).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Занятие не найдено"
        )
    return lesson


@router.post("/", response_model=LessonOut)
def create_lesson(lesson_data: LessonCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(
        Student.id == lesson_data.student_id,
        Student.tutor_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ученик не найден"
        )
    lesson = Lesson(**lesson_data.model_dump())
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.put("/{lesson_id}", response_model=LessonOut)
def update_lesson(lesson_id: int, lesson_data: LessonUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lesson = db.query(Lesson).join(Student).filter(
        Lesson.id == lesson_id,
        Student.tutor_id == current_user.id
    ).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Занятие не найдено"
        )
    for key, value in lesson_data.model_dump(exclude_unset=True).items():
        setattr(lesson, key, value)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.delete("/{lesson_id}")
def delete_lesson(lesson_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lesson = db.query(Lesson).join(Student).filter(
        Lesson.id == lesson_id,
        Student.tutor_id == current_user.id
    ).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Занятие не найдено"
        )
    db.delete(lesson)
    db.commit()
    return {"message": "Занятие удалено"}

@router.delete("/series/{series_id}")
def delete_series(series_id: str, from_date: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Lesson).join(Student).filter(
        Lesson.series_id == series_id,
        Student.tutor_id == current_user.id
    )
    if from_date:
        from datetime import datetime
        dt = datetime.fromisoformat(from_date)
        query = query.filter(Lesson.scheduled_at >= dt)
    
    lessons = query.all()
    for lesson in lessons:
        db.delete(lesson)
    db.commit()
    return {"message": f"Удалено занятий: {len(lessons)}"}