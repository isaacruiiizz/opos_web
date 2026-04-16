<template>
  <div class="grid grid-cols-2 gap-3 p-4 sm:grid-cols-3">
    <button v-for="m in modes" :key="m.id"
            @click="$emit('select', m.id)"
            class="flex flex-col items-center gap-2 p-4 rounded-2xl
                   bg-[var(--color-surface)] border transition-colors
                   hover:border-primary hover:bg-primary/5"
            :class="progress[m.id] ? 'border-primary/40' : 'border-[var(--color-border)]'">
      <span class="text-3xl">{{ m.icon }}</span>
      <span class="text-sm font-semibold">{{ m.label }}</span>
      <span class="text-xs text-gray-400 text-center">{{ m.desc }}</span>
      <span v-if="progress[m.id]"
            class="text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full">
        ● {{ progressLabel(m.id) }}
      </span>
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  progress: { type: Object, default: () => ({}) }
})
defineEmits(['select'])

const modes = [
  { id: 'test',     icon: '☑️', label: 'Test',         desc: '10 preguntes, 4 opcions' },
  { id: 'breus',    icon: '✍️', label: 'Breus',        desc: '5 preguntes curtes' },
  { id: 'suposit',  icon: '🏛️', label: 'Supòsit',      desc: 'Cas pràctic real' },
  { id: 'connecta', icon: '🔗', label: 'Connecta',     desc: 'Relaciona conceptes' },
  { id: 'buits',    icon: '📝', label: 'Omple buits',  desc: 'Completa les frases' },
]

function progressLabel(id) {
  const p = props.progress[id]
  if (!p) return null
  if (p.inProgress) return 'En progrés'
  if (p.current !== undefined && p.total) return `${p.current}/${p.total} fetes`
  return 'En progrés'
}
</script>
