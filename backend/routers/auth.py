from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from core.database import get_db
from core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from models.models import User, Student
from schemas.schemas import UserCreate, UserOut, Token, StudentAccountCreate

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    email = decode_access_token(token)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    return user


def require_tutor(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, что текущий пользователь — репетитор"""
    if current_user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для репетиторов"
        )
    return current_user


def require_student(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Проверяет, что текущий пользователь — ученик, и возвращает (user, student_profile)"""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для учеников"
        )
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль ученика не найден"
        )
    return current_user, student


@router.post("/register", response_model=UserOut)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role="tutor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/register-student", response_model=UserOut)
def register_student(
    data: StudentAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Репетитор создаёт аккаунт для ученика"""
    if current_user.role != "tutor":
        raise HTTPException(status_code=403, detail="Только репетитор может создавать аккаунты учеников")

    # Проверяем что ученик принадлежит этому репетитору
    student = db.query(Student).filter(
        Student.id == data.student_id,
        Student.tutor_id == current_user.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    if student.user_id:
        raise HTTPException(status_code=400, detail="У ученика уже есть аккаунт")

    # Проверяем что email не занят
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Этот email уже используется")

    # Создаём аккаунт
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=student.full_name,
        role="student",
    )
    db.add(user)
    db.flush()

    # Связываем с профилем ученика
    student.user_id = user.id
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user