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
          <h1 class="page-title">Создать задание</h1>
          <p class="page-subtitle">Составьте задание с автоматической проверкой</p>
        </div>
      </div>

      <!-- Основная форма -->
      <div class="form-card">
        <div class="form-row">
          <div class="form-field">
            <label class="form-label">Ученик</label>
            <select v-model="form.student_id" class="form-select">
              <option :value="null" disabled>Выберите ученика</option>
              <option v-for="s in students" :key="s.id" :value="s.id">
                {{ s.full_name }}{{ s.subject ? ` — ${s.subject}` : '' }}
              </option>
            </select>
          </div>
          <div class="form-field">
            <label class="form-label">Тема</label>
            <input
              v-model="form.topic"
              class="form-input"
              type="text"
              placeholder="Например: Квадратные уравнения"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-field">
            <label class="form-label">Название задания</label>
            <input
              v-model="form.title"
              class="form-input"
              type="text"
              placeholder="Домашнее задание №1"
            />
          </div>
          <div class="form-field">
            <label class="form-label">Срок сдачи <span style="color:#94a3b8; font-weight: 400">(опционально)</span></label>
            <input
              v-model="form.due_date"
              class="form-input"
              type="datetime-local"
            />
          </div>
        </div>

        <div class="form-field" style="margin-bottom: 0">
          <label class="form-label">Описание <span style="color:#94a3b8; font-weight: 400">(опционально)</span></label>
          <textarea
            v-model="form.description"
            class="form-textarea"
            rows="2"
            placeholder="Инструкции для ученика..."
          ></textarea>
        </div>
      </div>

      <!-- Заголовок секции вопросов -->
      <div class="section-header">
        <h2>
          <QuestionMarkCircleIcon />
          Вопросы
          <span class="section-header-count">({{ questions.length }})</span>
        </h2>
        <div class="add-question-row">
          <button class="btn-add-question" @click="addQuestion('test')">
            <PlusIcon />Тест
          </button>
          <button class="btn-add-question" @click="addQuestion('number')">
            <PlusIcon />Числовой
          </button>
          <button class="btn-add-question" @click="addQuestion('text')">
            <PlusIcon />Текстовый
          </button>
        </div>
      </div>

      <!-- Список вопросов -->
      <div v-if="questions.length === 0" class="empty-questions">
        Добавьте хотя бы один вопрос — нажмите «+ Тест», «+ Числовой» или «+ Текстовый»
      </div>

      <div v-for="(q, idx) in questions" :key="idx" class="q-edit-card">
        <div class="q-edit-head">
          <span class="q-num">{{ idx + 1 }}</span>
          <span class="q-type-chip" :class="q.question_type">
            {{ typeLabel(q.question_type) }}
          </span>
          <div class="q-edit-points">
            <span>Баллы:</span>
            <input v-model.number="q.points" type="number" min="0.5" step="0.5" />
          </div>
          <button class="btn-icon danger" @click="questions.splice(idx, 1)" title="Удалить вопрос">
            <XMarkIcon />
          </button>
        </div>

        <div class="form-field">
          <label class="form-label">Текст вопроса</label>
          <textarea
            v-model="q.question_text"
            class="form-textarea"
            rows="2"
            placeholder="Введите вопрос..."
          ></textarea>
        </div>

        <!-- Тест -->
        <div v-if="q.question_type === 'test'" class="options-block">
          <label class="form-label">Варианты ответа <span style="color:#94a3b8; font-weight: 400">(отметьте правильный)</span></label>
          <div class="options-list">
            <div v-for="(opt, oi) in q.optionsList" :key="oi" class="option-row">
              <label class="option-radio">
                <input
                  type="radio"
                  :name="`correct-${idx}`"
                  :checked="q.correct_answer === String(oi)"
                  @change="q.correct_answer = String(oi)"
                />
                <span class="option-radio-circle"></span>
              </label>
              <input
                v-model="q.optionsList[oi]"
                class="option-input"
                type="text"
                :placeholder="`Вариант ${oi + 1}`"
              />
              <button
                v-if="q.optionsList.length > 2"
                class="btn-icon danger"
                @click="q.optionsList.splice(oi, 1)"
                title="Удалить вариант"
              >
                <XMarkIcon />
              </button>
            </div>
          </div>
          <button
            v-if="q.optionsList.length < 6"
            class="btn-add-option"
            @click="q.optionsList.push('')"
          >
            <PlusIcon />Добавить вариант
          </button>
        </div>

        <!-- Числовой -->
        <div v-if="q.question_type === 'number'" class="form-field" style="margin-bottom: 0">
          <label class="form-label">Правильный ответ (число)</label>
          <input
            v-model="q.correct_answer"
            class="form-input"
            type="text"
            placeholder="Например: 42"
          />
        </div>

        <!-- Текстовый -->
        <div v-if="q.question_type === 'text'" class="form-field" style="margin-bottom: 0">
          <label class="form-label">Правильный ответ (текст)</label>
          <input
            v-model="q.correct_answer"
            class="form-input"
            type="text"
            placeholder="Точный ответ для сравнения"
          />
        </div>
      </div>

      <div v-if="error" class="form-error">{{ error }}</div>

      <div class="form-footer">
        <router-link to="/homeworks" class="btn btn-secondary">Отмена</router-link>
        <button class="btn btn-primary" @click="saveHomework" :disabled="saving">
          {{ saving ? 'Сохранение...' : 'Создать задание' }}
        </button>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import api from '@/api/index.js'
import {
  ArrowLeftIcon,
  PlusIcon,
  XMarkIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const students = ref([])
const saving = ref(false)
const error = ref('')

const form = ref({
  student_id: null,
  title: '',
  topic: '',
  description: '',
  due_date: '',
})

const questions = ref([])

function addQuestion(type) {
  questions.value.push({
    question_type: type,
    question_text: '',
    correct_answer: '',
    points: 1,
    optionsList: type === 'test' ? ['', '', '', ''] : [],
  })
}

function typeLabel(t) {
  if (t === 'test') return 'Тест'
  if (t === 'number') return 'Число'
  if (t === 'text') return 'Текст'
  return t
}

async function saveHomework() {
  error.value = ''
  if (!form.value.student_id) { error.value = 'Выберите ученика'; return }
  if (!form.value.title) { error.value = 'Введите название'; return }
  if (!form.value.topic) { error.value = 'Введите тему'; return }
  if (questions.value.length === 0) { error.value = 'Добавьте хотя бы один вопрос'; return }

  for (let i = 0; i < questions.value.length; i++) {
    const q = questions.value[i]
    if (!q.question_text) { error.value = `Вопрос ${i + 1}: введите текст`; return }
    if (!q.correct_answer && q.question_type !== 'test') {
      error.value = `Вопрос ${i + 1}: укажите правильный ответ`; return
    }
    if (q.question_type === 'test' && q.correct_answer === '') {
      error.value = `Вопрос ${i + 1}: отметьте правильный вариант`; return
    }
  }

  saving.value = true
  try {
    const payload = {
      student_id: form.value.student_id,
      title: form.value.title,
      topic: form.value.topic,
      description: form.value.description || null,
      due_date: form.value.due_date || null,
      questions: questions.value.map(q => ({
        question_text: q.question_text,
        question_type: q.question_type,
        options: q.question_type === 'test' ? JSON.stringify(q.optionsList) : null,
        correct_answer: q.correct_answer,
        points: q.points,
      })),
    }
    await api.post('/homeworks/', payload)
    router.push('/homeworks')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка сохранения'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const res = await api.get('/students/')
    students.value = res.data
  } catch (e) {
    console.error(e)
  }
})
</script>