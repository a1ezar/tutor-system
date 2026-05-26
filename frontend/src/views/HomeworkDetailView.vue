<template>
  <AppLayout>
    <div class="page-wrap">
      <!-- Назад -->
      <router-link to="/homeworks" class="back-link">
        <ArrowLeftIcon />
        К списку заданий
      </router-link>

      <!-- Header -->
      <div class="page-header">
        <div>
          <h1 class="page-title">{{ homework?.title || 'Задание' }}</h1>
          <p v-if="homework?.topic" class="page-subtitle">
            <span class="subject-chip" :class="subjectChipClass(homework.topic)">{{ homework.topic }}</span>
          </p>
        </div>
        <div class="page-actions">
          <button class="btn btn-danger" @click="deleteHomework">
            <TrashIcon />
            Удалить
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading-state">Загрузка...</div>

      <div v-else-if="homework">
        <!-- Вопросы -->
        <div class="section-header">
          <h2>
            <QuestionMarkCircleIcon />
            Вопросы
            <span class="section-header-count">({{ homework.questions.length }})</span>
          </h2>
        </div>

        <div v-for="q in homework.questions" :key="q.id" class="question-card">
          <div class="q-head">
            <span class="q-num">{{ q.order_num }}</span>
            <span class="q-type-chip" :class="q.question_type">
              {{ typeLabel(q.question_type) }}
            </span>
            <span class="q-points">{{ q.points }} {{ pluralize(q.points, ['балл', 'балла', 'баллов']) }}</span>
          </div>

          <div class="q-text">{{ q.question_text }}</div>

          <div v-if="q.question_type === 'test' && q.options" class="q-options">
            <div
              v-for="(opt, oi) in parseOptions(q.options)"
              :key="oi"
              class="q-opt"
              :class="{ correct: String(oi) === q.correct_answer }"
            >
              <span>{{ opt }}</span>
              <span v-if="String(oi) === q.correct_answer" class="q-opt-mark">
                <CheckIcon />
              </span>
            </div>
          </div>

          <div v-else class="q-answer-block">
            Правильный ответ: <strong>{{ q.correct_answer }}</strong>
          </div>
        </div>

        <!-- Попытки -->
        <div class="section-header">
          <h2>
            <ChartBarSquareIcon />
            Попытки учеников
            <span class="section-header-count">({{ attempts.length }})</span>
          </h2>
        </div>

        <div v-if="attempts.length === 0" class="empty-state">
          <div class="empty-state-icon">
            <UserGroupIcon />
          </div>
          <div class="empty-state-title">Ещё никто не выполнял</div>
          <div class="empty-state-text">
            Когда ученик пройдёт задание, его попытка появится здесь с разбором ответов.
          </div>
        </div>

        <div v-else>
          <div v-for="att in attempts" :key="att.id" class="attempt-card">
            <div class="attempt-head">
              <div class="attempt-score" :class="scoreClass(att.percentage)">
                {{ att.percentage }}%
              </div>
              <div class="attempt-info">
                <div class="attempt-info-points">{{ att.score }} / {{ att.max_score }} баллов</div>
                <div class="attempt-info-date">{{ formatDate(att.started_at) }}</div>
              </div>
            </div>

            <div class="attempt-answers">
              <div
                v-for="a in att.answers"
                :key="a.question_id"
                class="att-answer"
                :class="a.is_correct ? 'correct' : 'wrong'"
              >
                <span class="att-answer-label">Вопрос {{ a.question_id }}:</span>
                <span class="att-answer-text">{{ a.student_answer || '—' }}</span>
                <span class="att-answer-mark" :class="a.is_correct ? 'ok' : 'fail'">
                  <CheckIcon v-if="a.is_correct" />
                  <XMarkIcon v-else />
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import api from '@/api/index.js'
import {
  ArrowLeftIcon,
  TrashIcon,
  QuestionMarkCircleIcon,
  ChartBarSquareIcon,
  UserGroupIcon,
} from '@heroicons/vue/24/outline'
import { CheckIcon, XMarkIcon } from '@heroicons/vue/24/solid'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const homework = ref(null)
const attempts = ref([])

async function loadData() {
  loading.value = true
  try {
    const [hwRes, attRes] = await Promise.all([
      api.get(`/homeworks/${route.params.id}`),
      api.get(`/homeworks/${route.params.id}/attempts`),
    ])
    homework.value = hwRes.data
    attempts.value = attRes.data.attempts || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function deleteHomework() {
  if (!confirm('Удалить задание? Все попытки учеников также будут удалены.')) return
  try {
    await api.delete(`/homeworks/${route.params.id}`)
    router.push('/homeworks')
  } catch (e) {
    alert('Ошибка удаления')
  }
}

function parseOptions(options) {
  if (typeof options === 'string') {
    try { return JSON.parse(options) } catch { return [] }
  }
  return options || []
}

function typeLabel(t) {
  if (t === 'test') return 'Тест'
  if (t === 'number') return 'Число'
  if (t === 'text') return 'Текст'
  return t
}

function pluralize(n, forms) {
  const a = Math.abs(n) % 100
  const b = a % 10
  if (a > 10 && a < 20) return forms[2]
  if (b > 1 && b < 5) return forms[1]
  if (b === 1) return forms[0]
  return forms[2]
}

function scoreClass(p) {
  if (p >= 80) return 'sc-high'
  if (p >= 50) return 'sc-mid'
  return 'sc-low'
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })
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

onMounted(loadData)
</script>