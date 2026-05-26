<template>
  <div class="app-root">
    <!-- Mobile overlay -->
    <div v-if="mobileOpen" @click="mobileOpen = false" class="mobile-overlay"></div>

    <!-- SIDEBAR -->
    <aside class="sidebar" :class="{ open: mobileOpen }">
      <div class="sidebar-logo">
        <div class="sidebar-logo-icon">
          <AcademicCapIcon />
        </div>
        <div class="sidebar-logo-title">TutorPlatform</div>
      </div>

      <nav class="sidebar-nav">
        <template v-for="(section, idx) in groupedNav" :key="idx">
          <div v-if="section.title" class="nav-section-title">{{ section.title }}</div>
          <div class="nav-group">
            <router-link
              v-for="item in section.items"
              :key="item.to"
              :to="item.to"
              custom
              v-slot="{ href, navigate, isActive, isExactActive }"
            >
              <a
                :href="href"
                @click="(e) => { navigate(e); mobileOpen = false }"
                class="nav-link"
                :class="{ active: isActive || isExactActive }"
              >
                <component :is="(isActive || isExactActive) ? item.iconSolid : item.iconOutline" />
                <span>{{ item.label }}</span>
              </a>
            </router-link>
          </div>
        </template>
      </nav>

      <div class="sidebar-user">
        <div class="sidebar-user-row">
          <div class="user-avatar">{{ userInitials }}</div>
          <div class="user-info">
            <div class="user-name">{{ authStore.user?.full_name || 'Пользователь' }}</div>
            <div class="user-role">{{ authStore.isStudent ? 'Ученик' : 'Репетитор' }}</div>
          </div>
          <button @click="handleLogout" title="Выйти" class="user-logout">
            <ArrowRightOnRectangleIcon />
          </button>
        </div>
      </div>
    </aside>

    <!-- MAIN -->
    <main class="app-main">
      <header class="app-header">
        <div class="app-header-left">
          <button @click="mobileOpen = !mobileOpen" class="mobile-menu-btn">
            <Bars3Icon />
          </button>
          <h1 class="app-page-title">{{ pageTitle }}</h1>
        </div>

        <div class="app-header-right">
          <div class="search-wrap">
            <MagnifyingGlassIcon class="search-icon" />
            <input v-model="searchQuery" placeholder="Поиск..." class="search-input" />
          </div>
          <button class="bell-btn">
            <BellIcon />
            <span class="bell-dot"></span>
          </button>
        </div>
      </header>

      <div class="app-content">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

import {
  HomeIcon as HomeOutline,
  UsersIcon as UsersOutline,
  CalendarIcon as CalendarOutline,
  ClipboardDocumentListIcon as ClipboardOutline,
  DocumentTextIcon as DocumentOutline,
  ChartBarSquareIcon as ChartOutline,
  Bars3Icon,
  MagnifyingGlassIcon,
  BellIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/vue/24/outline'

import {
  HomeIcon as HomeSolid,
  UsersIcon as UsersSolid,
  CalendarIcon as CalendarSolid,
  ClipboardDocumentListIcon as ClipboardSolid,
  DocumentTextIcon as DocumentSolid,
  ChartBarSquareIcon as ChartSolid,
  AcademicCapIcon,
} from '@heroicons/vue/24/solid'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const searchQuery = ref('')
const mobileOpen = ref(false)

const tutorNav = [
  {
    title: 'Основное',
    items: [
      { to: '/dashboard', label: 'Главная',    iconOutline: HomeOutline,     iconSolid: HomeSolid },
      { to: '/students',  label: 'Ученики',    iconOutline: UsersOutline,    iconSolid: UsersSolid },
      { to: '/calendar',  label: 'Расписание', iconOutline: CalendarOutline, iconSolid: CalendarSolid },
    ],
  },
  {
    title: 'Учебный процесс',
    items: [
      { to: '/grades',    label: 'Журнал',           iconOutline: ClipboardOutline, iconSolid: ClipboardSolid },
      { to: '/homeworks', label: 'Домашние задания', iconOutline: DocumentOutline,  iconSolid: DocumentSolid },
      { to: '/analytics', label: 'Аналитика',        iconOutline: ChartOutline,     iconSolid: ChartSolid },
    ],
  },
]

const studentNav = [
  {
    title: null,
    items: [
      { to: '/student-dashboard', label: 'Главная',          iconOutline: HomeOutline,     iconSolid: HomeSolid },
      { to: '/my-homeworks',      label: 'Домашние задания', iconOutline: DocumentOutline, iconSolid: DocumentSolid },
    ],
  },
]

const groupedNav = computed(() => (authStore.isStudent ? studentNav : tutorNav))
const flatNav = computed(() => groupedNav.value.flatMap(s => s.items))

const userInitials = computed(() => {
  const name = authStore.user?.full_name || ''
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map(s => s[0]).join('').toUpperCase() || '?'
})

const pageTitle = computed(() => {
  const match = flatNav.value.find(n => route.path.startsWith(n.to))
  return match?.label || ''
})

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>