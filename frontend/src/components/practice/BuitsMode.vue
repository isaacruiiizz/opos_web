<template>
  <div class="px-4 py-6 max-w-lg mx-auto space-y-4">
    <div v-for="(s, i) in sentences" :key="i"
         class="p-3 rounded-xl border border-[var(--color-border)] space-y-2">
      <div v-if="!checked">
        <p class="text-sm text-gray-500">{{ s.frase.replace('___', '[   ]') }}</p>
        <input type="text" v-model="answers[i]"
               placeholder="Escriu aquí..."
               class="w-full mt-1 px-3 py-1.5 rounded-lg border border-[var(--color-border)]
                      text-sm bg-[var(--color-surface)] focus:outline-none focus:border-primary" />
      </div>
      <div v-else>
        <p class="text-sm" v-html="renderResult(s, answers[i])" />
        <span v-bind="i === 0 ? { 'data-result-0': '' } : {}"
              :class="isCorrect(s, answers[i]) ? 'text-green-600' : 'text-red-600'"
              class="text-xs font-semibold mt-1 block">
          <span class="inline-flex items-center gap-1">
            <svg v-if="isCorrect(s, answers[i])" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            <svg v-else width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            {{ isCorrect(s, answers[i]) ? 'Correcte' : `Correcta: ${s.paraules[0]}` }}
          </span>
        </span>
      </div>
    </div>

    <div v-if="!checked" class="flex justify-between mb-2">
      <button @click="emit('cancel', { inProgress: true })"
              class="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
        ← Sortir
      </button>
      <button @click="checked = true"
              class="flex items-center gap-1 text-xs text-orange-500 hover:text-orange-700">
        Finalitzar
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
      </button>
    </div>
    <button v-if="!checked" data-check @click="checked = true"
            class="w-full py-3 bg-primary text-white rounded-2xl font-semibold">
      Comprovar
    </button>
    <div v-else class="text-center pt-2">
      <p class="font-bold text-xl text-primary">{{ correctCount }}/{{ sentences.length }} correctes</p>
      <button @click="$emit('done', correctCount / sentences.length * 10)"
              class="mt-4 px-6 py-3 bg-primary text-white rounded-2xl font-semibold">
        Tornar als modes
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({ sentences: Array, topicId: String })
const emit = defineEmits(['done', 'cancel'])

const answers = ref(props.sentences.map(() => ''))
const checked = ref(false)

const isCorrect = (s, answer) =>
  answer?.toLowerCase().trim() === s.paraules[0]?.toLowerCase()

const correctCount = computed(() =>
  props.sentences.filter((s, i) => isCorrect(s, answers.value[i])).length
)

function renderResult(s, answer) {
  const correct = s.paraules[0]
  const right = isCorrect(s, answer)
  const colored = right
    ? `<strong class="text-green-600">${answer}</strong>`
    : `<strong class="text-red-600">${answer || '(buit)'}</strong> <span class="text-gray-400">(${correct})</span>`
  return s.frase.replace('___', colored)
}
</script>
