"""
Скрипт обучения ML-моделей для платформы репетиторов.

Запуск:
    python train_models.py

Что делает:
1. Генерирует синтетическую выборку из ~1000 учеников с реалистичным распределением оценок.
2. Извлекает 5 признаков: avg_grade, std_grade, trend, min_grade, max_grade.
3. Обучает:
   - RandomForestClassifier для классификации группы риска (3 класса: low/medium/high)
   - GradientBoostingRegressor для прогноза следующей оценки.
4. Печатает метрики (cross-validation accuracy, F1, MAE, RMSE, R²).
5. Сохраняет модели в backend/ml_models/*.pkl

Синтетика построена так, чтобы соответствовать педагогической логике:
- low risk:    avg ≥ 7.5, trend ≥ -0.1
- medium risk: 5.5 ≤ avg < 7.5, trend ≥ -0.3
- high risk:   avg < 5.5 или trend < -0.3

Это даёт ~30%/40%/30% распределение классов, что близко к реальному
распределению успеваемости в типичной школьной группе.
"""

import os
import numpy as np
from pathlib import Path
import joblib

from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, train_test_split, KFold
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report,
    mean_absolute_error, mean_squared_error, r2_score,
)

# --- Конфигурация ---
RANDOM_SEED = 42
N_STUDENTS = 1000          # размер синтетической выборки
GRADES_PER_STUDENT = 8     # средне число оценок на ученика
MODELS_DIR = Path(__file__).parent / "ml_models"
MODELS_DIR.mkdir(exist_ok=True)

np.random.seed(RANDOM_SEED)


# ============================================================
#  СИНТЕТИЧЕСКИЕ ДАННЫЕ
# ============================================================

def generate_synthetic_student(rng) -> tuple[list, str]:
    """
    Генерирует синтетического ученика и его оценки.

    Возвращает (список оценок, метка риска).
    Метка выводится из педагогических правил по результирующим оценкам.
    """
    profile = rng.choice(["strong", "average", "weak", "declining", "improving"],
                         p=[0.20, 0.40, 0.15, 0.10, 0.15])

    n = max(3, int(rng.normal(GRADES_PER_STUDENT, 2)))

    if profile == "strong":
        base, slope, noise = 8.5, 0.05, 0.6
    elif profile == "average":
        base, slope, noise = 6.5, 0.0, 0.8
    elif profile == "weak":
        base, slope, noise = 4.5, 0.0, 0.9
    elif profile == "declining":
        base, slope, noise = 7.0, -0.4, 0.7
    else:  # improving
        base, slope, noise = 5.0, 0.4, 0.7

    grades = []
    for i in range(n):
        v = base + slope * i + rng.normal(0, noise)
        v = max(1.0, min(10.0, round(v * 2) / 2))  # клиппинг + округление до 0.5
        grades.append(v)

    # Метка по результирующим оценкам (педагогические правила)
    avg = np.mean(grades)
    if len(grades) >= 3:
        x = np.arange(len(grades))
        slope_actual = np.polyfit(x, grades, 1)[0]
    else:
        slope_actual = 0

    if avg >= 7.5 and slope_actual >= -0.1:
        label = "low"
    elif avg >= 5.5 and slope_actual >= -0.3:
        label = "medium"
    else:
        label = "high"

    return grades, label


def extract_features(grades: list) -> list:
    """5 признаков для классификатора риска и регрессора прогноза."""
    values = np.array(grades, dtype=float)
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


def generate_dataset(n_students: int):
    """Создаёт две выборки: для классификации и для регрессии."""
    rng = np.random.default_rng(RANDOM_SEED)

    X_cls, y_cls = [], []
    X_reg, y_reg = [], []

    for _ in range(n_students):
        grades, label = generate_synthetic_student(rng)

        # Для классификации — фичи по всем оценкам, метка риска
        feats = extract_features(grades)
        X_cls.append(feats)
        y_cls.append(label)

        # Для регрессии — фичи по первым (n-1) оценкам, целевая = последняя оценка
        if len(grades) >= 3:
            feats_reg = extract_features(grades[:-1])
            X_reg.append(feats_reg)
            y_reg.append(grades[-1])

    return (np.array(X_cls), np.array(y_cls),
            np.array(X_reg), np.array(y_reg))


# ============================================================
#  ОБУЧЕНИЕ И ВАЛИДАЦИЯ
# ============================================================

