"""
ML-модуль платформы для репетиторов.

Архитектура:
    * predict_next_grade   — прогноз оценки через GradientBoostingRegressor (обученный)
    * classify_risk        — классификация риска через RandomForestClassifier (обученный)
    * analyze_topics       — статистический анализ по темам
    * recommend_review_topics — кривая забывания Эббингауза
    * cluster_students     — кластеризация через KMeans
    * full_analysis        — объединяет всё

Обученные модели (RF + GBR) загружаются из ml_models/*.pkl при импорте.
Если файлы не найдены, происходит graceful fallback на правила
(чтобы система запускалась даже до запуска train_models.py).

Для обучения моделей: запустить `python train_models.py` из backend/.
"""

import os
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime, timedelta

from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ============================================================
#  ЗАГРУЗКА ОБУЧЕННЫХ МОДЕЛЕЙ
# ============================================================

MODELS_DIR = Path(__file__).parent.parent / "ml_models"

_risk_model = None
_grade_model = None

try:
    _risk_model = joblib.load(MODELS_DIR / "risk_model.pkl")
    print(f"[predictor] Загружена модель риска: {type(_risk_model).__name__}")
except (FileNotFoundError, OSError):
    print(f"[predictor] Модель риска не найдена в {MODELS_DIR}. "
          f"Используется fallback на правила. Запустите train_models.py для обучения.")

try:
    _grade_model = joblib.load(MODELS_DIR / "grade_predictor.pkl")
    print(f"[predictor] Загружена модель прогноза: {type(_grade_model).__name__}")
except (FileNotFoundError, OSError):
    print(f"[predictor] Модель прогноза не найдена в {MODELS_DIR}. "
          f"Используется fallback на линейную регрессию.")


# ============================================================
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def _extract_features(grades_values: list) -> list:
    """Извлечение 5 признаков для ML-моделей.

    Признаки: [avg, std, trend, min, max].
    Используется одинаково в train_models.py и predictor.py — это критично.
    """
    values = np.array(grades_values, dtype=float)
    n = len(values)
    avg = float(np.mean(values))
    std = float(np.std(values))
    min_g = float(np.min(values))
    max_g = float(np.max(values))

    if n >= 2:
        x = np.arange(n)
        trend = float(np.polyfit(x, values, 1)[0])
    else:
        trend = 0.0

    return [avg, std, trend, min_g, max_g]


def _sorted_values(grades: list) -> list:
    """Сортирует оценки по дате создания и возвращает массив значений."""
    return [g["value"] for g in sorted(grades, key=lambda x: x["created_at"])]


# ============================================================
#  1. ПРОГНОЗ СЛЕДУЮЩЕЙ ОЦЕНКИ (GradientBoostingRegressor)
# ============================================================

def predict_next_grade(grades: list) -> dict:
    """Прогноз следующей оценки на основе истории.

    Использует обученный GradientBoostingRegressor (5 признаков).
    Fallback на LinearRegression, если модель не загружена.
    """
    if len(grades) < 2:
        return {
            "predicted": None,
            "trend": "insufficient_data",
            "message": "Недостаточно данных для прогноза (нужно минимум 2 оценки)"
        }

    values = _sorted_values(grades)
    features = _extract_features(values)
    trend_coef = features[2]

    # Метка тренда
    if trend_coef > 0.2:
        trend, trend_label = "improving", "Улучшается"
    elif trend_coef < -0.2:
        trend, trend_label = "declining", "Снижается"
    else:
        trend, trend_label = "stable", "Стабильно"

    # Основной путь — обученный GBR
    if _grade_model is not None and len(values) >= 3:
        try:
            predicted = float(_grade_model.predict([features])[0])
            predicted = max(1.0, min(10.0, round(predicted, 1)))
            avg_last_3 = round(float(np.mean(values[-3:])), 1)

            return {
                "predicted": predicted,
                "trend": trend,
                "trend_label": trend_label,
                "avg_last_3": avg_last_3,
                "total_grades": len(values),
                "model": "GradientBoostingRegressor",
                "message": f"Прогноз следующей оценки: {predicted}"
            }
        except Exception as e:
            print(f"[predictor] GBR ошибка, fallback: {e}")

    # Fallback — линейная регрессия по индексам
    X = np.array(range(len(values))).reshape(-1, 1)
    y = np.array(values)
    model = LinearRegression()
    model.fit(X, y)
    predicted = float(model.predict([[len(values)]])[0])
    predicted = max(1.0, min(10.0, round(predicted, 1)))
    avg_last_3 = round(float(np.mean(values[-3:])) if len(values) >= 3 else float(np.mean(values)), 1)

    return {
        "predicted": predicted,
        "trend": trend,
        "trend_label": trend_label,
        "avg_last_3": avg_last_3,
        "total_grades": len(values),
        "model": "LinearRegression (fallback)",
        "message": f"Прогноз следующей оценки: {predicted}"
    }


