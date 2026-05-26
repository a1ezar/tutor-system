"""
Скрипт валидации обученных ML-моделей.

Запуск:
    python evaluate_models.py

Что делает:
1. Загружает обученные модели (risk_model.pkl, grade_predictor.pkl) из ml_models/.
2. Генерирует ту же синтетическую выборку, что использовалась для обучения,
   с тем же random_seed — это даёт детерминированный hold-out тест.
3. Считает полный набор метрик:
   - Для RandomForestClassifier: accuracy, precision/recall/F1 по классам,
     macro/weighted F1, confusion matrix, cross-validation scores.
   - Для GradientBoostingRegressor: MAE, RMSE, R², MAPE,
     cross-validation MAE/RMSE/R².
4. Сохраняет:
   - reports/metrics.json — все метрики в структурированном виде.
   - reports/confusion_matrix.png — матрица ошибок для RF.
   - reports/regression_scatter.png — диаграмма рассеяния прогноз vs факт.
   - reports/feature_importances.png — важности признаков для обеих моделей.

Метрики и графики готовы для вставки в раздел 4.2 диплома.
"""

import json
import numpy as np
import joblib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # без GUI
import matplotlib.pyplot as plt

from sklearn.model_selection import cross_val_score, train_test_split, KFold
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, f1_score,
    confusion_matrix, classification_report,
    mean_absolute_error, mean_squared_error, r2_score,
    silhouette_score,
)
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Импорт функций генерации из train_models.py
import sys
sys.path.insert(0, str(Path(__file__).parent))
from train_models import generate_dataset, extract_features, N_STUDENTS, RANDOM_SEED


# --- Конфигурация ---
MODELS_DIR = Path(__file__).parent / "ml_models"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

FEATURE_NAMES = ["avg", "std", "trend", "min", "max"]
RISK_CLASSES = ["low", "medium", "high"]


# ============================================================
#  ВАЛИДАЦИЯ КЛАССИФИКАТОРА РИСКА
# ============================================================

