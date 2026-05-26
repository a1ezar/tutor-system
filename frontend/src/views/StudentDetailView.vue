<template>
  <AppLayout>
    <div class="page-wrap">
      <!-- Назад -->
      <router-link to="/students" class="back-link">
        <ArrowLeftIcon />
        К списку учеников
      </router-link>

      <div v-if="loading" class="loading-state">Загрузка...</div>

      <template v-else-if="student">
        <!-- Hero -->
        <div class="student-hero">
          <div class="hero-avatar">{{ initials(student.full_name) }}</div>

          <div class="hero-info">
            <h1 class="hero-name">{{ student.full_name }}</h1>
            <span v-if="student.subject" class="subject-chip" :class="subjectChipClass(student.subject)">
              {{ student.subject }}
            </span>
            <div class="hero-meta">
              <div v-if="student.phone" class="hero-meta-row">
                <PhoneIcon />
                {{ student.phone }}
              </div>
            </div>
            <div v-if="student.notes" class="hero-notes">
              {{ student.notes }}
            </div>
          </div>

          <div class="hero-stats">
            <div class="hero-stat">
              <div class="hero-stat-value">{{ grades.length }}</div>
              <div class="hero-stat-label">Оценок</div>
            </div>
            <div class="hero-stat">
              <div class="hero-stat-value accent">{{ avgGrade }}</div>
              <div class="hero-stat-label">Средний балл</div>
            </div>
            <div class="hero-stat">
              <div class="hero-stat-value">{{ lessons.length }}</div>
              <div class="hero-stat-label">Занятий</div>
            </div>
          </div>
        </div>

        <!-- Действия -->
        <div class="page-actions" style="margin-bottom: 24px; justify-content: flex-end">
          <button class="btn btn-secondary" @click="openEditModal">
            <PencilIcon />
            Редактировать
          </button>
        </div>

        <!-- Оценки -->
        <div class="detail-section">
          <div class="detail-section-head">
            <h2 class="detail-section-title">
              <ClipboardDocumentListIcon />
              История оценок
              <span class="detail-section-count">({{ grades.length }})</span>
            </h2>
            <button class="btn btn-primary" @click="openGradeModal">
              <PlusIcon />
              Добавить
            </button>
          </div>

          <div v-if="grades.length === 0" class="detail-empty">
            Оценок пока нет
          </div>

          <div v-else class="grade-list">
            <div v-for="grade in grades" :key="grade.id" class="grade-row">
              <div class="grade-row-main">
                <div class="grade-row-topic">{{ grade.topic }}</div>
                <div v-if="grade.comment" class="grade-row-comment">{{ grade.comment }}</div>
              </div>
              <div class="grade-row-date">{{ formatDate(grade.created_at) }}</div>
              <span class="grade-pill" :class="gradeClass(grade.value)">{{ grade.value }}</span>
            </div>
          </div>
        </div>

        <!-- Занятия -->
        <div class="detail-section">
          <div class="detail-section-head">
            <h2 class="detail-section-title">
              <CalendarIcon />
              Занятия
              <span class="detail-section-count">({{ lessons.length }})</span>
            </h2>
            <button class="btn btn-primary" @click="openLessonModal">
              <PlusIcon />
              Добавить
            </button>
          </div>

          <div v-if="lessons.length === 0" class="detail-empty">
            Занятий пока нет
          </div>

          <div v-else class="detail-lesson-list">
            <div v-for="lesson in lessons" :key="lesson.id" class="detail-lesson-row">
              <div class="lesson-date">
                <div class="lesson-date-day">{{ formatDay(lesson.scheduled_at) }}</div>
                <div class="lesson-date-mon">{{ formatMonth(lesson.scheduled_at) }}</div>
              </div>
              <div class="detail-lesson-info">
                <div class="detail-lesson-topic">{{ lesson.topic || 'Тема не указана' }}</div>
                <div class="detail-lesson-time">
                  {{ formatTime(lesson.scheduled_at) }} · {{ lesson.duration_minutes }} мин
                </div>
              </div>
              <span class="lesson-badge" :class="lesson.completed ? 'done' : 'pending'">
                <CheckIcon v-if="lesson.completed" />
                {{ lesson.completed ? 'Проведено' : 'Запланировано' }}
              </span>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Модалка редактирования ученика -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal">
        <div class="modal-head">
          <h2 class="modal-title">Редактировать ученика</h2>
          <button class="modal-close" @click="showEditModal = false" title="Закрыть">
            <XMarkIcon />
          </button>
        </div>
        <form @submit.prevent="saveStudent">
          <div class="modal-body">
            <div class="form-field">
              <label class="form-label">Полное имя</label>
              <input v-model="editForm.full_name" class="form-input" type="text" required />
            </div>
            <div class="form-field">
              <label class="form-label">Предмет</label>
              <input v-model="editForm.subject" class="form-input" type="text" required />
            </div>
            <div class="form-field">
              <label class="form-label">Телефон</label>
              <input v-model="editForm.phone" class="form-input" type="text" placeholder="+7 999 123 45 67" />
            </div>
            <div class="form-field">
              <label class="form-label">Заметки</label>
              <textarea v-model="editForm.notes" class="form-textarea" rows="3"></textarea>
            </div>
          </div>
          <div class="modal-foot">
            <button type="button" class="btn btn-secondary" @click="showEditModal = false">Отмена</button>
            <button type="submit" class="btn btn-primary">Сохранить</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Модалка оценки -->
    <div v-if="showGradeModal" class="modal-overlay" @click.self="showGradeModal = false">
      <div class="modal">
        <div class="modal-head">
          <h2 class="modal-title">Добавить оценку</h2>
          <button class="modal-close" @click="showGradeModal = false" title="Закрыть">
            <XMarkIcon />
          </button>
        </div>
        <form @submit.prevent="saveGrade">
          <div class="modal-body">
            <div class="form-field">
              <label class="form-label">Тема</label>
              <input
                v-model="gradeForm.topic"
                class="form-input"
                type="text"
                placeholder="Например: Производная сложной функции"
                required
              />
            </div>
            <div class="form-field">
              <label class="form-label">Оценка (1–10)</label>
              <input
                v-model.number="gradeForm.value"
                class="form-input"
                type="number"
                min="1"
                max="10"
                step="0.5"
                required
              />
            </div>
            <div class="form-field">
              <label class="form-label">Комментарий</label>
              <textarea
                v-model="gradeForm.comment"
                class="form-textarea"
                rows="3"
                placeholder="Что получилось, над чем поработать..."
              ></textarea>
            </div>
          </div>
          <div class="modal-foot">
            <button type="button" class="btn btn-secondary" @click="showGradeModal = false">Отмена</button>
            <button type="submit" class="btn btn-primary">Добавить</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Модалка занятия -->
    <div v-if="showLessonModal" class="modal-overlay" @click.self="showLessonModal = false">
      <div class="modal">
        <div class="modal-head">
          <h2 class="modal-title">Добавить занятие</h2>
          <button class="modal-close" @click="showLessonModal = false" title="Закрыть">
            <XMarkIcon />
          </button>
        </div>
        <form @submit.prevent="saveLesson">
          <div class="modal-body">
            <div class="form-row">
              <div class="form-field">
                <label class="form-label">Дата и время</label>
                <input v-model="lessonForm.scheduled_at" class="form-input" type="datetime-local" required />
              </div>
              <div class="form-field">
                <label class="form-label">Длительность (мин)</label>
                <input v-model.number="lessonForm.duration_minutes" class="form-input" type="number" min="15" max="240" step="15" />
              </div>
            </div>
            <div class="form-field">
              <label class="form-label">Тема</label>
              <input v-model="lessonForm.topic" class="form-input" type="text" />
            </div>
            <div class="form-field">
              <label class="form-label">Заметки</label>
              <textarea v-model="lessonForm.notes" class="form-textarea" rows="2"></textarea>
            </div>
          </div>
          <div class="modal-foot">
            <button type="button" class="btn btn-secondary" @click="showLessonModal = false">Отмена</button>
            <button type="submit" class="btn btn-primary">Добавить</button>
          </div>
        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import api from '@/api/index.js'
