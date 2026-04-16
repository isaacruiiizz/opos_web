<template>
  <div class="px-4 py-6 max-w-lg mx-auto">
    <div v-if="evaluated.length">
      <h2 class="font-bold text-lg mb-4">Resultats</h2>
      <div v-for="(r, i) in evaluated" :key="i"
           class="mb-4 p-4 rounded-2xl border border-[var(--color-border)]">
        <p class="font-semibold text-sm mb-1">{{ r.pregunta }}</p>
        <p class="text-xs text-gray-500 mb-2">La teva resposta: {{ r.resposta }}</p>
        <div class="flex items-center gap-2">
          <span :class="r.eval.puntuacio >= 7 ? 'text-green-600' : r.eval.puntuacio >= 5 ? 'text-yellow-600' : 'text-red-600'"
                class="font-bold text-lg">{{ r.eval.puntuacio }}/10</span>
          <span class="text-xs text-gray-500 flex-1">{{ r.eval.feedback }}</span>
        </div>
      </div>
      <p class="text-center font-bold text-xl mt-4 text-primary">
        Mitjana: {{ avgScore }}/10
      </p>
      <button @click="$emit('done', parseFloat(avgScore))"
              class="w-full mt-4 py-3 bg-primary text-white rounded-2xl font-semibold">
        Tornar als modes
      </button>
    </div>
    <div v-else>
      <div v-if="loading" class="text-center py-12 text-gray-400 animate-pulse">
        L'IA avalua les respostes…
      </div>
      <template v-else>
        <div class="mb-3 text-sm text-gray-400">Pregunta {{ current + 1 }} de {{ questions.length }}</div>
        <p class="font-semibold mb-3">{{ questions[current].pregunta }}</p>
        <textarea v-model="answers[current]" rows="5"
                  placeholder="Escriu la teva resposta aquí..."
                  class="w-full rounded-2xl border border-[var(--color-border)] p-3 text-sm
                         bg-[var(--color-surface)] resize-none focus:outline-none focus:border-primary" />
        <div class="flex gap-3 mt-3">
          <button v-if="current > 0" @click="current--"
                  class="px-4 py-2 rounded-xl border border-[var(--color-border)] text-sm">
            ← Anterior
          </button>
          <button v-if="current < questions.length - 1" @click="current++"
                  class="flex-1 px-4 py-3 bg-primary/10 text-primary rounded-2xl text-sm font-medium">
            Següent →
          </button>
          <button v-else @click="submitAll"
                  class="flex-1 px-4 py-3 bg-primary text-white rounded-2xl text-sm font-semibold">
            Avaluar amb IA
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { evaluateAnswer } from '../../api/client.js'

const props = defineProps({ questions: Array, topicId: String })
const emit = defineEmits(['done'])

const current = ref(0)
const answers = ref(props.questions.map(() => ''))
const evaluated = ref([])
const loading = ref(false)

const avgScore = computed(() => {
  if (!evaluated.value.length) return 0
  const sum = evaluated.value.reduce((a, r) => a + r.eval.puntuacio, 0)
  return (sum / evaluated.value.length).toFixed(1)
})

async function submitAll() {
  loading.value = true
  try {
    const evals = await Promise.all(
      props.questions.map((q, i) => {
        const ans = answers.value[i]?.trim()
        if (!ans) {
          return Promise.resolve({ puntuacio: 0, feedback: 'Sense resposta.', encerts: [], mancances: [] })
        }
        return evaluateAnswer({
          topic_id: props.topicId,
          mode: 'breus',
          pregunta: q.pregunta,
          resposta_usuari: ans,
          resposta_model: q.resposta_model || '',
        })
      })
    )
    evaluated.value = props.questions.map((q, i) => ({
      pregunta: q.pregunta,
      resposta: answers.value[i],
      eval: evals[i],
    }))
  } finally {
    loading.value = false
  }
}
</script>