def evaluate_risk_classifier(model, X, y):
    """Полная валидация RandomForestClassifier."""
    print("\n" + "=" * 70)
    print(" ВАЛИДАЦИЯ: RandomForestClassifier (классификация группы риска)")
    print("=" * 70)

    # 5-fold cross-validation
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    cv_acc = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
    cv_f1  = cross_val_score(model, X, y, cv=cv, scoring="f1_macro")

    print(f"\nCross-validation (5-fold):")
    print(f"  Accuracy:  {cv_acc.mean():.4f} ± {cv_acc.std():.4f}")
    print(f"  F1 macro:  {cv_f1.mean():.4f} ± {cv_f1.std():.4f}")

    # Hold-out 20%
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )
    # Переобучаем на train, чтобы был честный тест
    model_local = type(model)(**model.get_params())
    model_local.fit(X_train, y_train)
    y_pred = model_local.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    f1_weighted = f1_score(y_test, y_pred, average="weighted")
    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, y_pred, labels=RISK_CLASSES, zero_division=0
    )

    print(f"\nHold-out (20% test, n={len(y_test)}):")
    print(f"  Accuracy:    {acc:.4f}")
    print(f"  F1 macro:    {f1_macro:.4f}")
    print(f"  F1 weighted: {f1_weighted:.4f}")

    print(f"\nПо классам:")
    print(f"  {'Класс':<10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    for i, cls in enumerate(RISK_CLASSES):
        print(f"  {cls:<10} {precision[i]:>10.4f} {recall[i]:>10.4f} {f1[i]:>10.4f} {support[i]:>10d}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=RISK_CLASSES)
    print(f"\nConfusion matrix (rows=true, cols=predicted):")
    print(f"  {'':<10}" + "".join(f"{c:>10}" for c in RISK_CLASSES))
    for i, cls in enumerate(RISK_CLASSES):
        print(f"  {cls:<10}" + "".join(f"{cm[i][j]:>10d}" for j in range(len(RISK_CLASSES))))

    # Feature importances
    print(f"\nВажность признаков (feature_importances_):")
    importances = list(zip(FEATURE_NAMES, model.feature_importances_))
    importances.sort(key=lambda x: -x[1])
    for name, imp in importances:
        print(f"  {name:<10} {imp:.4f}")

    # Сохраняем графики
    plot_confusion_matrix(cm, RISK_CLASSES,
                          REPORTS_DIR / "confusion_matrix.png")
    plot_feature_importances(model.feature_importances_, FEATURE_NAMES,
                             title="Важность признаков — RandomForest (риск)",
                             output=REPORTS_DIR / "rf_feature_importances.png")

    return {
        "model_type": type(model).__name__,
        "cv_accuracy": {"mean": round(float(cv_acc.mean()), 4), "std": round(float(cv_acc.std()), 4)},
        "cv_f1_macro": {"mean": round(float(cv_f1.mean()), 4), "std": round(float(cv_f1.std()), 4)},
        "holdout": {
            "n_test": int(len(y_test)),
            "accuracy": round(float(acc), 4),
            "f1_macro": round(float(f1_macro), 4),
            "f1_weighted": round(float(f1_weighted), 4),
            "per_class": {
                cls: {
                    "precision": round(float(precision[i]), 4),
                    "recall":    round(float(recall[i]), 4),
                    "f1":        round(float(f1[i]), 4),
                    "support":   int(support[i]),
                }
                for i, cls in enumerate(RISK_CLASSES)
            },
            "confusion_matrix": {
                "labels": RISK_CLASSES,
                "matrix": cm.tolist(),
            },
        },
        "feature_importances": [
            {"feature": n, "importance": round(float(i), 4)} for n, i in importances
        ],
    }


# ============================================================
#  ВАЛИДАЦИЯ РЕГРЕССОРА ПРОГНОЗА
# ============================================================

def evaluate_grade_predictor(model, X, y):
    """Полная валидация GradientBoostingRegressor."""
    print("\n" + "=" * 70)
    print(" ВАЛИДАЦИЯ: GradientBoostingRegressor (прогноз оценки)")
    print("=" * 70)

    # 5-fold cross-validation
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    cv_mae = -cross_val_score(model, X, y, cv=cv, scoring="neg_mean_absolute_error")
    cv_mse = -cross_val_score(model, X, y, cv=cv, scoring="neg_mean_squared_error")
    cv_rmse = np.sqrt(cv_mse)
    cv_r2 = cross_val_score(model, X, y, cv=cv, scoring="r2")

    print(f"\nCross-validation (5-fold):")
    print(f"  MAE:   {cv_mae.mean():.4f} ± {cv_mae.std():.4f}")
    print(f"  RMSE:  {cv_rmse.mean():.4f} ± {cv_rmse.std():.4f}")
    print(f"  R²:    {cv_r2.mean():.4f} ± {cv_r2.std():.4f}")

    # Hold-out 20%
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )
    model_local = type(model)(**model.get_params())
    model_local.fit(X_train, y_train)
    y_pred = model_local.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    # MAPE с защитой от деления на ноль
    mape = float(np.mean(np.abs((y_test - y_pred) / np.maximum(np.abs(y_test), 0.1))) * 100)

    print(f"\nHold-out (20% test, n={len(y_test)}):")
    print(f"  MAE:   {mae:.4f}")
    print(f"  RMSE:  {rmse:.4f}")
    print(f"  R²:    {r2:.4f}")
    print(f"  MAPE:  {mape:.2f}%")

    # Анализ ошибок по диапазонам
    print(f"\nРаспределение ошибок:")
    errors = np.abs(y_test - y_pred)
    print(f"  ≤ 0.5 балла:  {np.sum(errors <= 0.5)} ({np.mean(errors <= 0.5) * 100:.1f}%)")
    print(f"  ≤ 1.0 балла:  {np.sum(errors <= 1.0)} ({np.mean(errors <= 1.0) * 100:.1f}%)")
    print(f"  ≤ 1.5 балла:  {np.sum(errors <= 1.5)} ({np.mean(errors <= 1.5) * 100:.1f}%)")
    print(f"  > 1.5 балла:  {np.sum(errors > 1.5)} ({np.mean(errors > 1.5) * 100:.1f}%)")

    # Feature importances
    print(f"\nВажность признаков (feature_importances_):")
    importances = list(zip(FEATURE_NAMES, model.feature_importances_))
    importances.sort(key=lambda x: -x[1])
    for name, imp in importances:
        print(f"  {name:<10} {imp:.4f}")

    # Графики
    plot_regression_scatter(y_test, y_pred,
                            REPORTS_DIR / "regression_scatter.png")
    plot_feature_importances(model.feature_importances_, FEATURE_NAMES,
                             title="Важность признаков — GradientBoosting (прогноз)",
                             output=REPORTS_DIR / "gbr_feature_importances.png")

    return {
        "model_type": type(model).__name__,
        "cv_mae":  {"mean": round(float(cv_mae.mean()),  4), "std": round(float(cv_mae.std()),  4)},
        "cv_rmse": {"mean": round(float(cv_rmse.mean()), 4), "std": round(float(cv_rmse.std()), 4)},
        "cv_r2":   {"mean": round(float(cv_r2.mean()),   4), "std": round(float(cv_r2.std()),   4)},
        "holdout": {
            "n_test": int(len(y_test)),
            "mae": round(float(mae), 4),
            "rmse": round(float(rmse), 4),
            "r2": round(float(r2), 4),
            "mape_percent": round(float(mape), 2),
            "error_distribution": {
                "le_0.5": int(np.sum(errors <= 0.5)),
                "le_1.0": int(np.sum(errors <= 1.0)),
                "le_1.5": int(np.sum(errors <= 1.5)),
                "gt_1.5": int(np.sum(errors > 1.5)),
            },
        },
        "feature_importances": [
            {"feature": n, "importance": round(float(i), 4)} for n, i in importances
        ],
    }


# ============================================================
#  ВАЛИДАЦИЯ КЛАСТЕРИЗАЦИИ KMEANS
# ============================================================

def evaluate_clustering(X):
    """Подбор оптимального k через silhouette score."""
    print("\n" + "=" * 70)
    print(" ВАЛИДАЦИЯ: KMeans (кластеризация учеников)")
    print("=" * 70)

    # Берём первые 5 признаков как в predictor.cluster_students
    # (на синтетике avg + std + trend + min + max, для имитации лента признаков)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print(f"\nSilhouette score для разного k:")
    results = []
    for k in range(2, 7):
        kmeans = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        if len(set(labels)) > 1:
            score = silhouette_score(X_scaled, labels)
        else:
            score = 0.0
        results.append({"k": k, "silhouette": round(float(score), 4),
                        "inertia": round(float(kmeans.inertia_), 2)})
        print(f"  k={k}: silhouette = {score:.4f}, inertia = {kmeans.inertia_:.2f}")

    best = max(results, key=lambda x: x["silhouette"])
    print(f"\nОптимальное k по silhouette: {best['k']} (score={best['silhouette']:.4f})")

    plot_silhouette_scores(results, REPORTS_DIR / "kmeans_silhouette.png")

    return {
        "model_type": "KMeans",
        "metric": "silhouette_score",
        "results": results,
        "optimal_k": best["k"],
        "optimal_silhouette": best["silhouette"],
    }


# ============================================================
#  ГРАФИКИ
# ============================================================

def plot_confusion_matrix(cm, classes, output):
    """Heatmap confusion matrix."""
    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    im = ax.imshow(cm, cmap="Blues", aspect="equal")

    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, fontsize=11)
    ax.set_yticklabels(classes, fontsize=11)
    ax.set_xlabel("Предсказанный класс", fontsize=12, fontweight="bold")
    ax.set_ylabel("Истинный класс", fontsize=12, fontweight="bold")
    ax.set_title("Матрица ошибок — RandomForestClassifier", fontsize=13, fontweight="bold")

    # Числа в ячейках
    max_v = cm.max()
    for i in range(len(classes)):
        for j in range(len(classes)):
            color = "white" if cm[i, j] > max_v / 2 else "#0f172a"
            ax.text(j, i, cm[i, j], ha="center", va="center",
                    color=color, fontsize=14, fontweight="bold")

    plt.colorbar(im, ax=ax, fraction=0.046)
    plt.tight_layout()
    plt.savefig(output, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Сохранено: {output}")


def plot_regression_scatter(y_true, y_pred, output):
    """Scatter plot предсказание vs факт."""
    fig, ax = plt.subplots(figsize=(7, 6), dpi=120)

    ax.scatter(y_true, y_pred, alpha=0.5, s=25, c="#4f46e5", edgecolors="white", linewidths=0.5)

    # Идеальная диагональ
    lims = [min(y_true.min(), y_pred.min()) - 0.5,
            max(y_true.max(), y_pred.max()) + 0.5]
    ax.plot(lims, lims, "--", c="#94a3b8", linewidth=1.5, label="Идеальный прогноз")

    # ±1 балл полосы
    ax.fill_between(lims, [l - 1 for l in lims], [l + 1 for l in lims],
                    color="#10b981", alpha=0.1, label="Зона ошибки ±1 балл")

    ax.set_xlabel("Истинная оценка", fontsize=12, fontweight="bold")
    ax.set_ylabel("Предсказанная оценка", fontsize=12, fontweight="bold")
    ax.set_title("Прогноз vs Факт — GradientBoostingRegressor", fontsize=13, fontweight="bold")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Сохранено: {output}")


def plot_feature_importances(importances, names, title, output):
    """Bar chart важности признаков."""
    # Сортируем по убыванию
    pairs = sorted(zip(names, importances), key=lambda x: x[1])

    fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
    colors = ["#4f46e5"] * len(pairs)
    colors[-1] = "#7c3aed"  # Самый важный — выделить

    y_pos = range(len(pairs))
    ax.barh(y_pos, [p[1] for p in pairs], color=colors, edgecolor="white")
    ax.set_yticks(y_pos)
    ax.set_yticklabels([p[0] for p in pairs], fontsize=11)
    ax.set_xlabel("Важность", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3)

    # Подписи значений
    for i, (_, v) in enumerate(pairs):
        ax.text(v + 0.005, i, f"{v:.3f}", va="center", fontsize=10)

    ax.set_xlim(0, max(p[1] for p in pairs) * 1.15)
    plt.tight_layout()
    plt.savefig(output, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Сохранено: {output}")


def plot_silhouette_scores(results, output):
    """График silhouette в зависимости от k."""
    fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
    ks = [r["k"] for r in results]
    scores = [r["silhouette"] for r in results]

    ax.plot(ks, scores, marker="o", markersize=10, linewidth=2.5, color="#4f46e5")
    best_k = max(results, key=lambda x: x["silhouette"])["k"]
    best_score = max(scores)
    ax.scatter([best_k], [best_score], s=200, color="#10b981", zorder=5,
               edgecolors="white", linewidths=2, label=f"Оптимум: k={best_k}")

    ax.set_xlabel("Число кластеров (k)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Silhouette score", fontsize=12, fontweight="bold")
    ax.set_title("Подбор k для KMeans по silhouette score", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=11)
    ax.set_xticks(ks)

    plt.tight_layout()
    plt.savefig(output, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Сохранено: {output}")


# ============================================================
#  MAIN
# ============================================================

def main():
    print(f"Загрузка моделей из {MODELS_DIR}...")
    risk_model = joblib.load(MODELS_DIR / "risk_model.pkl")
    grade_model = joblib.load(MODELS_DIR / "grade_predictor.pkl")
    print(f"  ✓ risk_model:  {type(risk_model).__name__}")
    print(f"  ✓ grade_model: {type(grade_model).__name__}")

    print(f"\nГенерация контрольной выборки ({N_STUDENTS} учеников)...")
    X_cls, y_cls, X_reg, y_reg = generate_dataset(N_STUDENTS)
    print(f"  ✓ Классификация: {len(X_cls)} примеров")
    print(f"  ✓ Регрессия:     {len(X_reg)} примеров")

    risk_report = evaluate_risk_classifier(risk_model, X_cls, y_cls)
    grade_report = evaluate_grade_predictor(grade_model, X_reg, y_reg)
    cluster_report = evaluate_clustering(X_cls)

    # Сохраняем сводный JSON
    metrics = {
        "dataset": {
            "synthetic": True,
            "n_students": N_STUDENTS,
            "random_seed": RANDOM_SEED,
            "features": FEATURE_NAMES,
        },
        "risk_classifier": risk_report,
        "grade_predictor": grade_report,
        "kmeans_clustering": cluster_report,
    }
    out_json = REPORTS_DIR / "metrics.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f" ВСЕ МЕТРИКИ СОХРАНЕНЫ:")
    print(f"   {out_json}")
    print(f"   {REPORTS_DIR}/confusion_matrix.png")
    print(f"   {REPORTS_DIR}/regression_scatter.png")
    print(f"   {REPORTS_DIR}/rf_feature_importances.png")
    print(f"   {REPORTS_DIR}/gbr_feature_importances.png")
    print(f"   {REPORTS_DIR}/kmeans_silhouette.png")
    print("=" * 70)


if __name__ == "__main__":
    main()
