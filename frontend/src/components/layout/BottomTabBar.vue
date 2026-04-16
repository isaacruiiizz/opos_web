<template>
  <nav class="fixed bottom-0 left-0 right-0 z-40 h-16 flex
              bg-[var(--color-surface)] border-t border-[var(--color-border)]">
    <RouterLink v-for="tab in tabs" :key="tab.to" :to="tab.to"
      class="flex-1 flex flex-col items-center justify-center gap-0.5 text-xs
             text-gray-500 dark:text-gray-400 transition-colors
             [&.router-link-active]:text-primary [&.router-link-active]:font-semibold">
      <span class="relative inline-block">
        <span class="text-2xl leading-none">{{ tab.icon }}</span>
        <span v-if="tab.badge === 'generating'"
              class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-primary animate-pulse" />
        <span v-else-if="tab.badge === 'ready'"
              class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-green-500" />
      </span>
      <span>{{ tab.label }}</span>
    </RouterLink>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { usePracticeStore } from '../../stores/practice.js'

const practice = usePracticeStore()

const practicaBadge = computed(() => {
  if (practice.anyGenerating) return 'generating'
  if (practice.anyReady) return 'ready'
  return null
})

const tabs = computed(() => [
  { to: '/apunts',   icon: '📖', label: 'Apunts',   badge: null },
  { to: '/flash',    icon: '🃏', label: 'Flash',     badge: null },
  { to: '/practica', icon: '🎯', label: 'Pràctica',  badge: practicaBadge.value },
  { to: '/progres',  icon: '📊', label: 'Progrés',   badge: null },
])
</script>
