<template>
  <AppLayout>
    <div class="page-wrap">
      <!-- Header -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Мои задания</h1>
          <p class="page-subtitle">Выполняйте задания и отслеживайте результаты</p>
        </div>
      </div>

      <!-- States -->
      <div v-if="loading" class="loading-state">Загрузка...</div>

      <div v-else-if="homeworks.length === 0" class="empty-state">
        <div class="empty-state-icon">
          <DocumentTextIcon />
        </div>
        <div class="empty-state-title">Заданий пока нет</div>
        <div class="empty-state-text">
          Когда репетитор пришлёт вам задание, оно появится здесь.
        </div>
      </div>

      <!-- Список заданий -->
      <div v-else class="hw-list">
        <div
          v-for="hw in homeworks"
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
              <span :class="['status-pill', `status-${hw.status}`]">
                {{ statusLabel(hw.status) }}
              </span>
            </div>
          </div>
          <div class="hw-card-bottom">
            <span v-if="hw.best_score !== null">
              Лучший результат: <strong class="hw-score-value" :class="scoreClass(hw.best_score)">{{ hw.best_score }} / 10</strong>
            </span>
            <span v-else class="hw-not-started">Ещё не выполнялось</span>
            <span v-if="hw.due_date" class="hw-due">Срок: {{ formatDate(hw.due_date) }}</span>
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
import { DocumentTextIcon } from '@heroicons/vue/24/outline'

const loading = ref(true)
const homeworks = ref([])

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}

function pluralize(n, forms) {
  const a = Math.abs(n) % 100
  const b = a % 10
  if (a > 10 && a < 20) return forms[2]
  if (b > 1 && b < 5) return forms[1]
  if (b === 1) return forms[0]
  return forms[2]
}

function statusLabel(s) {
  if (s === 'new') return 'Новое'
  if (s === 'completed') return 'Выполнено'
  if (s === 'in_progress') return 'В процессе'
  return s
}

function scoreClass(s) {
  if (s >= 8) return 'score-high'
  if (s >= 5) return 'score-mid'
  return 'score-low'
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