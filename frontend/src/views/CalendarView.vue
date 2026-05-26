<template>
  <AppLayout>
    <div class="page-wrap">
      <!-- Header -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Расписание</h1>
          <p class="page-subtitle">Календарь занятий с учениками</p>
        </div>
        <div class="page-actions">
          <button class="btn btn-primary" @click="openModal()">
            <PlusIcon />
            Добавить занятие
          </button>
        </div>
      </div>

      <!-- Календарь -->
      <div class="calendar-card">
        <FullCalendar :options="calendarOptions" />
      </div>
    </div>

    <!-- Модалка занятия -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-head">
          <h2 class="modal-title">{{ editingLesson ? 'Редактировать занятие' : 'Новое занятие' }}</h2>
          <button class="modal-close" @click="closeModal" title="Закрыть">
            <XMarkIcon />
          </button>
        </div>

        <form @submit.prevent="saveLesson">
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

            <div class="form-row">
              <div class="form-field">
                <label class="form-label">Дата и время</label>
                <input v-model="form.scheduled_at" class="form-input" type="datetime-local" required />
              </div>
              <div class="form-field">
                <label class="form-label">Длительность (мин)</label>
                <input
                  v-model.number="form.duration_minutes"
                  class="form-input"
                  type="number"
                  min="15"
                  max="240"
                  step="15"
                />
              </div>
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

            <div class="form-field">
              <label class="form-label">
                Заметки <span style="color:#94a3b8; font-weight: 400">(опционально)</span>
              </label>
              <textarea
                v-model="form.notes"
                class="form-textarea"
                rows="2"
                placeholder="Что обсудить, что подготовить..."
              ></textarea>
            </div>

            <!-- Тип занятия (только при создании) -->
            <div v-if="!editingLesson" class="form-field">
              <label class="form-label">Тип занятия</label>
              <div class="repeat-toggle">
                <button
                  type="button"
                  class="repeat-btn"
                  :class="{ active: !form.repeat }"
                  @click="form.repeat = false"
                >
                  <CalendarIcon />
                  Одиночное
                </button>
                <button
                  type="button"
                  class="repeat-btn"
                  :class="{ active: form.repeat }"
                  @click="form.repeat = true"
                >
                  <ArrowPathIcon />
                  Еженедельное
                </button>
              </div>
              <div v-if="form.repeat" class="repeat-hint">
                Будет создано занятие каждую неделю на 3 месяца вперёд (всего ~13 занятий)
              </div>
            </div>

            <!-- Чекбокс «проведено» (только при редактировании) -->
            <label v-if="editingLesson" class="checkbox-field">
              <input
                type="checkbox"
                v-model="form.completed"
                :true-value="1"
                :false-value="0"
              />
              <span>Занятие проведено</span>
            </label>
          </div>

          <div class="modal-foot" :class="{ 'with-danger': editingLesson }">
            <div v-if="editingLesson" class="left-actions">
              <button type="button" class="btn btn-danger" @click="deleteLesson">
                <TrashIcon />
                Удалить
              </button>
            </div>
            <div class="right-actions">
              <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
              <button type="submit" class="btn btn-primary">
                {{ editingLesson ? 'Сохранить' : 'Добавить' }}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>

    <!-- Диалог удаления серии -->
    <div v-if="showDeleteDialog" class="modal-overlay" @click.self="showDeleteDialog = false">
      <div class="modal">
        <div class="modal-head">
          <h2 class="modal-title">Удалить повторяющееся занятие</h2>
          <button class="modal-close" @click="showDeleteDialog = false" title="Закрыть">
            <XMarkIcon />
          </button>
        </div>

        <div class="modal-body">
          <p style="color: #64748b; font-size: 14px; margin-bottom: 16px;">
            Это занятие — часть серии. Что вы хотите удалить?
          </p>

          <div class="delete-options">
            <label class="delete-option">
              <input type="radio" v-model="deleteChoice" value="single" />
              <span>Только это занятие</span>
            </label>
            <label class="delete-option">
              <input type="radio" v-model="deleteChoice" value="following" />
              <span>Это и все последующие</span>
            </label>
            <label class="delete-option">
              <input type="radio" v-model="deleteChoice" value="all" />
              <span>Все занятия серии</span>
            </label>
          </div>
        </div>

        <div class="modal-foot">
          <button class="btn btn-secondary" @click="showDeleteDialog = false">Отмена</button>
          <button class="btn btn-danger" @click="confirmDelete">
            <TrashIcon />
            Удалить
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import ruLocale from '@fullcalendar/core/locales/ru'
import AppLayout from '@/components/AppLayout.vue'
import api from '@/api/index.js'
import {
  PlusIcon,
  XMarkIcon,
  TrashIcon,
  CalendarIcon,
  ArrowPathIcon,
} from '@heroicons/vue/24/outline'

const lessons = ref([])
const students = ref([])
const showModal = ref(false)
const showDeleteDialog = ref(false)
const deleteChoice = ref('single')
const editingLesson = ref(null)

const form = ref({
  student_id: '',
  scheduled_at: '',
  duration_minutes: 60,
  topic: '',
  notes: '',
  completed: 0,
  repeat: false,
})

function getStudentName(id) {
  return students.value.find(s => s.id === id)?.full_name || 'Неизвестный'
}

// Цвета для разных учеников — используем нашу палитру (indigo, violet, sky, amber, emerald, rose, fuchsia)
function getStudentColor(id) {
  const colors = [
    '#4f46e5', // indigo
    '#7c3aed', // violet
    '#0284c7', // sky
    '#d97706', // amber
    '#059669', // emerald
    '#e11d48', // rose
    '#c026d3', // fuchsia
    '#475569', // slate
  ]
  return colors[id % colors.length]
}

