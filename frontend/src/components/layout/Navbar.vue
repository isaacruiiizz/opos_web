<template>
  <header class="fixed top-0 left-0 right-0 z-40 h-14 flex items-center
                 px-3 gap-3 bg-[var(--color-surface)] border-b border-[var(--color-border)]">
    <button @click="ui.openDrawer()"
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>
    <span class="font-bold text-primary text-lg">OPOS C1</span>
    <span v-if="topics.activeTopic"
          class="flex-1 text-sm text-gray-500 dark:text-gray-400 truncate">
      {{ topics.activeTopic.title }}
    </span>
    <span v-else class="flex-1" />
    <button @click="ui.toggleTheme()"
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
      <!-- Sun (shown in dark mode to switch to light) -->
      <svg v-if="ui.theme === 'dark'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="4"/>
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>
      </svg>
      <!-- Moon (shown in light mode to switch to dark) -->
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
      </svg>
    </button>
  </header>
  <div class="h-14" />
</template>

<script setup>
import { useUiStore } from '../../stores/ui.js'
import { useTopicsStore } from '../../stores/topics.js'
const ui = useUiStore()
const topics = useTopicsStore()
</script>
