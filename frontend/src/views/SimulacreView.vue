<template>
  <div class="flex flex-col h-screen bg-[var(--color-bg)]">
    <!-- Navbar fixa d'examen -->
    <div class="flex items-center justify-between px-4 py-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] shrink-0">
      <div class="text-sm font-medium text-[var(--color-text)]">
        Pregunta <span class="font-bold text-primary">{{ currentIdx + 1 }}</span>/{{ simulacre.totalQuestions }}
      </div>
      <div class="flex items-center gap-2">
        <span class="text-xs px-2 py-0.5 rounded-full font-mono font-bold"
              :class="simulacre.timeRemaining < 900 ? 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400' : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'">
          ⏱ {{ formattedTime }}
        </span>
        <button @click="showIndex = true" class="text-xs text-primary underline">Índex</button>
      </div>
    </div>

    <!-- Pregunta actual -->
    <div class="flex-1 overflow-y-auto px-4 py-4">
      <div v-if="currentQ">
        <!-- Capçalera de la pregunta -->
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                :class="{
                  'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300': currentQ.tipus === 'test',
                  'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300': currentQ.tipus === 'breu',
                  'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300': currentQ.tipus === 'suposit',
                }">
            {{ { test: 'Tipus test', breu: 'Resposta breu', suposit: 'Supòsit pràctic' }[currentQ.tipus] }}
          </span>
          <span class="text-xs text-[var(--color-text-muted)]">{{ currentQ.tema_titol }}</span>
          <span class="text-xs font-medium text-amber-600 dark:text-amber-400">{{ currentQ.punts }} pts</span>
          <span class="text-xs px-1.5 py-0.5 rounded text-[var(--color-text-muted)]"
                :class="{
                  'bg-green-50 dark:bg-green-900/20': currentQ.dificultat === 'baixa',
                  'bg-yellow-50 dark:bg-yellow-900/20': currentQ.dificultat === 'mitjana',
                  'bg-red-50 dark:bg-red-900/20': currentQ.dificultat === 'alta',
                }">
            {{ currentQ.dificultat }}
          </span>
        </div>

        <!-- Enunciat -->
        <p class="text-sm font-medium text-[var(--color-text)] mb-4 leading-relaxed">{{ currentQ.enunciat }}</p>

        <!-- Opcions tipus test -->
        <div v-if="currentQ.tipus === 'test'" class="space-y-2">
          <button v-for="(text, key) in currentQ.opcions" :key="key"
                  @click="answerTest(key)"
                  :disabled="!!currentAnswer"
                  class="w-full text-left px-4 py-3 rounded-lg border text-sm transition-all"
                  :class="getOptionClass(key)">
            <span class="font-bold mr-2">{{ key }})</span>{{ text }}
          </button>

          <!-- Explicació post-resposta -->
          <div v-if="currentAnswer" class="mt-3 p-3 rounded-lg text-xs"
               :class="currentAnswer.correct ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300' : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300'">
            <span class="font-bold">{{ currentAnswer.correct ? '✓ Correcte!' : '✗ Incorrecte.' }}</span>
            {{ currentQ.explicacio }}
          </div>
        </div>

        <!-- Resposta breu o supòsit -->
        <div v-else>
          <textarea
            :value="currentAnswer?.value || ''"
            @input="answerOpen($event.target.value)"
            :placeholder="currentQ.tipus === 'suposit' ? 'Descriu el teu procediment de diagnòstic i resolució…' : 'Escriu la teva resposta (2-4 frases)…'"
            class="w-full h-36 px-3 py-2 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] resize-none focus:outline-none focus:border-primary"
          />
          <p class="text-xs text-[var(--color-text-muted)] mt-1">Resposta guardada automàticament</p>
        </div>
      </div>
    </div>

    <!-- Botons de navegació -->
    <div class="shrink-0 px-4 py-3 border-t border-[var(--color-border)] bg-[var(--color-surface)] flex gap-2">
      <button @click="prev" :disabled="currentIdx === 0"
              class="flex-1 py-2.5 rounded-lg text-sm font-medium border border-[var(--color-border)] disabled:opacity-40 active:scale-95 transition-all text-[var(--color-text)]">
        ← Anterior
      </button>
      <button v-if="currentIdx < simulacre.totalQuestions - 1" @click="next"
              class="flex-1 py-2.5 rounded-lg text-sm font-medium bg-primary text-white active:scale-95 transition-all">
        Següent →
      </button>
      <button v-else @click="confirmSubmit"
              class="flex-1 py-2.5 rounded-lg text-sm font-bold bg-amber-500 text-white active:scale-95 transition-all">
        Finalitzar
      </button>
    </div>

    <!-- Modal índex de preguntes -->
    <div v-if="showIndex" class="fixed inset-0 bg-black/50 z-50 flex items-end" @click.self="showIndex = false">
      <div class="bg-[var(--color-surface)] w-full rounded-t-2xl p-4 max-h-[60vh] overflow-y-auto">
        <h3 class="font-bold text-sm mb-3 text-[var(--color-text)]">Índex de preguntes</h3>
        <div class="grid grid-cols-8 gap-1.5">
          <button v-for="q in simulacre.questions" :key="q.id"
                  @click="goTo(q.id - 1); showIndex = false"
                  class="aspect-square rounded text-xs font-medium flex items-center justify-center transition-all"
                  :class="getIndexClass(q)">
            {{ q.id }}
          </button>
        </div>
        <div class="flex flex-wrap gap-3 mt-3 text-xs text-[var(--color-text-muted)]">
          <span><span class="inline-block w-3 h-3 rounded bg-green-400 mr-1"></span>Correcta</span>
          <span><span class="inline-block w-3 h-3 rounded bg-red-400 mr-1"></span>Incorrecta</span>
          <span><span class="inline-block w-3 h-3 rounded bg-blue-400 mr-1"></span>Resposta</span>
          <span><span class="inline-block w-3 h-3 rounded bg-gray-200 dark:bg-gray-700 mr-1"></span>Pendent</span>
        </div>
      </div>
    </div>

    <!-- Modal confirmació finalitzar -->
    <div v-if="showConfirm" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center px-6">
      <div class="bg-[var(--color-surface)] rounded-2xl p-6 w-full max-w-sm">
        <h3 class="font-bold text-base mb-2 text-[var(--color-text)]">Finalitzar examen?</h3>
        <p class="text-sm text-[var(--color-text-muted)] mb-4">
          Has respost {{ simulacre.answeredCount }}/{{ simulacre.totalQuestions }} preguntes.
          <span v-if="simulacre.answeredCount < simulacre.totalQuestions" class="text-amber-600 font-medium">
            {{ simulacre.totalQuestions - simulacre.answeredCount }} preguntes sense respondre.
          </span>
        </p>
        <div class="flex gap-3">
          <button @click="showConfirm = false" class="flex-1 py-2.5 rounded-lg border text-sm font-medium border-[var(--color-border)] text-[var(--color-text)]">Cancel·la</button>
          <button @click="doSubmit" class="flex-1 py-2.5 rounded-lg bg-amber-500 text-white text-sm font-bold">Enviar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSimulacreStore } from '../stores/simulacre.js'