# ============================================================
#  2. КЛАССИФИКАЦИЯ ГРУППЫ РИСКА (RandomForestClassifier)
# ============================================================

_RISK_META = {
    "low": {
        "label": "Высокие результаты",
        "color": "green",
        "recommendation": "Отличная успеваемость! Можно усложнять задания.",
    },
    "medium": {
        "label": "Стабильный прогресс",
        "color": "blue",
        "recommendation": "Хорошая динамика. Продолжайте в том же темпе.",
    },
    "high": {
        "label": "Требует внимания",
        "color": "red",
        "recommendation": "Рекомендуется уделить дополнительное внимание и разобрать проблемные темы.",
    },
}


def classify_risk(grades: list) -> dict:
    """Классификация ученика по группе риска.

    Использует обученный RandomForestClassifier на 5 признаках.
    Возвращает категорию + вероятности классов + интерпретацию.
    Fallback на правила, если модель не загружена.
    """
    if len(grades) < 3:
        return {
            "risk_level": "unknown",
            "risk_label": "Недостаточно данных",
            "risk_color": "gray",
            "message": "Нужно минимум 3 оценки для классификации"
        }

    values = _sorted_values(grades)
    features = _extract_features(values)
    avg, std, trend_coef, min_g, max_g = features

    # Основной путь — обученный RF
    if _risk_model is not None:
        try:
            X = np.array([features])
            risk_level = str(_risk_model.predict(X)[0])
            probas = _risk_model.predict_proba(X)[0]
            classes = [str(c) for c in _risk_model.classes_]
            confidence = float(probas[classes.index(risk_level)])

            meta = _RISK_META.get(risk_level, _RISK_META["medium"])

            return {
                "risk_level": risk_level,
                "risk_label": meta["label"],
                "risk_color": meta["color"],
                "avg_grade": round(avg, 1),
                "std_grade": round(std, 2),
                "confidence": round(confidence, 3),
                "probabilities": {
                    cls: round(float(p), 3) for cls, p in zip(classes, probas)
                },
                "recommendation": meta["recommendation"],
                "model": "RandomForestClassifier",
            }
        except Exception as e:
            print(f"[predictor] RF ошибка, fallback: {e}")

    # Fallback — правила
    if avg >= 7.5 and trend_coef >= -0.1:
        risk_level = "low"
    elif avg >= 5.5 and trend_coef >= -0.3:
        risk_level = "medium"
    else:
        risk_level = "high"

    meta = _RISK_META[risk_level]
    return {
        "risk_level": risk_level,
        "risk_label": meta["label"],
        "risk_color": meta["color"],
        "avg_grade": round(avg, 1),
        "std_grade": round(std, 2),
        "recommendation": meta["recommendation"],
        "model": "Rule-based (fallback)",
    }


# ============================================================
#  3. АНАЛИЗ ПО ТЕМАМ (статистический, без ML)
# ============================================================

def analyze_topics(grades: list) -> dict:
    """Анализ успеваемости по темам."""
    if len(grades) < 2:
        return {
            "topics": [],
            "weak_topics": [],
            "strong_topics": [],
            "message": "Недостаточно данных для анализа тем"
        }

    topic_grades = {}
    for grade in grades:
        topic = grade["topic"]
        if topic not in topic_grades:
            topic_grades[topic] = []
        topic_grades[topic].append(grade["value"])

    topics = []
    for topic, values in topic_grades.items():
        avg = float(np.mean(values))
        topics.append({
            "topic": topic,
            "avg": round(avg, 1),
            "count": len(values),
            "min": min(values),
            "max": max(values)
        })

    topics.sort(key=lambda x: x["avg"])
    weak_topics = [t for t in topics if t["avg"] < 6]
    strong_topics = [t for t in topics if t["avg"] >= 8]

    return {
        "topics": topics,
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
        "total_topics": len(topics)
    }


# ============================================================
#  4. РЕКОМЕНДАЦИИ ПО ПОВТОРЕНИЮ (кривая забывания Эббингауза)
# ============================================================

