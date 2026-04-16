<template>
  <nav class="fixed bottom-0 left-0 right-0 z-40 h-16 flex
              bg-[var(--color-surface)] border-t border-[var(--color-border)]">
    <RouterLink v-for="tab in tabs" :key="tab.to" :to="tab.to"
      class="flex-1 flex flex-col items-center justify-center gap-0.5 text-xs
             text-gray-500 dark:text-gray-400 transition-colors
             [&.router-link-active]:text-primary [&.router-link-active]:font-semibold">
      <span class="text-2xl leading-none">{{ tab.icon }}</span>
      <span>{{ tab.label }}</span>
    </RouterLink>
  </nav>
</template>

<script setup>
const tabs = [
  { to: '/apunts',   icon: '📖', label: 'Apunts'   },
  { to: '/flash',    icon: '🃏', label: 'Flash'     },
  { to: '/practica', icon: '🎯', label: 'Pràctica'  },
  { to: '/progres',  icon: '📊', label: 'Progrés'   },
]
</script>
