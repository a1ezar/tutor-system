import axios from 'axios'

// VITE_API_URL подставляется при сборке frontend.
// Локально (npm run dev) читается из frontend/.env.local
// На проде — из переменных окружения Timeweb Cloud.
// Если переменная не задана — fallback на localhost:8000 для разработки.
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Автоматически добавляем токен к каждому запросу
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Обработка ошибок авторизации
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      const path = window.location.pathname
      const onAuthPage = path === '/login' || path === '/register'
      // Не выкидываем со страницы входа/регистрации: иначе 401 от /auth/me
      // во время самого входа жёстко перезагружает страницу и ломает вход.
      if (!onAuthPage) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api