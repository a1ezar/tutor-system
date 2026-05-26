<template>
  <AppLayout>
    <div class="page-wrap">
      <!-- Header -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Ученики</h1>
          <p class="page-subtitle">Управление базой учеников</p>
        </div>
        <div class="page-actions">
          <button class="btn btn-primary" @click="openModal()">
            <PlusIcon />
            Добавить ученика
          </button>
        </div>
      </div>

      <!-- Search -->
      <div class="page-search">
        <MagnifyingGlassIcon class="page-search-icon" />
        <input
          v-model="search"
          class="page-search-input"
          type="text"
          placeholder="Поиск по имени или предмету..."
        />
      </div>

      <!-- States -->
      <div v-if="loading" class="loading-state">Загрузка...</div>

      <div v-else-if="filteredStudents.length === 0" class="empty-state">
        <div class="empty-state-icon">
          <UsersIcon />
        </div>
        <div class="empty-state-title">
          {{ search ? 'Ничего не найдено' : 'Учеников пока нет' }}
        </div>
        <div class="empty-state-text">
          {{ search
            ? 'Попробуйте изменить запрос или сбросить поиск.'
            : 'Добавьте первого ученика, чтобы начать вести занятия и оценки.' }}
        </div>
        <button v-if="!search" class="btn btn-primary" @click="openModal()">
          <PlusIcon />
          Добавить ученика
        </button>
      </div>

      <!-- Cards grid -->
      <div v-else class="cards-grid">
        <div
          v-for="student in filteredStudents"
          :key="student.id"
          class="student-card"
          @click="router.push(`/students/${student.id}`)"
        >
          <div class="student-card-avatar">{{ initials(student.full_name) }}</div>
          <div class="student-card-info">
            <div class="student-card-name">{{ student.full_name }}</div>
            <div class="student-card-subject">{{ student.subject || 'Предмет не указан' }}</div>
            <div v-if="student.phone" class="student-card-phone">{{ student.phone }}</div>
          </div>
          <div class="student-card-actions">
            <button class="btn-icon" title="Редактировать" @click.stop="openModal(student)">
              <PencilIcon />
            </button>
            <button class="btn-icon danger" title="Удалить" @click.stop="deleteStudent(student.id)">
              <TrashIcon />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-head">
          <h2 class="modal-title">{{ editingStudent ? 'Редактировать ученика' : 'Добавить ученика' }}</h2>
          <button class="modal-close" @click="closeModal" title="Закрыть">
            <XMarkIcon />
          </button>
        </div>

        <form @submit.prevent="saveStudent">
          <div class="modal-body">
            <div class="form-field">
              <label class="form-label">Полное имя</label>
              <input
                v-model="form.full_name"
                class="form-input"
                type="text"
                placeholder="Иванов Иван Иванович"
                required
              />
            </div>
            <div class="form-field">
              <label class="form-label">Предмет</label>
              <input
                v-model="form.subject"
                class="form-input"
                type="text"
                placeholder="Математика"
                required
              />
            </div>
            <div class="form-field">
              <label class="form-label">Телефон</label>
              <input
                v-model="form.phone"
                class="form-input"
                type="text"
                placeholder="+7 999 123 45 67"
              />
            </div>
            <div class="form-field">
              <label class="form-label">Заметки</label>
              <textarea
                v-model="form.notes"
                class="form-textarea"
                placeholder="Дополнительная информация..."
                rows="3"
              ></textarea>
            </div>
          </div>

          <div class="modal-foot">
            <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
            <button type="submit" class="btn btn-primary">
              {{ editingStudent ? 'Сохранить' : 'Добавить' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import api from '@/api/index.js'
import {
  MagnifyingGlassIcon,
  UsersIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const students = ref([])
const loading = ref(true)
const search = ref('')
const showModal = ref(false)
const editingStudent = ref(null)

const form = ref({
  full_name: '',
  subject: '',
  phone: '',
  notes: ''
})

const filteredStudents = computed(() => {
  if (!search.value) return students.value
  const q = search.value.toLowerCase()
  return students.value.filter(s =>
    s.full_name.toLowerCase().includes(q) ||
    (s.subject || '').toLowerCase().includes(q)
  )
})

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

async function loadStudents() {
  loading.value = true
  try {
    const response = await api.get('/students/')
    students.value = response.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function openModal(student = null) {
  editingStudent.value = student
  if (student) {
    form.value = { ...student }
  } else {
    form.value = { full_name: '', subject: '', phone: '', notes: '' }
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingStudent.value = null
}

async function saveStudent() {
  try {
    if (editingStudent.value) {
      await api.put(`/students/${editingStudent.value.id}`, form.value)
    } else {
      await api.post('/students/', form.value)
    }
    await loadStudents()
    closeModal()
  } catch (e) {
    console.error(e)
  }
}

async function deleteStudent(id) {
  if (!confirm('Удалить ученика? Все его занятия и оценки также будут удалены.')) return
  try {
    await api.delete(`/students/${id}`)
    await loadStudents()
  } catch (e) {
    console.error(e)
  }
}

onMounted(loadStudents)
</script>