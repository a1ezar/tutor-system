from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from routers.auth import get_current_user
from models.models import Student, User
from schemas.schemas import StudentCreate, StudentUpdate, StudentOut

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/", response_model=List[StudentOut])
def get_students(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Student).filter(Student.tutor_id == current_user.id).all()


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.tutor_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ученик не найден"
        )
    return student


@router.post("/", response_model=StudentOut)
def create_student(student_data: StudentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = Student(
        **student_data.model_dump(),
        tutor_id=current_user.id
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, student_data: StudentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.tutor_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ученик не найден"
        )
    for key, value in student_data.model_dump(exclude_unset=True).items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.tutor_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ученик не найден"
        )
    db.delete(student)
    db.commit()
    return {"message": "Ученик удалён"}