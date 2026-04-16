<template>
  <header class="fixed top-0 left-0 right-0 z-40 h-14 flex items-center
                 px-3 gap-3 bg-[var(--color-surface)] border-b border-[var(--color-border)]">
    <button @click="ui.openDrawer()"
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-xl">
      ☰
    </button>
    <span class="font-bold text-primary text-lg">OPOS C1</span>
    <span v-if="topics.activeTopic"
          class="flex-1 text-sm text-gray-500 dark:text-gray-400 truncate">
      {{ topics.activeTopic.title }}
    </span>
    <span v-else class="flex-1" />
    <button @click="ui.toggleTheme()"
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-xl">
      {{ ui.theme === 'dark' ? '☀️' : '🌙' }}
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
