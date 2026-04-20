<template>
  <div class="px-4 py-6 max-w-lg mx-auto">
    <!-- Resultat principal -->
    <div class="text-center mb-6">
      <div class="text-5xl font-bold mb-1"
           :class="results.passed ? 'text-green-500' : 'text-red-500'">
        {{ results.score.toFixed(1) }}
        <span class="text-2xl text-[var(--color-text-muted)]">/10</span>
      </div>
      <div class="text-lg font-semibold mb-2"
           :class="results.passed ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'">
        {{ results.passed ? '✓ APROVAT' : '✗ SUSPÈS' }}
      </div>
      <div class="text-sm text-[var(--color-text-muted)]">Temps: {{ formattedTime }}</div>

      <!-- Barra de progrés -->
      <div class="mt-3 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div class="h-full rounded-full transition-all duration-1000"
             :class="results.passed ? 'bg-green-500' : 'bg-red-500'"
             :style="{ width: `${Math.min(results.score * 10, 100)}%` }" />
      </div>
      <div class="flex justify-between text-xs text-[var(--color-text-muted)] mt-1">
        <span>0</span>
        <span class="font-medium text-amber-600">5 (mínim)</span>
        <span>10</span>
      </div>
    </div>

    <!-- Desglossament -->
    <div class="space-y-2 mb-6">
      <div class="flex items-center justify-between p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
        <span class="text-sm font-medium text-blue-800 dark:text-blue-300">🔵 Tipo test</span>
        <span class="text-sm font-bold text-blue-800 dark:text-blue-300">
          {{ results.testCorrect }}/{{ results.testTotal }} correctes
        </span>
      </div>
      <div class="flex items-center justify-between p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
        <span class="text-sm font-medium text-green-800 dark:text-green-300">🟢 Respostes breus</span>
        <span class="text-sm font-bold text-green-800 dark:text-green-300">
          {{ results.breusScore }}/{{ results.breusTotal }} punts
        </span>
      </div>
      <div class="flex items-center justify-between p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20">
        <span class="text-sm font-medium text-purple-800 dark:text-purple-300">🟣 Supòsits pràctics</span>
        <span class="text-sm font-bold text-purple-800 dark:text-purple-300">
          {{ results.supositScore }}/{{ results.supositTotal }} punts
        </span>
      </div>
    </div>

    <!-- Botons principals -->
    <div class="flex gap-3 mb-6">
      <button @click="showDetail = !showDetail"
              class="flex-1 py-2.5 rounded-lg border text-sm font-medium border-[var(--color-border)] text-[var(--color-text)]">
        {{ showDetail ? 'Amaga' : 'Veure' }} correcció
      </button>
      <button @click="$emit('new-exam')"
              class="flex-1 py-2.5 rounded-lg bg-amber-500 text-white text-sm font-bold active:scale-95 transition-all">
        Nou simulacre
      </button>
    </div>

    <!-- Correcció detallada -->
    <!-- Re-avaluar -->
<div v-if="simulacre.error" class="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-xs text-red-700 dark:text-red-300">
      ⚠️ {{ simulacre.error }}
    </div>
    <button @click="$emit('re-evaluate')"
            class="w-full mb-4 py-2 rounded-lg border border-[var(--color-border)] text-xs text-[var(--color-text-muted)] active:scale-95 transition-all">
      🔄 Tornar a avaluar respostes obertes amb IA
    </button>

    <div v-if="showDetail" class="space-y-4">
      <h3 class="font-bold text-sm text-[var(--color-text)]">Correcció detallada</h3>
      <div v-for="q in results.questions" :key="q.id" class="rounded-lg border border-[var(--color-border)] overflow-hidden">
        <div class="px-3 py-2 text-xs font-medium flex items-center gap-2"
             :class="getQuestionHeaderClass(q)">
          <span>P{{ q.id }}.</span>
          <span class="opacity-70 truncate flex-1">{{ q.tema_titol }}</span>
          <span class="shrink-0">{{ getQuestionScore(q) }}</span>
        </div>
        <div class="px-3 py-2">
          <p class="text-xs text-[var(--color-text)] mb-2">{{ q.enunciat }}</p>

          <!-- Tipo test -->
          <template v-if="q.tipus === 'test'">
            <div class="text-xs">
              <span class="font-medium">Resposta correcta: </span>
              <span class="text-green-600 dark:text-green-400 font-bold">{{ q.correcta }}) {{ q.opcions?.[q.correcta] }}</span>
            </div>
            <div v-if="results.answers[q.id] && results.answers[q.id].value !== q.correcta" class="text-xs mt-1">
              <span class="font-medium">La teva resposta: </span>
              <span class="text-red-500">{{ results.answers[q.id].value }}) {{ q.opcions?.[results.answers[q.id].value] }}</span>
            </div>
          </template>

          <!-- Breu / Supòsit -->
          <template v-else>
            <div class="text-xs mb-1">
              <span class="font-medium">La teva resposta: </span>
              <span class="italic text-[var(--color-text-muted)]">
                {{ results.answers[q.id]?.value || '(sense resposta)' }}
              </span>
            </div>
            <div v-if="results.answers[q.id]?.evaluation" class="text-xs mt-1 p-2 rounded bg-gray-50 dark:bg-gray-800">
              <div class="font-medium mb-0.5">Comentari IA:</div>
              {{ results.answers[q.id].evaluation.comentari }}
              <div v-if="results.answers[q.id].evaluation.mancances?.length" class="mt-1 text-amber-600 dark:text-amber-400">
                Faltava mencionar: {{ results.answers[q.id].evaluation.mancances.join(', ') }}
              </div>
            </div>
          </template>

          <p class="text-xs text-[var(--color-text-muted)] mt-2 italic border-t border-[var(--color-border)] pt-1">{{ q.explicacio }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSimulacreStore } from '../../stores/simulacre.js'

const props = defineProps({ results: { type: Object, required: true } })
defineEmits(['new-exam', 're-evaluate'])
const simulacre = useSimulacreStore()

const showDetail = ref(false)

const formattedTime = computed(() => {
  const t = props.results.timeTaken
  const h = Math.floor(t / 3600)
  const m = Math.floor((t % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
})

function getQuestionHeaderClass(q) {
  const ans = props.results.answers[q.id]
  if (!ans) return 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
  if (q.tipus === 'test') {
    return ans.correct
      ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
      : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
  }
  const factor = ans.evaluation?.factor ?? 0
  if (factor >= 1) return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
  if (factor >= 0.5) return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
  return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
}

function getQuestionScore(q) {
  const ans = props.results.answers[q.id]
  if (!ans || ans.points_earned === null || ans.points_earned === undefined) return '—'
  const earned = ans.points_earned
  return `${earned >= 0 ? '+' : ''}${Number(earned).toFixed(2)} pts`
}
</script>
