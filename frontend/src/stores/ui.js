import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const systemPrefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches
  const theme = ref(systemPrefersDark ? 'dark' : 'light')
  const drawerOpen = ref(false)
  const readingPct = ref(0)

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    document.documentElement.classList.toggle('dark', theme.value === 'dark')
  }

  function openDrawer() { drawerOpen.value = true }
  function closeDrawer() { drawerOpen.value = false }

  // Apply theme on init
  document.documentElement.classList.toggle('dark', theme.value === 'dark')

  return { theme, drawerOpen, readingPct, toggleTheme, openDrawer, closeDrawer }
})