import {
  ArrowLeftIcon,
  PencilIcon,
  PlusIcon,
  XMarkIcon,
  ClipboardDocumentListIcon,
  CalendarIcon,
  PhoneIcon,
} from '@heroicons/vue/24/outline'
import { CheckIcon } from '@heroicons/vue/24/solid'

const route = useRoute()
const studentId = route.params.id

const student = ref(null)
const grades = ref([])
const lessons = ref([])
const loading = ref(true)

const showEditModal = ref(false)
const showGradeModal = ref(false)
const showLessonModal = ref(false)

const editForm = ref({})
const gradeForm = ref({ topic: '', value: 5, comment: '' })
const lessonForm = ref({ scheduled_at: '', duration_minutes: 60, topic: '', notes: '' })

const avgGrade = computed(() => {
  if (!grades.value.length) return '—'
  const avg = grades.value.reduce((s, g) => s + g.value, 0) / grades.value.length
  return avg.toFixed(1)
})

async function loadData() {
  try {
    const [studentRes, gradesRes, lessonsRes] = await Promise.all([
      api.get(`/students/${studentId}`),
      api.get(`/grades/student/${studentId}`),
      api.get(`/lessons/student/${studentId}`),
    ])
    student.value = studentRes.data
    grades.value = gradesRes.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    lessons.value = lessonsRes.data.sort((a, b) => new Date(b.scheduled_at) - new Date(a.scheduled_at))
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function initials(fullName) {
  if (!fullName) return '?'
  return fullName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(s => s[0])
    .join('')
    .toUpperCase()
}

function openEditModal() {
  editForm.value = { ...student.value }
  showEditModal.value = true
}

function openGradeModal() {
  gradeForm.value = { topic: '', value: 5, comment: '' }
  showGradeModal.value = true
}

function openLessonModal() {
  lessonForm.value = { scheduled_at: '', duration_minutes: 60, topic: '', notes: '' }
  showLessonModal.value = true
}

async function saveStudent() {
  await api.put(`/students/${studentId}`, editForm.value)
  await loadData()
  showEditModal.value = false
}

async function saveGrade() {
  await api.post('/grades/', { ...gradeForm.value, student_id: parseInt(studentId) })
  await loadData()
  showGradeModal.value = false
}

async function saveLesson() {
  await api.post('/lessons/', { ...lessonForm.value, student_id: parseInt(studentId) })
  await loadData()
  showLessonModal.value = false
}

function formatDate(dt) {
  return new Date(dt).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}
function formatDay(dt) { return new Date(dt).getDate() }
function formatMonth(dt) {
  return new Date(dt).toLocaleString('ru', { month: 'short' }).replace('.', '')
}
function formatTime(dt) {
  return new Date(dt).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
}

function gradeClass(value) {
  if (value >= 8) return 'high'
  if (value >= 6) return 'mid'
  return 'low'
}

function subjectChipClass(subject) {
  const s = (subject || '').toLowerCase()
  if (/алгеб|матем/.test(s))      return 'sky'
  if (/геометр/.test(s))          return 'violet'
  if (/егэ|огэ|подготов/.test(s)) return 'amber'
  if (/физик/.test(s))            return 'indigo'
  if (/хим/.test(s))              return 'emerald'
  if (/русск|литер/.test(s))      return 'rose'
  if (/англ|нем|франц/.test(s))   return 'fuchsia'
  return 'slate'
}

onMounted(loadData)
</script>