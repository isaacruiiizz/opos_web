<template>
  <div class="px-4 py-6 max-w-lg mx-auto">
    <div v-if="finished" class="text-center py-6">
      <p class="text-5xl mb-3">{{ scoreEmoji }}</p>
      <p class="text-3xl font-bold text-primary">{{ score }}/10</p>
      <p class="text-gray-500 mt-1">{{ correctCount }} de {{ questions.length }} correctes</p>
      <button @click="$emit('done', score)" class="mt-6 px-6 py-3 bg-primary text-white rounded-2xl font-semibold">
        Tornar als modes
      </button>
    </div>
    <template v-else>
      <div class="mb-3 flex justify-between">
        <button @click="emit('cancel', { current, total: questions.length })"
                class="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
          ← Sortir
        </button>
        <button @click="finished = true"
                class="flex items-center gap-1 text-xs text-orange-500 hover:text-orange-700">
          Finalitzar ✓
        </button>
      </div>
      <div class="mb-3 flex items-center justify-between text-sm text-gray-400">
        <span>Pregunta {{ current + 1 }} de {{ questions.length }}</span>
        <span class="font-semibold text-primary">{{ correctCount }} ✓</span>
      </div>
      <p class="text-base font-semibold mb-5 leading-snug">
        {{ questions[current].pregunta }}
      </p>
      <div class="space-y-3">
        <button v-for="(text, key) in questions[current].opcions" :key="key"
                :data-option="key"
                @click="answer(key)"
                :disabled="answered"
                :class="optionClass(key)"
                class="w-full text-left px-4 py-3 rounded-2xl border text-sm
                       transition-colors disabled:cursor-default font-medium">
          <span class="font-bold mr-2">{{ key }}.</span>{{ text }}
        </button>
      </div>
      <div v-if="answered" class="mt-4 p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-sm">
        {{ questions[current].explicacio }}
      </div>
      <button v-if="answered" @click="next"
              class="w-full mt-4 py-3 bg-primary text-white rounded-2xl font-semibold">
        {{ current < questions.length - 1 ? 'Següent' : 'Veure resultat' }}
      </button>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({ questions: Array, topicId: String })
const emit = defineEmits(['done', 'cancel'])

const current = ref(0)
const answered = ref(false)
const selected = ref(null)
const results = ref([])
const finished = ref(false)

const correctCount = computed(() => results.value.filter(r => r).length)
const score = computed(() => parseFloat((correctCount.value / props.questions.length * 10).toFixed(1)))
const scoreEmoji = computed(() => score.value >= 7 ? '🎉' : score.value >= 5 ? '👍' : '📚')

function answer(key) {
  if (answered.value) return
  selected.value = key
  answered.value = true
  results.value.push(key === props.questions[current.value].correcta)
}

function optionClass(key) {
  if (!answered.value) return 'border-[var(--color-border)] hover:border-primary hover:bg-primary/5'
  const isCorrect = key === props.questions[current.value].correcta
  const isSelected = key === selected.value
  if (isCorrect) return 'border-green-400 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
  if (isSelected && !isCorrect) return 'border-red-400 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
  return 'border-[var(--color-border)] opacity-50'
}

function next() {
  if (current.value < props.questions.length - 1) {
    current.value++
    answered.value = false
    selected.value = null
  } else {
    finished.value = true
  }
}
</script>