const calendarEvents = computed(() =>
  lessons.value.map(lesson => ({
    id: lesson.id,
    title: getStudentName(lesson.student_id) + (lesson.topic ? ` — ${lesson.topic}` : ''),
    start: lesson.scheduled_at,
    end: new Date(new Date(lesson.scheduled_at).getTime() + lesson.duration_minutes * 60000).toISOString(),
    backgroundColor: lesson.completed ? '#94a3b8' : getStudentColor(lesson.student_id),
    borderColor: lesson.completed ? '#94a3b8' : getStudentColor(lesson.student_id),
    extendedProps: { lesson },
  }))
)

const calendarOptions = computed(() => ({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: 'timeGridWeek',
  locale: ruLocale,
  timeZone: 'local',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay',
  },
  buttonText: {
    today: 'Сегодня',
    month: 'Месяц',
    week: 'Неделя',
    day: 'День',
  },
  events: calendarEvents.value,
  editable: true,
  selectable: true,
  selectMirror: true,
  dayMaxEvents: true,
  allDaySlot: false,
  slotMinTime: '07:00:00',
  slotMaxTime: '22:00:00',
  height: 'auto',
  nowIndicator: true,
  select: handleDateSelect,
  eventClick: handleEventClick,
  eventDrop: handleEventDrop,
  eventResize: handleEventResize,
}))

function handleDateSelect(info) {
  const localDate = new Date(info.start)
  const offset = localDate.getTimezoneOffset()
  const corrected = new Date(localDate.getTime() - offset * 60000)
  const scheduled_at = corrected.toISOString().slice(0, 16)

  form.value = {
    student_id: '',
    scheduled_at,
    duration_minutes: 60,
    topic: '',
    notes: '',
    completed: 0,
    repeat: false,
  }
  editingLesson.value = null
  showModal.value = true
}

function handleEventClick(info) {
  const lesson = info.event.extendedProps.lesson
  editingLesson.value = lesson
  const scheduled_at = lesson.scheduled_at.slice(0, 16)
  form.value = { ...lesson, scheduled_at }
  showModal.value = true
}

async function handleEventDrop(info) {
  const lesson = info.event.extendedProps.lesson
  const newStart = info.event.startStr.slice(0, 16)
  try {
    await api.put(`/lessons/${lesson.id}`, { ...lesson, scheduled_at: newStart })
    await loadData()
  } catch (e) {
    console.error(e)
    info.revert()
  }
}

async function handleEventResize(info) {
  const lesson = info.event.extendedProps.lesson
  const start = new Date(info.event.startStr)
  const end = new Date(info.event.endStr)
  const duration_minutes = Math.round((end - start) / 60000)
  try {
    await api.put(`/lessons/${lesson.id}`, { ...lesson, duration_minutes })
    await loadData()
  } catch (e) {
    console.error(e)
    info.revert()
  }
}

function openModal() {
  editingLesson.value = null
  form.value = {
    student_id: '',
    scheduled_at: '',
    duration_minutes: 60,
    topic: '',
    notes: '',
    completed: 0,
    repeat: false,
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingLesson.value = null
}

async function saveLesson() {
  try {
    if (editingLesson.value) {
      await api.put(`/lessons/${editingLesson.value.id}`, form.value)
    } else if (form.value.repeat) {
      const start = new Date(form.value.scheduled_at)
      const until = new Date(start)
      until.setMonth(until.getMonth() + 3)

      const series_id = `series_${Date.now()}_${Math.random().toString(36).slice(2)}`

      const dates = []
      let current = new Date(start)
      while (current <= until) {
        dates.push(new Date(current))
        current.setDate(current.getDate() + 7)
      }

      await Promise.all(
        dates.map(date => {
          const offset = date.getTimezoneOffset()
          const corrected = new Date(date.getTime() - offset * 60000)
          const scheduled_at = corrected.toISOString().slice(0, 16)
          return api.post('/lessons/', {
            student_id: form.value.student_id,
            scheduled_at,
            duration_minutes: form.value.duration_minutes,
            topic: form.value.topic,
            notes: form.value.notes,
            completed: 0,
            series_id,
          })
        })
      )
    } else {
      await api.post('/lessons/', form.value)
    }
    await loadData()
    closeModal()
  } catch (e) {
    console.error(e)
  }
}

async function deleteLesson() {
  if (editingLesson.value.series_id) {
    deleteChoice.value = 'single'
    showDeleteDialog.value = true
  } else {
    if (!confirm('Удалить занятие?')) return
    try {
      await api.delete(`/lessons/${editingLesson.value.id}`)
      await loadData()
      closeModal()
    } catch (e) {
      console.error(e)
    }
  }
}

async function confirmDelete() {
  try {
    if (deleteChoice.value === 'single') {
      await api.delete(`/lessons/${editingLesson.value.id}`)
    } else if (deleteChoice.value === 'following') {
      await api.delete(`/lessons/series/${editingLesson.value.series_id}`, {
        params: { from_date: editingLesson.value.scheduled_at },
      })
    } else if (deleteChoice.value === 'all') {
      await api.delete(`/lessons/series/${editingLesson.value.series_id}`)
    }
    await loadData()
    showDeleteDialog.value = false
    closeModal()
  } catch (e) {
    console.error(e)
  }
}

async function loadData() {
  try {
    const [lessonsRes, studentsRes] = await Promise.all([
      api.get('/lessons/'),
      api.get('/students/'),
    ])
    lessons.value = lessonsRes.data
    students.value = studentsRes.data
  } catch (e) {
    console.error(e)
  }
}

onMounted(loadData)
</script>