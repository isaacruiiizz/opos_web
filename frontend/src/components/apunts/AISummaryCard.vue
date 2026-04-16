<template>
  <div v-if="loading"
       class="rounded-2xl border border-[#c4b5fd] bg-gradient-to-br from-[#f5f3ff] to-[#eff6ff] p-4 mb-5 animate-pulse">
    <div class="h-3 bg-purple-200 rounded w-24 mb-3"></div>
    <div class="h-3 bg-purple-100 rounded w-full mb-2"></div>
    <div class="h-3 bg-purple-100 rounded w-4/5"></div>
  </div>

  <div v-else-if="summary"
       class="rounded-2xl border border-[#c4b5fd] bg-gradient-to-br from-[#f5f3ff] to-[#eff6ff] p-4 mb-5">
    <div class="flex items-center justify-between mb-2.5">
      <span class="inline-flex items-center gap-1.5 text-[0.65rem] font-bold text-primary
                   bg-primary/10 px-2 py-0.5 rounded-full tracking-wide">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>
          <path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2"/>
        </svg>
        RESUM IA
      </span>
      <span class="text-[0.65rem] text-gray-400">{{ sectionCount }} seccions</span>
    </div>
    <p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-3">{{ summary.summary }}</p>
    <div class="flex flex-wrap gap-1.5">
      <span v-for="chip in summary.chips" :key="chip.label"
            class="inline-flex items-center gap-1 text-[0.68rem] font-medium px-2 py-0.5 rounded-full"
            :class="chipClass(chip.category)">
        {{ chip.label }}
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  summary: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  sectionCount: { type: Number, default: 0 },
})

function chipClass(category) {
  const map = {
    concept: 'bg-blue-100 text-blue-700',
    law: 'bg-green-100 text-green-700',
    alert: 'bg-orange-100 text-orange-700',
    exam: 'bg-red-100 text-red-700',
  }
  return map[category] || 'bg-gray-100 text-gray-600'
}
</script>
