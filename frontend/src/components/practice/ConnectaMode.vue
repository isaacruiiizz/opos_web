<template>
  <div class="px-4 py-6 max-w-lg mx-auto">
    <div v-if="finished" class="text-center py-8">
      <p class="text-5xl mb-3">{{ score === total ? '🎉' : '💪' }}</p>
      <p class="text-2xl font-bold text-primary">{{ score }}/{{ total }} correctes</p>
      <button @click="$emit('done', score / total * 10)"
              class="mt-6 px-6 py-3 bg-primary text-white rounded-2xl font-semibold">
        Tornar als modes
      </button>
    </div>
    <div v-else class="grid grid-cols-2 gap-3">
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
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({ pairs: Array, topicId: String })
const emit = defineEmits(['done'])

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
