import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import engine, Base
from routers import auth, students, lessons, grades, analytics, homeworks

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tutor System API",
    description="Интеллектуальная система для репетитора",
    version="1.0.0"
)

# CORS_ORIGINS можно задать через переменную окружения как список URL,
# разделённых запятыми. По умолчанию разрешён локальный dev-сервер Vite.
# Пример для production:
#   CORS_ORIGINS=https://alezar-tutor.online,https://www.alezar-tutor.online
cors_env = os.getenv("CORS_ORIGINS", "http://localhost:5173")
cors_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(lessons.router)
app.include_router(grades.router)
app.include_router(analytics.router)
app.include_router(homeworks.router)


@app.get("/")
def root():
    return {"message": "Tutor System API работает"}


@app.get("/health")
def health():
    return {"status": "ok"}