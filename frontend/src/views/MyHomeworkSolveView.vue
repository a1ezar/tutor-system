<template>
  <AppLayout>
    <div class="solve">
      <div v-if="loading" class="loading">Загрузка задания...</div>

      <!-- Результат после отправки -->
      <div v-else-if="result" class="result-section">
        <div class="result-card">
          <div class="result-icon">{{ result.percentage >= 80 ? '🎉' : result.percentage >= 50 ? '👍' : '📚' }}</div>
          <div class="result-title">
            {{ result.percentage >= 80 ? 'Отлично!' : result.percentage >= 50 ? 'Неплохо!' : 'Нужно повторить' }}
          </div>
          <div class="result-score" :class="scoreClass(result.percentage)">
            {{ result.percentage }}%
          </div>
          <div class="result-details">
            {{ result.score }} / {{ result.max_score }} баллов · Оценка: {{ result.grade_10 }}
          </div>

          <div class="result-answers">
            <div v-for="(a, i) in result.answers" :key="i" :class="['ra-item', a.is_correct ? 'ra-ok' : 'ra-fail']">
              <span class="ra-num">{{ i + 1 }}</span>
              <span class="ra-answer">{{ a.student_answer || '—' }}</span>
              <span class="ra-mark">{{ a.is_correct ? '✓' : '✗' }}</span>
              <span class="ra-pts">{{ a.points_earned }} б.</span>
            </div>
          </div>

          <div class="result-actions">
            <router-link to="/my-homeworks" class="btn-back">← К заданиям</router-link>
          </div>
        </div>
      </div>

      <!-- Выполнение задания -->
      <div v-else-if="homework">
        <div class="page-header">
          <div>
            <h1>{{ homework.title }}</h1>
            <p class="subtitle">{{ homework.topic }}</p>
          </div>
          <div class="q-counter">{{ answeredCount }} / {{ homework.questions.length }}</div>
        </div>

        <div v-if="homework.description" class="description">{{ homework.description }}</div>

        <div v-for="(q, idx) in homework.questions" :key="q.id" class="q-card">
          <div class="q-header">
            <span class="q-num">{{ idx + 1 }}</span>
            <span class="q-type" :class="`type-${q.question_type}`">
              {{ q.question_type === 'test' ? 'Тест' : q.question_type === 'number' ? 'Число' : 'Текст' }}
            </span>
            <span class="q-pts">{{ q.points }} б.</span>
          </div>
          <div class="q-text">{{ q.question_text }}</div>

          <!-- Тест -->
          <div v-if="q.question_type === 'test'" class="q-options">
            <label v-for="(opt, oi) in parseOptions(q.options)" :key="oi"
              :class="['q-option', { selected: answers[q.id] === String(oi) }]"
            >
              <input type="radio" :name="`q-${q.id}`" :value="String(oi)" v-model="answers[q.id]" />
              <span>{{ opt }}</span>
            </label>
          </div>

          <!-- Число -->
          <div v-if="q.question_type === 'number'" class="q-input-wrap">
            <input v-model="answers[q.id]" type="number" step="any" placeholder="Введите число" class="q-input" />
          </div>

          <!-- Текст -->
          <div v-if="q.question_type === 'text'" class="q-input-wrap">
            <input v-model="answers[q.id]" type="text" placeholder="Введите ответ" class="q-input" />
          </div>
        </div>

        <div v-if="error" class="form-error">{{ error }}</div>

        <div class="form-actions">
          <button class="btn-submit" @click="submitHomework" :disabled="submitting">
            {{ submitting ? 'Отправка...' : 'Отправить ответы' }}
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import api from '@/api/index.js'

const route = useRoute()
const loading = ref(true)
const homework = ref(null)
const answers = ref({})
const result = ref(null)
const submitting = ref(false)
const error = ref('')

const answeredCount = computed(() => {
  return Object.values(answers.value).filter(v => v !== '' && v !== null && v !== undefined).length
})

function parseOptions(optStr) {
  try { return JSON.parse(optStr) } catch { return [] }
}

async function submitHomework() {
  error.value = ''
  const answersList = homework.value.questions.map(q => ({
    question_id: q.id,
    student_answer: answers.value[q.id] || ''
  }))

  const unanswered = answersList.filter(a => !a.student_answer).length
  if (unanswered > 0 && !confirm(`Вы не ответили на ${unanswered} вопрос(ов). Отправить?`)) return

  submitting.value = true
  try {
    const res = await api.post(`/homeworks/my/${route.params.id}/submit`, { answers: answersList })
    result.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка отправки'
  } finally { submitting.value = false }
}