def recommend_review_topics(grades: list, now: str = None) -> dict:
    """Темы для повторения по модели Эббингауза: retention = e^(-t/S).

    S (сила памяти) зависит от средней оценки по теме и количества повторений.
    """
    if len(grades) < 3:
        return {
            "recommendations": [],
            "message": "Недостаточно данных для рекомендаций (нужно минимум 3 оценки)"
        }

    if now is None:
        current_time = datetime.utcnow()
    else:
        try:
            current_time = datetime.fromisoformat(now.replace("Z", "").replace("+00:00", ""))
        except ValueError:
            current_time = datetime.utcnow()

    topic_data = {}
    for grade in grades:
        topic = grade["topic"]
        created = grade["created_at"]
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created.replace("Z", "").replace("+00:00", ""))
            except ValueError:
                try:
                    created = datetime.fromisoformat(created[:19])
                except ValueError:
                    continue
        if topic not in topic_data:
            topic_data[topic] = []
        topic_data[topic].append({"value": grade["value"], "date": created})

    recommendations = []
    urgent_count = 0

    for topic, entries in topic_data.items():
        entries.sort(key=lambda x: x["date"])
        last_entry = entries[-1]
        last_grade = last_entry["value"]
        last_date = last_entry["date"]

        repetitions = len(entries)
        avg_grade = float(np.mean([e["value"] for e in entries]))

        # Сила памяти S: чем выше оценка и больше повторений, тем медленнее забывается
        # Базовая формула: S = base * (avg_grade / 10) * sqrt(repetitions)
        S_base = 14  # базовая сила памяти, дней
        S = S_base * (avg_grade / 10.0) * np.sqrt(repetitions)

        # Время с последнего повторения, в днях
        delta_days = (current_time - last_date).total_seconds() / 86400
        delta_days = max(0, delta_days)

        # Кривая Эббингауза: retention = exp(-t/S)
        retention = float(np.exp(-delta_days / max(S, 0.1)))
        needs_review = retention < 0.5

        if needs_review:
            urgent_count += 1

        # Рекомендуемая дата следующего повторения — когда retention упадёт до 0.5
        next_review_offset = S * np.log(2)  # из exp(-t/S) = 0.5 → t = S * ln(2)
        next_review_date = last_date + timedelta(days=next_review_offset)

        recommendations.append({
            "topic": topic,
            "last_grade": last_grade,
            "avg_grade": round(avg_grade, 1),
            "repetitions": repetitions,
            "days_since_review": int(delta_days),
            "retention": round(retention, 3),
            "needs_review": needs_review,
            "next_review_date": next_review_date.isoformat() + "Z",
        })

    # Сортировка: сначала срочные, потом по retention
    recommendations.sort(key=lambda x: (not x["needs_review"], x["retention"]))

    return {
        "recommendations": recommendations,
        "urgent_count": urgent_count,
        "total_topics": len(recommendations),
    }


# ============================================================
#  5. КЛАСТЕРИЗАЦИЯ УЧЕНИКОВ (KMeans)
# ============================================================

def cluster_students(students_data: list) -> dict:
    """K-Means кластеризация учеников по 5 признакам."""
    if len(students_data) < 3:
        return {
            "clusters": [],
            "students": [],
            "message": "Нужно минимум 3 ученика для кластеризации"
        }

    features_list = []
    student_ids = []
    student_names = []

    for s in students_data:
        grades = s.get("grades", [])
        if len(grades) < 2:
            continue

        values = _sorted_values(grades)
        avg_grade = float(np.mean(values))
        grade_std = float(np.std(values))
        total_grades = len(values)
        lessons_count = s.get("lessons_count", 0)

        # Тренд через линейную регрессию
        X = np.array(range(len(values))).reshape(-1, 1)
        model = LinearRegression()
        model.fit(X, np.array(values))
        grade_trend = float(model.coef_[0])

        features_list.append([avg_grade, grade_trend, grade_std, total_grades, lessons_count])
        student_ids.append(s["student_id"])
        student_names.append(s["student_name"])

    if len(features_list) < 3:
        return {
            "clusters": [],
            "students": [],
            "message": "Недостаточно учеников с оценками для кластеризации (нужно минимум 3)"
        }

    features = np.array(features_list)
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # Определяем число кластеров
    if len(features_list) <= 5:
        n_clusters = 2
    else:
        n_clusters = min(3, len(features_list))

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features_scaled)

    # Silhouette score (метрика качества кластеризации)
    silhouette = None
    if len(features_list) > n_clusters:
        try:
            from sklearn.metrics import silhouette_score
            silhouette = float(silhouette_score(features_scaled, labels))
        except Exception:
            silhouette = None

    # Собираем характеристики каждого кластера
    raw_clusters = []
    for cluster_id in range(n_clusters):
        mask = labels == cluster_id
        cluster_features = features[mask]

        c_avg = float(np.mean(cluster_features[:, 0]))
        c_trend = float(np.mean(cluster_features[:, 1]))
        c_std = float(np.mean(cluster_features[:, 2]))
        c_count = int(np.sum(mask))

        raw_clusters.append({
            "cluster_id": int(cluster_id),
            "avg_grade": round(c_avg, 1),
            "avg_trend": round(c_trend, 2),
            "avg_std": round(c_std, 2),
            "count": c_count,
        })

    # Сортируем кластеры по среднему баллу и навешиваем метки
    raw_clusters.sort(key=lambda x: -x["avg_grade"])
    clusters = []
    for rank, c in enumerate(raw_clusters):
        label, color, description = _classify_cluster_by_rank(
            rank, n_clusters, c["avg_grade"], c["avg_trend"], c["avg_std"]
        )
        c["label"] = label
        c["color"] = color
        c["description"] = description
        clusters.append(c)

    # Назначаем каждому ученику его кластер
    cluster_id_to_meta = {c["cluster_id"]: c for c in clusters}
    students_result = []
    for i, sid in enumerate(student_ids):
        meta = cluster_id_to_meta[int(labels[i])]
        students_result.append({
            "student_id": sid,
            "student_name": student_names[i],
            "cluster_id": int(labels[i]),
            "cluster_label": meta["label"],
            "cluster_color": meta["color"],
            "features": {
                "avg_grade": round(features[i][0], 1),
                "trend": round(features[i][1], 2),
                "std": round(features[i][2], 2),
                "total_grades": int(features[i][3]),
                "lessons_count": int(features[i][4]),
            }
        })

    return {
        "clusters": clusters,
        "students": students_result,
        "n_clusters": n_clusters,
        "silhouette_score": round(silhouette, 3) if silhouette is not None else None,
        "model": "KMeans",
    }


