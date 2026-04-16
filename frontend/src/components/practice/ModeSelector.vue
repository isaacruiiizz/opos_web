<template>
  <div class="grid grid-cols-2 gap-3 p-4 sm:grid-cols-3">
    <button v-for="m in modes" :key="m.id"
            @click="!generating[m.id] && $emit('select', m.id)"
            :disabled="generating[m.id]"
            class="flex flex-col items-center gap-2 p-4 rounded-2xl
                   bg-[var(--color-surface)] border transition-colors disabled:cursor-default"
            :class="cardClass(m.id)">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
           v-html="m.icon" />
      <span class="text-sm font-semibold">{{ m.label }}</span>
      <span class="text-xs text-gray-400 text-center">
        {{ generating[m.id] ? 'Generant…' : m.desc }}
      </span>
      <!-- States: generating > error > ready > in-progress -->
      <span v-if="generating[m.id]"
            class="text-xs text-primary animate-pulse mt-0.5 flex items-center gap-1">
        <svg class="animate-spin" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="9" stroke-opacity="0.25"/><path d="M12 3a9 9 0 0 1 9 9"/></svg>
        Treballant en segon pla…
      </span>
      <span v-else-if="errors[m.id]"
            class="text-xs font-medium text-red-600 bg-red-50 dark:bg-red-900/20 px-2 py-0.5 rounded-full text-center leading-tight flex items-center gap-1">
        <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        Error · Clica per reintentar
      </span>
      <span v-else-if="ready[m.id]"
            class="text-xs font-medium text-green-700 bg-green-100 dark:bg-green-900/20 px-2 py-0.5 rounded-full flex items-center gap-1">
        <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        Llest! Clica per comenzar
      </span>
      <span v-else-if="progress[m.id]"
            class="text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full flex items-center gap-1">
        <span class="inline-block w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0"></span>
        {{ progressLabel(m.id) }}
      </span>
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  progress:   { type: Object, default: () => ({}) },
  generating: { type: Object, default: () => ({}) },
  ready:      { type: Object, default: () => ({}) },
  errors:     { type: Object, default: () => ({}) },
})
defineEmits(['select'])

const modes = [
  { id: 'test',     icon: '<rect x="2" y="3" width="20" height="18" rx="2"/><path d="m9 12 2 2 4-4"/>', label: 'Test',         desc: '10 preguntes, 4 opcions' },
  { id: 'breus',    icon: '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"/>', label: 'Breus',        desc: '5 preguntes curtes' },
  { id: 'suposit',  icon: '<rect x="3" y="9" width="18" height="13" rx="1"/><path d="M3 9 12 3l9 6"/>', label: 'Supòsit',      desc: 'Cas pràctic real' },
  { id: 'connecta', icon: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>', label: 'Connecta',     desc: 'Relaciona conceptes' },
  { id: 'buits',    icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>', label: 'Omple buits',  desc: 'Completa les frases' },
]

function cardClass(id) {
  if (props.generating[id]) return 'border-primary/30 opacity-80'
  if (props.errors[id])     return 'border-red-400 hover:border-red-500 hover:bg-red-50 dark:hover:bg-red-900/10'
  if (props.ready[id])      return 'border-green-400 hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-900/10'
  if (props.progress[id])   return 'border-primary/40 hover:border-primary hover:bg-primary/5'
  return 'border-[var(--color-border)] hover:border-primary hover:bg-primary/5'
}

function progressLabel(id) {
  const p = props.progress[id]
  if (!p) return null
  if (p.inProgress) return 'En progrés'
  if (p.current !== undefined && p.total) return `${p.current}/${p.total} fetes`
  return 'En progrés'
}
</script>