function scoreClass(p) { if (p >= 80) return 'sc-high'; if (p >= 50) return 'sc-mid'; return 'sc-low' }

onMounted(async () => {
  try {
    const res = await api.get(`/homeworks/my/${route.params.id}`)
    homework.value = res.data
    // Инициализируем ответы
    for (const q of res.data.questions) { answers.value[q.id] = '' }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
})
</script>

<style scoped>
h1 { font-size: 28px; font-weight: 700; color: #1e1b4b; margin-bottom: 6px; }
.subtitle { color: #6b7280; font-size: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.loading { text-align: center; padding: 60px; color: #6b7280; background: white; border-radius: 16px; }
.q-counter { font-size: 16px; font-weight: 700; color: #4f46e5; background: #eef2ff; padding: 6px 16px; border-radius: 20px; }
.description { background: #f9fafb; padding: 14px 18px; border-radius: 10px; color: #374151; font-size: 14px; margin-bottom: 20px; line-height: 1.5; }

.q-card { background: white; border-radius: 16px; padding: 24px; margin-bottom: 14px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.q-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.q-num { width: 30px; height: 30px; background: #4f46e5; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; }
.q-type { padding: 3px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.type-test { background: #dbeafe; color: #2563eb; } .type-number { background: #d1fae5; color: #059669; } .type-text { background: #fef3c7; color: #d97706; }
.q-pts { margin-left: auto; font-size: 13px; color: #6b7280; }
.q-text { font-size: 16px; color: #1e1b4b; margin-bottom: 16px; line-height: 1.5; }

.q-options { display: flex; flex-direction: column; gap: 8px; }
.q-option { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border: 2px solid #e5e7eb; border-radius: 10px; cursor: pointer; transition: all 0.2s; font-size: 15px; color: #374151; }
.q-option:hover { border-color: #a5b4fc; }
.q-option.selected { border-color: #4f46e5; background: #eef2ff; }
.q-option input { display: none; }

.q-input-wrap { max-width: 300px; }
.q-input { width: 100%; padding: 12px 16px; border: 2px solid #e5e7eb; border-radius: 10px; font-size: 15px; outline: none; box-sizing: border-box; }
.q-input:focus { border-color: #4f46e5; box-shadow: 0 0 0 3px rgba(79,70,229,0.1); }

.form-error { color: #dc2626; background: #fee2e2; padding: 10px 16px; border-radius: 8px; margin: 12px 0; font-size: 14px; }
.form-actions { margin-top: 20px; display: flex; justify-content: center; }
.btn-submit { padding: 14px 48px; background: linear-gradient(135deg,#4f46e5,#7c3aed); color: white; border: none; border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer; transition: all 0.2s; }
.btn-submit:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(79,70,229,0.4); }
.btn-submit:disabled { opacity: 0.6; }

/* Результат */
.result-card { background: white; border-radius: 20px; padding: 40px; text-align: center; box-shadow: 0 4px 24px rgba(0,0,0,0.08); max-width: 600px; margin: 0 auto; }
.result-icon { font-size: 56px; margin-bottom: 12px; }
.result-title { font-size: 24px; font-weight: 800; color: #1e1b4b; margin-bottom: 8px; }
.result-score { font-size: 48px; font-weight: 800; margin-bottom: 8px; }
.sc-high { color: #059669; } .sc-mid { color: #d97706; } .sc-low { color: #dc2626; }
.result-details { font-size: 16px; color: #6b7280; margin-bottom: 24px; }

.result-answers { text-align: left; margin-bottom: 24px; }
.ra-item { display: flex; align-items: center; gap: 12px; padding: 8px 12px; border-radius: 8px; margin-bottom: 4px; font-size: 14px; }
.ra-ok { background: #f0fdf4; }
.ra-fail { background: #fef2f2; }
.ra-num { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; background: #e5e7eb; color: #374151; }
.ra-answer { flex: 1; color: #374151; }
.ra-mark { font-size: 16px; font-weight: 700; }
.ra-ok .ra-mark { color: #059669; } .ra-fail .ra-mark { color: #dc2626; }
.ra-pts { font-size: 12px; color: #6b7280; }

.result-actions { margin-top: 16px; }
.btn-back { color: #4f46e5; text-decoration: none; font-weight: 600; font-size: 15px; }
</style>