def _classify_cluster_by_rank(rank: int, total: int, avg_grade: float,
                              trend: float, std: float) -> tuple:
    """Назначение метки кластеру по его рангу (0 = лучший)."""
    if total == 2:
        if rank == 0:
            return ("Успешные ученики", "#10b981",
                    f"Средний балл {avg_grade}, стабильно высокая успеваемость")
        else:
            return ("Требуют внимания", "#f43f5e",
                    f"Средний балл {avg_grade}, нужна дополнительная поддержка")
    # 3 кластера
    if rank == 0:
        return ("Отличники", "#10b981",
                f"Средний балл {avg_grade}, стабильные результаты")
    if rank == total - 1:
        return ("Требуют внимания", "#f43f5e",
                f"Средний балл {avg_grade}, нужна поддержка")
    return ("Хорошисты", "#f59e0b",
            f"Средний балл {avg_grade}, есть потенциал для роста")


# ============================================================
#  6. ПОЛНЫЙ АНАЛИЗ
# ============================================================

def full_analysis(grades: list) -> dict:
    """Полный анализ ученика."""
    return {
        "prediction": predict_next_grade(grades),
        "risk": classify_risk(grades),
        "topics": analyze_topics(grades),
        "review": recommend_review_topics(grades)
    }


# ============================================================
#  ИНТЕРПРЕТИРУЕМОСТЬ — ОТЛАДОЧНАЯ ИНФОРМАЦИЯ О МОДЕЛИ
# ============================================================

def get_model_info() -> dict:
    """Возвращает метаинформацию о загруженных моделях.

    Может пригодиться для отдельного эндпоинта /analytics/model-info
    и для отладки на защите дипломной работы.
    """
    info = {
        "risk_model": None,
        "grade_model": None,
    }

    if _risk_model is not None:
        feature_names = ["avg", "std", "trend", "min", "max"]
        importances = list(zip(feature_names, _risk_model.feature_importances_.tolist()))
        importances.sort(key=lambda x: -x[1])
        info["risk_model"] = {
            "type": type(_risk_model).__name__,
            "n_estimators": getattr(_risk_model, "n_estimators", None),
            "max_depth": getattr(_risk_model, "max_depth", None),
            "classes": list(_risk_model.classes_),
            "feature_importances": [
                {"feature": name, "importance": round(imp, 3)}
                for name, imp in importances
            ],
        }

    if _grade_model is not None:
        feature_names = ["avg", "std", "trend", "min", "max"]
        importances = list(zip(feature_names, _grade_model.feature_importances_.tolist()))
        importances.sort(key=lambda x: -x[1])
        info["grade_model"] = {
            "type": type(_grade_model).__name__,
            "n_estimators": getattr(_grade_model, "n_estimators", None),
            "max_depth": getattr(_grade_model, "max_depth", None),
            "learning_rate": getattr(_grade_model, "learning_rate", None),
            "feature_importances": [
                {"feature": name, "importance": round(imp, 3)}
                for name, imp in importances
            ],
        }

    return info
