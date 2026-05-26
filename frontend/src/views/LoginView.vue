<template>
  <div class="auth-root">
    <!-- ЛЕВАЯ ПАНЕЛЬ — БРЕНД (десктоп) -->
    <div class="auth-hero">
      <div class="auth-hero-content">
        <div class="auth-hero-logo">
          <div class="auth-hero-logo-icon">
            <AcademicCapIcon />
          </div>
          <div class="auth-hero-logo-text">TutorPlatform</div>
        </div>
      </div>

      <div class="auth-hero-headline">
        <h1 class="auth-hero-title">Платформа для&nbsp;современного репетитора</h1>
        <p class="auth-hero-subtitle">
          Управляйте учениками, расписанием и&nbsp;домашними заданиями в&nbsp;одном месте. ML&#8209;аналитика покажет, кому нужна дополнительная помощь.
        </p>

        <div class="auth-hero-features">
          <div class="auth-hero-feature">
            <div class="auth-hero-feature-icon"><CheckIcon /></div>
            Журнал оценок и&nbsp;прогресс по&nbsp;каждому ученику
          </div>
          <div class="auth-hero-feature">
            <div class="auth-hero-feature-icon"><CheckIcon /></div>
            Календарь занятий с&nbsp;автоматическими напоминаниями
          </div>
          <div class="auth-hero-feature">
            <div class="auth-hero-feature-icon"><CheckIcon /></div>
            ML&#8209;модель определяет учеников группы риска
          </div>
        </div>
      </div>

      <div class="auth-hero-footer">© 2026 TutorPlatform · СПбПУ</div>
    </div>

    <!-- ПРАВАЯ ПАНЕЛЬ — ФОРМА -->
    <div class="auth-form-wrap">
      <div class="auth-form-card">
        <div class="auth-mobile-logo">
          <div class="auth-mobile-logo-icon"><AcademicCapIcon /></div>
          <div class="auth-mobile-logo-text">TutorPlatform</div>
        </div>

        <h2 class="auth-title">С возвращением</h2>
        <p class="auth-subtitle">Войдите в свой аккаунт, чтобы продолжить</p>

        <div v-if="authStore.error" class="auth-error">
          <ExclamationCircleIcon />
          {{ authStore.error }}
        </div>

        <form class="auth-form" @submit.prevent="handleLogin">
          <div class="form-field">
            <label class="form-label">Email</label>
            <input
              v-model="email"
              class="form-input"
              type="email"
              placeholder="example@mail.com"
              autocomplete="email"
              required
            />
          </div>

          <div class="form-field">
            <label class="form-label">Пароль</label>
            <input
              v-model="password"
              class="form-input"
              type="password"
              placeholder="Введите пароль"
              autocomplete="current-password"
              required
            />
          </div>

          <button type="submit" class="auth-submit-btn" :disabled="authStore.loading">
            {{ authStore.loading ? 'Входим...' : 'Войти' }}
          </button>
        </form>

        <p class="auth-footer">
          Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import {
  AcademicCapIcon,
  CheckIcon,
} from '@heroicons/vue/24/solid'
import {
  ExclamationCircleIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')

async function handleLogin() {
  await authStore.login(email.value, password.value)
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
  }
}
</script>