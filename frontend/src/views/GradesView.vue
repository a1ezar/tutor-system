<template>
  <AppLayout>
    <div class="page-wrap">
      <!-- Header -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Журнал</h1>
          <p class="page-subtitle">Оценки и успеваемость учеников</p>
        </div>
        <div class="page-actions">
          <button class="btn btn-primary" @click="openModal()">
            <PlusIcon />
            Добавить оценку
          </button>
        </div>
      </div>

      <!-- Фильтр -->
      <div class="filter-row">
        <select v-model="filterStudent" class="filter-select">
          <option value="">Все ученики</option>
          <option v-for="s in students" :key="s.id" :value="s.id">
            {{ s.full_name }}
          </option>
        </select>
      </div>

      <!-- States -->
      <div v-if="loading" class="loading-state">Загрузка...</div>

      <div v-else-if="filteredGrades.length === 0" class="empty-state">
        <div class="empty-state-icon">
          <ClipboardDocumentListIcon />
        </div>
        <div class="empty-state-title">
          {{ filterStudent ? 'У этого ученика пока нет оценок' : 'Оценок пока нет' }}
        </div>
        <div class="empty-state-text">
          Добавьте первую оценку, чтобы начать вести журнал успеваемости.
        </div>
        <button class="btn btn-primary" @click="openModal()">
          <PlusIcon />
          Добавить оценку
        </button>
      </div>

      <template v-else>
        <!-- Десктоп: таблица -->
        <div class="data-table show-desktop">
          <div class="data-table-head">
            <div>Ученик</div>
            <div>Тема</div>
            <div>Оценка</div>
            <div>Комментарий</div>
            <div>Дата</div>
            <div style="text-align: right">Действия</div>
          </div>
          <div
            v-for="grade in filteredGrades"
            :key="grade.id"
            class="data-table-row"
          >
            <div class="cell-student">
              <div class="cell-student-avatar">{{ initials(getStudentName(grade.student_id)) }}</div>
              <div class="cell-student-name">{{ getStudentName(grade.student_id) }}</div>
            </div>
            <div class="cell-topic">
              <span class="subject-chip" :class="subjectChipClass(grade.topic)">{{ grade.topic }}</span>
            </div>
            <div>
              <span class="grade-pill" :class="gradeClass(grade.value)">{{ grade.value }}</span>
            </div>
            <div class="cell-comment">{{ grade.comment || '—' }}</div>
            <div class="cell-date">{{ formatDate(grade.created_at) }}</div>
            <div class="cell-actions">
              <button class="btn-icon" title="Редактировать" @click="openModal(grade)">
                <PencilIcon />
              </button>
              <button class="btn-icon danger" title="Удалить" @click="deleteGrade(grade.id)">
                <TrashIcon />
              </button>
            </div>
          </div>
        </div>

        <!-- Мобильный: карточки -->
        <div class="data-cards show-mobile">
          <div v-for="grade in filteredGrades" :key="grade.id" class="data-card">
            <div class="data-card-head">
              <div class="data-card-student">
                <div class="cell-student-avatar">{{ initials(getStudentName(grade.student_id)) }}</div>
                <div class="cell-student-name">{{ getStudentName(grade.student_id) }}</div>
              </div>
              <span class="grade-pill" :class="gradeClass(grade.value)">{{ grade.value }}</span>
            </div>
            <div class="data-card-topic">
              <span class="subject-chip" :class="subjectChipClass(grade.topic)">{{ grade.topic }}</span>
            </div>
            <div v-if="grade.comment" class="data-card-comment">{{ grade.comment }}</div>
            <div class="data-card-foot">
              <span>{{ formatDate(grade.created_at) }}</span>
              <div class="data-card-actions">
                <button class="btn-icon" title="Редактировать" @click="openModal(grade)">
                  <PencilIcon />
                </button>
                <button class="btn-icon danger" title="Удалить" @click="deleteGrade(grade.id)">
                  <TrashIcon />
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Модалка -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-head">
          <h2 class="modal-title">{{ editingGrade ? 'Редактировать оценку' : 'Добавить оценку' }}</h2>
          <button class="modal-close" @click="closeModal" title="Закрыть">
            <XMarkIcon />
          </button>
        </div>

        <form @submit.prevent="saveGrade">
          <div class="modal-body">
            <div class="form-field">
              <label class="form-label">Ученик</label>
              <select v-model="form.student_id" class="form-select" required>
                <option value="" disabled>Выберите ученика</option>
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
                required
              />
            </div>
            <div class="form-field">
              <label class="form-label">Оценка (1–10)</label>
              <input
                v-model.number="form.value"
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
                v-model="form.comment"
                class="form-textarea"
                placeholder="Что получилось, что нужно подтянуть..."
                rows="3"
              ></textarea>
            </div>
          </div>

          <div class="modal-foot">
            <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
            <button type="submit" class="btn btn-primary">
              {{ editingGrade ? 'Сохранить' : 'Добавить' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import api from '@/api/index.js'
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  XMarkIcon,
  ClipboardDocumentListIcon,
} from '@heroicons/vue/24/outline'

const grades = ref([])
const students = ref([])
const loading = ref(true)
const showModal = ref(false)
const editingGrade = ref(null)
const filterStudent = ref('')

const form = ref({
  student_id: '',
  topic: '',
  value: 5,
  comment: '',
})

const filteredGrades = computed(() => {
  if (!filterStudent.value) return grades.value
  return grades.value.filter(g => g.student_id === filterStudent.value)
})

async function loadData() {
  loading.value = true
  try {
    const [gradesRes, studentsRes] = await Promise.all([
      api.get('/grades/'),
      api.get('/students/'),
    ])
    grades.value = gradesRes.data.sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    )
    students.value = studentsRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function getStudentName(id) {
  return students.value.find(s => s.id === id)?.full_name || 'Неизвестный'
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

function formatDate(dt) {
  return new Date(dt).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' })
}

function gradeClass(value) {
  if (value >= 8) return 'high'
  if (value >= 6) return 'mid'
  return 'low'
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

function openModal(grade = null) {
  editingGrade.value = grade
  if (grade) {
    form.value = { ...grade }
  } else {
    form.value = { student_id: '', topic: '', value: 5, comment: '' }
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingGrade.value = null
}

async function saveGrade() {
  try {
    if (editingGrade.value) {
      await api.put(`/grades/${editingGrade.value.id}`, form.value)
    } else {
      await api.post('/grades/', form.value)
    }
    await loadData()
    closeModal()
  } catch (e) {
    console.error(e)
  }
}

async function deleteGrade(id) {
  if (!confirm('Удалить оценку?')) return
  try {
    await api.delete(`/grades/${id}`)
    await loadData()
  } catch (e) {
    console.error(e)
  }
}

onMounted(loadData)
</script>