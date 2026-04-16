<template>
  <nav class="fixed bottom-0 left-0 right-0 z-40 h-16 flex
              bg-[var(--color-surface)] border-t border-[var(--color-border)]">
    <RouterLink v-for="tab in tabs" :key="tab.to" :to="tab.to"
      class="flex-1 flex flex-col items-center justify-center gap-0.5 text-xs
             text-gray-500 dark:text-gray-400 transition-colors
             [&.router-link-active]:text-primary [&.router-link-active]:font-semibold">
      <span class="relative inline-block">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
             v-html="tab.icon" />
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
  {
    to: '/apunts',
    label: 'Apunts',
    badge: null,
    icon: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
  },
  {
    to: '/flash',
    label: 'Flash',
    badge: null,
    icon: '<path d="m2 20 10-5 10 5"/><path d="m2 15 10-5 10 5"/><path d="m2 10 10-5 10 5"/>',
  },
  {
    to: '/practica',
    label: 'Pràctica',
    badge: practicaBadge.value,
    icon: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
  },
  {
    to: '/progres',
    label: 'Progrés',
    badge: null,
    icon: '<line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/>',
  },
])
</script>
