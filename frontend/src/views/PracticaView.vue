<template>
  <div>
    <!-- Simulacre d'Examen (sempre a dalt, independent del tema) -->
    <SimulacreCard
      :last-result="simulacre.lastResult"
      :generating="simulacre.generating"
      :has-draft="hasDraft"
      :error="simulacre.error"
      :round-state="simulacre.roundState"
      @start="startSimulacre"
    />

    <!-- Divisor -->
    <div class="flex items-center gap-3 px-4 py-2">
      <div class="flex-1 h-px bg-[var(--color-border)]"></div>
      <span class="text-xs text-[var(--color-text-muted)] font-medium">Pràctica per tema</span>
      <div class="flex-1 h-px bg-[var(--color-border)]"></div>
    </div>

    <!-- Selector de tema -->
    <div class="overflow-x-auto flex gap-2 px-4 py-2 border-b border-[var(--color-border)]">
      <button v-for="t in topics.topics" :key="t.id"
              @click="activeTopic = t.id"
              :class="activeTopic === t.id ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap">
        T{{ t.number }}
      </button>
    </div>

    <ModeSelector v-if="!activeMode"
                  :progress="modeProgress"
                  :generating="modeGenerating"
                  :ready="modeReady"
                  :errors="modeErrors"
                  @select="startMode" />
    <TestMode v-else-if="activeMode === 'test' && questions.length"
              :questions="questions" :topic-id="activeTopic"
              @done="finishSession" @cancel="cancelMode" />
    <BreusMode v-else-if="activeMode === 'breus' && questions.length"
               :questions="questions" :topic-id="activeTopic"
               @done="finishSession" @cancel="cancelMode" />
    <SupositMode v-else-if="activeMode === 'suposit' && suposit"
                 :suposit="suposit" :topic-id="activeTopic"
                 @done="finishSession" @cancel="cancelMode" />
    <ConnectaMode v-else-if="activeMode === 'connecta' && questions.length"
                  :pairs="questions" :topic-id="activeTopic"
                  @done="finishSession" @cancel="cancelMode" />
    <BuitsMode v-else-if="activeMode === 'buits' && questions.length"
               :sentences="questions" :topic-id="activeTopic"
               @done="finishSession" @cancel="cancelMode" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTopicsStore } from '../stores/topics.js'
import { usePracticeStore } from '../stores/practice.js'
import { useSimulacreStore } from '../stores/simulacre.js'
import { saveSession } from '../api/client.js'
import SimulacreCard from '../components/practice/SimulacreCard.vue'
import ModeSelector from '../components/practice/ModeSelector.vue'
import TestMode from '../components/practice/TestMode.vue'
import BreusMode from '../components/practice/BreusMode.vue'
import SupositMode from '../components/practice/SupositMode.vue'
import ConnectaMode from '../components/practice/ConnectaMode.vue'
import BuitsMode from '../components/practice/BuitsMode.vue'

const MODES = ['test', 'breus', 'suposit', 'connecta', 'buits']

const router = useRouter()
const topics = useTopicsStore()
const practice = usePracticeStore()
const simulacre = useSimulacreStore()

const activeTopic = ref(topics.activeTopicId)
const activeMode = ref(null)
const questions = ref([])
const suposit = ref(null)

const hasDraft = computed(() => {
  try {
    const raw = sessionStorage.getItem('opos_simulacre_v1')
    if (!raw) return false
    const draft = JSON.parse(raw)
    return !!(draft?.questions?.length && draft?.timeRemaining > 0)
  } catch { return false }
})

const modeGenerating = computed(() => {
  return Object.fromEntries(MODES.map(m => [m, practice.isGenerating(activeTopic.value, m)]))
})
const modeReady = computed(() => {
  return Object.fromEntries(MODES.map(m => [m, practice.isReady(activeTopic.value, m)]))
})
const modeProgress = computed(() => practice.getProgress(activeTopic.value))
const modeErrors = computed(() => {
  return Object.fromEntries(
    MODES.map(m => [m, practice.getError(activeTopic.value, m)]).filter(([, v]) => v)
  )
})

simulacre.loadLastResult()
onMounted(() => {
  simulacre.loadRoundState()
})

async function startSimulacre() {
  await simulacre.startGeneration()
  if (simulacre.phase === 'exam') {
    router.push('/simulacre')
  }
}

async function startMode(mode) {
  await practice.requestNotifications()
  practice.clearError(activeTopic.value, mode)

  const content = practice.getContent(activeTopic.value, mode)
  if (content) {
    practice.markSeen(activeTopic.value, mode)
    activeMode.value = mode
    if (mode === 'suposit') suposit.value = content
    else questions.value = content
    return
  }

  if (practice.isGenerating(activeTopic.value, mode)) return

  practice.generate(activeTopic.value, mode)
}

function cancelMode(progressObj) {
  practice.setProgress(activeTopic.value, activeMode.value, progressObj)
  activeMode.value = null
}

async function finishSession(score) {
  const mode = activeMode.value
  practice.clearContent(activeTopic.value, mode)
  practice.clearProgress(activeTopic.value, mode)
  await saveSession({
    topic_id: activeTopic.value,
    mode,
    score,
    questions_json: JSON.stringify(questions.value),
    answers_json: '[]',
    feedback_json: '{}',
  })
  topics.updateTopicProgress(activeTopic.value, score * 10)
  activeMode.value = null
  questions.value = []
  suposit.value = null
}

watch(activeTopic, () => {
  activeMode.value = null
  questions.value = []
  suposit.value = null
})
</script>
