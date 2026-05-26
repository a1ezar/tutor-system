<template>
  <AppLayout>
    <div class="page-wrap">
      <!-- Header -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Задания</h1>
          <p class="page-subtitle">Создание и проверка домашних заданий</p>
        </div>
        <div class="page-actions">
          <router-link to="/homeworks/create" class="btn btn-primary">
            <PlusIcon />
            Создать задание
          </router-link>
        </div>
      </div>

      <!-- States -->
      <div v-if="loading" class="loading-state">Загрузка...</div>

      <div v-else>
        <!-- Список ДЗ или пустое состояние -->
        <div v-if="homeworks.length > 0" class="hw-list">
          <div
            v-for="hw in homeworks"
            :key="hw.id"
            class="hw-card"
            @click="$router.push(`/homeworks/${hw.id}`)"
          >
            <div class="hw-card-top">
              <div class="hw-info">
                <div class="hw-title">{{ hw.title }}</div>
                <div class="hw-meta">
                  <span v-if="hw.topic" class="subject-chip" :class="subjectChipClass(hw.topic)">
                    {{ hw.topic }}
                  </span>
                  <span class="hw-meta-item">
                    <UserIcon />
                    {{ hw.student_name }}
                  </span>
                </div>
              </div>
              <div class="hw-stats">
                <div class="hw-stat">
                  <div class="hw-stat-value">{{ hw.questions_count }}</div>
                  <div class="hw-stat-label">вопросов</div>
                </div>
                <div class="hw-stat">
                  <div class="hw-stat-value">{{ hw.attempts_count }}</div>
                  <div class="hw-stat-label">попыток</div>
                </div>
                <div v-if="hw.best_score !== null" class="hw-stat">
                  <div class="hw-stat-value" :class="scoreClass(hw.best_score)">{{ hw.best_score }}</div>
                  <div class="hw-stat-label">лучший</div>
                </div>
              </div>
            </div>
            <div class="hw-card-bottom">
              <span>Создано: {{ formatDate(hw.created_at) }}</span>
              <span v-if="hw.due_date" class="hw-due">Срок: {{ formatDate(hw.due_date) }}</span>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <div class="empty-state-icon">
            <DocumentTextIcon />
          </div>
          <div class="empty-state-title">Заданий пока нет</div>
          <div class="empty-state-text">
            Создайте первое задание, чтобы ученики смогли его выполнить и получить автоматическую оценку.
          </div>
          <router-link to="/homeworks/create" class="btn btn-primary">
            <PlusIcon />
            Создать задание
          </router-link>
        </div>

        <!-- Аккаунты учеников -->
        <div class="accounts-section">
          <div class="section-head">
            <h3 class="section-title">Аккаунты учеников</h3>
            <p class="section-sub">Создайте аккаунт, чтобы ученик мог входить и выполнять задания</p>
          </div>

          <div v-if="students.length === 0" class="empty-state" style="padding: 32px 16px; margin: 0;">
            <div class="empty-state-text" style="margin: 0;">
              Сначала добавьте учеников на странице «Ученики».
            </div>
          </div>

          <div v-else class="accounts-list">
            <div v-for="s in students" :key="s.id" class="account-row">
              <div class="account-info">
                <div class="account-avatar">{{ initials(s.full_name) }}</div>
                <div>
                  <div class="account-name">{{ s.full_name }}</div>
                  <div class="account-subject">{{ s.subject || 'Без предмета' }}</div>
                </div>
              </div>
              <div v-if="s.user_id" class="account-status">
                <CheckCircleIcon />
                Аккаунт создан
              </div>
              <button v-else class="btn btn-secondary" @click="openCreateAccount(s)">
                <KeyIcon />
                Создать аккаунт
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка создания аккаунта -->
    <div v-if="showAccountModal" class="modal-overlay" @click.self="showAccountModal = false">
      <div class="modal">
        <div class="modal-head">
          <h2 class="modal-title">Создать аккаунт ученика</h2>
          <button class="modal-close" @click="showAccountModal = false" title="Закрыть">
            <XMarkIcon />
          </button>
        </div>

        <div class="modal-body">
          <p class="modal-desc">
            <strong>{{ selectedStudent?.full_name }}</strong> сможет входить в систему по этим данным и выполнять задания.
          </p>

          <div class="form-field">
            <label class="form-label">Email ученика</label>
            <input
              v-model="accountForm.email"
              class="form-input"
              type="email"
              placeholder="student@example.com"
              autocomplete="off"
            />
          </div>
          <div class="form-field">
            <label class="form-label">Пароль</label>
            <input
              v-model="accountForm.password"
              class="form-input"
              type="text"
              placeholder="Придумайте пароль"
              autocomplete="off"
            />
          </div>

          <div v-if="accountError" class="form-error">{{ accountError }}</div>
        </div>

        <div class="modal-foot">
          <button class="btn btn-secondary" @click="showAccountModal = false">Отмена</button>
          <button class="btn btn-primary" @click="createAccount" :disabled="accountLoading">
            {{ accountLoading ? 'Создание...' : 'Создать' }}
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import api from '@/api/index.js'
import {
  PlusIcon,
  UserIcon,
  DocumentTextIcon,
  KeyIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { CheckCircleIcon } from '@heroicons/vue/24/solid'

const loading = ref(true)
const homeworks = ref([])
const students = ref([])
const showAccountModal = ref(false)
const selectedStudent = ref(null)
const accountForm = ref({ email: '', password: '' })
const accountError = ref('')
const accountLoading = ref(false)

async function loadData() {
  loading.value = true
  try {
    const [hwRes, stRes] = await Promise.all([
      api.get('/homeworks/'),
      api.get('/students/'),
    ])
    homeworks.value = hwRes.data
    students.value = stRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function openCreateAccount(student) {
  selectedStudent.value = student
  accountForm.value = { email: '', password: '' }
  accountError.value = ''
  showAccountModal.value = true
}

async function createAccount() {
  if (!accountForm.value.email || !accountForm.value.password) {
    accountError.value = 'Заполните все поля'
    return
  }
  accountLoading.value = true
  accountError.value = ''
  try {
    await api.post('/auth/register-student', {
      student_id: selectedStudent.value.id,
      email: accountForm.value.email,
      password: accountForm.value.password,
    })
    showAccountModal.value = false
    await loadData()
  } catch (e) {
    accountError.value = e.response?.data?.detail || 'Ошибка создания аккаунта'
  } finally {
    accountLoading.value = false
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

function scoreClass(s) {
  if (s >= 8) return 'score-high'
  if (s >= 5) return 'score-mid'
  return 'score-low'
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
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