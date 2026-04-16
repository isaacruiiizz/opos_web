<template>
  <div class="grid grid-cols-2 gap-3 p-4 sm:grid-cols-3">
    <button v-for="m in modes" :key="m.id"
            @click="!generating[m.id] && $emit('select', m.id)"
            :disabled="generating[m.id]"
            class="flex flex-col items-center gap-2 p-4 rounded-2xl
                   bg-[var(--color-surface)] border transition-colors disabled:cursor-default"
            :class="cardClass(m.id)">
      <span class="text-3xl">{{ m.icon }}</span>
      <span class="text-sm font-semibold">{{ m.label }}</span>
      <span class="text-xs text-gray-400 text-center">
        {{ generating[m.id] ? 'Generant…' : m.desc }}
      </span>
      <!-- States: generating > error > ready > in-progress -->
      <span v-if="generating[m.id]"
            class="text-xs text-primary animate-pulse mt-0.5">⏳ Treballant en segon pla…</span>
      <span v-else-if="errors[m.id]"
            class="text-xs font-medium text-red-600 bg-red-50 dark:bg-red-900/20 px-2 py-0.5 rounded-full text-center leading-tight">
        ✗ Error · Clica per reintentar
      </span>
      <span v-else-if="ready[m.id]"
            class="text-xs font-medium text-green-700 bg-green-100 dark:bg-green-900/20 px-2 py-0.5 rounded-full">
        ✓ Llest! Clica per comenzar
      </span>
      <span v-else-if="progress[m.id]"
            class="text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full">
        ● {{ progressLabel(m.id) }}
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
  { id: 'test',     icon: '☑️', label: 'Test',         desc: '10 preguntes, 4 opcions' },
  { id: 'breus',    icon: '✍️', label: 'Breus',        desc: '5 preguntes curtes' },
  { id: 'suposit',  icon: '🏛️', label: 'Supòsit',      desc: 'Cas pràctic real' },
  { id: 'connecta', icon: '🔗', label: 'Connecta',     desc: 'Relaciona conceptes' },
  { id: 'buits',    icon: '📝', label: 'Omple buits',  desc: 'Completa les frases' },
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
