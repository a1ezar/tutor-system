<template>
  <AppLayout>
    <div class="page-wrap">
      <!-- Приветствие -->
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

      <div v-if="loading" class="loading-state">Загрузка...</div>

      <template v-else>
        <!-- Стат-карточки -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-card-head">
              <div class="stat-icon indigo">
                <DocumentTextIcon />
              </div>
            </div>
            <div class="stat-label">Всего заданий</div>
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-foot">за всё время</div>
          </div>

          <div class="stat-card">
            <div class="stat-card-head">
              <div class="stat-icon violet">
                <BellAlertIcon />
              </div>
              <span v-if="stats.newCount > 0" class="stat-badge violet">{{ stats.newCount }} ждёт</span>
            </div>
            <div class="stat-label">Новых</div>
            <div class="stat-value">{{ stats.newCount }}</div>
            <div class="stat-foot">{{ stats.newCount > 0 ? 'нужно выполнить' : 'все выполнены' }}</div>
          </div>

          <div class="stat-card">
            <div class="stat-card-head">
              <div class="stat-icon emerald">
                <CheckCircleIcon />
              </div>
            </div>
            <div class="stat-label">Выполнено</div>
            <div class="stat-value">{{ stats.completed }}</div>
            <div class="stat-foot">из {{ stats.total }}</div>
          </div>

          <div class="stat-card">
            <div class="stat-card-head">
              <div class="stat-icon amber">
                <StarIcon />
              </div>
            </div>
            <div class="stat-label">Средний балл</div>
            <div class="stat-value">
              {{ stats.avgScore || '—' }}<span v-if="stats.avgScore" class="suffix">/10</span>
            </div>
            <div class="stat-foot">по выполненным</div>
          </div>
        </div>

        <!-- Новые задания -->
        <div v-if="newHomeworks.length > 0" class="detail-section" style="margin-top: 8px">
          <div class="detail-section-head">
            <h2 class="detail-section-title">
              <BellAlertIcon />
              Новые задания
              <span class="detail-section-count">({{ newHomeworks.length }})</span>
            </h2>
            <router-link to="/my-homeworks" class="section-link">Все задания →</router-link>
          </div>

          <div class="hw-list">
            <div
              v-for="hw in newHomeworks"
              :key="hw.id"
              class="hw-card"
              @click="$router.push(`/my-homeworks/${hw.id}`)"
            >
              <div class="hw-card-top">
                <div class="hw-info">
                  <div class="hw-title">{{ hw.title }}</div>
                  <div class="hw-meta">
                    <span v-if="hw.topic" class="subject-chip" :class="subjectChipClass(hw.topic)">
                      {{ hw.topic }}
                    </span>
                    <span class="hw-meta-item">
                      <DocumentTextIcon />
                      {{ hw.questions_count }} {{ pluralize(hw.questions_count, ['вопрос', 'вопроса', 'вопросов']) }}
                    </span>
                  </div>
                </div>
                <div class="hw-stats">
                  <span class="status-pill status-new">Новое</span>
                </div>
              </div>
              <div v-if="hw.due_date" class="hw-card-bottom">
                <span class="hw-due">Срок: {{ formatDate(hw.due_date) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Пустое состояние -->
        <div v-if="homeworks.length === 0" class="empty-state">
          <div class="empty-state-icon">
            <DocumentTextIcon />
          </div>
          <div class="empty-state-title">Заданий пока нет</div>
          <div class="empty-state-text">
            Когда репетитор пришлёт задание, оно появится здесь.
          </div>
        </div>

        <!-- Если новых нет, но есть выполненные -->
        <div v-else-if="newHomeworks.length === 0" class="empty-state" style="margin-top: 8px">
          <div class="empty-state-icon" style="background: #ecfdf5; color: #10b981">
            <CheckCircleIcon />
          </div>
          <div class="empty-state-title">Все задания выполнены</div>
          <div class="empty-state-text">
            Отличная работа! Ваши результаты можно посмотреть на странице «Домашние задания».
          </div>
          <router-link to="/my-homeworks" class="btn btn-secondary">
            Посмотреть результаты
          </router-link>
        </div>
      </template>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { useAuthStore } from '@/stores/auth.js'
import api from '@/api/index.js'
import {
  DocumentTextIcon,
  BellAlertIcon,
  StarIcon,
} from '@heroicons/vue/24/outline'
import { CheckCircleIcon } from '@heroicons/vue/24/solid'

const authStore = useAuthStore()
const loading = ref(true)
const homeworks = ref([])

const firstName = computed(() => {
  const full = authStore.user?.full_name || ''
  const parts = full.split(/\s+/).filter(Boolean)
  return parts.length >= 2 ? parts[1] : (parts[0] || 'друг')
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return 'Доброй ночи'
  if (h < 12) return 'Доброе утро'
  if (h < 18) return 'Привет'
  return 'Добрый вечер'
})

const todayDate = computed(() => {
  return new Date().toLocaleDateString('ru', { weekday: 'long', day: 'numeric', month: 'long' })
})

const newHomeworks = computed(() => homeworks.value.filter(h => h.status === 'new'))
const completedHomeworks = computed(() => homeworks.value.filter(h => h.status === 'completed'))

const stats = computed(() => {
  const total = homeworks.value.length
  const newCount = newHomeworks.value.length
  const completed = completedHomeworks.value.length
  const scores = homeworks.value.filter(h => h.best_score !== null).map(h => h.best_score)
  const avgScore = scores.length > 0
    ? Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10
    : null
  return { total, newCount, completed, avgScore }
})

const subtitle = computed(() => {
  const n = newHomeworks.value.length
  if (n === 0) return homeworks.value.length === 0
    ? 'Задания появятся, когда репетитор их пришлёт'
    : 'Все задания выполнены — отличная работа!'
  return `У вас ${n} ${pluralize(n, ['новое задание', 'новых задания', 'новых заданий'])}`
})

function pluralize(n, forms) {
  const a = Math.abs(n) % 100
  const b = a % 10
  if (a > 10 && a < 20) return forms[2]
  if (b > 1 && b < 5) return forms[1]
  if (b === 1) return forms[0]
  return forms[2]
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
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
    const res = await api.get('/homeworks/my/list')
    homeworks.value = res.data.homeworks
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>