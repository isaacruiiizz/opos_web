<template>
  <div class="px-4 py-6 max-w-lg mx-auto">
    <div v-if="finished" class="text-center py-8">
      <div class="flex justify-center mb-3">
        <svg v-if="score === total" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-primary">
          <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/>
        </svg>
        <svg v-else width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-primary">
          <circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>
        </svg>
      </div>
      <p class="text-2xl font-bold text-primary">{{ score }}/{{ total }} correctes</p>
      <button @click="$emit('done', score / total * 10)"
              class="mt-6 px-6 py-3 bg-primary text-white rounded-2xl font-semibold">
        Tornar als modes
      </button>
    </div>
    <div v-else>
      <div class="mb-3 flex justify-between">
        <button @click="emit('cancel', { current: score, total: total })"
                class="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
          ← Sortir
        </button>
        <button @click="emit('done', score / total * 10)"
                class="flex items-center gap-1 text-xs text-orange-500 hover:text-orange-700">
          Finalitzar
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        </button>
      </div>
      <div class="grid grid-cols-2 gap-3">
      <div class="space-y-2">
        <p class="text-xs font-semibold uppercase text-gray-400 mb-2 text-center">Termes</p>
        <button v-for="(t, i) in shuffledTermes" :key="'t'+i"
                @click="selectTerm(i)"
                :class="termClass(i)"
                class="w-full px-3 py-2 rounded-xl border text-sm font-medium text-left transition-colors">
          {{ t.terme }}
        </button>
      </div>
      <div class="space-y-2">
        <p class="text-xs font-semibold uppercase text-gray-400 mb-2 text-center">Definicions</p>
        <button v-for="(d, i) in shuffledDefs" :key="'d'+i"
                @click="selectDef(i)"
                :class="defClass(i)"
                class="w-full px-3 py-2 rounded-xl border text-xs text-left transition-colors">
          {{ d.definicio }}
        </button>
      </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({ pairs: Array, topicId: String })
const emit = defineEmits(['done', 'cancel'])

function shuffle(arr) { return [...arr].sort(() => Math.random() - 0.5) }

const shuffledTermes = ref(shuffle(props.pairs))
const shuffledDefs = ref(shuffle(props.pairs))
const selectedTerm = ref(null)
const matched = ref({})
const score = ref(0)
const total = computed(() => props.pairs.length)
const finished = computed(() => Object.keys(matched.value).length === total.value)

function selectTerm(i) {
  if (matched.value[i] !== undefined) return
  selectedTerm.value = i
}

function selectDef(defIdx) {
  if (selectedTerm.value === null) return
  const tIdx = selectedTerm.value
  const terme = shuffledTermes.value[tIdx]
  const def = shuffledDefs.value[defIdx]
  const isMatch = terme.terme === def.terme
  matched.value[tIdx] = { defIdx, correct: isMatch }
  if (isMatch) score.value++
  selectedTerm.value = null
}

function termClass(i) {
  if (i === selectedTerm.value) return 'border-primary bg-primary/10'
  const m = matched.value[i]
  if (m === undefined) return 'border-[var(--color-border)] hover:border-primary'
  return m.correct ? 'border-green-400 bg-green-100 dark:bg-green-900/20' : 'border-red-400 bg-red-100 dark:bg-red-900/20'
}

function defClass(defIdx) {
  const used = Object.values(matched.value).find(m => m.defIdx === defIdx)
  if (!used) return 'border-[var(--color-border)] hover:border-primary'
  return used.correct ? 'border-green-400 bg-green-100 dark:bg-green-900/20' : 'border-red-400 bg-red-100 dark:bg-red-900/20'
}
</script>