def train_risk_classifier(X, y):
    print("\n" + "=" * 60)
    print("RandomForestClassifier — классификация группы риска")
    print("=" * 60)

    print(f"Размер выборки: {len(X)} учеников")
    unique, counts = np.unique(y, return_counts=True)
    print("Распределение классов:")
    for cls, cnt in zip(unique, counts):
        print(f"  {cls:8s}: {cnt:4d} ({cnt / len(y) * 100:.1f}%)")

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_leaf=5,
        random_state=RANDOM_SEED,
        class_weight="balanced",
    )

    # 5-fold cross-validation
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    acc_scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
    f1_scores = cross_val_score(model, X, y, cv=cv, scoring="f1_macro")

    print(f"\nCross-validation (5-fold):")
    print(f"  Accuracy: {acc_scores.mean():.3f} ± {acc_scores.std():.3f}")
    print(f"  F1 macro: {f1_scores.mean():.3f} ± {f1_scores.std():.3f}")

    # Финальное обучение на всей выборке
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"\nHold-out (20% test):")
    print(f"  Accuracy: {accuracy_score(y_test, y_pred):.3f}")
    print(f"  F1 macro: {f1_score(y_test, y_pred, average='macro'):.3f}")

    print("\nКлассификационный отчёт (test):")
    print(classification_report(y_test, y_pred, digits=3))

    # Важность признаков
    feature_names = ["avg", "std", "trend", "min", "max"]
    print("Важность признаков (feature_importances_):")
    for name, imp in sorted(
        zip(feature_names, model.feature_importances_),
        key=lambda x: -x[1]
    ):
        print(f"  {name:6s}: {imp:.3f}")

    # Переобучаем на всей выборке для production
    model.fit(X, y)
    return model


def train_grade_predictor(X, y):
    print("\n" + "=" * 60)
    print("GradientBoostingRegressor — прогноз следующей оценки")
    print("=" * 60)

    print(f"Размер выборки: {len(X)} учеников")
    print(f"Распределение целевой:")
    print(f"  mean={y.mean():.2f}, std={y.std():.2f}, min={y.min():.1f}, max={y.max():.1f}")

    model = GradientBoostingRegressor(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.05,
        min_samples_leaf=10,
        random_state=RANDOM_SEED,
    )

    # 5-fold cross-validation
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    neg_mae = cross_val_score(model, X, y, cv=cv, scoring="neg_mean_absolute_error")
    neg_mse = cross_val_score(model, X, y, cv=cv, scoring="neg_mean_squared_error")
    r2 = cross_val_score(model, X, y, cv=cv, scoring="r2")

    print(f"\nCross-validation (5-fold):")
    print(f"  MAE:  {-neg_mae.mean():.3f} ± {neg_mae.std():.3f}")
    print(f"  RMSE: {np.sqrt(-neg_mse.mean()):.3f}")
    print(f"  R²:   {r2.mean():.3f} ± {r2.std():.3f}")

    # Hold-out
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"\nHold-out (20% test):")
    print(f"  MAE:  {mean_absolute_error(y_test, y_pred):.3f}")
    print(f"  RMSE: {np.sqrt(mean_squared_error(y_test, y_pred)):.3f}")
    print(f"  R²:   {r2_score(y_test, y_pred):.3f}")

    # Важность признаков
    feature_names = ["avg", "std", "trend", "min", "max"]
    print("\nВажность признаков (feature_importances_):")
    for name, imp in sorted(
        zip(feature_names, model.feature_importances_),
        key=lambda x: -x[1]
    ):
        print(f"  {name:6s}: {imp:.3f}")

    # Финальное обучение на всей выборке
    model.fit(X, y)
    return model


# ============================================================
#  MAIN
# ============================================================

def main():
    print(f"Генерация {N_STUDENTS} синтетических учеников...")
    X_cls, y_cls, X_reg, y_reg = generate_dataset(N_STUDENTS)

    risk_model = train_risk_classifier(X_cls, y_cls)
    grade_model = train_grade_predictor(X_reg, y_reg)

    # Сохранение
    risk_path = MODELS_DIR / "risk_model.pkl"
    grade_path = MODELS_DIR / "grade_predictor.pkl"

    joblib.dump(risk_model, risk_path)
    joblib.dump(grade_model, grade_path)

    print("\n" + "=" * 60)
    print("Модели сохранены:")
    print(f"  {risk_path}")
    print(f"  {grade_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
