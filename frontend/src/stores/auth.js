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
        const formData = new FormData()
        formData.append('username', email)
        formData.append('password', password)
        const response = await api.post('/auth/login', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.token = response.data.access_token
        localStorage.setItem('token', this.token)
        await this.fetchMe()
      } catch (e) {
        this.error = 'Неверный email или пароль'
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
        await this.login(email, password)
      } catch (e) {
        this.error = 'Ошибка регистрации'
      } finally {
        this.loading = false
      }
    },

    async fetchMe() {
      try {
        const response = await api.get('/auth/me')
        this.user = response.data
      } catch (e) {
        this.logout()
      }
    },

    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
    }
  }
})