from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from routers.auth import get_current_user
from models.models import User, Student, Grade, Lesson
from ml.predictor import (
    full_analysis, predict_next_grade, classify_risk,
    analyze_topics, recommend_review_topics, cluster_students,
    get_model_info,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/student/{student_id}")
def get_student_analytics(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.tutor_id == current_user.id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    grades = db.query(Grade).filter(Grade.student_id == student_id).all()
    grades_data = [
        {
            "id": g.id,
            "value": g.value,
            "topic": g.topic,
            "created_at": str(g.created_at)
        }
        for g in grades
    ]

    analysis = full_analysis(grades_data)
    return {
        "student_id": student_id,
        "student_name": student.full_name,
        "grades_count": len(grades_data),
        **analysis
    }


@router.get("/overview")
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    students = db.query(Student).filter(Student.tutor_id == current_user.id).all()

    result = []
    for student in students:
        grades = db.query(Grade).filter(Grade.student_id == student.id).all()
        grades_data = [
            {
                "id": g.id,
                "value": g.value,
                "topic": g.topic,
                "created_at": str(g.created_at)
            }
            for g in grades
        ]

        risk = classify_risk(grades_data)
        prediction = predict_next_grade(grades_data)

        result.append({
            "student_id": student.id,
            "student_name": student.full_name,
            "subject": student.subject,
            "grades_count": len(grades_data),
            "avg_grade": risk.get("avg_grade"),
            "risk_level": risk.get("risk_level"),
            "risk_label": risk.get("risk_label"),
            "risk_color": risk.get("risk_color"),
            "predicted_next": prediction.get("predicted"),
            "trend": prediction.get("trend"),
            "trend_label": prediction.get("trend_label")
        })

    return {
        "total_students": len(students),
        "students": result
    }


@router.get("/clusters")
def get_clusters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Кластеризация всех учеников репетитора по паттернам обучения"""
    students = db.query(Student).filter(Student.tutor_id == current_user.id).all()

    students_data = []
    for student in students:
        grades = db.query(Grade).filter(Grade.student_id == student.id).all()
        lessons_count = db.query(Lesson).filter(Lesson.student_id == student.id).count()

        grades_data = [
            {
                "id": g.id,
                "value": g.value,
                "topic": g.topic,
                "created_at": str(g.created_at)
            }
            for g in grades
        ]

        students_data.append({
            "student_id": student.id,
            "student_name": student.full_name,
            "subject": student.subject,
            "grades": grades_data,
            "lessons_count": lessons_count
        })

    result = cluster_students(students_data)
    return result


# ============================================================
# Информация о ML-моделях (для прозрачности и интерпретируемости)
# ============================================================

@router.get("/model-info")
def get_models_info(
    current_user: User = Depends(get_current_user)
):
    """Метаинформация о загруженных ML-моделях.

    Возвращает типы моделей, гиперпараметры и важности признаков —
    для отображения на странице аналитики и для прозрачности
    работы алгоритмов.
    """
    return get_model_info()