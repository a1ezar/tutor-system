<template>
  <AppLayout>
    <div class="page-wrap">
      <!-- Header -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Аналитика</h1>
          <p class="page-subtitle">Интеллектуальный анализ успеваемости с использованием ML</p>
        </div>
        <div class="page-actions">
          <div class="tabs-bar">
            <button class="tab-btn" :class="{ active: activeTab === 'students' }" @click="activeTab = 'students'">
              <UserGroupIcon />
              Ученики
            </button>
            <button class="tab-btn" :class="{ active: activeTab === 'clusters' }" @click="activeTab = 'clusters'; loadClusters()">
              <Squares2X2Icon />
              Кластеры
            </button>
            <button class="tab-btn" :class="{ active: activeTab === 'models' }" @click="activeTab = 'models'; loadModelInfo()">
              <CpuChipIcon />
              О модели
            </button>
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading-state">Загрузка аналитики...</div>

      <div v-else>
        <!-- ================== TAB: УЧЕНИКИ ================== -->
        <div v-if="activeTab === 'students'">
          <div v-if="overview.students.length === 0" class="empty-state">
            <div class="empty-state-icon">
              <ChartBarSquareIcon />
            </div>
            <div class="empty-state-title">Недостаточно данных</div>
            <div class="empty-state-text">
              Добавьте учеников и хотя бы 3 оценки по каждому, чтобы ML-модель могла построить аналитику.
            </div>
          </div>

          <!-- Сетка учеников -->
          <div v-else class="cards-grid">
            <div
              v-for="student in overview.students"
              :key="student.student_id"
              class="an-card"
              :class="{ active: selectedStudentId === student.student_id }"
              @click="selectStudent(student.student_id)"
            >
              <div class="an-card-top">
                <div class="student-card-avatar">{{ initials(student.student_name) }}</div>
                <div class="an-card-info">
                  <div class="an-card-name">{{ student.student_name }}</div>
                  <div class="an-card-subject">{{ student.subject || 'Без предмета' }}</div>
                </div>
                <span class="risk-badge" :class="student.risk_color">{{ student.risk_label }}</span>
              </div>

              <div class="an-card-stats">
                <div class="an-card-stat">
                  <div class="an-card-stat-value" :class="gradeClass(student.avg_grade)">
                    {{ student.avg_grade ?? '—' }}
                  </div>
                  <div class="an-card-stat-label">Ср. балл</div>
                </div>
                <div class="an-card-stat">
                  <div class="an-card-stat-value">{{ student.grades_count }}</div>
                  <div class="an-card-stat-label">Оценок</div>
                </div>
                <div class="an-card-stat">
                  <div class="an-card-stat-value">{{ student.predicted_next ?? '—' }}</div>
                  <div class="an-card-stat-label">Прогноз</div>
                </div>
                <div class="an-card-stat">
                  <div class="trend-cell" :class="student.trend">
                    <ArrowTrendingUpIcon v-if="student.trend === 'improving'" />
                    <ArrowTrendingDownIcon v-else-if="student.trend === 'declining'" />
                    <MinusIcon v-else />
                  </div>
                  <div class="an-card-stat-label">Тренд</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="!selectedAnalytics && overview.students.length > 0" class="select-hint">
            <CursorArrowRaysIcon />
            Нажмите на карточку ученика для детального анализа
          </div>

          <!-- Детальная аналитика -->
          <div v-if="selectedAnalytics" class="an-detail">
            <h2 class="an-detail-title">
              Детальный анализ — {{ selectedAnalytics.student_name }}
            </h2>

            <div class="an-grid">
              <!-- Прогноз -->
              <div class="an-detail-card">
                <div class="an-detail-card-title">
                  <span class="title-left">
                    <SparklesIcon />
                    Прогноз оценки
                  </span>
                </div>
                <div v-if="selectedAnalytics.prediction.predicted" class="prediction-value">
                  {{ selectedAnalytics.prediction.predicted }}
                </div>
                <div v-else class="prediction-empty">{{ selectedAnalytics.prediction.message }}</div>
                <div class="prediction-meta">
                  <div v-if="selectedAnalytics.prediction.trend_label">
                    Тренд: <strong>{{ selectedAnalytics.prediction.trend_label }}</strong>
                  </div>
                  <div v-if="selectedAnalytics.prediction.avg_last_3">
                    Средняя за последние 3 оценки: <strong>{{ selectedAnalytics.prediction.avg_last_3 }}</strong>
                  </div>
                </div>
              </div>

              <!-- Группа риска -->
              <div class="an-detail-card">
                <div class="an-detail-card-title">
                  <span class="title-left">
                    <ExclamationTriangleIcon />
                    Группа риска
                  </span>
                </div>
                <div class="risk-large" :class="selectedAnalytics.risk.risk_color">
                  {{ selectedAnalytics.risk.risk_label }}
                </div>
                <div class="risk-stats">
                  <div>Средний балл: <strong>{{ selectedAnalytics.risk.avg_grade }}</strong></div>
                  <div>Разброс: <strong>{{ selectedAnalytics.risk.std_grade }}</strong></div>
                </div>
                <div class="recommendation-box">
                  <LightBulbIcon />
                  {{ selectedAnalytics.risk.recommendation }}
                </div>
              </div>
            </div>

            <!-- Рекомендации по повторению -->
            <div
              v-if="selectedAnalytics.review && selectedAnalytics.review.recommendations.length > 0"
              class="an-detail-card"
              style="margin-bottom: 20px;"
            >
              <div class="an-detail-card-title">
                <span class="title-left">
                  <ClockIcon />
                  Рекомендации по повторению
                </span>
                <span v-if="selectedAnalytics.review.urgent_count > 0" class="urgent-badge">
                  {{ selectedAnalytics.review.urgent_count }} срочных
                </span>
              </div>
              <p class="review-description">
                На основе кривой забывания Эббингауза — темы, которые ученик может забыть
              </p>

              <div class="review-list">
                <div
                  v-for="rec in selectedAnalytics.review.recommendations"
                  :key="rec.topic"
                  class="review-item"
                  :class="{ urgent: rec.needs_review }"
                >
                  <div class="review-item-head">
                    <span class="review-item-topic">{{ rec.topic }}</span>
                    <span v-if="rec.needs_review" class="review-urgent-tag">
                      <ExclamationCircleIcon style="width: 11px; height: 11px;" />
                      Повторить
                    </span>
                  </div>

                  <div class="retention-bar-wrap">
                    <div
                      class="retention-bar"
                      :class="retentionBarClass(rec.retention)"
                      :style="{ width: `${rec.retention * 100}%` }"
                    ></div>
                  </div>

                  <div class="review-meta">
                    <span>Запоминание: <strong>{{ Math.round(rec.retention * 100) }}%</strong></span>
                    <span>Последняя: <strong>{{ rec.last_grade }}</strong></span>
                    <span>Дней назад: <strong>{{ rec.days_since_review }}</strong></span>
                    <span>Повторений: <strong>{{ rec.repetitions }}</strong></span>
                  </div>

                  <div class="review-next-date">
                    Рекомендуемое повторение: {{ formatDate(rec.next_review_date) }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Анализ по темам -->
            <div class="an-detail-card">
              <div class="an-detail-card-title">
                <span class="title-left">
                  <BookOpenIcon />
                  Анализ по темам
                </span>
              </div>

              <div v-if="selectedAnalytics.topics.topics.length === 0" style="text-align: center; color: #94a3b8; padding: 24px; font-size: 14px;">
                Недостаточно данных для анализа по темам
              </div>

              <div v-else>
                <div v-for="topic in selectedAnalytics.topics.topics" :key="topic.topic" class="topic-row">
                  <div class="topic-name">{{ topic.topic }}</div>
                  <div class="topic-bar-wrap">
                    <div class="topic-bar" :class="topicBarClass(topic.avg)" :style="{ width: `${topic.avg * 10}%` }"></div>
                  </div>
                  <div class="topic-grade" :class="gradeClass(topic.avg)">{{ topic.avg }}</div>
                  <div class="topic-count">{{ topic.count }} оц.</div>
                </div>

                <div v-if="selectedAnalytics.topics.weak_topics.length > 0" class="topics-summary weak">
                  <ExclamationTriangleIcon />
                  <div>
                    <strong>Проблемные темы:</strong>
                    {{ selectedAnalytics.topics.weak_topics.map(t => t.topic).join(', ') }}
                  </div>
                </div>
                <div v-if="selectedAnalytics.topics.strong_topics.length > 0" class="topics-summary strong">
                  <CheckCircleIcon />
                  <div>
                    <strong>Сильные темы:</strong>
                    {{ selectedAnalytics.topics.strong_topics.map(t => t.topic).join(', ') }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ================== TAB: КЛАСТЕРЫ ================== -->
        <div v-if="activeTab === 'clusters'">
          <div v-if="clustersLoading" class="loading-state">Кластеризация учеников...</div>

          <div v-else-if="clustersData && clustersData.clusters.length > 0">
            <!-- Карточки кластеров -->
            <div class="clusters-grid">
              <div
                v-for="cluster in clustersData.clusters"
                :key="cluster.cluster_id"
                class="cluster-card"
                :style="{ borderLeftColor: cluster.color }"
              >
                <div class="cluster-head">
                  <div class="cluster-dot" :style="{ background: cluster.color }"></div>
                  <div class="cluster-label">{{ cluster.label }}</div>
                  <div class="cluster-count">{{ cluster.count }} уч.</div>
                </div>
                <div class="cluster-description">{{ cluster.description }}</div>
                <div class="cluster-stats">
                  <div class="cluster-stat">
                    <span class="cluster-stat-value" :class="gradeClass(cluster.avg_grade)">{{ cluster.avg_grade }}</span>
                    <span class="cluster-stat-label">Ср. балл</span>
                  </div>
                  <div class="cluster-stat">
                    <span class="cluster-stat-value" :class="trendClass(cluster.avg_trend)">
                      {{ cluster.avg_trend > 0 ? '+' : '' }}{{ cluster.avg_trend }}
                    </span>
                    <span class="cluster-stat-label">Тренд</span>
                  </div>
                  <div class="cluster-stat">
                    <span class="cluster-stat-value">{{ cluster.avg_std }}</span>
                    <span class="cluster-stat-label">Разброс</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Таблица распределения -->
            <h2 class="an-detail-title" style="margin-top: 24px;">
              Распределение учеников по группам
            </h2>
            <div class="cluster-table">
              <div class="cluster-table-head">
                <span>Ученик</span>
                <span>Группа</span>
                <span>Ср. балл</span>
                <span>Тренд</span>
                <span>Оценок</span>
                <span>Занятий</span>
              </div>
              <div v-for="s in clustersData.students" :key="s.student_id" class="cluster-table-row">
                <span class="cluster-table-name">{{ s.student_name }}</span>
                <span>
                  <span class="cluster-mini-badge" :style="{ background: s.cluster_color + '20', color: s.cluster_color }">
                    <span class="mini-dot" :style="{ background: s.cluster_color }"></span>
                    {{ s.cluster_label }}
                  </span>
                </span>
                <span :class="gradeClass(s.features.avg_grade)" style="font-weight: 600;">{{ s.features.avg_grade }}</span>
                <span :class="trendClass(s.features.trend)" style="font-weight: 600;">
                  {{ s.features.trend > 0 ? '+' : '' }}{{ s.features.trend }}
                </span>
                <span style="color: #475569;">{{ s.features.total_grades }}</span>
                <span style="color: #475569;">{{ s.features.lessons_count }}</span>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            <div class="empty-state-icon">
              <Squares2X2Icon />
            </div>
            <div class="empty-state-title">Недостаточно данных для кластеризации</div>
            <div class="empty-state-text">
              {{ clustersData?.message || 'Нужно минимум 3 ученика с оценками, чтобы ML-модель могла разделить их на группы.' }}
            </div>
          </div>
        </div>

        <!-- ================== TAB: О МОДЕЛИ ================== -->
        <div v-if="activeTab === 'models'">
          <div v-if="modelInfoLoading" class="loading-state">Загрузка информации о моделях...</div>

          <div v-else-if="modelInfo">
            <p style="color: #64748b; font-size: 14px; margin-bottom: 20px;">
              Платформа использует обученные модели машинного обучения для прогноза оценок и классификации учеников по группам риска. Ниже — типы моделей, их параметры и важность признаков.
            </p>

            <div class="an-grid">
              <!-- RandomForest -->
              <div v-if="modelInfo.risk_model" class="model-card">
                <div class="model-card-head">
                  <div class="model-card-icon indigo">
                    <ShieldCheckIcon />
                  </div>
                  <div>
                    <div class="model-card-name">{{ modelInfo.risk_model.type }}</div>
                    <div class="model-card-purpose">Классификация группы риска</div>
                  </div>
                </div>

                <div class="model-card-params">
                  <div class="model-param">
                    <span class="model-param-label">Деревьев</span>
                    <span class="model-param-value">{{ modelInfo.risk_model.n_estimators }}</span>
                  </div>
                  <div class="model-param">
                    <span class="model-param-label">Глубина</span>
                    <span class="model-param-value">{{ modelInfo.risk_model.max_depth }}</span>
                  </div>
                  <div class="model-param">
                    <span class="model-param-label">Классов</span>
                    <span class="model-param-value">{{ modelInfo.risk_model.classes.length }}</span>
                  </div>
                </div>

                <div class="model-section-title">Важность признаков</div>
                <div class="model-importances">
                  <div v-for="(f, i) in modelInfo.risk_model.feature_importances" :key="f.feature" class="model-imp-row">
                    <span class="model-imp-name">{{ featureLabel(f.feature) }}</span>
                    <div class="model-imp-bar-wrap">
                      <div
                        class="model-imp-bar"
                        :class="{ top: i === 0 }"
                        :style="{ width: `${f.importance * 100}%` }"
                      ></div>
                    </div>
                    <span class="model-imp-value">{{ (f.importance * 100).toFixed(1) }}%</span>
                  </div>
                </div>

                <div class="model-classes">
                  Классы: <strong v-for="(c, i) in modelInfo.risk_model.classes" :key="c">{{ classLabel(c) }}{{ i < modelInfo.risk_model.classes.length - 1 ? ', ' : '' }}</strong>
                </div>
              </div>

              <!-- GradientBoosting -->
              <div v-if="modelInfo.grade_model" class="model-card">
                <div class="model-card-head">
                  <div class="model-card-icon violet">
                    <SparklesIcon />
                  </div>
                  <div>
                    <div class="model-card-name">{{ modelInfo.grade_model.type }}</div>
                    <div class="model-card-purpose">Прогноз следующей оценки</div>
                  </div>
                </div>

                <div class="model-card-params">
                  <div class="model-param">
                    <span class="model-param-label">Деревьев</span>
                    <span class="model-param-value">{{ modelInfo.grade_model.n_estimators }}</span>
                  </div>
                  <div class="model-param">
                    <span class="model-param-label">Глубина</span>
                    <span class="model-param-value">{{ modelInfo.grade_model.max_depth }}</span>
                  </div>
                  <div class="model-param">
                    <span class="model-param-label">Шаг обучения</span>
                    <span class="model-param-value">{{ modelInfo.grade_model.learning_rate }}</span>
                  </div>
                </div>

                <div class="model-section-title">Важность признаков</div>
                <div class="model-importances">
                  <div v-for="(f, i) in modelInfo.grade_model.feature_importances" :key="f.feature" class="model-imp-row">
                    <span class="model-imp-name">{{ featureLabel(f.feature) }}</span>
                    <div class="model-imp-bar-wrap">
                      <div
                        class="model-imp-bar violet"
                        :class="{ top: i === 0 }"
                        :style="{ width: `${f.importance * 100}%` }"
                      ></div>
                    </div>
                    <span class="model-imp-value">{{ (f.importance * 100).toFixed(1) }}%</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Описание признаков -->
            <div class="an-detail-card" style="margin-top: 20px;">
              <div class="an-detail-card-title">
                <span class="title-left">
                  <BookOpenIcon />
                  Используемые признаки
                </span>
              </div>
              <p style="color: #64748b; font-size: 13px; margin-bottom: 14px;">
                Из истории оценок ученика извлекаются следующие признаки и подаются на вход моделям.
              </p>
              <div class="feature-list">
                <div class="feature-item">
                  <div class="feature-name">avg</div>
                  <div class="feature-desc">Средняя оценка по всем работам</div>
                </div>
                <div class="feature-item">
                  <div class="feature-name">std</div>
                  <div class="feature-desc">Стандартное отклонение — стабильность оценок</div>
                </div>
                <div class="feature-item">
                  <div class="feature-name">trend</div>
                  <div class="feature-desc">Коэффициент наклона прямой регрессии — динамика</div>
                </div>
                <div class="feature-item">
                  <div class="feature-name">min</div>
                  <div class="feature-desc">Минимальная оценка за период</div>
                </div>
                <div class="feature-item">
                  <div class="feature-name">max</div>
                  <div class="feature-desc">Максимальная оценка за период</div>
                </div>
              </div>
            </div>

            <!-- Метрики качества (статически — те, что мы получили через evaluate_models.py) -->
            <div class="an-detail-card" style="margin-top: 20px;">
              <div class="an-detail-card-title">
                <span class="title-left">
                  <ChartBarSquareIcon />
                  Метрики качества моделей
                </span>
              </div>
              <p style="color: #64748b; font-size: 13px; margin-bottom: 14px;">
                Получены на синтетической выборке из 1000 учеников с использованием 5-кратной кросс-валидации.
              </p>

              <div class="metrics-table">
                <div class="metrics-row metrics-head">
                  <span>Модель</span>
                  <span>Метрика</span>
                  <span>Значение</span>
                </div>
                <div class="metrics-row">
                  <span class="metrics-model">RandomForest</span>
                  <span>Accuracy (5-fold CV)</span>
                  <span class="metrics-value good">0.863 ± 0.022</span>
                </div>
                <div class="metrics-row">
                  <span class="metrics-model">RandomForest</span>
                  <span>F1 macro</span>
                  <span class="metrics-value good">0.852 ± 0.023</span>
                </div>
                <div class="metrics-row">
                  <span class="metrics-model">GradientBoosting</span>
                  <span>MAE (5-fold CV)</span>
                  <span class="metrics-value good">0.760 ± 0.026</span>
                </div>
                <div class="metrics-row">
                  <span class="metrics-model">GradientBoosting</span>
                  <span>RMSE</span>
                  <span class="metrics-value">0.962</span>
                </div>
                <div class="metrics-row">
                  <span class="metrics-model">GradientBoosting</span>
                  <span>R²</span>
                  <span class="metrics-value good">0.689 ± 0.037</span>
                </div>
                <div class="metrics-row">
                  <span class="metrics-model">KMeans</span>
                  <span>Silhouette score</span>
                  <span class="metrics-value good">0.43</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            <div class="empty-state-icon">
              <CpuChipIcon />
            </div>
            <div class="empty-state-title">Модели не загружены</div>
            <div class="empty-state-text">
              ML-модели не были найдены в backend. Запустите train_models.py.
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import api from '@/api/index.js'
import {
  UserGroupIcon,
  Squares2X2Icon,
  ChartBarSquareIcon,
  SparklesIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  ClockIcon,
  ExclamationCircleIcon,
  BookOpenIcon,
  CursorArrowRaysIcon,
  MinusIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CpuChipIcon,
  ShieldCheckIcon,
} from '@heroicons/vue/24/outline'
import { CheckCircleIcon } from '@heroicons/vue/24/solid'

const loading = ref(true)
const overview = ref({ students: [] })
const selectedStudentId = ref(null)
const selectedAnalytics = ref(null)
const activeTab = ref('students')
const clustersLoading = ref(false)
const clustersData = ref(null)
const modelInfoLoading = ref(false)
const modelInfo = ref(null)

async function loadOverview() {
  try {
    const res = await api.get('/analytics/overview')
    overview.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function selectStudent(id) {
  if (selectedStudentId.value === id) {
    selectedStudentId.value = null
    selectedAnalytics.value = null
    return
  }
  selectedStudentId.value = id
  try {
    const res = await api.get(`/analytics/student/${id}`)
    selectedAnalytics.value = res.data
  } catch (e) {
    console.error(e)
  }
}

async function loadClusters() {
  if (clustersData.value) return
  clustersLoading.value = true
  try {
    const res = await api.get('/analytics/clusters')
    clustersData.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    clustersLoading.value = false
  }
}

async function loadModelInfo() {
  if (modelInfo.value) return
  modelInfoLoading.value = true
  try {
    const res = await api.get('/analytics/model-info')
    modelInfo.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    modelInfoLoading.value = false
  }
}

function initials(fullName) {
  if (!fullName) return '?'
  return fullName.split(/\s+/).filter(Boolean).slice(0, 2).map(s => s[0]).join('').toUpperCase()
}

function gradeClass(value) {
  if (value === null || value === undefined || value === '—') return ''
  if (value >= 8) return 'grade-high'
  if (value >= 6) return 'grade-mid'
  return 'grade-low'
}

function topicBarClass(value) {
  if (value >= 8) return 'bar-high'
  if (value >= 6) return 'bar-mid'
  return 'bar-low'
}

function retentionBarClass(retention) {
  if (retention >= 0.7) return 'retention-good'
  if (retention >= 0.4) return 'retention-warning'
  return 'retention-danger'
}

function trendClass(trend) {
  if (trend >= 0.2) return 'grade-high'
  if (trend <= -0.2) return 'grade-low'
  return 'grade-mid'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}

function featureLabel(f) {
  const labels = {
    avg: 'Средняя оценка',
    std: 'Стандартное отклонение',
    trend: 'Тренд (наклон регрессии)',
    min: 'Минимальная оценка',
    max: 'Максимальная оценка',
  }
  return labels[f] || f
}

function classLabel(c) {
  const labels = {
    low: 'Низкий риск',
    medium: 'Средний риск',
    high: 'Высокий риск',
  }
  return labels[c] || c
}

onMounted(loadOverview)
</script>