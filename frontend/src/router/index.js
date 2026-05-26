import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true }
    },
    // --- Роуты репетитора ---
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true, role: 'tutor' }
    },
    {
      path: '/students',
      name: 'students',
      component: () => import('@/views/StudentsView.vue'),
      meta: { requiresAuth: true, role: 'tutor' }
    },
    {
      path: '/students/:id',
      name: 'student-detail',
      component: () => import('@/views/StudentDetailView.vue'),
      meta: { requiresAuth: true, role: 'tutor' }
    },
    {
      path: '/grades',
      name: 'grades',
      component: () => import('@/views/GradesView.vue'),
      meta: { requiresAuth: true, role: 'tutor' }
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: () => import('@/views/AnalyticsView.vue'),
      meta: { requiresAuth: true, role: 'tutor' }
    },
    {
      path: '/calendar',
      name: 'calendar',
      component: () => import('@/views/CalendarView.vue'),
      meta: { requiresAuth: true, role: 'tutor' }
    },
    {
      path: '/homeworks',
      name: 'homeworks',
      component: () => import('@/views/HomeworksView.vue'),
      meta: { requiresAuth: true, role: 'tutor' }
    },
    {
      path: '/homeworks/create',
      name: 'homework-create',
      component: () => import('@/views/HomeworkCreateView.vue'),
      meta: { requiresAuth: true, role: 'tutor' }
    },
    {
      path: '/homeworks/:id',
      name: 'homework-detail',
      component: () => import('@/views/HomeworkDetailView.vue'),
      meta: { requiresAuth: true, role: 'tutor' }
    },
    // --- Роуты ученика ---
    {
      path: '/student-dashboard',
      name: 'student-dashboard',
      component: () => import('@/views/StudentDashboardView.vue'),
      meta: { requiresAuth: true, role: 'student' }
    },
    {
      path: '/my-homeworks',
      name: 'my-homeworks',
      component: () => import('@/views/MyHomeworksView.vue'),
      meta: { requiresAuth: true, role: 'student' }
    },
    {
      path: '/my-homeworks/:id',
      name: 'my-homework-solve',
      component: () => import('@/views/MyHomeworkSolveView.vue'),
      meta: { requiresAuth: true, role: 'student' }
    }
  ]
})

// Защита роутов
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }

  if (to.meta.guest && token) {
    // Перенаправляем на нужный дашборд по роли
    try {
      const { useAuthStore } = await import('@/stores/auth.js')
      const authStore = useAuthStore()
      if (!authStore.user) {
        await authStore.fetchMe()
      }
      if (authStore.isStudent) {
        next('/student-dashboard')
      } else {
        next('/dashboard')
      }
    } catch {
      next('/dashboard')
    }
    return
  }

  // Проверка роли
  if (to.meta.role && token) {
    try {
      const { useAuthStore } = await import('@/stores/auth.js')
      const authStore = useAuthStore()
      if (!authStore.user) {
        await authStore.fetchMe()
      }
      if (authStore.userRole !== to.meta.role) {
        // Перенаправляем на свой дашборд
        if (authStore.isStudent) {
          next('/student-dashboard')
        } else {
          next('/dashboard')
        }
        return
      }
    } catch {
      next('/login')
      return
    }
  }

  // Редирект с / на нужный дашборд
  if (to.path === '/' || to.path === '/dashboard') {
    if (token) {
      try {
        const { useAuthStore } = await import('@/stores/auth.js')
        const authStore = useAuthStore()
        if (!authStore.user) {
          await authStore.fetchMe()
        }
        if (authStore.isStudent) {
          next('/student-dashboard')
          return
        }
      } catch {}
    }
  }

  next()
})

export default router