const router = useRouter()
const simulacre = useSimulacreStore()

const currentIdx = ref(0)
const showIndex = ref(false)
const showConfirm = ref(false)
let timerInterval = null

const currentQ = computed(() => simulacre.questions[currentIdx.value] || null)
const currentAnswer = computed(() => currentQ.value ? simulacre.answers[currentQ.value.id] : null)

const formattedTime = computed(() => {
  const t = simulacre.timeRemaining
  const h = Math.floor(t / 3600)
  const m = Math.floor((t % 3600) / 60)
  const s = t % 60
  return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

onMounted(() => {
  if (simulacre.phase !== 'exam') {
    router.replace('/practica')
    return
  }
  timerInterval = setInterval(() => {
    simulacre.tickTimer()
    if (simulacre.timeRemaining === 0) {
      clearInterval(timerInterval)
      doSubmit()
    }
  }, 1000)
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})

function prev() { if (currentIdx.value > 0) currentIdx.value-- }
function next() { if (currentIdx.value < simulacre.totalQuestions - 1) currentIdx.value++ }
function goTo(idx) { currentIdx.value = idx }

function answerTest(key) {
  if (!currentQ.value || simulacre.answers[currentQ.value.id]) return
  simulacre.answerTest(currentQ.value.id, key)
}

function answerOpen(text) {
  if (!currentQ.value) return
  simulacre.answerOpen(currentQ.value.id, text)
}

function confirmSubmit() { showConfirm.value = true }

async function doSubmit() {
  showConfirm.value = false
  if (timerInterval) clearInterval(timerInterval)
  await simulacre.submitExam()
  if (simulacre.phase === 'results') {
    router.push('/simulacre/resultats')
  }
}

function getOptionClass(key) {
  const ans = currentAnswer.value
  if (!ans) {
    return 'border-[var(--color-border)] hover:border-primary hover:bg-primary/5 active:scale-[0.98]'
  }
  if (key === currentQ.value.correcta) return 'border-green-500 bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300'
  if (key === ans.value && !ans.correct) return 'border-red-400 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300'
  return 'border-[var(--color-border)] opacity-50'
}

function getIndexClass(q) {
  const ans = simulacre.answers[q.id]
  if (!ans) return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
  if (q.tipus === 'test') {
    return ans.correct ? 'bg-green-400 text-white' : 'bg-red-400 text-white'
  }
  return ans.value ? 'bg-blue-400 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600'
}
</script>
