<template>
  <div class="space-y-1">
    <div class="flex justify-between items-center text-sm">
      <span class="truncate font-medium" :title="label">{{ label }}</span>
      <span class="text-xs font-semibold ml-2 flex-shrink-0"
            :class="pct >= 80 ? 'text-green-600' : pct >= 40 ? 'text-yellow-600' : 'text-gray-400'">
        {{ Math.round(pct) }}%
      </span>
    </div>
    <div class="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
      <div class="h-full rounded-full transition-all duration-500"
           :class="pct >= 80 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-400' : 'bg-gray-300'"
           :style="{ width: pct + '%' }" />
    </div>
  </div>
</template>
<script setup>
defineProps({ label: String, pct: { type: Number, default: 0 } })
</script>
