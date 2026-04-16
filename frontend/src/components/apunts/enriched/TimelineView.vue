<template>
  <div class="timeline py-1">
    <div v-for="(item, i) in data" :key="i" class="flex gap-3 mb-1">
      <div class="flex flex-col items-center flex-shrink-0">
        <div class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
             :style="{ background: stepColor(i, data.length) }">
          {{ item.step }}
        </div>
        <div v-if="i < data.length - 1" class="w-0.5 flex-1 min-h-3.5 bg-[var(--color-border)] mt-0.5"></div>
      </div>
      <div class="pb-3">
        <p class="text-sm font-semibold text-[var(--color-text)]">{{ item.title }}</p>
        <p class="text-xs text-gray-500 mt-0.5 leading-snug">{{ item.desc }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ data: { type: Array, required: true } })

function stepColor(i, total) {
  if (i === total - 1) return '#22c55e'
  if (i === 0) return '#3b82f6'
  return '#8b5cf6'
}
</script>
