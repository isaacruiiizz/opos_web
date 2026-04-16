<template>
  <div class="h-[3px] bg-[var(--color-border)] sticky z-[9]" :style="{ top: topOffset + 'px' }">
    <div class="h-full bg-gradient-to-r from-primary to-blue-400 transition-[width] duration-200"
         :style="{ width: pct + '%' }"></div>
  </div>
</template>

<script setup>
defineProps({
  pct: { type: Number, default: 0 },
  topOffset: { type: Number, default: 45 },
})
</script>
