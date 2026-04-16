<template>
  <div class="space-y-2 mt-1">
    <div v-for="(box, i) in data" :key="i"
         class="rounded-lg px-3 py-2.5 flex gap-2.5 items-start text-sm leading-relaxed"
         :class="variantClass(box.variant)">
      <span class="flex-shrink-0 mt-0.5">
        <svg v-if="box.variant === 'law'" class="w-4 h-4 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
        </svg>
        <svg v-else-if="box.variant === 'important'" class="w-4 h-4 text-yellow-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
          <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <svg v-else class="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
        </svg>
      </span>
      <div>
        <strong v-if="box.title" class="font-semibold">{{ box.title }}:</strong>
        {{ box.text }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ data: { type: Array, required: true } })

function variantClass(variant) {
  if (variant === 'law') return 'bg-blue-50 border-l-[3px] border-blue-400'
  if (variant === 'important') return 'bg-yellow-50 border-l-[3px] border-yellow-400'
  return 'bg-green-50 border-l-[3px] border-green-400'
}
</script>
