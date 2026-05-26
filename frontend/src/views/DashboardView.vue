<template>
  <AppLayout>
    <div class="page-wrap">

      <!-- Greeting -->
      <div class="greeting-row">
        <div>
          <h2 class="greeting-title">
            {{ greeting }}, <span class="accent">{{ firstName }}</span>
          </h2>
          <p class="greeting-subtitle">{{ subtitle }}</p>
        </div>
        <div class="greeting-date">
          <div class="greeting-date-label">Сегодня</div>
          <div class="greeting-date-value">{{ todayDate }}</div>
        </div>
      </div>

      <!-- Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-card-head">
            <div class="stat-icon indigo"><UsersIcon /></div>
            <span v-if="stats.studentsDelta > 0" class="stat-badge">
              <ArrowUpIcon />+{{ stats.studentsDelta }}
            </span>
          </div>
          <div class="stat-label">Учеников</div>
          <div class="stat-value">{{ stats.students }}</div>
          <div class="stat-foot">
            {{ stats.studentsDelta > 0 ? `+${stats.studentsDelta} новых за месяц` : 'всего активных' }}
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-card-head">
            <div class="stat-icon violet"><CalendarIcon /></div>
            <span v-if="stats.lessonsThisWeek > 0" class="stat-badge violet">
              {{ stats.lessonsThisWeek }} нед
            </span>
          </div>
          <div class="stat-label">Занятий</div>
          <div class="stat-value">{{ stats.lessons }}</div>
          <div class="stat-foot">
            {{ stats.lessonsThisWeek > 0 ? `${stats.lessonsThisWeek} на этой неделе` : 'за всё время' }}
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-card-head">
            <div class="stat-icon amber"><ClipboardDocumentListIcon /></div>
          </div>
          <div class="stat-label">Оценок</div>
          <div class="stat-value">{{ stats.grades }}</div>
          <div class="stat-foot">за всё время</div>
        </div>

        <div class="stat-card">
          <div class="stat-card-head">
            <div class="stat-icon emerald"><StarIcon /></div>
            <span v-if="stats.avgGrade" class="stat-badge"><ArrowUpIcon />рост</span>
          </div>
          <div class="stat-label">Средний балл</div>
          <div class="stat-value">
            {{ stats.avgGrade || '—' }}<span v-if="stats.avgGrade" class="suffix">/10</span>
          </div>
          <div class="stat-foot">по всем ученикам</div>
        </div>
      </div>

      <!-- Charts -->
      <div class="charts-grid">
        <div class="section-card chart-main">
          <div class="section-head">
            <h3 class="section-title">Динамика оценок</h3>
            <p class="section-sub">Последние 10 оценок</p>
          </div>
          <div v-if="gradesTrend.length < 2" class="chart-empty">
            Добавьте больше оценок для отображения графика
          </div>
          <v-chart v-else :option="gradesChartOption" style="height: 260px;" autoresize />
        </div>

        <!-- Группы риска -->
        <div class="section-card risk-card">
          <div class="section-head">
            <h3 class="section-title">Группы риска</h3>
            <p class="section-sub">По данным ML-модели</p>
          </div>

          <div v-if="riskTotalKnown === 0" class="risk-empty">
            Недостаточно данных. Нужно минимум 3 оценки по ученику.
          </div>

          <div v-else class="risk-list">
            <div>
              <div class="risk-item-head">
                <span class="risk-label"><span class="risk-dot emerald"></span>Высокие результаты</span>
                <span class="risk-count emerald">{{ riskCounts.low }}</span>
              </div>
              <div class="risk-bar-track"><div class="risk-bar-fill emerald" :style="{ width: riskPercent('low') + '%' }"></div></div>
            </div>
            <div>
              <div class="risk-item-head">
                <span class="risk-label"><span class="risk-dot amber"></span>Стабильный прогресс</span>
                <span class="risk-count amber">{{ riskCounts.medium }}</span>
              </div>
              <div class="risk-bar-track"><div class="risk-bar-fill amber" :style="{ width: riskPercent('medium') + '%' }"></div></div>
            </div>
            <div>
              <div class="risk-item-head">
                <span class="risk-label"><span class="risk-dot rose"></span>Требуют внимания</span>
                <span class="risk-count rose">{{ riskCounts.high }}</span>
              </div>
              <div class="risk-bar-track"><div class="risk-bar-fill rose" :style="{ width: riskPercent('high') + '%' }"></div></div>
            </div>
            <div v-if="riskCounts.unknown > 0" class="risk-footer-note">
              {{ riskCounts.unknown }} {{ pluralize(riskCounts.unknown, ['ученик', 'ученика', 'учеников']) }} без классификации
            </div>
          </div>

          <div class="risk-link-wrap">
            <router-link to="/analytics" class="section-link">Открыть аналитику →</router-link>
          </div>
        </div>
      </div>

      <!-- Upcoming -->
      <div class="lessons-card">
        <div class="lessons-head">
          <div>
            <h3 class="section-title">Ближайшие занятия</h3>
            <p class="section-sub">
              {{ upcomingLessons.length }} {{ pluralize(upcomingLessons.length, ['запланированное', 'запланированных', 'запланированных']) }}
            </p>
          </div>
          <router-link to="/calendar" class="section-link">Все занятия →</router-link>
        </div>

        <div v-if="upcomingLessons.length === 0" class="lessons-empty">
          Нет запланированных занятий
        </div>

        <div v-else>
          <div
            v-for="lesson in upcomingLessons"
            :key="lesson.id"
            class="lesson-row"
            :class="{ today: isToday(lesson.scheduled_at) }"
          >
            <div class="lesson-date">
              <div class="lesson-date-day">{{ formatDay(lesson.scheduled_at) }}</div>
              <div class="lesson-date-mon">{{ formatMonth(lesson.scheduled_at) }}</div>
            </div>

            <div class="lesson-body">
              <div class="lesson-title-row">
                <span class="lesson-student-name">{{ getStudentName(lesson.student_id) }}</span>
                <span v-if="lesson.topic" class="subject-chip" :class="subjectChipClass(lesson.topic)">
                  {{ lesson.topic }}
                </span>
              </div>
              <div class="lesson-time">{{ formatTime(lesson.scheduled_at) }}</div>
            </div>

            <span v-if="isToday(lesson.scheduled_at)" class="status-badge today">
              <span class="dot"></span>Сегодня
            </span>
            <span v-else-if="isTomorrow(lesson.scheduled_at)" class="status-badge tomorrow">Завтра</span>
            <span v-else class="status-badge other">{{ formatDate(lesson.scheduled_at) }}</span>
          </div>
        </div>
      </div>

    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import AppLayout from '@/components/AppLayout.vue'
