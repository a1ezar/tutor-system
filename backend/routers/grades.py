from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from routers.auth import get_current_user
from models.models import Grade, Student, User
from schemas.schemas import GradeCreate, GradeUpdate, GradeOut

router = APIRouter(prefix="/grades", tags=["grades"])


@router.get("/", response_model=List[GradeOut])
def get_grades(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Grade).join(Student).filter(
        Student.tutor_id == current_user.id
    ).all()


@router.get("/student/{student_id}", response_model=List[GradeOut])
def get_grades_by_student(student_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.tutor_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ученик не найден"
        )
    return db.query(Grade).filter(Grade.student_id == student_id).all()


@router.get("/{grade_id}", response_model=GradeOut)
def get_grade(grade_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    grade = db.query(Grade).join(Student).filter(
        Grade.id == grade_id,
        Student.tutor_id == current_user.id
    ).first()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оценка не найдена"
        )
    return grade


@router.post("/", response_model=GradeOut)
def create_grade(grade_data: GradeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(
        Student.id == grade_data.student_id,
        Student.tutor_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ученик не найден"
        )
    grade = Grade(**grade_data.model_dump())
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return grade


@router.put("/{grade_id}", response_model=GradeOut)
def update_grade(grade_id: int, grade_data: GradeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    grade = db.query(Grade).join(Student).filter(
        Grade.id == grade_id,
        Student.tutor_id == current_user.id
    ).first()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оценка не найдена"
        )
    for key, value in grade_data.model_dump(exclude_unset=True).items():
        setattr(grade, key, value)
    db.commit()
    db.refresh(grade)
    return grade


@router.delete("/{grade_id}")
def delete_grade(grade_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    grade = db.query(Grade).join(Student).filter(
        Grade.id == grade_id,
        Student.tutor_id == current_user.id
    ).first()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оценка не найдена"
        )
    db.delete(grade)
    db.commit()
    return {"message": "Оценка удалена"}