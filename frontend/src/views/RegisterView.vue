<template>
  <div class="auth-root">
    <!-- ЛЕВАЯ ПАНЕЛЬ — БРЕНД -->
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
        <h1 class="auth-hero-title">Начните вести учеников цифрово</h1>
        <p class="auth-hero-subtitle">
          Бесплатная регистрация для&nbsp;репетиторов. Создайте аккаунт за&nbsp;30&nbsp;секунд и&nbsp;получите доступ ко&nbsp;всем функциям платформы.
        </p>

        <div class="auth-hero-features">
          <div class="auth-hero-feature">
            <div class="auth-hero-feature-icon"><CheckIcon /></div>
            Неограниченное количество учеников
          </div>
          <div class="auth-hero-feature">
            <div class="auth-hero-feature-icon"><CheckIcon /></div>
            Автоматическая проверка домашних заданий
          </div>
          <div class="auth-hero-feature">
            <div class="auth-hero-feature-icon"><CheckIcon /></div>
            ML&#8209;аналитика и&nbsp;прогноз успеваемости
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

        <h2 class="auth-title">Создание аккаунта</h2>
        <p class="auth-subtitle">Регистрация для репетитора — бесплатно</p>

        <div v-if="authStore.error" class="auth-error">
          <ExclamationCircleIcon />
          {{ authStore.error }}
        </div>

        <form class="auth-form" @submit.prevent="handleRegister">
          <div class="form-field">
            <label class="form-label">Полное имя</label>
            <input
              v-model="fullName"
              class="form-input"
              type="text"
              placeholder="Иванов Иван Иванович"
              autocomplete="name"
              required
            />
          </div>

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
              placeholder="Минимум 6 символов"
              autocomplete="new-password"
              minlength="6"
              required
            />
          </div>

          <button type="submit" class="auth-submit-btn" :disabled="authStore.loading">
            {{ authStore.loading ? 'Регистрируем...' : 'Создать аккаунт' }}
          </button>
        </form>

        <p class="auth-footer">
          Уже есть аккаунт? <router-link to="/login">Войти</router-link>
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

const fullName = ref('')
const email = ref('')
const password = ref('')

async function handleRegister() {
  await authStore.register(email.value, password.value, fullName.value)
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
  }
}
</script>