import { useAuthStore } from '@/stores/auth.js'
import api from '@/api/index.js'
import {
  UsersIcon,
  CalendarIcon,
  ClipboardDocumentListIcon,
  StarIcon,
  ArrowUpIcon,
} from '@heroicons/vue/24/outline'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const authStore = useAuthStore()

const stats = ref({
  students: 0,
  studentsDelta: 0,
  lessons: 0,
  lessonsThisWeek: 0,
  grades: 0,
  avgGrade: 0,
})
const gradesTrend = ref([])
const riskCounts = ref({ low: 0, medium: 0, high: 0, unknown: 0 })
const upcomingLessons = ref([])
const students = ref([])

const riskTotalKnown = computed(() =>
  riskCounts.value.low + riskCounts.value.medium + riskCounts.value.high
)

function riskPercent(level) {
  const total = riskTotalKnown.value
  if (total === 0) return 0
  return Math.round((riskCounts.value[level] / total) * 100)
}

const firstName = computed(() => {
  const full = authStore.user?.full_name || ''
  const parts = full.split(/\s+/).filter(Boolean)
  return parts.length >= 2 ? parts[1] : (parts[0] || 'Дмитрий')
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return 'Доброй ночи'
  if (h < 12) return 'Доброе утро'
  if (h < 18) return 'Добрый день'
  return 'Добрый вечер'
})

const subtitle = computed(() => {
  const todayCount = upcomingLessons.value.filter(l => isToday(l.scheduled_at)).length
  if (todayCount === 0) return 'На сегодня занятий не запланировано'
  return `Сегодня у вас ${todayCount} ${pluralize(todayCount, ['занятие', 'занятия', 'занятий'])}`
})

const todayDate = computed(() => {
  const d = new Date()
  return d.toLocaleDateString('ru', { weekday: 'long', day: 'numeric', month: 'long' })
})

const gradesChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 20, bottom: 40 },
  xAxis: {
    type: 'category',
    data: gradesTrend.value.map(g => g.date),
    axisLabel: { fontSize: 11, color: '#64748b' },
    axisLine: { lineStyle: { color: '#e2e8f0' } },
  },
  yAxis: {
    type: 'value',
    min: 1,
    max: 10,
    axisLabel: { fontSize: 11, color: '#64748b' },
    splitLine: { lineStyle: { color: '#f1f5f9' } },
  },
  series: [{
    data: gradesTrend.value.map(g => g.value),
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 7,
    lineStyle: { color: '#4f46e5', width: 2.5 },
    itemStyle: { color: '#4f46e5' },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(79,70,229,0.25)' },
          { offset: 1, color: 'rgba(79,70,229,0.02)' },
        ],
      },
    },
  }],
}))

function getStudentName(id) {
  return students.value.find(s => s.id === id)?.full_name || 'Неизвестный'
}

function pluralize(n, forms) {
  const a = Math.abs(n) % 100
  const b = a % 10
  if (a > 10 && a < 20) return forms[2]
  if (b > 1 && b < 5) return forms[1]
  if (b === 1) return forms[0]
  return forms[2]
}

function formatDay(dt) { return new Date(dt).getDate() }
function formatMonth(dt) { return new Date(dt).toLocaleString('ru', { month: 'short' }).replace('.', '') }
function formatTime(dt) {
  return new Date(dt).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
}
function formatDate(dt) {
  return new Date(dt).toLocaleDateString('ru', { day: '2-digit', month: '2-digit' })
}

function isToday(dt) {
  const d = new Date(dt)
  const now = new Date()
  return d.toDateString() === now.toDateString()
}
function isTomorrow(dt) {
  const d = new Date(dt)
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  return d.toDateString() === tomorrow.toDateString()
}

function subjectChipClass(topic) {
  const t = (topic || '').toLowerCase()
  if (/алгеб|матем/.test(t))      return 'sky'
  if (/геометр/.test(t))          return 'violet'
  if (/егэ|огэ|подготов/.test(t)) return 'amber'
  if (/физик/.test(t))            return 'indigo'
  if (/хим/.test(t))              return 'emerald'
  if (/русск|литер/.test(t))      return 'rose'
  if (/англ|нем|франц/.test(t))   return 'fuchsia'
  return 'slate'
}

onMounted(async () => {
  try {
    const [studentsRes, lessonsRes, gradesRes, overviewRes] = await Promise.all([
      api.get('/students/'),
      api.get('/lessons/'),
      api.get('/grades/'),
      api.get('/analytics/overview').catch(() => null),
    ])

    students.value = studentsRes.data
    const allGrades = gradesRes.data
    const allLessons = lessonsRes.data

    stats.value.students = studentsRes.data.length
    stats.value.lessons = allLessons.length
    stats.value.grades = allGrades.length

    const monthAgo = new Date()
    monthAgo.setMonth(monthAgo.getMonth() - 1)
    stats.value.studentsDelta = studentsRes.data.filter(s => s.created_at && new Date(s.created_at) >= monthAgo).length

    const weekStart = new Date()
    weekStart.setDate(weekStart.getDate() - 7)
    stats.value.lessonsThisWeek = allLessons.filter(l => new Date(l.scheduled_at) >= weekStart).length

    if (allGrades.length > 0) {
      const avg = allGrades.reduce((s, g) => s + g.value, 0) / allGrades.length
      stats.value.avgGrade = avg.toFixed(1)
    }

    const sorted = [...allGrades].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
    gradesTrend.value = sorted.slice(-10).map(g => ({
      date: new Date(g.created_at).toLocaleDateString('ru', { day: '2-digit', month: '2-digit' }),
      value: g.value,
    }))

    if (overviewRes && overviewRes.data && Array.isArray(overviewRes.data.students)) {
      const counts = { low: 0, medium: 0, high: 0, unknown: 0 }
      for (const s of overviewRes.data.students) {
        if (s.risk_level in counts) {
          counts[s.risk_level]++
        }
      }
      riskCounts.value = counts
    }

    const now = new Date()
    upcomingLessons.value = allLessons
      .filter(l => !l.completed && new Date(l.scheduled_at) >= now)
      .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
      .slice(0, 5)
  } catch (e) {
    console.error('Не удалось загрузить данные дашборда:', e)
  }
})
</script>