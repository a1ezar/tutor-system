import { defineStore } from 'pinia'
import api from '@/api/index.js'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: state => !!state.token,
    isTutor: state => state.user?.role === 'tutor',
    isStudent: state => state.user?.role === 'student',
    userRole: state => state.user?.role || null
  },

  actions: {
    async login(email, password) {
      this.loading = true
      this.error = null
      try {
        // 1. Получаем токен. Сразу после деплоя контейнер бэкенда «холодный»,
        //    и первый запрос может не дойти (таймаут/502) — делаем одну
        //    повторную попытку, чтобы вход срабатывал с первого клика.
        const token = await this._requestToken(email, password)
        this.token = token
        localStorage.setItem('token', token)

        // 2. Профиль грузим отдельно и устойчиво: его временный сбой
        //    не должен выглядеть как «неверный пароль».
        await this._loadProfile()
      } catch (e) {
        this.token = null
        this.user = null
        localStorage.removeItem('token')
        const status = e.response?.status
        // 400/401 — это действительно неверные данные.
        // Всё остальное (нет ответа, 5xx) — проблема со связью/сервером.
        this.error = (status === 400 || status === 401)
          ? 'Неверный email или пароль'
          : 'Сервер недоступен, попробуйте ещё раз'
      } finally {
        this.loading = false
      }
    },

    async register(email, password, fullName) {
      this.loading = true
      this.error = null
      try {
        await api.post('/auth/register', {
          email,
          password,
          full_name: fullName
        })
      } catch (e) {
        const status = e.response?.status
        this.error = (status === 400 || status === 409)
          ? 'Пользователь с таким email уже существует'
          : 'Ошибка регистрации, попробуйте ещё раз'
        this.loading = false
        return
      }
      this.loading = false
      // Регистрация прошла — сразу логинимся теми же данными.
      await this.login(email, password)
    },

    async fetchMe() {
      const { data } = await api.get('/auth/me')
      this.user = data
    },

    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
    },

    // ---------- внутренние помощники ----------

    async _requestToken(email, password, retry = true) {
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)
      try {
        const { data } = await api.post('/auth/login', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        return data.access_token
      } catch (e) {
        // Транзиентная ошибка: ответа нет (сеть/таймаут) или 5xx —
        // одна повторная попытка после короткой паузы.
        const transient = !e.response || e.response.status >= 500
        if (retry && transient) {
          await new Promise(r => setTimeout(r, 900))
          return this._requestToken(email, password, false)
        }
        throw e
      }
    },

    async _loadProfile(retry = true) {
      try {
        await this.fetchMe()
      } catch (e) {
        if (retry) {
          await new Promise(r => setTimeout(r, 900))
          return this._loadProfile(false)
        }
        throw e
      }
    }
  }
})